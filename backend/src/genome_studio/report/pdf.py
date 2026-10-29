"""PDF report generation with reportlab.

Uses the platypus (flowables) API. Registers DejaVu Sans if available
for full Unicode (Cyrillic, etc.); falls back to Helvetica otherwise.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from genome_studio import __version__


_FONTS_DIR = Path(__file__).parent / "fonts"


def _register_fonts() -> tuple[str, str]:
    """Register DejaVu fonts if present.

    Returns (regular_font_name, bold_font_name).
    """
    regular = _FONTS_DIR / "DejaVuSans.ttf"
    bold = _FONTS_DIR / "DejaVuSans-Bold.ttf"

    if regular.exists() and bold.exists():
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(regular)))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(bold)))
            pdfmetrics.registerFontFamily(
                "DejaVuSans",
                normal="DejaVuSans",
                bold="DejaVuSans-Bold",
                italic="DejaVuSans",
                boldItalic="DejaVuSans-Bold",
            )
            return "DejaVuSans", "DejaVuSans-Bold"
        except Exception:
            pass

    return "Helvetica", "Helvetica-Bold"


_REGULAR, _BOLD = _register_fonts()


def _safe(text: Any) -> str:
    """Escape special characters for reportlab Paragraph markup."""
    s = str(text)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def _styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    body = ParagraphStyle(
        name="BodyTextCustom",
        parent=ss["BodyText"],
        fontName=_REGULAR,
        fontSize=10,
        leading=13,
    )
    heading1 = ParagraphStyle(
        name="Heading1Custom",
        parent=ss["Heading1"],
        fontName=_BOLD,
        fontSize=18,
        leading=22,
    )
    heading2 = ParagraphStyle(
        name="Heading2Custom",
        parent=ss["Heading2"],
        fontName=_BOLD,
        fontSize=14,
        leading=18,
    )
    heading3 = ParagraphStyle(
        name="Heading3Custom",
        parent=ss["Heading3"],
        fontName=_BOLD,
        fontSize=11,
        leading=14,
    )
    small = ParagraphStyle(
        name="Small",
        parent=body,
        fontSize=9,
        textColor=colors.grey,
    )
    mono = ParagraphStyle(
        name="Mono",
        parent=body,
        fontName="Courier",
        fontSize=8,
        leading=10,
    )
    return {
        "title": heading1,
        "h2": heading2,
        "h3": heading3,
        "body": body,
        "small": small,
        "mono": mono,
    }


def _kv_table(rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [Paragraph(f"<b>{_safe(k)}</b>", styles["body"]),
         Paragraph(_safe(v), styles["body"])]
        for k, v in rows
    ]
    t = Table(data, colWidths=[4 * cm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.lightgrey),
    ]))
    return t


def _two_col_table(header: list[str], rows: list[list[str]], styles: dict[str, Any]) -> Table:
    data = [[Paragraph(f"<b>{_safe(h)}</b>", styles["body"]) for h in header]]
    for row in rows:
        data.append([Paragraph(_safe(c), styles["body"]) for c in row])
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    return t


def _section_title(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(_safe(text), styles["h2"])


def _render_project_header(project: dict, styles: dict[str, Any]) -> list:
    out: list = []
    out.append(Paragraph("Genome Studio — Project Report", styles["title"]))
    out.append(Spacer(1, 0.3 * cm))
    out.append(_kv_table([
        ("Project", project.get("name", "?")),
        ("Organism", project.get("organism") or "—"),
        ("Description", project.get("description") or "—"),
        ("Project ID", str(project.get("id", "?"))),
        ("Created", project.get("created_at", "?")),
        ("Updated", project.get("updated_at", "?")),
    ], styles))
    out.append(Spacer(1, 0.2 * cm))
    out.append(Paragraph(
        "Generated " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        + " — Genome Studio v" + __version__,
        styles["small"],
    ))
    return out


def _render_warnings(warnings: list[dict], styles: dict[str, Any]) -> list:
    out: list = []
    out.append(_section_title("Warnings", styles))
    if not warnings:
        out.append(Paragraph("No warnings.", styles["body"]))
        return out

    open_w = [w for w in warnings if w.get("status") == "open"]
    ack_w = [w for w in warnings if w.get("status") == "acknowledged"]

    out.append(Paragraph(
        "Open: <b>" + str(len(open_w)) + "</b>, "
        "Acknowledged: <b>" + str(len(ack_w)) + "</b>",
        styles["body"],
    ))
    out.append(Spacer(1, 0.2 * cm))

    for w in warnings:
        head = "[" + w.get("severity", "?").upper() + "] "
        head += w.get("type", "?") + " (" + w.get("level", "?") + ")"
        out.append(Paragraph(_safe(head), styles["h3"]))
        out.append(Paragraph(_safe(w.get("message", "")), styles["body"]))
        status = w.get("status", "?")
        if status == "acknowledged":
            out.append(Paragraph(
                "✓ Acknowledged by " + _safe(w.get("acknowledged_by", "?"))
                + ": " + _safe(w.get("acknowledgment_note", "")),
                styles["small"],
            ))
        out.append(Spacer(1, 0.2 * cm))
    return out


def _render_plan(exp: dict, styles: dict[str, Any]) -> list:
    payload = exp.get("payload") or {}
    plan = (payload.get("plan") if "plan" in payload else payload) or {}
    goal = plan.get("goal", {})
    iv = plan.get("intervention", {})
    steps = plan.get("steps", [])

    out: list = [_section_title("Plan — " + exp.get("title", "?"), styles)]
    out.append(_kv_table([
        ("Intent", goal.get("intent", "?")),
        ("Target gene", goal.get("target", {}).get("gene", "?")),
        ("Organism", goal.get("target", {}).get("organism", "?")),
        ("Intervention", iv.get("kind", "?")),
        ("Predicted effect", f"{iv.get('predicted_effect', 0):.2f}"),
        ("Off-target risk", f"{iv.get('off_target_risk', 0):.2f}"),
        ("Essentiality risk", f"{iv.get('essentiality_risk', 0):.2f}"),
        ("Complexity", str(iv.get("complexity", "?"))),
    ], styles))
    out.append(Spacer(1, 0.2 * cm))

    if iv.get("rationale"):
        out.append(Paragraph("<b>Rationale:</b> " + _safe(iv["rationale"]), styles["body"]))
        out.append(Spacer(1, 0.2 * cm))

    if steps:
        out.append(Paragraph("<b>Steps:</b>", styles["body"]))
        rows = [[str(s.get("order", "?")), s.get("action", "?"), s.get("description", "?")]
                for s in steps]
        out.append(_two_col_table(["#", "Action", "Description"], rows, styles))
    return out


def _render_guides(exp: dict, styles: dict[str, Any]) -> list:
    payload = exp.get("payload") or {}
    guides = payload.get("guides", []) if isinstance(payload, dict) else []
    out: list = [_section_title("CRISPR guides — " + exp.get("title", "?"), styles)]
    if not guides:
        out.append(Paragraph("No guides.", styles["body"]))
        return out

    rows = [
        [str(i + 1), g.get("spacer", "?"), g.get("pam", "?"),
         g.get("strand", "?"), f"{g.get('gc_content', 0):.2f}", f"{g.get('score', 0):.2f}"]
        for i, g in enumerate(guides)
    ]
    out.append(_two_col_table(
        ["#", "Spacer", "PAM", "Strand", "GC", "Score"], rows, styles,
    ))
    return out


def _render_offtarget(exp: dict, styles: dict[str, Any]) -> list:
    payload = exp.get("payload") or {}
    summary = payload.get("summary", {})
    hits = payload.get("hits", [])
    out: list = [_section_title("Off-target — " + exp.get("title", "?"), styles)]
    out.append(_kv_table([
        ("Total hits", str(summary.get("total", 0))),
        ("Perfect (0 mm)", str(summary.get("perfect", 0))),
        ("Near (1-2 mm)", str(summary.get("near", 0))),
        ("Distant (>=3 mm)", str(summary.get("distant", 0))),
        ("Risk score", f"{summary.get('risk', 0):.2f}"),
    ], styles))
    if hits:
        out.append(Spacer(1, 0.2 * cm))
        rows = [
            [str(i + 1), h.get("locus_label", "?"), h.get("strand", "?"),
             str(h.get("mismatches", 0)), h.get("spacer", "?")]
            for i, h in enumerate(hits[:20])
        ]
        out.append(_two_col_table(
            ["#", "Locus", "Strand", "MM", "Spacer"], rows, styles,
        ))
        if len(hits) > 20:
            out.append(Paragraph(
                "Showing first 20 of " + str(len(hits)) + " hits.", styles["small"],
            ))
    return out


def _render_simulation(exp: dict, styles: dict[str, Any]) -> list:
    payload = exp.get("payload") or {}
    effect = payload.get("effect", {})
    tree = payload.get("consequence_tree", {})
    out: list = [_section_title("Simulation — " + exp.get("title", "?"), styles)]
    out.append(_kv_table([
        ("Effect type", effect.get("effect_type", "?")),
        ("Severity", f"{effect.get('severity', 0):.2f}"),
        ("Description", effect.get("description", "?")),
    ], styles))
    out.append(Spacer(1, 0.2 * cm))
    out.append(Paragraph("<b>Consequence tree:</b>", styles["body"]))
    _tree_to_text(tree, out, styles, depth=0)
    return out


def _tree_to_text(node: dict, out: list, styles: dict[str, Any], depth: int) -> None:
    if not isinstance(node, dict):
        return
    indent = "  " * depth
    line = indent + "[" + node.get("type", "?") + "] "
    line += node.get("description", "") or "(no description)"
    line += " (" + f"{node.get('confidence', 0):.0%}" + ")"
    out.append(Paragraph(_safe(line), styles["mono"]))
    for child in node.get("children", []) or []:
        _tree_to_text(child, out, styles, depth + 1)


def _render_sequencing(exp: dict, styles: dict[str, Any]) -> list:
    payload = exp.get("payload") or {}
    sanger = payload.get("sanger") or {}
    ngs = payload.get("ngs") or {}
    out: list = [_section_title("Sequencing — " + exp.get("title", "?"), styles)]

    alleles = sanger.get("alleles") or ngs.get("alleles") or []
    if alleles:
        rows = [[a.get("name", "?"), f"{a.get('fraction', 0):.2f}"] for a in alleles]
        out.append(_two_col_table(["Allele", "Fraction"], rows, styles))

    if ngs:
        out.append(Spacer(1, 0.2 * cm))
        out.append(Paragraph("<b>NGS:</b> total reads " + str(ngs.get("total_reads", 0)), styles["body"]))
    return out


def _render_experiments(experiments: list[dict], styles: dict[str, Any]) -> list:
    out: list = []
    latest: dict[str, dict] = {}
    for e in experiments:
        kind = e.get("kind", "?")
        if kind not in latest:
            latest[kind] = e

    if "plan" in latest:
        out.extend(_render_plan(latest["plan"], styles))
        out.append(Spacer(1, 0.5 * cm))

    if "crispr_design" in latest:
        out.extend(_render_guides(latest["crispr_design"], styles))
        out.append(Spacer(1, 0.5 * cm))

    if "offtarget" in latest:
        out.extend(_render_offtarget(latest["offtarget"], styles))
        out.append(Spacer(1, 0.5 * cm))

    if "simulation" in latest:
        out.extend(_render_simulation(latest["simulation"], styles))
        out.append(Spacer(1, 0.5 * cm))

    if "sequencing" in latest:
        out.extend(_render_sequencing(latest["sequencing"], styles))
        out.append(Spacer(1, 0.5 * cm))

    return out


def build_project_pdf(
    project: dict,
    experiments: list[dict],
    warnings: list[dict],
) -> bytes:
    """Build a PDF report for a project."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Genome Studio Report",
        author="Genome Studio",
    )
    styles = _styles()
    story: list = []

    story.extend(_render_project_header(project, styles))
    story.append(Spacer(1, 0.4 * cm))

    story.append(_section_title("Summary", styles))
    story.append(_kv_table([
        ("Experiments", str(len(experiments))),
        ("Warnings", str(len(warnings))),
    ], styles))
    story.append(Spacer(1, 0.3 * cm))

    story.extend(_render_warnings(warnings, styles))
    story.append(PageBreak())
    story.extend(_render_experiments(experiments, styles))

    doc.build(story)
    return buffer.getvalue()