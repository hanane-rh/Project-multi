"""Part 4 — Entropy coding.

Picks a single, well-tested backend: pickle the payload (so frame records,
motion fields and `CodecConfig` survive a round-trip) then DEFLATE the bytes
at maximum compression.  DEFLATE = LZ77 + Huffman, the same family used in
JPEG/MPEG entropy backends in practice.
"""
from __future__ import annotations

import pickle
import zlib


COMPRESSION_LEVEL = 9   # 1=fastest, 9=smallest; encode time is irrelevant here


def pack(payload: object) -> bytes:
    """Serialise + losslessly compress an arbitrary Python payload."""
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    return zlib.compress(raw, COMPRESSION_LEVEL)


def unpack(blob: bytes) -> object:
    """Inverse of `pack`."""
    return pickle.loads(zlib.decompress(blob))
