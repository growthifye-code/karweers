"""Generic branded (dark + lime SK) PDF builder for AI-generated collateral."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from blueprint_pdf import _styles, _cover

INK = colors.HexColor("#0A0A0A")
LIME = colors.HexColor("#C6F135")


def build_collateral_pdf(content: dict) -> bytes:
    """content = {title, subtitle, sections:[{heading, body}], key_takeaways:[...]}."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title=content.get("title", "SK Collateral"))
    S = _styles()
    story = []
    _cover(story, S, content.get("title", "SK Insight"), content.get("subtitle", "Sudarshan Karweer · Strategic Advisory"))

    for sec in content.get("sections", []):
        head = (sec.get("heading") or "").strip()
        if head:
            story.append(Paragraph(head, S["h2"]))
            story.append(HRFlowable(width="100%", thickness=1, color=LIME, spaceAfter=8))
        body = sec.get("body") or ""
        paras = body.split("\n") if isinstance(body, str) else list(body)
        for p in paras:
            p = (p or "").strip()
            if p:
                story.append(Paragraph(p, S["body"]))
        story.append(Spacer(1, 6))

    takeaways = content.get("key_takeaways") or []
    if takeaways:
        story.append(Spacer(1, 8))
        rows = [[Paragraph("Key takeaways", S["cellhead"])]]
        for t in takeaways:
            rows.append([Paragraph(f'<font color="#7c9a12">■</font>&nbsp;&nbsp;{t}', S["cell"])])
        tbl = Table(rows, colWidths=[168 * mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7ffe0")),
            ("BOX", (0, 0), (-1, -1), 1, INK),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 16))
    story.append(Paragraph("© Sudarshan Karweer · Strategic Advisory · www.sudarshankarweer.com", S["small"]))
    doc.build(story)
    return buf.getvalue()
