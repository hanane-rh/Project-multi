"""On-disk bitstream container — the MV1 format.

Wire layout (after DEFLATE decompression):

    pickled dict {
        "magic":        b"MV1\\x00",          # format identifier
        "version":      int,                   # bumped on breaking changes
        "config":       CodecConfig,           # frozen dataclass
        "frame_shape":  (H, W),                # luma resolution (pre-padding)
        "chroma_shape": (H, W),                # chroma resolution (pre-padding)
        "frames":       list[FrameRecord],     # per-frame payloads
        "extras":       dict[str, Any],        # free-form metadata
    }
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..config import CodecConfig
from ..pipeline import entropy


MAGIC = b"MV1\x00"
VERSION = 1


@dataclass
class FrameRecord:
    """One frame's worth of quantised coefficients (+ motion if predicted)."""
    kind: str                             # "I" or "P"
    luma_q: np.ndarray                    # quantised Y coefficients
    chroma_b_q: np.ndarray                # quantised Cb coefficients
    chroma_r_q: np.ndarray                # quantised Cr coefficients
    motion: np.ndarray | None = None      # (rows, cols, 2) int16, P-frames only


@dataclass
class Bitstream:
    """In-memory representation of a decoded MV1 container."""
    config: CodecConfig
    frame_shape: tuple[int, int]
    chroma_shape: tuple[int, int]
    frames: list[FrameRecord] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


def write_bitstream(stream: Bitstream, path: str | Path) -> int:
    """Serialise + DEFLATE `stream` to `path`.  Returns bytes written."""
    payload = {
        "magic":        MAGIC,
        "version":      VERSION,
        "config":       stream.config,
        "frame_shape":  stream.frame_shape,
        "chroma_shape": stream.chroma_shape,
        "frames":       stream.frames,
        "extras":       stream.extras,
    }
    blob = entropy.pack(payload)
    Path(path).write_bytes(blob)
    return len(blob)


def read_bitstream(path: str | Path) -> Bitstream:
    """Inverse of `write_bitstream` — raises on a malformed file."""
    blob = Path(path).read_bytes()
    payload = entropy.unpack(blob)
    if not isinstance(payload, dict) or payload.get("magic") != MAGIC:
        raise ValueError(f"Not a valid MV1 bitstream: {path}")
    if payload.get("version") != VERSION:
        raise ValueError(
            f"Unsupported MV1 version {payload.get('version')} (expected {VERSION})"
        )
    return Bitstream(
        config=payload["config"],
        frame_shape=payload["frame_shape"],
        chroma_shape=payload["chroma_shape"],
        frames=payload["frames"],
        extras=payload.get("extras", {}),
    )
