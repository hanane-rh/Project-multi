"""Read/write a folder of sequential frames (PNG or JPG)."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


_IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp"}


def load_frame_sequence(folder: str | Path) -> list[np.ndarray]:
    """Read every supported image in `folder`, sorted by filename."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Frame folder not found: {folder}")
    paths = sorted(p for p in folder.iterdir() if p.suffix.lower() in _IMG_EXT)
    if not paths:
        raise ValueError(f"No image frames found in {folder}")
    frames: list[np.ndarray] = []
    for p in paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            raise IOError(f"Failed to read frame: {p}")
        frames.append(img)
    return frames


def save_frame_sequence(
    frames: Iterable[np.ndarray],
    folder: str | Path,
    prefix: str = "frame",
) -> list[Path]:
    """Write frames as `<prefix>_NNNN.png` in `folder` (folder is created)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for idx, frame in enumerate(frames):
        out = folder / f"{prefix}_{idx:04d}.png"
        if not cv2.imwrite(str(out), frame):
            raise IOError(f"Failed to write {out}")
        written.append(out)
    return written
