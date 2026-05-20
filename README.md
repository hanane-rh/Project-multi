# mpeg4mini — Simplified MPEG-4 Video Encoder Pipeline





## Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Tested with **Python 3.10+**.  Pure Python + NumPy/SciPy/OpenCV/Matplotlib;
no compiled extensions of our own.

---

## Quick start — 60 seconds

```bash
# 1. synthesise a small test clip (16 frames, 192×144)
python main.py sample

# 2. encode → video.bin
python main.py encode data/sample_frames -o video.bin --gop 8 --qf 50

# 3. decode → data/decoded/, also print per-frame PSNR
python main.py decode video.bin -o data/decoded --reference data/sample_frames

# 4. render the Part 5b pipeline figure
python main.py visualise data/sample_frames video.bin -o figures/pipeline.png

# 5. compression-ratio / PSNR sweeps for the report
python main.py experiments data/sample_frames -o figures/experiments.png
```

You should see ~46× compression at QF=50 and a mean PSNR of ~32 dB.

---

## CLI reference

```
python main.py sample      [--out DIR] [--num N] [--size W H]
python main.py encode      FRAMES_DIR [-o video.bin] [--gop G] [--qf QF] [--search S]
python main.py decode      video.bin  [-o DIR]       [--reference FRAMES_DIR]
python main.py visualise   FRAMES_DIR video.bin [-o pipeline.png]
python main.py experiments FRAMES_DIR              [-o experiments.png]
```

Run `python main.py <subcommand> --help` for the full per-command flag list.

---

## Repository layout

```
version1_highend/
├── main.py                       ← single CLI entry point
├── requirements.txt
├── README.md                     ← this file
├── report.pdf                    ← academic report (built from scripts/)
├── guide.pdf                     ← code-walkthrough guide
├── video.bin                     ← sample encoded bitstream
│
├── mpeg4mini/                    ← the codec package
│   ├── __init__.py
│   ├── config.py                 ← CodecConfig + JPEG Q-tables
│   ├── codec.py                  ← Encoder, Decoder
│   ├── metrics.py                ← PSNR, StreamStats
│   ├── visualise.py              ← Part 5b figure
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── preprocess.py         ← Part 1 — BGR↔YCbCr, 4:2:0
│   │   ├── intra.py              ← Part 2 — DCT + quantise
│   │   ├── inter.py              ← Part 3 — motion estimation
│   │   └── entropy.py            ← Part 4 — DEFLATE
│   └── io/
│       ├── __init__.py
│       ├── frames.py             ← read/write image folders
│       └── bitstream.py          ← MV1 container format
│
├── scripts/                      ← one-shot utilities (not imported by codec)
│   ├── make_sample_frames.py     ← synthesise the test clip
│   ├── run_experiments.py        ← QF / GOP sweeps
│   ├── build_report.py           ← produce report.pdf
│   └── build_guide.py            ← produce guide.pdf
│
├── data/
│   ├── sample_frames/            ← 16 synthesised input PNGs
│   └── decoded/                  ← reconstructed PNGs (regenerated)
│
└── figures/
    ├── pipeline.png              ← Part 5b — all-stages figure
    └── experiments.png           ← Part 5c — sweeps
```

---

## Configuration

`mpeg4mini.config.CodecConfig` is the one source of truth for every tunable
parameter:

| field              | default | meaning                                |
| ------------------ | ------- | -------------------------------------- |
| `gop_size`         | 8       | I-frame every `gop_size` frames        |
| `quality_factor`   | 50      | libjpeg-style scaling 1..100           |
| `dct_block_size`   | 8       | DCT tile                               |
| `macroblock_size`  | 16      | motion-estimation tile                 |
| `search_range`     | 8       | ±S pixel window for block matching     |
| `chroma_subsample` | True    | 4:2:0 if True, else 4:4:4              |

---

## Bitstream format (MV1)

A pickled dict, then DEFLATE-compressed at level 9.  Decompressed payload:

```python
{
    "magic":        b"MV1\x00",
    "version":      1,
    "config":       CodecConfig(...),     # all encode parameters
    "frame_shape":  (H, W),               # luma resolution before padding
    "chroma_shape": (H, W),               # chroma resolution before padding
    "frames":       [FrameRecord, ...],   # one per video frame
    "extras":       {},                   # free-form metadata
}
```

Each `FrameRecord` carries:

* `kind` — `"I"` or `"P"`
* `luma_q`, `chroma_b_q`, `chroma_r_q` — `int16` quantised DCT coefficients
  (intra) or residual coefficients (inter)
* `motion` — `int16 (rows, cols, 2)` motion field, only on P-frames

---

## How to read the source

If you want to understand the codec end-to-end, follow this trail:

1. **`mpeg4mini/config.py`** — start with `CodecConfig`; everything else
   takes one as input.
2. **`mpeg4mini/pipeline/preprocess.py`** — colour conversion is the only
   non-trivial maths in the per-frame I/O.
3. **`mpeg4mini/pipeline/intra.py`** — the DCT-then-quantise core; this is
   what an I-frame *is*.
4. **`mpeg4mini/pipeline/inter.py`** — block-matching motion estimation.
   Read `estimate()` then `compensate()`.
5. **`mpeg4mini/codec.py`** — the orchestrator.  `Encoder.push()` dispatches
   to `_encode_intra` or `_encode_inter`; `Decoder._decode_one` mirrors it.
6. **`mpeg4mini/io/bitstream.py`** — what actually lands on disk.
7. **`mpeg4mini/visualise.py`** — opinionated matplotlib figure; safe to
   ignore until you've understood the rest.

`guide.pdf` walks through these same files in narrative form with diagrams.

---

## License & attribution

Educational project for the USTHB *Multimedia Systems* module.
JPEG Q-tables are public-domain (ITU-T T.81 Annex K).
