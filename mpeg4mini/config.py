"""Codec configuration and the standard JPEG quantisation tables.

`CodecConfig` is the single dataclass that flows through every stage of the
pipeline.  The luminance and chrominance Q-tables come from Annex K of the
JPEG (ITU-T T.81) standard; `scaled_quant_table` applies the libjpeg
quality-factor scaling so the same table works at any QF in [1, 100].
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np


# --------------------------------------------------------------------------- #
#  Standard JPEG quantisation tables (ITU-T T.81 Annex K)                     #
# --------------------------------------------------------------------------- #

LUMA_QUANT_TABLE: Final[np.ndarray] = np.array([
    [16, 11, 10, 16,  24,  40,  51,  61],
    [12, 12, 14, 19,  26,  58,  60,  55],
    [14, 13, 16, 24,  40,  57,  69,  56],
    [14, 17, 22, 29,  51,  87,  80,  62],
    [18, 22, 37, 56,  68, 109, 103,  77],
    [24, 35, 55, 64,  81, 104, 113,  92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103,  99],
], dtype=np.float32)

CHROMA_QUANT_TABLE: Final[np.ndarray] = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
], dtype=np.float32)


# --------------------------------------------------------------------------- #
#  Configuration                                                              #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class CodecConfig:
    """All tunable parameters for one encode/decode session."""

    gop_size: int = 8                  # one I-frame every `gop_size` frames
    quality_factor: int = 50           # 1..100, higher → better quality
    dct_block_size: int = 8            # DCT tile (Part 2)
    macroblock_size: int = 16          # motion-estimation tile (Part 3)
    search_range: int = 8              # ±S pixel window for block matching
    chroma_subsample: bool = True      # 4:2:0 if True, 4:4:4 otherwise

    def __post_init__(self) -> None:
        if not 1 <= self.quality_factor <= 100:
            raise ValueError("quality_factor must lie in [1, 100]")
        if self.gop_size < 1:
            raise ValueError("gop_size must be ≥ 1")
        if self.macroblock_size % self.dct_block_size:
            raise ValueError(
                "macroblock_size must be a multiple of dct_block_size"
            )
        if self.search_range < 0:
            raise ValueError("search_range must be ≥ 0")


# --------------------------------------------------------------------------- #
#  Quality-factor scaling (libjpeg convention)                                #
# --------------------------------------------------------------------------- #

def scaled_quant_table(base: np.ndarray, quality_factor: int) -> np.ndarray:
    """Scale a JPEG base table by a quality factor in [1, 100].

    Higher QF → smaller table values → less aggressive quantisation.
    """
    qf = int(np.clip(quality_factor, 1, 100))
    scale = 5000.0 / qf if qf < 50 else 200.0 - 2.0 * qf
    scaled = np.floor((base * scale + 50.0) / 100.0)
    return np.clip(scaled, 1, 255).astype(np.int32)


@dataclass(frozen=True)
class QuantTables:
    """The two scaled Q-tables actually used at runtime."""
    luma: np.ndarray
    chroma: np.ndarray

    @classmethod
    def for_quality(cls, qf: int) -> "QuantTables":
        return cls(
            luma=scaled_quant_table(LUMA_QUANT_TABLE, qf),
            chroma=scaled_quant_table(CHROMA_QUANT_TABLE, qf),
        )
