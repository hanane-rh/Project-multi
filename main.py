#!/usr/bin/env python3
"""mpeg4mini — single command-line entry point.

Usage:
    python main.py sample                           # synthesise test frames
    python main.py encode FRAMES_DIR [OPTIONS]      # → video.bin
    python main.py decode video.bin  [OPTIONS]      # → decoded/ + PSNR
    python main.py visualise FRAMES_DIR video.bin   # → pipeline.png
    python main.py experiments FRAMES_DIR           # → experiments.png

Run `python main.py <subcommand> --help` for the per-command flags.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make the local package importable regardless of CWD.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


# --------------------------------------------------------------------------- #
#  Sub-commands                                                               #
# --------------------------------------------------------------------------- #

def cmd_sample(args: argparse.Namespace) -> int:
    from scripts.make_sample_frames import synthesise_clip
    paths = synthesise_clip(args.out, n_frames=args.num, size=tuple(args.size))
    print(f"Wrote {len(paths)} frames to {args.out}")
    return 0


def cmd_encode(args: argparse.Namespace) -> int:
    from mpeg4mini import CodecConfig, Encoder
    from mpeg4mini.io import load_frame_sequence, write_bitstream

    frames = load_frame_sequence(args.frames)
    cfg = CodecConfig(
        gop_size=args.gop,
        quality_factor=args.qf,
        search_range=args.search,
    )
    enc = Encoder(cfg)
    t0 = time.time()
    enc.push_many(frames)
    stream = enc.finalise()
    nbytes = write_bitstream(stream, args.out)
    t1 = time.time()

    original = sum(f.nbytes for f in frames)
    print(f"Encoded {len(frames)} frames in {t1 - t0:.2f}s")
    print(f"  original   : {original:>10,d} bytes")
    print(f"  compressed : {nbytes:>10,d} bytes  →  {args.out}")
    print(f"  ratio      : {original / nbytes:>10.2f}×")
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    from mpeg4mini import Decoder
    from mpeg4mini.io import read_bitstream, save_frame_sequence, load_frame_sequence
    from mpeg4mini.metrics import psnr_db

    stream = read_bitstream(args.bitstream)
    frames = Decoder(stream).decode_all()
    save_frame_sequence(frames, args.out)
    print(f"Decoded {len(frames)} frames → {args.out}")

    if args.reference:
        refs = load_frame_sequence(args.reference)
        print(f"\nPSNR vs {args.reference}:")
        for i, (ref, rec) in enumerate(zip(refs, frames)):
            kind = stream.frames[i].kind
            print(f"  frame {i:>3d} ({kind})  {psnr_db(ref, rec):6.2f} dB")
    return 0


def cmd_visualise(args: argparse.Namespace) -> int:
    from mpeg4mini import visualise
    from mpeg4mini.io import read_bitstream, load_frame_sequence

    frames = load_frame_sequence(args.frames)
    stream = read_bitstream(args.bitstream)
    out = visualise.render(frames, stream, args.out)
    print(f"Wrote pipeline figure → {out}")
    return 0


def cmd_experiments(args: argparse.Namespace) -> int:
    from scripts.run_experiments import run_and_plot
    out = run_and_plot(args.frames, args.out)
    print(f"Wrote experiments figure → {out}")
    return 0


# --------------------------------------------------------------------------- #
#  Argument parsing                                                           #
# --------------------------------------------------------------------------- #

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mpeg4mini",
        description="Simplified MPEG-4-style video codec.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sample", help="generate synthetic sample frames")
    s.add_argument("--out", type=Path, default=HERE / "data" / "sample_frames")
    s.add_argument("--num", type=int, default=12)
    s.add_argument("--size", type=int, nargs=2, default=[192, 144],
                   metavar=("W", "H"))
    s.set_defaults(func=cmd_sample)

    e = sub.add_parser("encode", help="encode a folder of frames → .bin")
    e.add_argument("frames", type=Path)
    e.add_argument("-o", "--out", type=Path, default=HERE / "video.bin")
    e.add_argument("--gop",     type=int, default=8)
    e.add_argument("--qf",      type=int, default=50)
    e.add_argument("--search",  type=int, default=8)
    e.set_defaults(func=cmd_encode)

    d = sub.add_parser("decode", help="decode a .bin back to frames")
    d.add_argument("bitstream", type=Path)
    d.add_argument("-o", "--out", type=Path, default=HERE / "data" / "decoded")
    d.add_argument("--reference", type=Path, default=None,
                   help="folder of original frames, to compute PSNR")
    d.set_defaults(func=cmd_decode)

    v = sub.add_parser("visualise", help="render the Part 5b pipeline figure")
    v.add_argument("frames",    type=Path)
    v.add_argument("bitstream", type=Path)
    v.add_argument("-o", "--out", type=Path,
                   default=HERE / "figures" / "pipeline.png")
    v.set_defaults(func=cmd_visualise)

    x = sub.add_parser("experiments", help="ratio-vs-QF and ratio-vs-GOP sweeps")
    x.add_argument("frames", type=Path)
    x.add_argument("-o", "--out", type=Path,
                   default=HERE / "figures" / "experiments.png")
    x.set_defaults(func=cmd_experiments)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
