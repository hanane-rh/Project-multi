"""Sweep the two parameters demanded by the brief and plot the curves.

Produces a single 3-panel figure:
    * compression ratio vs quality factor   (GOP = 8)
    * compression ratio vs GOP size         (QF  = 50)
    * mean PSNR     vs quality factor       (GOP = 8)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from mpeg4mini import CodecConfig, Decoder, Encoder
from mpeg4mini.io import load_frame_sequence, write_bitstream, read_bitstream
from mpeg4mini.metrics import original_size, psnr_db


_QF_GRID  = [10, 20, 30, 50, 70, 85, 95]
_GOP_GRID = [1, 2, 4, 8, 12, 16]


# --------------------------------------------------------------------------- #

def _encode_to_temp(frames, cfg: CodecConfig) -> tuple[int, list[np.ndarray]]:
    enc = Encoder(cfg)
    enc.push_many(frames)
    stream = enc.finalise()
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        nbytes = write_bitstream(stream, f.name)
        path = f.name
    recon = Decoder(read_bitstream(path)).decode_all()
    Path(path).unlink(missing_ok=True)
    return nbytes, recon


def _mean_psnr(refs, recons) -> float:
    vals = [psnr_db(r, c) for r, c in zip(refs, recons) if np.isfinite(psnr_db(r, c))]
    return float(np.mean(vals)) if vals else float("inf")


# --------------------------------------------------------------------------- #

def run_and_plot(frames_dir: str | Path, output_path: str | Path) -> Path:
    frames = load_frame_sequence(frames_dir)
    raw = original_size(frames)

    ratio_qf, psnr_qf = [], []
    for qf in _QF_GRID:
        nbytes, recon = _encode_to_temp(frames, CodecConfig(quality_factor=qf, gop_size=8))
        ratio_qf.append(raw / nbytes)
        psnr_qf.append(_mean_psnr(frames, recon))

    ratio_gop = []
    for g in _GOP_GRID:
        nbytes, _ = _encode_to_temp(frames, CodecConfig(gop_size=g, quality_factor=50))
        ratio_gop.append(raw / nbytes)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), dpi=110)
    fig.suptitle("mpeg4mini — parameter sweeps", fontsize=14, fontweight="bold")

    axes[0].plot(_QF_GRID, ratio_qf, "o-", color="#1f77b4", linewidth=2)
    axes[0].set_xlabel("Quality factor")
    axes[0].set_ylabel("Compression ratio")
    axes[0].set_title("Ratio vs QF  (GOP = 8)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(_GOP_GRID, ratio_gop, "s-", color="#d62728", linewidth=2)
    axes[1].set_xlabel("GOP size")
    axes[1].set_ylabel("Compression ratio")
    axes[1].set_title("Ratio vs GOP  (QF = 50)")
    axes[1].grid(alpha=0.3)

    axes[2].plot(_QF_GRID, psnr_qf, "^-", color="#2ca02c", linewidth=2)
    axes[2].set_xlabel("Quality factor")
    axes[2].set_ylabel("Mean PSNR (dB)")
    axes[2].set_title("Quality vs QF  (GOP = 8)")
    axes[2].grid(alpha=0.3)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=110)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("frames", type=Path)
    p.add_argument("-o", "--out", type=Path,
                   default=HERE.parent / "figures" / "experiments.png")
    a = p.parse_args()
    out = run_and_plot(a.frames, a.out)
    print(f"Wrote {out}")
