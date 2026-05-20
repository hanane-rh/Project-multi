"""Part 3 — Inter-frame coding (P-frames).

Full-search block matching with SAD (sum of absolute differences) as the
matching cost.  Operates on the luma plane at the macroblock size declared in
`CodecConfig`; chroma motion vectors are derived by halving when 4:2:0 is on.
"""
from __future__ import annotations

import numpy as np


# --------------------------------------------------------------------------- #
#  Matching cost                                                              #
# --------------------------------------------------------------------------- #

def _sad(a: np.ndarray, b: np.ndarray) -> int:
    """Sum of absolute differences — cheap, integer-only matching cost."""
    return int(np.abs(a.astype(np.int32) - b.astype(np.int32)).sum())


# --------------------------------------------------------------------------- #
#  Block matching                                                             #
# --------------------------------------------------------------------------- #

def estimate(
    current: np.ndarray,
    reference: np.ndarray,
    macroblock: int,
    search_range: int,
) -> np.ndarray:
    """Full-search motion estimation.

    Returns an int16 motion-vector field of shape (rows, cols, 2) — last axis
    is (dy, dx) in pixel units, where rows = H/MB and cols = W/MB.
    """
    h, w = current.shape
    rows, cols = h // macroblock, w // macroblock
    motion = np.zeros((rows, cols, 2), dtype=np.int16)

    # Pad the reference once so the search window never falls off the edges.
    pad = search_range
    ref = np.pad(reference, pad, mode="edge")

    for by in range(rows):
        for bx in range(cols):
            y0 = by * macroblock
            x0 = bx * macroblock
            block = current[y0:y0 + macroblock, x0:x0 + macroblock]
            best_cost = float("inf")
            best = (0, 0)
            for dy in range(-search_range, search_range + 1):
                for dx in range(-search_range, search_range + 1):
                    cand = ref[
                        y0 + dy + pad : y0 + dy + pad + macroblock,
                        x0 + dx + pad : x0 + dx + pad + macroblock,
                    ]
                    cost = _sad(block, cand)
                    if cost < best_cost:
                        best_cost = cost
                        best = (dy, dx)
            motion[by, bx] = best
    return motion


def compensate(
    reference: np.ndarray,
    motion: np.ndarray,
    macroblock: int,
) -> np.ndarray:
    """Build the motion-compensated prediction from `reference` and `motion`."""
    h, w = reference.shape
    rows, cols, _ = motion.shape
    pad = int(np.max(np.abs(motion))) if motion.size else 0
    ref = np.pad(reference, pad, mode="edge")
    pred = np.zeros_like(reference)
    for by in range(rows):
        for bx in range(cols):
            dy, dx = motion[by, bx]
            y0 = by * macroblock
            x0 = bx * macroblock
            pred[y0:y0 + macroblock, x0:x0 + macroblock] = ref[
                y0 + int(dy) + pad : y0 + int(dy) + pad + macroblock,
                x0 + int(dx) + pad : x0 + int(dx) + pad + macroblock,
            ]
    return pred


def scale_for_chroma(motion: np.ndarray) -> np.ndarray:
    """Halve motion vectors for 4:2:0 chroma planes (integer division)."""
    return (motion // 2).astype(np.int16)
