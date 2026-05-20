"""Part 1 — Pre-processing.

BGR ↔ YCbCr conversion (ITU-R BT.601) and 4:2:0 chroma subsampling.
"""
from __future__ import annotations

import numpy as np


# ITU-R BT.601 transform, expressed for BGR ordering (OpenCV convention).
#   Y  =  0.299 R + 0.587 G + 0.114 B
#   Cb =  0.500 B − 0.331264 G − 0.168736 R + 128
#   Cr =  0.500 R − 0.418688 G − 0.081312 B + 128
_M_BGR_TO_YCBCR = np.array([
    [ 0.114,    0.587,     0.299    ],
    [ 0.5,     -0.331264, -0.168736 ],
    [-0.081312, -0.418688,  0.5     ],
], dtype=np.float32)

_M_YCBCR_TO_BGR = np.linalg.inv(_M_BGR_TO_YCBCR).astype(np.float32)


# --------------------------------------------------------------------------- #
#  Colour space                                                               #
# --------------------------------------------------------------------------- #

def to_ycbcr(bgr: np.ndarray) -> np.ndarray:
    """Convert an HxWx3 BGR uint8 image to a float32 YCbCr image (chroma+128)."""
    img = bgr.astype(np.float32)
    out = img @ _M_BGR_TO_YCBCR.T
    out[..., 1] += 128.0
    out[..., 2] += 128.0
    return out


def to_bgr(ycbcr: np.ndarray) -> np.ndarray:
    """Inverse of `to_ycbcr`.  Returns uint8 BGR clipped to [0, 255]."""
    centred = ycbcr.astype(np.float32).copy()
    centred[..., 1] -= 128.0
    centred[..., 2] -= 128.0
    bgr = centred @ _M_YCBCR_TO_BGR.T
    return np.clip(bgr, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
#  Chroma subsampling — 4:2:0                                                 #
# --------------------------------------------------------------------------- #

def chroma_down(plane: np.ndarray) -> np.ndarray:
    """4:2:0 box-filter downsample of a single chroma plane."""
    h, w = plane.shape
    h2, w2 = (h // 2) * 2, (w // 2) * 2
    box = plane[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2)
    return box.mean(axis=(1, 3))


def chroma_up(plane: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    """Nearest-neighbour upsample to (h, w)."""
    up = np.repeat(np.repeat(plane, 2, axis=0), 2, axis=1)
    th, tw = target_hw
    return up[:th, :tw]


def split(
    ycbcr: np.ndarray,
    subsample: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (Y, Cb, Cr); chroma planes are halved when `subsample=True`."""
    y, cb, cr = ycbcr[..., 0], ycbcr[..., 1], ycbcr[..., 2]
    if subsample:
        cb = chroma_down(cb)
        cr = chroma_down(cr)
    return y, cb, cr


def merge(
    y: np.ndarray,
    cb: np.ndarray,
    cr: np.ndarray,
    subsample: bool,
) -> np.ndarray:
    """Inverse of `split` — produces an HxWx3 YCbCr image."""
    if subsample:
        cb = chroma_up(cb, y.shape)
        cr = chroma_up(cr, y.shape)
    return np.stack([y, cb, cr], axis=-1)


# --------------------------------------------------------------------------- #
#  Padding helpers — used by both intra and inter stages                      #
# --------------------------------------------------------------------------- #

def pad_to_multiple(plane: np.ndarray, multiple: int) -> np.ndarray:
    """Edge-pad a 2D plane up to a multiple of `multiple` on both axes."""
    h, w = plane.shape
    pad_h = (-h) % multiple
    pad_w = (-w) % multiple
    if pad_h == 0 and pad_w == 0:
        return plane
    return np.pad(plane, ((0, pad_h), (0, pad_w)), mode="edge")


def crop(plane: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    """Inverse of pad_to_multiple — strip the padding rows/columns."""
    h, w = target_hw
    return plane[:h, :w]
