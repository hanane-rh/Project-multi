"""Build a reader's guide to the mpeg4mini source tree (guide.pdf).

This document is intended for someone opening the project for the first time:
it walks through every module of the codec in narrative form, shows the data
flow between them and explains where each part of the assignment lives.

Same visual style as `report.pdf` but with a different cover and a
guide-oriented body.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)


HERE   = Path(__file__).resolve().parent.parent
LOGO   = Path("/Users/mac/multi/usthb_bw.png")
OUTPUT = HERE / "guide.pdf"

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
ACCENT = colors.HexColor("#0b3d91")
SOFT   = colors.HexColor("#f4f6fa")


# --------------------------------------------------------------------------- #
#  Styles                                                                     #
# --------------------------------------------------------------------------- #

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "cover_uni": ParagraphStyle(
            "cover_uni", parent=base,
            fontName="Helvetica-Bold", fontSize=12.5, leading=15,
            alignment=TA_CENTER, textColor=ACCENT,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base,
            fontName="Helvetica", fontSize=10.5, leading=13,
            alignment=TA_CENTER, textColor=colors.HexColor("#333"),
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base,
            fontName="Helvetica-Bold", fontSize=22, leading=27,
            alignment=TA_CENTER, textColor=colors.black,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base,
            fontName="Helvetica-Oblique", fontSize=14, leading=18,
            alignment=TA_CENTER, textColor=ACCENT, spaceBefore=4, spaceAfter=10,
        ),
        "cover_blurb": ParagraphStyle(
            "cover_blurb", parent=base,
            fontName="Times-Italic", fontSize=11.5, leading=15,
            alignment=TA_CENTER, textColor=colors.HexColor("#444"),
        ),

        "h1": ParagraphStyle(
            "h1", parent=base,
            fontName="Helvetica-Bold", fontSize=15, leading=19,
            spaceBefore=14, spaceAfter=6, textColor=ACCENT,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base,
            fontName="Helvetica-Bold", fontSize=12, leading=15,
            spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#222"),
        ),
        "body": ParagraphStyle(
            "body", parent=base,
            fontName="Times-Roman", fontSize=11, leading=15,
            alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base,
            fontName="Times-Roman", fontSize=11, leading=14,
            leftIndent=14, bulletIndent=2, spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code", parent=base,
            fontName="Courier", fontSize=8.5, leading=11,
            leftIndent=8, rightIndent=8,
            backColor=SOFT, borderColor=colors.HexColor("#dde3ee"),
            borderWidth=0.5, borderPadding=6,
            spaceBefore=4, spaceAfter=6,
        ),
        "tree": ParagraphStyle(
            "tree", parent=base,
            fontName="Courier", fontSize=8.8, leading=11.5,
            leftIndent=2, rightIndent=2,
            backColor=SOFT, borderColor=colors.HexColor("#dde3ee"),
            borderWidth=0.5, borderPadding=8,
            spaceBefore=4, spaceAfter=6,
        ),
        "note": ParagraphStyle(
            "note", parent=base,
            fontName="Helvetica-Oblique", fontSize=10, leading=13,
            leftIndent=8, textColor=colors.HexColor("#555"),
            backColor=colors.HexColor("#fff8e7"),
            borderColor=colors.HexColor("#f0d57a"),
            borderWidth=0.4, borderPadding=6,
            spaceBefore=4, spaceAfter=8,
        ),
    }


# --------------------------------------------------------------------------- #
#  Page header / footer                                                       #
# --------------------------------------------------------------------------- #

def _header_footer(c: canvas.Canvas, doc) -> None:
    c.saveState()
    c.setFont("Helvetica", 8.5)
    y = PAGE_H - MARGIN + 0.5 * cm
    for line in (
        "Département d'Informatique",
        "Faculté d'Électronique et d'Informatique",
        "USTHB",
    ):
        c.drawString(MARGIN, y, line)
        y -= 10
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(
        PAGE_W - MARGIN, PAGE_H - MARGIN + 0.5 * cm,
        "mpeg4mini — Guide de lecture",
    )
    c.setStrokeColor(ACCENT); c.setLineWidth(0.6)
    rule_y = PAGE_H - MARGIN - 0.45 * cm
    c.line(MARGIN, rule_y, PAGE_W - MARGIN, rule_y)
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#666"))
    c.drawCentredString(PAGE_W / 2, MARGIN / 2, f"– {doc.page} –")
    c.restoreState()


# --------------------------------------------------------------------------- #
#  Cover                                                                      #
# --------------------------------------------------------------------------- #

def _hr(*, width: float, color, thickness: float = 1.0):
    t = Table([[""]], colWidths=[width], rowHeights=[0.001 * cm])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), thickness, color)]))
    t.hAlign = "CENTER"
    return t


def _cover_story(s) -> list:
    story: list = []
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Université des Sciences et de la Technologie Houari Boumediene",
                           s["cover_uni"]))
    story.append(Paragraph("Faculté d'Électronique et d'Informatique — Département d'Informatique",
                           s["cover_sub"]))
    story.append(Spacer(1, 1.0 * cm))
    if LOGO.exists():
        img = Image(str(LOGO), width=4.0 * cm, height=4.0 * 328 / 612 * cm)
        img.hAlign = "CENTER"
        story.append(img)
    story.append(Spacer(1, 1.0 * cm))

    story.append(_hr(width=13 * cm, color=ACCENT, thickness=1.2))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Guide de lecture du code", s["cover_subtitle"]))
    story.append(Paragraph("mpeg4mini", s["cover_title"]))
    story.append(Paragraph("Simplified MPEG-4 Video Encoder Pipeline", s["cover_subtitle"]))
    story.append(_hr(width=13 * cm, color=ACCENT, thickness=1.2))
    story.append(Spacer(1, 1.2 * cm))

    story.append(Paragraph(
        "Ce document accompagne le projet : il décrit l'arborescence, le rôle "
        "de chaque module et le flot des données. À lire avant d'ouvrir le "
        "code source — environ 15 minutes de lecture.",
        s["cover_blurb"],
    ))
    story.append(PageBreak())
    return story


# --------------------------------------------------------------------------- #
#  Body                                                                       #
# --------------------------------------------------------------------------- #

def _body_story(s) -> list:
    story: list = []

    # 1 — Comment lire ce guide
    story.append(Paragraph("1.&nbsp;&nbsp;Comment lire ce guide", s["h1"]))
    story.append(Paragraph(
        "Le projet implémente un codec vidéo en cinq étapes : pré-traitement, "
        "DCT/quantification, estimation de mouvement, codage entropique, "
        "évaluation. Chacune de ces étapes vit dans son propre fichier Python — "
        "vous pouvez donc lire le code dans l'ordre du sujet et tout retrouver.",
        s["body"],
    ))
    story.append(Paragraph(
        "Conseil : commencez par <font face='Courier'>main.py</font> "
        "(point d'entrée), passez à <font face='Courier'>mpeg4mini/codec.py</font> "
        "(qui orchestre tout) puis descendez dans les sous-modules de "
        "<font face='Courier'>mpeg4mini/pipeline/</font> au besoin.",
        s["body"],
    ))

    # 2 — Arborescence
    story.append(Paragraph("2.&nbsp;&nbsp;Arborescence du projet", s["h1"]))
    story.append(Preformatted(
        "version1_highend/\n"
        "|-- main.py                       point d'entree CLI unique\n"
        "|-- requirements.txt              dependances pip\n"
        "|-- README.md                     demarrage rapide\n"
        "|-- report.pdf                    rapport academique\n"
        "|-- guide.pdf                     ce document\n"
        "|-- video.bin                     exemple encode (sortie d'encode)\n"
        "|\n"
        "|-- mpeg4mini/                    PACKAGE PRINCIPAL\n"
        "|   |-- __init__.py               reexpose Encoder / Decoder / CodecConfig\n"
        "|   |-- config.py                 CodecConfig + tables JPEG\n"
        "|   |-- codec.py                  Encoder, Decoder (orchestration)\n"
        "|   |-- metrics.py                PSNR, StreamStats\n"
        "|   |-- visualise.py              figure pipeline (Partie 5b)\n"
        "|   |\n"
        "|   |-- pipeline/                 LES 5 ETAPES, UNE PAR FICHIER\n"
        "|   |   |-- preprocess.py         Partie 1 -- BGR<->YCbCr, 4:2:0\n"
        "|   |   |-- intra.py              Partie 2 -- DCT + quantification\n"
        "|   |   |-- inter.py              Partie 3 -- block matching\n"
        "|   |   `-- entropy.py            Partie 4 -- DEFLATE\n"
        "|   |\n"
        "|   `-- io/\n"
        "|       |-- frames.py             lecture/ecriture d'un dossier d'images\n"
        "|       `-- bitstream.py          conteneur MV1 (format disque)\n"
        "|\n"
        "|-- scripts/                      utilitaires (non importes par le codec)\n"
        "|   |-- make_sample_frames.py     synthese du clip de test\n"
        "|   |-- run_experiments.py        balayages QF / GOP\n"
        "|   |-- build_report.py           genere report.pdf\n"
        "|   `-- build_guide.py            genere ce guide.pdf\n"
        "|\n"
        "|-- data/\n"
        "|   |-- sample_frames/            entree -- 16 PNG 192x144\n"
        "|   `-- decoded/                  sortie reconstruite apres decode\n"
        "|\n"
        "`-- figures/\n"
        "    |-- pipeline.png              figure des 5 etapes (Partie 5b)\n"
        "    `-- experiments.png           sweeps QF / GOP (Partie 5c)",
        s["tree"],
    ))
    story.append(Paragraph(
        "Règle d'or : tout ce qui est <i>algorithme du codec</i> vit sous "
        "<font face='Courier'>mpeg4mini/</font>. Tout ce qui est "
        "<i>script jetable</i> ou <i>génération de livrables</i> vit sous "
        "<font face='Courier'>scripts/</font>.",
        s["note"],
    ))

    # 3 — Flot des données
    story.append(Paragraph("3.&nbsp;&nbsp;Flot des données end-to-end", s["h1"]))
    story.append(Paragraph(
        "Une trame BGR traverse les modules dans cet ordre côté encodeur :",
        s["body"],
    ))
    story.append(Preformatted(
        "  frame_NNNN.png      (BGR uint8)            <-- io/frames.load_frame_sequence\n"
        "        |\n"
        "        v\n"
        "  pipeline.preprocess.to_ycbcr        -- Partie 1\n"
        "        |   (Y, Cb, Cr float32, chroma 4:2:0 sous-echantillonne)\n"
        "        v\n"
        "  pipeline.preprocess.pad_to_multiple   (alignement DCT/macroblock)\n"
        "        |\n"
        "        v\n"
        "  +---- trame I  ----+         +---- trame P  ------------------------+\n"
        "  | pipeline.intra.  |         | pipeline.inter.estimate   -- Partie 3|\n"
        "  |   encode_plane   |         |   -> motion vectors (rows, cols, 2)  |\n"
        "  |  (DCT + quant)   |         | pipeline.inter.compensate            |\n"
        "  |   -- Partie 2    |         |   -> prediction                      |\n"
        "  +------------------+         | residual = current - prediction      |\n"
        "        |                      | pipeline.intra.encode_residual       |\n"
        "        |                      |   -> quant. coefficients  -- Partie 2|\n"
        "        |                      +--------------------------------------+\n"
        "        v\n"
        "  io.bitstream.FrameRecord(kind, luma_q, chroma_b_q, chroma_r_q, motion?)\n"
        "        |\n"
        "        v  (encoder accumule N records)\n"
        "  io.bitstream.write_bitstream\n"
        "        |   pickle + DEFLATE niveau 9   -- Partie 4\n"
        "        v\n"
        "  video.bin",
        s["tree"],
    ))
    story.append(Paragraph(
        "Côté décodeur, exactement l'inverse : "
        "<font face='Courier'>read_bitstream</font> → "
        "<font face='Courier'>Decoder.decode_all</font> → "
        "<font face='Courier'>pipeline.intra.decode_plane</font> ou "
        "<font face='Courier'>decode_residual</font> + "
        "<font face='Courier'>inter.compensate</font> → "
        "<font face='Courier'>preprocess.merge</font> → "
        "<font face='Courier'>preprocess.to_bgr</font> → PNG.",
        s["body"],
    ))

    # 4 — Module par module
    story.append(Paragraph("4.&nbsp;&nbsp;Module par module", s["h1"]))

    story.append(Paragraph("4.1.&nbsp;&nbsp;mpeg4mini/config.py — configuration", s["h2"]))
    story.append(Paragraph(
        "Une seule dataclass <font face='Courier'>CodecConfig</font> "
        "(gel : <font face='Courier'>frozen=True</font>) contient tous les "
        "paramètres : taille de GOP, facteur qualité, taille de bloc DCT et "
        "de macrobloc, fenêtre de recherche, drapeau 4:2:0. La fonction "
        "<font face='Courier'>scaled_quant_table</font> applique la mise à "
        "l'échelle libjpeg sur les tables JPEG standard.",
        s["body"],
    ))
    story.append(Preformatted(
        "@dataclass(frozen=True)\n"
        "class CodecConfig:\n"
        "    gop_size: int = 8\n"
        "    quality_factor: int = 50\n"
        "    dct_block_size: int = 8\n"
        "    macroblock_size: int = 16\n"
        "    search_range: int = 8\n"
        "    chroma_subsample: bool = True",
        s["code"],
    ))

    story.append(Paragraph("4.2.&nbsp;&nbsp;mpeg4mini/pipeline/preprocess.py — Partie 1", s["h2"]))
    story.append(Paragraph(
        "Conversion BGR ↔ YCbCr selon ITU-R BT.601 (matrice constante), puis "
        "sous-échantillonnage chromatique 4:2:0 par filtre boîte 2×2. Trois "
        "fonctions utiles à connaître :",
        s["body"],
    ))
    for line in (
        "<font face='Courier'>to_ycbcr(bgr) → ycbcr</font> &nbsp;— conversion couleur (Cb/Cr centrés à 128).",
        "<font face='Courier'>split(ycbcr, subsample) → (Y, Cb, Cr)</font> &nbsp;— sépare et sous-échantillonne.",
        "<font face='Courier'>pad_to_multiple(plane, k)</font> &nbsp;— remplissage edge avant DCT.",
    ):
        story.append(Paragraph(f"• {line}", s["bullet"]))

    story.append(Paragraph("4.3.&nbsp;&nbsp;mpeg4mini/pipeline/intra.py — Partie 2", s["h2"]))
    story.append(Paragraph(
        "Cœur de la compression intra : découpe en blocs 8×8, DCT-II "
        "orthonormée via <font face='Courier'>scipy.fft.dctn</font>, division "
        "par la table Q. Quatre fonctions miroirs :",
        s["body"],
    ))
    for line in (
        "<font face='Courier'>encode_plane / decode_plane</font> &nbsp;— I-frames (recentrage ±128).",
        "<font face='Courier'>encode_residual / decode_residual</font> &nbsp;— résiduels P-frames (déjà zéro-moyenne).",
        "<font face='Courier'>tile / untile</font> &nbsp;— passage plan ↔ liste de blocs (helpers internes).",
    ):
        story.append(Paragraph(f"• {line}", s["bullet"]))

    story.append(Paragraph("4.4.&nbsp;&nbsp;mpeg4mini/pipeline/inter.py — Partie 3", s["h2"]))
    story.append(Paragraph(
        "Estimation de mouvement par <i>recherche exhaustive</i> sur une "
        "fenêtre ±S, coût = somme des différences absolues (SAD). Le résultat "
        "est un champ d'entiers <font face='Courier'>int16 (rows, cols, 2)</font> "
        "qui voyage tel quel dans le bitstream — c'est la métadonnée la plus "
        "compacte qu'on puisse produire.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>Astuce d'implémentation.</b> La référence est paddée une seule "
        "fois en mode <font face='Courier'>'edge'</font> avant la boucle, "
        "ce qui évite tout test de bord à l'intérieur du double-for. Pour "
        "accélérer (×3 ou ×4), remplacer la double boucle par une recherche "
        "en trois passes — interface inchangée.",
        s["note"],
    ))

    story.append(Paragraph("4.5.&nbsp;&nbsp;mpeg4mini/pipeline/entropy.py — Partie 4", s["h2"]))
    story.append(Paragraph(
        "Deux fonctions de cinq lignes chacune : "
        "<font face='Courier'>pack(obj)</font> sérialise par "
        "<font face='Courier'>pickle</font> puis compresse par "
        "<font face='Courier'>zlib</font> niveau 9 ; "
        "<font face='Courier'>unpack(blob)</font> fait l'inverse. C'est volontairement "
        "minimal — la complexité du codec ne se trouve pas ici.",
        s["body"],
    ))

    story.append(Paragraph("4.6.&nbsp;&nbsp;mpeg4mini/codec.py — orchestration", s["h2"]))
    story.append(Paragraph(
        "Le <font face='Courier'>Encoder</font> est <i>stateful</i> : on "
        "<font face='Courier'>push(bgr)</font> les trames une à une, puis "
        "on appelle <font face='Courier'>finalise()</font> qui renvoie un "
        "<font face='Courier'>Bitstream</font>. La méthode "
        "<font face='Courier'>push</font> décide elle-même si la trame est "
        "I (début de GOP ou premier frame) ou P et délègue à "
        "<font face='Courier'>_encode_intra</font> / "
        "<font face='Courier'>_encode_inter</font>.",
        s["body"],
    ))
    story.append(Paragraph(
        "Le <font face='Courier'>Decoder</font> reçoit un "
        "<font face='Courier'>Bitstream</font> au constructeur et expose "
        "<font face='Courier'>decode_all()</font> qui renvoie la liste BGR "
        "complète, recadrée à la résolution d'origine.",
        s["body"],
    ))

    story.append(Paragraph("4.7.&nbsp;&nbsp;mpeg4mini/io/bitstream.py — format MV1", s["h2"]))
    story.append(Paragraph(
        "Le conteneur sur disque est un dictionnaire pickle compressé "
        "(<font face='Courier'>magic = b'MV1\\\\x00'</font>, version 1) qui "
        "contient la config, les dimensions originales et la liste des "
        "<font face='Courier'>FrameRecord</font>. Décompresser un "
        "<font face='Courier'>.bin</font> à la main :",
        s["body"],
    ))
    story.append(Preformatted(
        "import zlib, pickle\n"
        "payload = pickle.loads(zlib.decompress(open('video.bin','rb').read()))\n"
        "print(payload['magic'], payload['version'], len(payload['frames']))",
        s["code"],
    ))

    story.append(Paragraph("4.8.&nbsp;&nbsp;mpeg4mini/visualise.py — Partie 5b", s["h2"]))
    story.append(Paragraph(
        "Cinq lignes de figure matplotlib (originaux, planes YCbCr, bloc 8×8 "
        "à travers DCT/Q, vecteurs de mouvement + résiduels, reconstructions). "
        "Cette fonction est volontairement isolée du chemin chaud "
        "encode/decode : matplotlib n'est importé que si vous appelez "
        "<font face='Courier'>render</font>.",
        s["body"],
    ))

    story.append(Paragraph("4.9.&nbsp;&nbsp;mpeg4mini/metrics.py — Partie 5a", s["h2"]))
    story.append(Paragraph(
        "PSNR par trame, taille brute (somme des octets BGR uint8), et la "
        "dataclass <font face='Courier'>StreamStats</font> qui synthétise "
        "ratio + PSNR moyen + nombre de I-frames / P-frames.",
        s["body"],
    ))

    # 5 — Tableau récap modules
    story.append(Paragraph("5.&nbsp;&nbsp;Tableau récapitulatif des modules", s["h1"]))
    rows = [
        ["Fichier", "Partie", "Lignes", "Rôle"],
        ["mpeg4mini/config.py",              "—",    " ~80", "Config + tables JPEG"],
        ["mpeg4mini/pipeline/preprocess.py", "1",    " ~95", "Couleur + 4:2:0 + padding"],
        ["mpeg4mini/pipeline/intra.py",      "2",    "~100", "DCT + quant (plan ou résiduel)"],
        ["mpeg4mini/pipeline/inter.py",      "3",    " ~80", "Estimation + compensation"],
        ["mpeg4mini/pipeline/entropy.py",    "4",    " ~25", "DEFLATE wrapper"],
        ["mpeg4mini/codec.py",               "—",    "~200", "Encoder + Decoder"],
        ["mpeg4mini/io/bitstream.py",        "4",    " ~75", "Format MV1 sur disque"],
        ["mpeg4mini/io/frames.py",           "—",    " ~45", "I/O d'images PNG/JPG"],
        ["mpeg4mini/visualise.py",           "5b",   "~135", "Figure pipeline"],
        ["mpeg4mini/metrics.py",             "5a",   " ~55", "PSNR + stats"],
        ["main.py",                          "—",    "~135", "CLI 5 sous-commandes"],
    ]
    tbl = Table(rows, colWidths=[6.6 * cm, 1.3 * cm, 1.4 * cm, 7.0 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",     (0, 1), (0, -1), "Courier"),
        ("FONTNAME",     (1, 1), (2, -1), "Helvetica"),
        ("FONTNAME",     (3, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("ALIGN",        (1, 1), (2, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SOFT, colors.white]),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0de")),
        ("BOX",          (0, 0), (-1, -1), 0.4, ACCENT),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)

    # 6 — Comment exécuter
    story.append(Paragraph("6.&nbsp;&nbsp;Comment exécuter le projet", s["h1"]))
    story.append(Preformatted(
        "# 1. Environnement\n"
        "python -m venv .venv && source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "\n"
        "# 2. Pipeline complet en 4 commandes\n"
        "python main.py sample\n"
        "python main.py encode      data/sample_frames -o video.bin --gop 8 --qf 50\n"
        "python main.py decode      video.bin -o data/decoded --reference data/sample_frames\n"
        "python main.py visualise   data/sample_frames video.bin -o figures/pipeline.png\n"
        "python main.py experiments data/sample_frames -o figures/experiments.png\n"
        "\n"
        "# 3. Régénérer le rapport et ce guide\n"
        "python scripts/build_report.py\n"
        "python scripts/build_guide.py",
        s["code"],
    ))

    # 7 — Comment modifier
    story.append(Paragraph("7.&nbsp;&nbsp;Comment modifier / étendre", s["h1"]))
    for line in (
        "<b>Changer la table de quantification</b> — modifier "
        "<font face='Courier'>LUMA_QUANT_TABLE</font> ou "
        "<font face='Courier'>CHROMA_QUANT_TABLE</font> dans "
        "<font face='Courier'>config.py</font>. Tout le pipeline relit la "
        "table à chaque encode/decode.",
        "<b>Remplacer la recherche exhaustive</b> — réécrire "
        "<font face='Courier'>pipeline.inter.estimate</font> avec la même "
        "signature ; le codec consomme uniquement le champ "
        "<font face='Courier'>(rows, cols, 2) int16</font> retourné.",
        "<b>Changer l'algorithme entropique</b> — remplacer "
        "<font face='Courier'>pack/unpack</font> dans "
        "<font face='Courier'>pipeline/entropy.py</font> (ex : zstandard, "
        "Huffman par soi-même). Le format MV1 reste valide tant que la paire "
        "est compatible.",
        "<b>Ajouter un sous-commande CLI</b> — éditer "
        "<font face='Courier'>main.py</font> : ajouter une fonction "
        "<font face='Courier'>cmd_xxx</font> et la déclarer dans "
        "<font face='Courier'>_build_parser</font>.",
    ):
        story.append(Paragraph(f"• {line}", s["bullet"]))

    # 8 — Glossaire
    story.append(Paragraph("8.&nbsp;&nbsp;Mini-glossaire", s["h1"]))
    gloss = [
        ["Terme",      "Sens dans ce projet"],
        ["I-frame",    "Trame codée seule, sans référence (DCT pur)."],
        ["P-frame",    "Trame codée par différence avec la précédente (motion + résiduel)."],
        ["GOP",        "Group of Pictures — distance entre deux I-frames."],
        ["Macrobloc",  "Bloc 16×16 utilisé pour l'estimation de mouvement."],
        ["MV",         "Motion vector — déplacement (dy, dx) d'un macrobloc."],
        ["SAD",        "Sum of Absolute Differences — coût de matching."],
        ["DCT-II",     "Discrete Cosine Transform type II, orthonormée."],
        ["QF",         "Quality Factor — échelle libjpeg [1, 100]."],
        ["DEFLATE",    "Algorithme de zlib : LZ77 + Huffman."],
        ["MV1",        "Notre conteneur disque (magic = b'MV1\\\\x00')."],
    ]
    g = Table(gloss, colWidths=[3.0 * cm, 13.0 * cm])
    g.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (1, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SOFT, colors.white]),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0de")),
        ("BOX",          (0, 0), (-1, -1), 0.4, ACCENT),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(g)
    return story


# --------------------------------------------------------------------------- #
#  Build                                                                      #
# --------------------------------------------------------------------------- #

def build(output: Path = OUTPUT) -> Path:
    s = _styles()
    doc = SimpleDocTemplate(
        str(output), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 1.4 * cm, bottomMargin=MARGIN,
    )
    doc.build(
        _cover_story(s) + _body_story(s),
        onFirstPage=lambda c, d: None,
        onLaterPages=_header_footer,
    )
    return output


if __name__ == "__main__":
    out = build()
    print(f"Wrote {out}  ({out.stat().st_size / 1024:.1f} KB)")
