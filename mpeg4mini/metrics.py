"""Part 5a — quality metrics (PSNR + frame-type breakdown + compression ratio)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


# --------------------------------------------------------------------------- #
#  Reports                                                                    #
# --------------------------------------------------------------------------- #

@dataclass
class FrameStats:
    index: int
    kind: str           # "I" or "P"
    psnr_db: float


@dataclass
class StreamStats:
    original_bytes: int
    compressed_bytes: int
    num_i_frames: int
    num_p_frames: int
    per_frame: list[FrameStats]

    @property
    def compression_ratio(self) -> float:
        if self.compressed_bytes == 0:
            return float("inf")
        return self.original_bytes / self.compressed_bytes

    @property
    def mean_psnr_db(self) -> float:
        finite = [f.psnr_db for f in self.per_frame if np.isfinite(f.psnr_db)]
        return float(np.mean(finite)) if finite else float("inf")


# --------------------------------------------------------------------------- #
#  Metrics                                                                    #
# --------------------------------------------------------------------------- #

def psnr_db(reference: np.ndarray, reconstruction: np.ndarray) -> float:
    """Peak signal-to-noise ratio in dB (assumes 8-bit input)."""
    ref = reference.astype(np.float64)
    rec = reconstruction.astype(np.float64)
    mse = float(np.mean((ref - rec) ** 2))
    if mse == 0:
        return float("inf")
    return 20.0 * np.log10(255.0) - 10.0 * np.log10(mse)


def file_size(path: str | Path) -> int:
    return Path(path).stat().st_size


def original_size(frames: list[np.ndarray]) -> int:
    """Sum of raw 8-bit BGR bytes — the denominator for compression ratio."""
    return sum(f.nbytes for f in frames)
