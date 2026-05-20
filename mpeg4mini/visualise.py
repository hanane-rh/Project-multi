"""Part 5b — single matplotlib figure visualising every pipeline stage.

Stages depicted (one row each):
    1. Original frames                    — input sequence (up to 5 frames)
    2. Color space                        — Y / Cb / Cr planes of frame 0
    3. DCT & Quantisation                 — raw 8×8 block, DCT, Q, recon, Q-table
    4. Motion vectors + Residual map      — overlay on a P-frame, plus residual
    5. Reconstructed frames               — decoded output sequence
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.fft import dctn

from .codec import Decoder
from .config import QuantTables
from .io.bitstream import Bitstream
from .pipeline import inter, preprocess


# ----- styling ------------------------------------------------------------- #
_TITLE = {"fontsize": 11, "fontweight": "bold", "color": "#222"}
_LABEL = {"fontsize":  9, "color": "#444"}


def _imshow(ax, img, *, gray: bool = False, **kw):
    if gray:
        ax.imshow(img, cmap="gray", **kw)
    else:
        # OpenCV gives BGR — convert before display.
        if img.ndim == 3:
            img = img[..., ::-1]
        ax.imshow(img, **kw)
    ax.set_xticks([]); ax.set_yticks([])


# --------------------------------------------------------------------------- #

def render(
    originals: list[np.ndarray],
    stream: Bitstream,
    output_path: str | Path,
    *,
    max_strip: int = 5,
) -> Path:
    """Render the pipeline figure and save it as a PNG."""
    output_path = Path(output_path)
    decoded = Decoder(stream).decode_all()
    n = len(originals)

    # Pick frames for the strip: 5 evenly spaced, including first and last.
    strip_idx = (
        list(range(n)) if n <= max_strip
        else [int(round(i)) for i in np.linspace(0, n - 1, max_strip)]
    )

    fig = plt.figure(figsize=(15, 14), dpi=110)
    fig.suptitle(
        "MPEG-4-mini — pipeline visualisation",
        fontsize=15, fontweight="bold", y=0.995,
    )
    gs = fig.add_gridspec(
        5, max_strip,
        height_ratios=[1.0, 1.0, 1.0, 1.0, 1.0],
        hspace=0.45, wspace=0.18,
    )

    # ---------------------------------------------------------- Row 1 — input
    for col, idx in enumerate(strip_idx):
        ax = fig.add_subplot(gs[0, col])
        _imshow(ax, originals[idx])
        ax.set_title(f"Frame {idx}", **_LABEL)
    fig.text(0.005, 0.91, "1. Original", **_TITLE, rotation=90, va="center")

    # ----------------------------------------------------- Row 2 — color planes
    ycbcr = preprocess.to_ycbcr(originals[0])
    for col, (plane, name) in enumerate(zip(
        [ycbcr[..., 0], ycbcr[..., 1], ycbcr[..., 2]],
        ["Y (luma)", "Cb", "Cr"],
    )):
        ax = fig.add_subplot(gs[1, col])
        _imshow(ax, plane, gray=True)
        ax.set_title(name, **_LABEL)
    fig.text(0.005, 0.71, "2. Color space", **_TITLE, rotation=90, va="center")

    # ------------------------------------------------ Row 3 — single 8×8 block
    y_plane = ycbcr[..., 0]
    by, bx = y_plane.shape[0] // 2 & ~7, y_plane.shape[1] // 2 & ~7
    block = y_plane[by:by + 8, bx:bx + 8].astype(np.float32) - 128.0
    coeffs = dctn(block, type=2, norm="ortho")
    tables = QuantTables.for_quality(stream.config.quality_factor)
    q = np.round(coeffs / tables.luma).astype(np.int16)
    deq = q.astype(np.float32) * tables.luma
    from scipy.fft import idctn
    recon = idctn(deq, type=2, norm="ortho") + 128.0

    panels = [
        (block + 128.0, "raw 8×8",       "gray"),
        (np.log(np.abs(coeffs) + 1),    "|DCT| (log)", "viridis"),
        (q,                              "quantised",  "coolwarm"),
        (recon,                          "reconstr.",  "gray"),
        (tables.luma,                    "Q-table (luma)", "magma"),
    ]
    for col, (img, name, cmap) in enumerate(panels):
        ax = fig.add_subplot(gs[2, col])
        im = ax.imshow(img, cmap=cmap)
        ax.set_title(name, **_LABEL)
        ax.set_xticks([]); ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    fig.text(0.005, 0.51, "3. DCT & Quant", **_TITLE, rotation=90, va="center")

    # ------------------------------ Row 4 — motion vectors + residual map (P-frame)
    p_idx = next(
        (i for i, rec in enumerate(stream.frames) if rec.kind == "P"), None,
    )
    if p_idx is not None:
        mv = stream.frames[p_idx].motion
        ref = originals[p_idx - 1]
        cur = originals[p_idx]
        rec_cur = decoded[p_idx]

        ax = fig.add_subplot(gs[3, 0:3])
        _imshow(ax, cur)
        mb = stream.config.macroblock_size
        rows, cols, _ = mv.shape
        xs = np.arange(cols) * mb + mb / 2
        ys = np.arange(rows) * mb + mb / 2
        X, Y = np.meshgrid(xs, ys)
        # Skip nearly-zero motion to declutter; show non-zero MVs prominently.
        mag = np.hypot(mv[..., 0], mv[..., 1])
        keep = mag > 0.5
        ax.quiver(
            X[keep], Y[keep],
            mv[..., 1][keep], -mv[..., 0][keep],    # flip dy: image y grows down
            color="#00ffd5", angles="xy", scale_units="xy", scale=0.5,
            width=0.008, headwidth=5, headlength=4,
            edgecolor="black", linewidth=0.8,
        )
        # Also dot every macroblock center so the lattice is visible.
        ax.scatter(X, Y, s=4, c="white", alpha=0.4)
        ax.set_title(f"Motion vectors  —  P-frame {p_idx}", **_LABEL)

        residual = (cur.astype(np.int16) - rec_cur.astype(np.int16)).mean(axis=-1)
        vmax = float(np.percentile(np.abs(residual), 99) + 1e-6)
        ax = fig.add_subplot(gs[3, 3:5])
        im = ax.imshow(residual, cmap="seismic", vmin=-vmax, vmax=vmax)
        ax.set_title(f"Residual map  —  P-frame {p_idx}", **_LABEL)
        ax.set_xticks([]); ax.set_yticks([])
        fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    fig.text(0.005, 0.31, "4. Motion + Residual", **_TITLE, rotation=90, va="center")

    # ------------------------------------------------- Row 5 — reconstructions
    for col, idx in enumerate(strip_idx):
        ax = fig.add_subplot(gs[4, col])
        _imshow(ax, decoded[idx])
        kind = stream.frames[idx].kind
        ax.set_title(f"Frame {idx}  ({kind})", **_LABEL)
    fig.text(0.005, 0.11, "5. Reconstructed", **_TITLE, rotation=90, va="center")

    fig.subplots_adjust(left=0.04, right=0.99, top=0.965, bottom=0.02)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=110)
    plt.close(fig)
    return output_path
