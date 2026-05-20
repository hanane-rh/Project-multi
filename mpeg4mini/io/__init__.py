"""I/O layer: image folders in, MV1 bitstreams out."""
from .frames import load_frame_sequence, save_frame_sequence
from .bitstream import (
    Bitstream,
    FrameRecord,
    MAGIC,
    VERSION,
    write_bitstream,
    read_bitstream,
)

__all__ = [
    "Bitstream",
    "FrameRecord",
    "MAGIC",
    "VERSION",
    "write_bitstream",
    "read_bitstream",
    "load_frame_sequence",
    "save_frame_sequence",
]
