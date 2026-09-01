"""Strategy toolkit PDF generator — branded one-pagers with framework + operational guidelines."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from blueprint_pdf import _styles, _cover

INK = colors.HexColor("#0A0A0A")
LIME = colors.HexColor("#C6F135")
LIGHT = colors.HexColor("#e5e7eb")


def _grid_flowable(S, grid):
    if grid.get("type") == "2x2":
        q = grid["quadrants"]
        def cell(item):
            return [Paragraph(item["title"], S["cellhead"]), Spacer(1, 3), Paragraph(item["desc"], S["cell"])]
        data = [[cell(q[0]), cell(q[1])], [cell(q[2]), cell(q[3])]]
        t = Table(data, colWidths=[82 * mm, 82 * mm], rowHeights=[42 * mm, 42 * mm])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, INK),
            ("INNERGRID", (0, 0), (-1, -1), 1, INK),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f7ffe0")),
            ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#f7ffe0")),
        ]))
        return t
    rows = [[Paragraph(f'<b>{it["title"]}</b>', S["cell"]), Paragraph(it["desc"], S["cell"])] for it in grid["items"]]
    t = Table(rows, colWidths=[52 * mm, 112 * mm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    return t


def _bullets(S, items):
    return [Paragraph(f'<font color="#7c9a12">■</font>&nbsp;&nbsp;{it}', S["body"]) for it in items]


def _steps(S, items):
    return [Paragraph(f'<b><font color="#7c9a12">{i+1}.</font></b>&nbsp;&nbsp;{it}', S["body"]) for i, it in enumerate(items)]


def build_tool_pdf(tool):
    buf = BytesIO()
    S = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title=tool["name"])
    story = []
    _cover(story, S, tool["name"], tool.get("tagline", ""))
    story.append(Paragraph("WHAT IT IS", S["kicker"]))
    story.append(Paragraph(tool.get("what_it_is", ""), S["body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("THE FRAMEWORK", S["kicker"]))
    story.append(Spacer(1, 4))
    story.append(_grid_flowable(S, tool["grid"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("WHEN TO USE IT", S["kicker"]))
    for f in _bullets(S, tool.get("when_to_use", [])):
        story.append(f)
    story.append(Spacer(1, 6))
    story.append(Paragraph("HOW TO RUN IT — OPERATIONAL GUIDELINES", S["kicker"]))
    for f in _steps(S, tool.get("how_to", [])):
        story.append(f)
    if tool.get("watch_outs"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("WATCH-OUTS", S["kicker"]))
        for f in _bullets(S, tool["watch_outs"]):
            story.append(f)
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=LIME))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Want help applying this to a live decision? Book a 1:1 strategy session with Sudarshan Karweer at "
        "<b>www.sudarshankarweer.com</b>.", S["body"]))
    story.append(Paragraph("© Sudarshan Karweer · Strategic Advisory. Framework worksheet for professional use.", S["small"]))
def _tool_section(S, tool, PageBreak_cls):
    flow = [PageBreak_cls()]
    flow.append(Paragraph(tool["category"].upper(), S["kicker"]))
    flow.append(Paragraph(tool["name"], S["h1"]))
    if tool.get("tagline"):
        flow.append(Paragraph(tool["tagline"], S["small"]))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(tool.get("what_it_is", ""), S["body"]))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph("THE FRAMEWORK", S["kicker"]))
    flow.append(Spacer(1, 4))
    flow.append(_grid_flowable(S, tool["grid"]))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph("WHEN TO USE IT", S["kicker"]))
    flow += _bullets(S, tool.get("when_to_use", []))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph("HOW TO RUN IT — OPERATIONAL GUIDELINES", S["kicker"]))
    flow += _steps(S, tool.get("how_to", []))
    if tool.get("watch_outs"):
        flow.append(Spacer(1, 6))
        flow.append(Paragraph("WATCH-OUTS", S["kicker"]))
        flow += _bullets(S, tool["watch_outs"])
    return flow


def build_toolkit_bundle_pdf():
    """The complete 13-tool toolkit as one premium download."""
    from reportlab.platypus import PageBreak
    from strategy_tools import STRATEGY_TOOLS
    buf = BytesIO()
    S = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title="The Complete Strategy Toolkit")
    story = []
    _cover(story, S, "The Complete\nStrategy Toolkit",
           f"{len(STRATEGY_TOOLS)} consultant-grade frameworks, with operational guidelines")
    story.append(Paragraph("WHAT'S INSIDE", S["kicker"]))
    story.append(Paragraph("Thirteen frameworks", S["h2"]))
    contents = [[Paragraph(f'<b>{i+1}.</b>&nbsp; {t["name"]}', S["cell"]),
                 Paragraph(t["category"], S["cell"])] for i, t in enumerate(STRATEGY_TOOLS)]
    ct = Table(contents, colWidths=[120 * mm, 44 * mm])
    ct.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LIGHT),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LEFTPADDING", (0, 0), (0, -1), 0)]))
    story.append(ct)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Each framework below includes the diagram, when to use it, and step-by-step operational guidelines. "
                           "These are the tools Sudarshan Karweer uses on live strategy engagements.", S["body"]))
    for t in STRATEGY_TOOLS:
        story += _tool_section(S, t, PageBreak)
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=LIME))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Put these to work on a live decision — book a 1:1 strategy session at <b>www.sudarshankarweer.com</b>.", S["body"]))
    story.append(Paragraph("© Sudarshan Karweer · Strategic Advisory. For professional use.", S["small"]))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

