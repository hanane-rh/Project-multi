"""Top-level Encoder/Decoder — orchestrates the four pipeline stages.

Encode flow:

    BGR ──preprocess.to_ycbcr──► YCbCr ──preprocess.split──► (Y, Cb, Cr)
        ├─ I-frame:  each plane → intra.encode_plane     → quantised + reference
        └─ P-frame:  Y → inter.estimate(prev_Y)          → motion vectors
                     each plane − compensated_prediction → residual
                     residual → intra.encode_residual    → quantised + reference

Decode flow is the formal inverse.  Both sides share the same `CodecConfig`
and the same scaled Q-tables (`QuantTables.for_quality`).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from .config import CodecConfig, QuantTables
from .io.bitstream import Bitstream, FrameRecord
from .pipeline import inter, intra, preprocess


# --------------------------------------------------------------------------- #
#  Encoder                                                                    #
# --------------------------------------------------------------------------- #

class Encoder:
    """Stateful encoder.  Feed frames in arrival order, then `finalise()`."""

    def __init__(self, config: CodecConfig):
        self.config = config
        self._tables = QuantTables.for_quality(config.quality_factor)
        self._records: list[FrameRecord] = []
        self._prev: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None
        self._frame_shape: tuple[int, int] | None = None
        self._chroma_shape: tuple[int, int] | None = None
        self._frame_idx = 0

    # -- public ------------------------------------------------------------- #

    def push(self, bgr: np.ndarray) -> None:
        """Encode a single BGR frame."""
        ycbcr = preprocess.to_ycbcr(bgr)
        y, cb, cr = preprocess.split(ycbcr, self.config.chroma_subsample)
        if self._frame_shape is None:
            self._frame_shape = y.shape
            self._chroma_shape = cb.shape

        # Pad once for the encode pass; the decoder crops back on output.
        mb = self.config.macroblock_size
        bs = self.config.dct_block_size
        y_p  = preprocess.pad_to_multiple(y,  mb)
        cb_p = preprocess.pad_to_multiple(cb, bs)
        cr_p = preprocess.pad_to_multiple(cr, bs)

        is_i = (self._frame_idx % self.config.gop_size) == 0 or self._prev is None
        if is_i:
            record, recon = self._encode_intra(y_p, cb_p, cr_p)
        else:
            record, recon = self._encode_inter(y_p, cb_p, cr_p)

        self._records.append(record)
        self._prev = recon
        self._frame_idx += 1

    def push_many(self, frames: Iterable[np.ndarray]) -> None:
        for f in frames:
            self.push(f)

    def finalise(self) -> Bitstream:
        if self._frame_shape is None:
            raise RuntimeError("No frames pushed")
        return Bitstream(
            config=self.config,
            frame_shape=self._frame_shape,
            chroma_shape=self._chroma_shape or self._frame_shape,
            frames=self._records,
        )

    # -- private ------------------------------------------------------------ #

    def _encode_intra(
        self,
        y: np.ndarray, cb: np.ndarray, cr: np.ndarray,
    ) -> tuple[FrameRecord, tuple[np.ndarray, np.ndarray, np.ndarray]]:
        y_q,  y_r  = intra.encode_plane(y,  self._tables.luma,   self.config.dct_block_size)
        cb_q, cb_r = intra.encode_plane(cb, self._tables.chroma, self.config.dct_block_size)
        cr_q, cr_r = intra.encode_plane(cr, self._tables.chroma, self.config.dct_block_size)
        return (
            FrameRecord(kind="I", luma_q=y_q, chroma_b_q=cb_q, chroma_r_q=cr_q),
            (y_r, cb_r, cr_r),
        )

    def _encode_inter(
        self,
        y: np.ndarray, cb: np.ndarray, cr: np.ndarray,
    ) -> tuple[FrameRecord, tuple[np.ndarray, np.ndarray, np.ndarray]]:
        assert self._prev is not None
        prev_y, prev_cb, prev_cr = self._prev

        # Luma motion estimation.
        mv = inter.estimate(
            current=y.astype(np.uint8),
            reference=prev_y.astype(np.uint8),
            macroblock=self.config.macroblock_size,
            search_range=self.config.search_range,
        )
        pred_y = inter.compensate(prev_y, mv, self.config.macroblock_size)
        y_q, y_res_recon = intra.encode_residual(
            y.astype(np.float32) - pred_y.astype(np.float32),
            self._tables.luma,
            self.config.dct_block_size,
        )
        recon_y = np.clip(pred_y + y_res_recon, 0.0, 255.0)

        # Chroma — reuse the luma motion vectors, halved when 4:2:0.
        if self.config.chroma_subsample:
            mv_c = inter.scale_for_chroma(mv)
            mb_c = self.config.macroblock_size // 2
        else:
            mv_c = mv
            mb_c = self.config.macroblock_size

        pred_cb = inter.compensate(prev_cb, mv_c, mb_c)
        pred_cr = inter.compensate(prev_cr, mv_c, mb_c)
        cb_q, cb_res_recon = intra.encode_residual(
            cb.astype(np.float32) - pred_cb.astype(np.float32),
            self._tables.chroma,
            self.config.dct_block_size,
        )
        cr_q, cr_res_recon = intra.encode_residual(
            cr.astype(np.float32) - pred_cr.astype(np.float32),
            self._tables.chroma,
            self.config.dct_block_size,
        )
        recon_cb = np.clip(pred_cb + cb_res_recon, 0.0, 255.0)
        recon_cr = np.clip(pred_cr + cr_res_recon, 0.0, 255.0)

        return (
            FrameRecord(
                kind="P",
                luma_q=y_q, chroma_b_q=cb_q, chroma_r_q=cr_q,
                motion=mv,
            ),
            (recon_y, recon_cb, recon_cr),
        )


# --------------------------------------------------------------------------- #
#  Decoder                                                                    #
# --------------------------------------------------------------------------- #

class Decoder:
    """Stateful decoder.  Construct from a `Bitstream`, call `decode_all()`."""

    def __init__(self, stream: Bitstream):
        self.stream = stream
        self.config = stream.config
        self._tables = QuantTables.for_quality(self.config.quality_factor)
        self._prev: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None

    # -- public ------------------------------------------------------------- #

    def decode_all(self) -> list[np.ndarray]:
        """Return every frame as an HxWx3 BGR uint8 image (original size)."""
        out: list[np.ndarray] = []
        for rec in self.stream.frames:
            y, cb, cr = self._decode_one(rec)
            self._prev = (y, cb, cr)
            ycbcr = preprocess.merge(y, cb, cr, self.config.chroma_subsample)
            bgr = preprocess.to_bgr(ycbcr)
            out.append(preprocess.crop(bgr, self.stream.frame_shape))
        return out

    # -- private ------------------------------------------------------------ #

    def _padded_shapes(self) -> tuple[tuple[int, int], tuple[int, int]]:
        mb = self.config.macroblock_size
        bs = self.config.dct_block_size
        fh, fw = self.stream.frame_shape
        ch, cw = self.stream.chroma_shape
        luma = (((fh + mb - 1) // mb) * mb, ((fw + mb - 1) // mb) * mb)
        chroma = (((ch + bs - 1) // bs) * bs, ((cw + bs - 1) // bs) * bs)
        return luma, chroma

    def _decode_one(
        self, rec: FrameRecord,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        luma_hw, chroma_hw = self._padded_shapes()
        bs = self.config.dct_block_size

        if rec.kind == "I":
            y  = intra.decode_plane(rec.luma_q,     self._tables.luma,   luma_hw,   bs)
            cb = intra.decode_plane(rec.chroma_b_q, self._tables.chroma, chroma_hw, bs)
            cr = intra.decode_plane(rec.chroma_r_q, self._tables.chroma, chroma_hw, bs)
            return y, cb, cr

        if self._prev is None:
            raise RuntimeError("Encountered P-frame before any I-frame")
        prev_y, prev_cb, prev_cr = self._prev
        if rec.motion is None:
            raise RuntimeError("P-frame is missing its motion field")

        pred_y = inter.compensate(prev_y, rec.motion, self.config.macroblock_size)
        y = np.clip(
            pred_y + intra.decode_residual(rec.luma_q, self._tables.luma, luma_hw, bs),
            0.0, 255.0,
        )

        if self.config.chroma_subsample:
            mv_c = inter.scale_for_chroma(rec.motion)
            mb_c = self.config.macroblock_size // 2
        else:
            mv_c = rec.motion
            mb_c = self.config.macroblock_size

        pred_cb = inter.compensate(prev_cb, mv_c, mb_c)
        pred_cr = inter.compensate(prev_cr, mv_c, mb_c)
        cb = np.clip(
            pred_cb + intra.decode_residual(rec.chroma_b_q, self._tables.chroma, chroma_hw, bs),
            0.0, 255.0,
        )
        cr = np.clip(
            pred_cr + intra.decode_residual(rec.chroma_r_q, self._tables.chroma, chroma_hw, bs),
            0.0, 255.0,
        )
        return y, cb, cr
