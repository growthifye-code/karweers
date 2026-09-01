"""Leadership Blueprint PDF generation (reportlab). Dark + lime SK brand."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)

INK = colors.HexColor("#0A0A0A")
LIME = colors.HexColor("#C6F135")
GREY = colors.HexColor("#4b5563")
LIGHT = colors.HexColor("#e5e7eb")


def _styles():
    ss = getSampleStyleSheet()
    styles = {
        "kicker": ParagraphStyle("kicker", parent=ss["Normal"], fontName="Helvetica-Bold",
                                 fontSize=9, textColor=colors.HexColor("#7c9a12"), spaceAfter=4, leading=12,
                                 tracking=1),
        "h1": ParagraphStyle("h1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=26,
                             textColor=INK, spaceAfter=6, leading=30, alignment=TA_LEFT),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=15,
                             textColor=INK, spaceBefore=16, spaceAfter=8, leading=18),
        "body": ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=10.5,
                               textColor=colors.HexColor("#1f2937"), leading=16, spaceAfter=8),
        "small": ParagraphStyle("small", parent=ss["Normal"], fontName="Helvetica", fontSize=8.5,
                                textColor=GREY, leading=12),
        "cell": ParagraphStyle("cell", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5,
                               textColor=colors.HexColor("#1f2937"), leading=14),
        "cellhead": ParagraphStyle("cellhead", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9.5,
                                   textColor=INK, leading=14),
        "coverbig": ParagraphStyle("coverbig", fontName="Helvetica-Bold", fontSize=34, textColor=colors.white,
                                   leading=40),
        "coversub": ParagraphStyle("coversub", fontName="Helvetica", fontSize=13, textColor=colors.HexColor("#d1d5db"),
                                   leading=20),
        "logo": ParagraphStyle("logo", fontName="Helvetica-Bold", fontSize=22, textColor=colors.white, leading=26),
    }
    return styles


def _cover(story, S, title, subtitle):
    band = Table([[""]], colWidths=[170 * mm], rowHeights=[125 * mm])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 22),
        ("RIGHTPADDING", (0, 0), (-1, -1), 22),
        ("TOPPADDING", (0, 0), (-1, -1), 26),
    ]))
    inner = [
        Paragraph('S<font color="#C6F135">K.</font>', S["logo"]),
        Spacer(1, 6),
        Paragraph("SUDARSHAN KARWEER · STRATEGIC ADVISORY", ParagraphStyle(
            "ck", fontName="Helvetica-Bold", fontSize=8.5, textColor=LIME, leading=12)),
        Spacer(1, 54),
        Paragraph(title, S["coverbig"]),
        Spacer(1, 12),
        Paragraph(subtitle, S["coversub"]),
    ]
    band = Table([[inner]], colWidths=[170 * mm], rowHeights=[130 * mm])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 26),
        ("RIGHTPADDING", (0, 0), (-1, -1), 26),
    ]))
    story.append(band)
    story.append(Spacer(1, 14))


def _score_table(S, scores):
    rows = [[Paragraph("Trait", S["cellhead"]), Paragraph("Score", S["cellhead"]), Paragraph("", S["cellhead"])]]
    data = []
    for k, v in scores.items():
        try:
            pct = max(0, min(100, int(v)))
        except Exception:
            pct = 0
        bar = Table([[""]], colWidths=[max(1, pct) * 0.9 * mm], rowHeights=[7])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIME), ("BOX", (0, 0), (-1, -1), 0, LIME)]))
        data.append([Paragraph(k, S["cell"]), Paragraph(f"{pct}/100", S["cell"]), bar])
    t = Table(rows + data, colWidths=[55 * mm, 22 * mm, 93 * mm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _bullet_list(S, items):
    flow = []
    for it in items:
        flow.append(Paragraph(f'<font color="#7c9a12">■</font>&nbsp;&nbsp;{it}', S["body"]))
    return flow


def build_personalized_pdf(name, scores, quadrant, blueprint):
    """Personalized 'Leadership Blueprint (Pro)' from a completed Big-Five assessment."""
    buf = BytesIO()
    S = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title="Leadership Blueprint")
    story = []
    who = (name or "Leader").strip().split(" ")[0]
    q = quadrant or {}
    _cover(story, S, "The Leadership\nBlueprint", f"A private profile prepared for {who}")
    story.append(Paragraph("YOUR LEADERSHIP QUADRANT", S["kicker"]))
    story.append(Paragraph(q.get("name", "Leadership Profile"), S["h1"]))
    if q.get("tagline"):
        story.append(Paragraph(q["tagline"], S["small"]))
    story.append(Spacer(1, 8))
    if blueprint.get("narrative"):
        story.append(Paragraph(blueprint["narrative"], S["body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("YOUR PROFILE", S["kicker"]))
    story.append(Paragraph("The five dimensions", S["h2"]))
    story.append(_score_table(S, scores or {}))

    if blueprint.get("strengths"):
        story.append(Paragraph("WHERE YOU'RE STRONG", S["kicker"]))
        story.append(Paragraph("Signature strengths", S["h2"]))
        for f in _bullet_list(S, blueprint["strengths"]):
            story.append(f)

    if blueprint.get("blind_spots"):
        story.append(Paragraph("WATCH-OUTS", S["kicker"]))
        story.append(Paragraph("Blind spots to manage", S["h2"]))
        for b in blueprint["blind_spots"]:
            if isinstance(b, dict):
                story.append(Paragraph(f'<b>{b.get("spot","")}</b> — {b.get("why","")}', S["body"]))
            else:
                story.append(Paragraph(str(b), S["body"]))

    if blueprint.get("roadmap"):
        story.append(PageBreak())
        story.append(Paragraph("YOUR 12-MONTH PLAN", S["kicker"]))
        story.append(Paragraph("The operating roadmap", S["h2"]))
        rows = [[Paragraph("Horizon", S["cellhead"]), Paragraph("Milestone", S["cellhead"]),
                 Paragraph("Action", S["cellhead"])]]
        for r in blueprint["roadmap"]:
            if isinstance(r, dict):
                rows.append([Paragraph(r.get("horizon", ""), S["cell"]),
                             Paragraph(r.get("milestone", ""), S["cell"]),
                             Paragraph(r.get("action", ""), S["cell"])])
        t = Table(rows, colWidths=[26 * mm, 48 * mm, 96 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)

    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=1, color=LIME))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Want to work through this in person? Book a 1:1 strategy session with Sudarshan at "
        "<b>www.sudarshankarweer.com</b>.", S["body"]))
    story.append(Paragraph(
        "Big Five profile via Mini-IPIP (Donnellan et al., 2006), public domain. This blueprint reflects "
        "Sudarshan Karweer's coaching perspective and is prepared privately for you.", S["small"]))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def build_starter_pdf():
    """Generic evergreen 'Leadership Blueprint Starter' — the free lead-magnet download."""
    buf = BytesIO()
    S = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title="Leadership Blueprint Starter")
    story = []
    _cover(story, S, "The Leadership\nBlueprint",
           "A starter framework for leaders who want to run leadership like a system")

    sections = [
        ("01 · THE OPERATING SYSTEM", "Lead like a system, not a personality",
         "Great leaders don't rely on mood or memory. They install rituals. Pick three that run without you: a weekly "
         "priorities review, a monthly capital & risk check, and a quarterly strategy reset. When leadership is a "
         "system, your team stops waiting for you and starts moving with you."),
        ("02 · STRATEGY", "Decide fewer things, better",
         "Most teams are busy, not aligned. Write your one-page strategy: the single wedge you're pressing, the three "
         "bets that support it, and the one metric that proves it's working. Kill everything that doesn't ladder up. "
         "Clarity at the top compounds into speed everywhere below."),
        ("03 · CAPITAL & BANKABILITY", "Be fundable before you fundraise",
         "Capital follows credibility. Before you approach investors or lenders, de-risk the story: a clean financial "
         "model, a data room that answers questions before they're asked, and a narrative that connects your wedge to "
         "cash flows. Bankability is built in the quarters before the raise, not the week of it."),
        ("04 · PEOPLE", "Hire for the seat, not the moment",
         "Your calendar is your real strategy. Audit where your hours go for two weeks. Then delegate, delete, or "
         "redesign anything that isn't the highest-leverage use of you. Build a leadership bench by giving real "
         "decisions — not just tasks — to the people you're growing."),
        ("05 · THE 90-DAY LOOP", "Ship, review, reset",
         "Ambition without cadence drifts. Run your leadership in 90-day loops: set three outcomes, review weekly, "
         "and reset at the end. Small, relentless loops beat grand annual plans every time."),
    ]
    for kicker, h, body in sections:
        story.append(Paragraph(kicker, S["kicker"]))
        story.append(Paragraph(h, S["h2"]))
        story.append(Paragraph(body, S["body"]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=LIME))
    story.append(Spacer(1, 8))
    story.append(Paragraph("YOUR NEXT STEP", S["kicker"]))
    story.append(Paragraph(
        "This is the starter. To turn it into <b>your</b> plan, take the free Leadership Assessment and unlock a "
        "personalised Blueprint built on your own profile — strengths, blind spots and a 12-month roadmap. "
        "Visit <b>www.sudarshankarweer.com/assessment</b>.", S["body"]))
    story.append(Paragraph("© Sudarshan Karweer · Strategic Advisory & Executive Coaching", S["small"]))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
