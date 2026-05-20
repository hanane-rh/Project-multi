"""Part 2 — Intra-frame coding.

Forward path:   plane − 128 → 8×8 DCT-II → quantise → int16 coefficients.
Inverse path:   int16 coefficients → dequantise → 8×8 IDCT → plane + 128.

Single-plane in / single-plane out — applies to Y, Cb and Cr alike.  The
higher-level codec decides which Q-table to pass for each plane.
"""
from __future__ import annotations

import numpy as np
from scipy.fft import dctn, idctn


# --------------------------------------------------------------------------- #
#  Block tiling                                                               #
# --------------------------------------------------------------------------- #

def tile(plane: np.ndarray, block: int) -> np.ndarray:
    """Reshape an HxW plane into (rows*cols, block, block) tiles."""
    h, w = plane.shape
    if h % block or w % block:
        raise ValueError(f"plane shape {plane.shape} not divisible by {block}")
    rows, cols = h // block, w // block
    return (
        plane.reshape(rows, block, cols, block)
             .transpose(0, 2, 1, 3)
             .reshape(rows * cols, block, block)
    )


def untile(blocks: np.ndarray, hw: tuple[int, int], block: int) -> np.ndarray:
    """Inverse of `tile`."""
    h, w = hw
    rows, cols = h // block, w // block
    return (
        blocks.reshape(rows, cols, block, block)
              .transpose(0, 2, 1, 3)
              .reshape(h, w)
    )


# --------------------------------------------------------------------------- #
#  DCT + quantisation, fused                                                  #
# --------------------------------------------------------------------------- #

def encode_plane(
    plane: np.ndarray,
    q_table: np.ndarray,
    block: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """Forward intra path.

    Returns `(quantised, reconstructed)`:
      * `quantised`     — int16, shape (N, block, block); what gets stored.
      * `reconstructed` — float32 plane, shape (H, W); needed as a reference
                          for subsequent P-frames.
    """
    centred = plane.astype(np.float32) - 128.0
    blocks = tile(centred, block)
    coeffs = dctn(blocks, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    quant = np.round(coeffs / q_table[None, :, :]).astype(np.int16)

    # Inverse path on the encoder side so we have a reference reconstruction.
    dequant = quant.astype(np.float32) * q_table[None, :, :]
    recon_blocks = idctn(dequant, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    recon = untile(recon_blocks, plane.shape, block) + 128.0
    return quant, np.clip(recon, 0.0, 255.0)


def decode_plane(
    quant: np.ndarray,
    q_table: np.ndarray,
    plane_hw: tuple[int, int],
    block: int = 8,
) -> np.ndarray:
    """Inverse intra path (decoder side)."""
    dequant = quant.astype(np.float32) * q_table[None, :, :]
    recon_blocks = idctn(dequant, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    plane = untile(recon_blocks, plane_hw, block) + 128.0
    return np.clip(plane, 0.0, 255.0)


# --------------------------------------------------------------------------- #
#  Residual variant (zero-mean — used by Part 3 / inter)                      #
# --------------------------------------------------------------------------- #

def encode_residual(
    residual: np.ndarray,
    q_table: np.ndarray,
    block: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """Same as `encode_plane` but on already-zero-mean data (no ±128 shift)."""
    blocks = tile(residual.astype(np.float32), block)
    coeffs = dctn(blocks, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    quant = np.round(coeffs / q_table[None, :, :]).astype(np.int16)

    dequant = quant.astype(np.float32) * q_table[None, :, :]
    recon_blocks = idctn(dequant, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    recon = untile(recon_blocks, residual.shape, block)
    return quant, recon


def decode_residual(
    quant: np.ndarray,
    q_table: np.ndarray,
    plane_hw: tuple[int, int],
    block: int = 8,
) -> np.ndarray:
    """Inverse residual path (decoder side)."""
    dequant = quant.astype(np.float32) * q_table[None, :, :]
    recon_blocks = idctn(dequant, type=2, norm="ortho", axes=(-2, -1)).astype(np.float32)
    return untile(recon_blocks, plane_hw, block)
