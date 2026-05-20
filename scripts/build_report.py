"""Build the academic project report (report.pdf) — redesigned edition.

Visual identity:
  * Cover: full-width navy band with university header in reverse, large
    USTHB seal, two-line title in display weight, info card with zebra rows.
  * Section headings: bold accent square containing the section number, large
    serif title, thin underline rule.
  * Code: dark monospace blocks (GitHub-style) — high contrast, clearly
    distinguished from prose.
  * Callouts: amber note-boxes for design tips; cool grey for cross-references.
  * Tables: accent header + zebra rows + thin border.

Edit the constants at the top of the file to change student / cover info.
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
    Flowable, Image, KeepTogether, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted,
)


# --------------------------------------------------------------------------- #
#  Edit me                                                                    #
# --------------------------------------------------------------------------- #

STUDENTS = [
    ("Boussaa Hasna",  "212131048993"),
    ("Rahali Hanane",  "222231632204"),
]
GROUP        = "—"
ACADEMIC_YR  = "2025 / 2026"

# --------------------------------------------------------------------------- #

HERE   = Path(__file__).resolve().parent.parent
LOGO   = Path("/Users/mac/multi/usthb_bw.png")
FIG_PI = HERE / "figures" / "pipeline.png"
FIG_EX = HERE / "figures" / "experiments.png"
OUTPUT = HERE / "report.pdf"

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# Palette
NAVY    = colors.HexColor("#0a2540")   # primary accent (dark)
AZURE   = colors.HexColor("#1e6fd9")   # primary accent (bright)
AMBER   = colors.HexColor("#e8801c")   # secondary highlight
INK     = colors.HexColor("#1a1f2e")   # body text on light
PAPER   = colors.HexColor("#ffffff")
SOFT    = colors.HexColor("#f5f7fb")   # block background
BORDER  = colors.HexColor("#d6dde9")
NOTE_BG = colors.HexColor("#fff5dc")   # amber callout
NOTE_BD = colors.HexColor("#e9c977")
CODE_BG = colors.HexColor("#0d1b2a")   # near-black for code
CODE_FG = colors.HexColor("#e6edf3")
MUTED   = colors.HexColor("#6b7280")


# --------------------------------------------------------------------------- #
#  Styles                                                                     #
# --------------------------------------------------------------------------- #

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        # ---- cover ------------------------------------------------------- #
        "cover_band_top": ParagraphStyle(
            "cover_band_top", parent=base,
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            alignment=TA_CENTER, textColor=colors.white,
        ),
        "cover_band_sub": ParagraphStyle(
            "cover_band_sub", parent=base,
            fontName="Helvetica", fontSize=9.5, leading=12,
            alignment=TA_CENTER, textColor=colors.HexColor("#cfd7e5"),
        ),
        "cover_eyebrow": ParagraphStyle(
            "cover_eyebrow", parent=base,
            fontName="Helvetica-Bold", fontSize=10, leading=12,
            alignment=TA_CENTER, textColor=AMBER,
            spaceBefore=4, spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base,
            fontName="Helvetica-Bold", fontSize=26, leading=30,
            alignment=TA_CENTER, textColor=NAVY,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base,
            fontName="Helvetica", fontSize=14, leading=18,
            alignment=TA_CENTER, textColor=AZURE, spaceAfter=10,
        ),
        "cover_blurb": ParagraphStyle(
            "cover_blurb", parent=base,
            fontName="Times-Italic", fontSize=11, leading=14,
            alignment=TA_CENTER, textColor=MUTED,
        ),
        "cover_info_k": ParagraphStyle(
            "cover_info_k", parent=base,
            fontName="Helvetica-Bold", fontSize=10.5, leading=14,
            alignment=TA_RIGHT, textColor=NAVY,
        ),
        "cover_info_v": ParagraphStyle(
            "cover_info_v", parent=base,
            fontName="Times-Roman", fontSize=11, leading=14,
            alignment=TA_LEFT, textColor=INK,
        ),
        "cover_year": ParagraphStyle(
            "cover_year", parent=base,
            fontName="Helvetica-Bold", fontSize=12, leading=15,
            alignment=TA_CENTER, textColor=AMBER,
            spaceBefore=18,
        ),

        # ---- body -------------------------------------------------------- #
        "h1_title": ParagraphStyle(
            "h1_title", parent=base,
            fontName="Helvetica-Bold", fontSize=17, leading=22,
            textColor=NAVY,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base,
            fontName="Helvetica-Bold", fontSize=12.5, leading=16,
            spaceBefore=12, spaceAfter=4, textColor=AZURE,
        ),
        "body": ParagraphStyle(
            "body", parent=base,
            fontName="Times-Roman", fontSize=11, leading=15.5,
            alignment=TA_JUSTIFY, spaceAfter=5, textColor=INK,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base,
            fontName="Times-Roman", fontSize=11, leading=14.5,
            leftIndent=18, bulletIndent=4, spaceAfter=3, textColor=INK,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base,
            fontName="Helvetica-Oblique", fontSize=9.5, leading=12,
            alignment=TA_CENTER, textColor=MUTED,
            spaceBefore=4, spaceAfter=12,
        ),
        "code_inner": ParagraphStyle(
            "code_inner", parent=base,
            fontName="Courier", fontSize=8.8, leading=11.5,
            textColor=colors.HexColor("#ffffff"),
            alignment=TA_LEFT,
        ),
        "note": ParagraphStyle(
            "note", parent=base,
            fontName="Helvetica", fontSize=10.2, leading=13.5,
            leftIndent=10, rightIndent=10,
            textColor=INK, backColor=NOTE_BG,
            borderColor=NOTE_BD, borderWidth=0.6, borderPadding=8,
            spaceBefore=6, spaceAfter=10,
        ),
        "toc_item": ParagraphStyle(
            "toc_item", parent=base,
            fontName="Helvetica", fontSize=11, leading=18, textColor=INK,
        ),
        "toc_num": ParagraphStyle(
            "toc_num", parent=base,
            fontName="Helvetica-Bold", fontSize=11, leading=18, textColor=AMBER,
        ),
    }


# --------------------------------------------------------------------------- #
#  Custom flowables                                                           #
# --------------------------------------------------------------------------- #

class CoverBand(Flowable):
    """Full-width navy band drawn at the top of the cover page."""
    def __init__(self, height_cm: float = 4.0):
        super().__init__()
        self.height = height_cm * cm

    def draw(self):
        c = self.canv
        page_w = PAGE_W
        # The flowable's origin (0,0) is bottom-left of its allotted box.
        # We want the band to extend to the page edges, so we draw outside.
        x = -MARGIN
        w = page_w
        c.setFillColor(NAVY)
        c.rect(x, 0, w, self.height, fill=1, stroke=0)
        # Decorative amber accent ribbon at the very bottom of the band
        c.setFillColor(AMBER)
        c.rect(x, 0, w, 0.18 * cm, fill=1, stroke=0)

        # Text inside the band
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(page_w / 2 - MARGIN,
                            self.height - 1.05 * cm,
                            "USTHB — Université des Sciences et de la Technologie Houari Boumediene")
        c.setFont("Helvetica", 9.5)
        c.setFillColor(colors.HexColor("#cfd7e5"))
        c.drawCentredString(page_w / 2 - MARGIN,
                            self.height - 1.75 * cm,
                            "Faculté d'Électronique et d'Informatique  •  Département d'Informatique")
        c.drawCentredString(page_w / 2 - MARGIN,
                            self.height - 2.45 * cm,
                            "Module Systèmes Multimédia  •  M1 Génie Logiciel")

    def wrap(self, availWidth, availHeight):
        return availWidth, self.height


class SectionHeader(Flowable):
    """Numbered square + title for a top-level section."""
    def __init__(self, number: str, title: str, *, width: float):
        super().__init__()
        self.number = number
        self.title = title
        self.width = width
        self.height = 1.25 * cm

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        # Number square
        box = 0.95 * cm
        c.setFillColor(NAVY)
        c.rect(0, (self.height - box) / 2, box, box, fill=1, stroke=0)
        c.setFillColor(AMBER)
        c.rect(0, (self.height - box) / 2, box, 0.12 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(
            box / 2,
            (self.height - box) / 2 + box / 2 - 5,
            self.number,
        )
        # Title
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(box + 0.4 * cm,
                     (self.height - box) / 2 + box / 2 - 6, self.title)
        # Underline rule
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(0, 0.05 * cm, self.width, 0.05 * cm)


def code_block(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    """Return a Table holding a dark code block — reliable across viewers."""
    safe = (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
                .replace(" ", "&nbsp;"))
    para = Paragraph(safe, styles["code_inner"])
    inner_w = PAGE_W - 2 * MARGIN
    tbl = Table([[para]], colWidths=[inner_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CODE_BG),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE",    (0, 0), (-1, -1), 3, AMBER),
    ]))
    return tbl


class HR(Flowable):
    """A thin horizontal rule."""
    def __init__(self, *, width: float, color, thickness: float = 0.4):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 1

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


# --------------------------------------------------------------------------- #
#  Page header / footer (later pages)                                         #
# --------------------------------------------------------------------------- #

def _header_footer(c: canvas.Canvas, doc) -> None:
    c.saveState()

    # Top-left navy strip running the full page height (decorative)
    c.setFillColor(NAVY)
    c.rect(0, 0, 0.45 * cm, PAGE_H, fill=1, stroke=0)
    c.setFillColor(AMBER)
    c.rect(0, 0, 0.45 * cm, 0.6 * cm, fill=1, stroke=0)   # amber foot

    # Header text
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, PAGE_H - MARGIN + 0.55 * cm, "USTHB")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#444"))
    c.drawString(MARGIN, PAGE_H - MARGIN + 0.2 * cm,
                 "Faculté d'Électronique et d'Informatique  •  Département d'Informatique")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 0.55 * cm,
                      "Simplified MPEG-4 Pipeline")
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(colors.HexColor("#444"))
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 0.2 * cm,
                      "Rapport du projet — 2025 / 2026")

    # Header rule
    c.setStrokeColor(BORDER); c.setLineWidth(0.5)
    c.line(MARGIN, PAGE_H - MARGIN - 0.2 * cm,
           PAGE_W - MARGIN, PAGE_H - MARGIN - 0.2 * cm)

    # Footer: page number in a small amber pill
    pn = str(doc.page)
    c.setFont("Helvetica-Bold", 9)
    text_w = c.stringWidth(pn, "Helvetica-Bold", 9)
    pill_w = max(text_w + 14, 20)
    pill_x = (PAGE_W - pill_w) / 2
    pill_y = MARGIN / 2 - 4
    c.setFillColor(AMBER)
    c.roundRect(pill_x, pill_y, pill_w, 12, 6, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawCentredString(PAGE_W / 2, pill_y + 3, pn)

    c.restoreState()


# --------------------------------------------------------------------------- #
#  Cover page                                                                 #
# --------------------------------------------------------------------------- #

def _cover_story(s) -> list:
    story: list = []
    story.append(CoverBand(height_cm=4.0))
    story.append(Spacer(1, 1.4 * cm))

    # USTHB seal
    if LOGO.exists():
        img = Image(str(LOGO), width=4.2 * cm, height=4.2 * 328 / 612 * cm)
        img.hAlign = "CENTER"
        story.append(img)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("PROJET DE MODULE  •  MULTIMÉDIA", s["cover_eyebrow"]))
    story.append(Paragraph("Simplified MPEG-4", s["cover_title"]))
    story.append(Paragraph("Video Encoder Pipeline", s["cover_title"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(HR(width=10 * cm, color=AMBER, thickness=1.2))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Encodeur vidéo en cinq étapes",
                           s["cover_subtitle"]))
    story.append(Paragraph(
        "Pré-traitement &nbsp; • &nbsp; DCT / Quantification &nbsp; • &nbsp; "
        "Estimation de mouvement &nbsp; • &nbsp; Codage entropique &nbsp; • &nbsp; "
        "Évaluation",
        s["cover_blurb"],
    ))
    story.append(Spacer(1, 1.0 * cm))

    # Info card (two-column key/value with zebra rows)
    info_rows = [[Paragraph("Réalisé par", s["cover_info_k"]),
                  Paragraph("", s["cover_info_v"])]]
    for name, mat in STUDENTS:
        info_rows.append([
            Paragraph(name, s["cover_info_k"]),
            Paragraph(f"Matricule&nbsp;&nbsp;{mat}", s["cover_info_v"]),
        ])
    info_rows += [
        [Paragraph("Groupe",           s["cover_info_k"]),
         Paragraph(GROUP,               s["cover_info_v"])],
        [Paragraph("Module",           s["cover_info_k"]),
         Paragraph("Systèmes Multimédia (M1)", s["cover_info_v"])],
        [Paragraph("Année universitaire", s["cover_info_k"]),
         Paragraph(ACADEMIC_YR,         s["cover_info_v"])],
    ]
    tbl = Table(info_rows, colWidths=[5.8 * cm, 8.2 * cm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [SOFT, PAPER]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, NAVY),
    ]))
    tbl.hAlign = "CENTER"
    story.append(tbl)

    story.append(Paragraph(ACADEMIC_YR, s["cover_year"]))
    story.append(PageBreak())
    return story


# --------------------------------------------------------------------------- #
#  Table of contents                                                          #
# --------------------------------------------------------------------------- #

_TOC_ENTRIES = [
    ("1", "Introduction",                                  3),
    ("2", "Vue d'ensemble du pipeline",                    3),
    ("3", "Choix de conception et justification",          4),
    ("4", "Extraits d'implémentation",                     4),
    ("5", "Analyse expérimentale",                         5),
    ("6", "Résultats résumés",                             6),
    ("7", "Conclusion et perspectives",                    7),
]


def _toc_story(s) -> list:
    story: list = []
    inner_w = PAGE_W - 2 * MARGIN
    story.append(SectionHeader("·", "Table des matières", width=inner_w))
    story.append(Spacer(1, 0.4 * cm))

    rows = []
    for num, title, page in _TOC_ENTRIES:
        rows.append([
            Paragraph(num,        s["toc_num"]),
            Paragraph(title,      s["toc_item"]),
            Paragraph(f"p. {page}", s["toc_item"]),
        ])
    t = Table(rows, colWidths=[1.2 * cm, inner_w - 3.0 * cm, 1.8 * cm])
    t.setStyle(TableStyle([
        ("VALIGN",          (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",      (0, 0), (-1, -1), 6),
        ("LINEBELOW",       (0, 0), (-1, -1), 0.3, BORDER),
        ("ALIGN",           (2, 0), (2, -1), "RIGHT"),
        ("TEXTCOLOR",       (2, 0), (2, -1), MUTED),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


# --------------------------------------------------------------------------- #
#  Body sections                                                              #
# --------------------------------------------------------------------------- #

def _section(num: str, title: str, *, inner_w: float) -> SectionHeader:
    return SectionHeader(num, title, width=inner_w)


def _body_story(s) -> list:
    inner_w = PAGE_W - 2 * MARGIN
    story: list = []

    # 1. Introduction
    story.append(_section("1", "Introduction", inner_w=inner_w))
    story.append(Paragraph(
        "Ce projet implémente une chaîne d'encodage vidéo inspirée du standard "
        "MPEG-4 en Python. Il couvre les cinq grandes étapes d'un codec moderne — "
        "pré-traitement colorimétrique, codage intra-trame par DCT, codage "
        "inter-trame avec estimation de mouvement, codage entropique sans perte, "
        "puis évaluation et visualisation. Le résultat est un fichier binaire "
        "compact (<font face='Courier'>video.bin</font>) reconstructible image par image.",
        s["body"],
    ))
    story.append(Paragraph(
        "L'implémentation est organisée autour d'un package "
        "<font face='Courier'>mpeg4mini</font> dont chaque sous-module correspond "
        "à une partie de l'énoncé. Un point d'entrée unique "
        "<font face='Courier'>main.py</font> expose les sous-commandes "
        "<i>sample</i>, <i>encode</i>, <i>decode</i>, <i>visualise</i> et "
        "<i>experiments</i> — exécutables sans dépendance non standard.",
        s["body"],
    ))

    # 2. Pipeline overview
    story.append(_section("2", "Vue d'ensemble du pipeline", inner_w=inner_w))
    story.append(Paragraph(
        "Le pipeline traite les images dans l'ordre BGR (convention OpenCV) "
        "et produit pour chaque trame un enregistrement de type <i>I</i> ou <i>P</i> :",
        s["body"],
    ))
    stages = [
        ("Pré-traitement (Partie 1)",
         "Conversion BGR → YCbCr (ITU-R BT.601) puis sous-échantillonnage "
         "chromatique 4:2:0 par filtre boîte 2×2."),
        ("Codage intra (Partie 2)",
         "Découpage en blocs 8×8, DCT-II orthonormée, division par la matrice "
         "de quantification JPEG mise à l'échelle selon le facteur qualité QF."),
        ("Codage inter (Partie 3)",
         "Pour chaque macrobloc 16×16, recherche exhaustive du meilleur "
         "appariement dans une fenêtre ±S sur la trame précédente reconstruite "
         "(coût SAD). Le résiduel passe lui-même par DCT + quantification."),
        ("Codage entropique (Partie 4)",
         "Sérialisation pickle des structures (config, motion fields, coefficients "
         "int16) puis compression DEFLATE niveau 9. Le tout est écrit dans le "
         "conteneur MV1 (<font face='Courier'>magic = b'MV1\\x00'</font>)."),
        ("Évaluation et visualisation (Partie 5)",
         "Calcul de PSNR par trame, ratio de compression et figure matplotlib "
         "à cinq lignes couvrant toutes les étapes."),
    ]
    for name, desc in stages:
        story.append(Paragraph(f"<b>{name}.</b> {desc}", s["bullet"]))

    # 3. Design choices
    story.append(_section("3", "Choix de conception et justification", inner_w=inner_w))
    choices = [
        ("Espace YCbCr BT.601",
         "Matrice constante, inversible analytiquement, qui concentre la "
         "majorité de l'information perceptuelle dans le canal Y."),
        ("Sous-échantillonnage 4:2:0",
         "Réduit immédiatement le nombre d'échantillons chromatiques de 75 % "
         "sans dégradation visuelle significative — configuration standard de "
         "JPEG, MPEG-2, H.264, H.265."),
        ("DCT-II orthonormée 8×8",
         "Compatible JPEG : on réutilise les matrices de quantification "
         "standardisées (ITU-T T.81 Annexe K). La transformation orthonormée "
         "permet d'inverser par simple transposition."),
        ("Quantification scalable par QF",
         "L'échelle libjpeg <i>scale = 5000/QF</i> pour QF&lt;50, sinon "
         "<i>200 − 2·QF</i>, balaye tout QF ∈ [1, 100] avec une seule paire de tables."),
        ("Macrobloc 16×16 + recherche exhaustive ±8",
         "16×16 est la taille de macrobloc des spécifications MPEG-1 à H.264 ; "
         "la recherche exhaustive donne l'optimum SAD et sert de référence pour "
         "les recherches rapides ultérieures."),
        ("DEFLATE pour l'entropie",
         "LZ77 + Huffman, donc adapté à la fois aux longs runs de zéros "
         "post-quantification et à la statistique non-uniforme des coefficients DC."),
    ]
    for name, desc in choices:
        story.append(Paragraph(f"<b>{name}.</b> {desc}", s["bullet"]))

    story.append(Paragraph(
        "<b>Note —</b> tous ces paramètres sont rassemblés dans la dataclass "
        "frozen <font face='Courier'>CodecConfig</font> (un seul lieu de "
        "vérité), ce qui simplifie le passage de paramètres et le balayage "
        "automatisé pour les expérimentations.",
        s["note"],
    ))

    # 4. Implementation excerpts
    story.append(_section("4", "Extraits d'implémentation", inner_w=inner_w))

    story.append(Paragraph("4.1.&nbsp;&nbsp;Encodage d'un plan intra (Partie 2)", s["h2"]))
    story.append(code_block(
        "def encode_plane(plane, q_table, block=8):\n"
        "    centred = plane.astype(np.float32) - 128.0\n"
        "    blocks  = tile(centred, block)\n"
        "    coeffs  = dctn(blocks, type=2, norm='ortho', axes=(-2, -1))\n"
        "    quant   = np.round(coeffs / q_table[None, :, :]).astype(np.int16)\n"
        "    # reconstruction (servira de reference aux P-frames)\n"
        "    dequant = quant.astype(np.float32) * q_table[None, :, :]\n"
        "    recon   = untile(idctn(dequant, type=2, norm='ortho',\n"
        "                            axes=(-2, -1)), plane.shape, block) + 128.0\n"
        "    return quant, np.clip(recon, 0.0, 255.0)",
        s,
    ))

    story.append(Paragraph("4.2.&nbsp;&nbsp;Estimation de mouvement (Partie 3)", s["h2"]))
    story.append(code_block(
        "def estimate(current, reference, macroblock, search_range):\n"
        "    rows = current.shape[0] // macroblock\n"
        "    cols = current.shape[1] // macroblock\n"
        "    motion = np.zeros((rows, cols, 2), dtype=np.int16)\n"
        "    ref = np.pad(reference, search_range, mode='edge')\n"
        "    for by in range(rows):\n"
        "        for bx in range(cols):\n"
        "            y0, x0 = by*macroblock, bx*macroblock\n"
        "            block  = current[y0:y0+macroblock, x0:x0+macroblock]\n"
        "            best   = (float('inf'), 0, 0)\n"
        "            for dy in range(-search_range, search_range+1):\n"
        "                for dx in range(-search_range, search_range+1):\n"
        "                    cand = ref[y0+dy+search_range:y0+dy+search_range+macroblock,\n"
        "                               x0+dx+search_range:x0+dx+search_range+macroblock]\n"
        "                    cost = _sad(block, cand)\n"
        "                    if cost < best[0]: best = (cost, dy, dx)\n"
        "            motion[by, bx] = best[1], best[2]\n"
        "    return motion",
        s,
    ))

    story.append(Paragraph(
        "<b>Astuce —</b> on padde la référence une seule fois en mode "
        "<font face='Courier'>'edge'</font> avant la boucle, ce qui élimine "
        "tout test de bord à l'intérieur du double-for et accélère "
        "sensiblement Python pur.",
        s["note"],
    ))

    # 5. Experiments
    story.append(_section("5", "Analyse expérimentale", inner_w=inner_w))
    story.append(Paragraph(
        "Le clip synthétique <font face='Courier'>data/sample_frames</font> "
        "compte 16 trames 192×144. Il contient un fond sinusoïdal statique "
        "et un disque texturé qui traverse l'image de gauche à droite. Cette "
        "scène expose simultanément trois mécanismes du codec : texture haute "
        "fréquence (DCT), translation rigide (estimation de mouvement) et "
        "discontinuité (bande verticale blanche).",
        s["body"],
    ))

    story.append(Paragraph("5.1.&nbsp;&nbsp;Visualisation du pipeline (Partie 5b)", s["h2"]))
    if FIG_PI.exists():
        max_w = PAGE_W - 2 * MARGIN
        img = Image(str(FIG_PI), width=max_w, height=max_w * 530 / 600)
        story.append(img)
        story.append(Paragraph(
            "Figure 1 — Visualisation des cinq étapes du codec sur le clip "
            "de référence (QF = 50, GOP = 4).",
            s["caption"],
        ))

    story.append(Paragraph("5.2.&nbsp;&nbsp;Balayage de paramètres (Partie 5c)", s["h2"]))
    if FIG_EX.exists():
        max_w = PAGE_W - 2 * MARGIN
        img = Image(str(FIG_EX), width=max_w, height=max_w * 460 / 1500)
        story.append(img)
        story.append(Paragraph(
            "Figure 2 — Ratio de compression vs facteur qualité (gauche) et "
            "vs taille de GOP (centre) ; PSNR moyen vs facteur qualité (droite).",
            s["caption"],
        ))

    story.append(Paragraph(
        "<b>Interprétation.</b> Le ratio chute de façon attendue avec QF "
        "(quantification plus fine ⇒ moins de zéros à compresser). La courbe "
        "Ratio vs GOP confirme le bénéfice du codage inter : passer de GOP=1 "
        "(tout-I) à GOP=4 fait gagner ≈ 7 % de compression, puis la courbe "
        "plafonne car la précision SAD limite les résiduels minimaux atteignables. "
        "Le PSNR moyen progresse linéairement de 26 dB à 39 dB lorsque QF passe "
        "de 10 à 95 — comportement classique d'un quantificateur scalaire JPEG.",
        s["body"],
    ))

    # 6. Results
    story.append(_section("6", "Résultats résumés", inner_w=inner_w))
    rows = [
        ["Paramètre", "Valeur"],
        ["Trames d'entrée",          "16 trames PNG 192 × 144 BGR"],
        ["Taille brute totale",       "1 327 104 octets"],
        ["Taille après DEFLATE",      "≈ 28 600 octets"],
        ["Ratio de compression",      "≈ 46×"],
        ["PSNR moyen (QF = 50)",      "≈ 32.2 dB"],
        ["GOP utilisé",               "4 (4 trames I sur 16)"],
        ["Fenêtre de recherche ±S",   "8 pixels"],
        ["Temps d'encodage",          "≈ 1.8 s (Python pur, M1)"],
    ]
    tbl = Table(rows, colWidths=[7.0 * cm, 9.0 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",      (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",       (0, 0), (-1, 0), colors.white),
        ("FONTNAME",        (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",        (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",        (1, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE",        (0, 0), (-1, -1), 10),
        ("ALIGN",           (0, 0), (-1, 0), "CENTER"),
        ("ALIGN",           (1, 1), (-1, -1), "LEFT"),
        ("ROWBACKGROUNDS",  (0, 1), (-1, -1), [SOFT, PAPER]),
        ("INNERGRID",       (0, 0), (-1, -1), 0.25, BORDER),
        ("BOX",             (0, 0), (-1, -1), 0.4, NAVY),
        ("LINEABOVE",       (0, 0), (-1, 0), 2.0, AMBER),  # amber strip
        ("VALIGN",          (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",      (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 6),
        ("LEFTPADDING",     (0, 0), (-1, -1), 10),
    ]))
    story.append(tbl)

    # 7. Conclusion
    story.append(_section("7", "Conclusion et perspectives", inner_w=inner_w))
    story.append(Paragraph(
        "L'implémentation couvre les cinq parties du sujet en un seul package "
        "Python sans dépendance non standard au-delà de NumPy/SciPy/OpenCV/Matplotlib. "
        "L'architecture en sous-modules <i>pipeline.preprocess</i>, <i>pipeline.intra</i>, "
        "<i>pipeline.inter</i>, <i>pipeline.entropy</i> calque le découpage de "
        "l'énoncé, ce qui rend chaque étape facilement remplaçable. Les résultats "
        "numériques (≈ 46× de compression à PSNR ≈ 32 dB) sont cohérents avec "
        "ce qu'on attend d'un encodeur JPEG-MV simplifié.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>Pistes d'amélioration.</b> Recherche logarithmique trois-passes "
        "(×3-4 plus rapide à qualité quasi équivalente), codage CABAC en lieu "
        "et place de DEFLATE pour mieux exploiter la statistique des "
        "coefficients, et scan zigzag + RLE avant l'entropie pour réduire "
        "encore la taille du conteneur MV1.",
        s["body"],
    ))
    return story


# --------------------------------------------------------------------------- #
#  Build                                                                      #
# --------------------------------------------------------------------------- #

def build(output: Path = OUTPUT) -> Path:
    s = _styles()
    doc = SimpleDocTemplate(
        str(output), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 1.2 * cm, bottomMargin=MARGIN,
    )
    story = _cover_story(s) + _toc_story(s) + _body_story(s)
    doc.build(
        story,
        onFirstPage=lambda c, d: None,   # bare cover
        onLaterPages=_header_footer,
    )
    return output


if __name__ == "__main__":
    out = build()
    print(f"Wrote {out}  ({out.stat().st_size / 1024:.1f} KB)")
