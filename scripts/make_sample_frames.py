"""Generate a synthetic test clip with enough visual content to make every
pipeline stage interesting:

  * A textured background (sinusoidal grating) — exercises the DCT.
  * A coloured, textured "puck" that translates with constant velocity
    and rotates slowly — exercises motion estimation.
  * A bright vertical stripe pattern — accentuates motion residuals.
  * Mild Gaussian noise — breaks perfect prediction.

Default output: 12 frames at 192×144 (PAL-ish small footprint).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
#  Scene synthesis                                                            #
# --------------------------------------------------------------------------- #

def _background(h: int, w: int, frame_idx: int) -> np.ndarray:
    """Static sinusoidal grating with a slow brightness drift."""
    xs = np.arange(w, dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys)
    # Two crossed sinusoids → checker-like texture.
    grating = (
        0.5 + 0.25 * np.sin(2 * np.pi * X / 32.0)
            + 0.25 * np.sin(2 * np.pi * Y / 24.0)
    )
    drift = 0.05 * np.sin(2 * np.pi * frame_idx / 24.0)
    bgr = np.stack([
        (grating * 110 + 80 + 30 * drift),                    # B
        (grating * 130 + 70 + 30 * drift),                    # G
        (grating * 160 + 50 + 30 * drift),                    # R
    ], axis=-1)
    return np.clip(bgr, 0, 255).astype(np.uint8)


def _puck(canvas: np.ndarray, cx: int, cy: int, angle_deg: float) -> None:
    """Composite a textured rotating disc on the canvas (in place)."""
    h, w = canvas.shape[:2]
    radius = 20
    y0, y1 = max(0, cy - radius), min(h, cy + radius)
    x0, x1 = max(0, cx - radius), min(w, cx + radius)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dy = yy - cy
    dx = xx - cx
    inside = (dy * dy + dx * dx) <= radius * radius
    # Polar texture (radial bars) for rotation visibility.
    theta = np.arctan2(dy, dx) - np.deg2rad(angle_deg)
    bars = 0.5 + 0.5 * np.cos(6.0 * theta)
    rgb = np.stack([
        bars * 230 + 25,                  # B
        bars *  90 + 30,                  # G
        bars * 200 + 25,                  # R
    ], axis=-1).astype(np.uint8)
    region = canvas[y0:y1, x0:x1]
    region[inside] = rgb[inside]


def _stripe_overlay(frame: np.ndarray) -> None:
    """Add a single bright vertical stripe (in place)."""
    h, w = frame.shape[:2]
    sx = w * 3 // 4
    frame[:, sx:sx + 2] = (255, 255, 255)


def _add_noise(frame: np.ndarray, sigma: float = 3.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, size=frame.shape).astype(np.float32)
    out = frame.astype(np.float32) + noise
    return np.clip(out, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
#  Public API                                                                 #
# --------------------------------------------------------------------------- #

def render_frame(frame_idx: int, n_frames: int, size: tuple[int, int]) -> np.ndarray:
    w, h = size
    frame = _background(h, w, frame_idx)

    # Puck travels left → right with a slight vertical bob and rotates.
    t = frame_idx / max(1, n_frames - 1)
    cx = int(round(30 + (w - 60) * t))
    cy = int(round(h // 2 + 12 * np.sin(2 * np.pi * t)))
    angle = 40.0 * frame_idx
    _puck(frame, cx, cy, angle)
    _stripe_overlay(frame)
    return _add_noise(frame, sigma=0.8, seed=frame_idx)


def synthesise_clip(
    out_dir: str | Path,
    *,
    n_frames: int = 12,
    size: Sequence[int] = (192, 144),
) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i in range(n_frames):
        frame = render_frame(i, n_frames, (size[0], size[1]))
        p = out_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(p), frame)
        paths.append(p)
    return paths


# --------------------------------------------------------------------------- #
#  Stand-alone usage                                                          #
# --------------------------------------------------------------------------- #

def _cli() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--num", type=int, default=12)
    p.add_argument("--size", type=int, nargs=2, default=[192, 144])
    a = p.parse_args()
    paths = synthesise_clip(a.out, n_frames=a.num, size=tuple(a.size))
    print(f"Wrote {len(paths)} frames to {a.out}")


if __name__ == "__main__":
    _cli()
