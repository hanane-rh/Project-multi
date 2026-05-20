"""The five pipeline stages, in spec order.

    Part 1 — preprocess   (BGR → YCbCr, 4:2:0)
    Part 2 — intra        (DCT + quantise an I-frame plane)
    Part 3 — inter        (motion estimation + residual coding for P-frames)
    Part 4 — entropy      (DEFLATE)
    Part 5 — visualise    (see mpeg4mini.visualise — keeps matplotlib out of
                           the encode/decode hot path)
"""
from . import preprocess, intra, inter, entropy

__all__ = ["preprocess", "intra", "inter", "entropy"]
