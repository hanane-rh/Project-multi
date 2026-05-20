"""mpeg4mini — a simplified MPEG-4-style video codec.

Public surface:

    from mpeg4mini import Encoder, Decoder, CodecConfig
    from mpeg4mini.io import write_bitstream, read_bitstream

The five pipeline stages live under `mpeg4mini.pipeline`:

    preprocess   — Part 1 — color conversion + chroma subsampling
    intra        — Part 2 — DCT + quantisation for I-frames
    inter        — Part 3 — motion estimation + residual coding for P-frames
    entropy      — Part 4 — lossless DEFLATE compression
    (visualise   — Part 5b — single matplotlib figure, top-level module)
"""
from .config import CodecConfig
from .codec import Encoder, Decoder

__all__ = ["CodecConfig", "Encoder", "Decoder"]
__version__ = "1.0.0"
