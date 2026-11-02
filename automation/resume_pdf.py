"""Write a two-page PDF that keeps every section of the original resume."""

import io
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from .resume_facts import (
    ADDITIONAL,
    CERTIFICATIONS,
    CONTACT,
    EDUCATION,
    LEADERSHIP,
    SKILL_GROUPS,
)


def _escape(text: str) -> str:
    """Plain text only. Angle brackets become text so a tag cannot show up as <br/>."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _styles(body: float) -> dict:
    # Body size is the knob that lands the same content on two pages.
    leading = body + 2.15
    return {
        "name": ParagraphStyle("name", fontName="Times-Bold", fontSize=body + 6, leading=body + 8, alignment=1, spaceAfter=1),
        "contact": ParagraphStyle("contact", fontName="Times-Roman", fontSize=body - 0.6, leading=body + 1.4, alignment=1, textColor="#222222"),
        "h": ParagraphStyle("h", fontName="Times-Bold", fontSize=body + 1.1, leading=body + 2.4, spaceBefore=5, spaceAfter=1, textColor="#111111"),
        "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=body, leading=leading),
        "role": ParagraphStyle("role", fontName="Times-Bold", fontSize=body, leading=leading, spaceBefore=3),
        "meta": ParagraphStyle("meta", fontName="Times-Italic", fontSize=body - 0.5, leading=leading, textColor="#333333"),
        "bullet": ParagraphStyle("bullet", fontName="Times-Roman", fontSize=body, leading=leading, leftIndent=9, bulletIndent=0, spaceBefore=0.4),
    }


def _rule() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.6, color="#222222", spaceBefore=0, spaceAfter=2)


def _bullet(text: str, styles: dict) -> Paragraph:
    return Paragraph("•  " + _escape(text), styles["bullet"])


def _story(resume: dict, body: float) -> list:
    styles = _styles(body)
    phone = CONTACT.get("phone_display") or CONTACT["phone"]
    story = [
        Paragraph(_escape(CONTACT["name"]), styles["name"]),
        Paragraph(
            _escape(f"{phone}   |   {CONTACT['email']}   |   {CONTACT['location']}"),
            styles["contact"],
        ),
        Paragraph(
            _escape(f"{CONTACT['linkedin']}   |   Portfolio: {CONTACT['portfolio']}"),
            styles["contact"],
        ),
        Spacer(1, 2),
        Paragraph("PROFESSIONAL SUMMARY", styles["h"]),
        _rule(),
        Paragraph(_escape(resume["summary"]), styles["body"]),
    ]
    # Job words already on the resume. They sit under the summary for ATS, with no company line.
    if resume.get("keywords"):
        story.append(Spacer(1, 1.5))
        story.append(Paragraph(_escape("Role keywords: " + ", ".join(resume["keywords"]) + "."), styles["body"]))

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["h"]))
    story.append(_rule())
    for role in resume["roles"]:
        story.append(Paragraph(_escape(f"{role['title']} — {role['company']}"), styles["role"]))
        meta = role["when"]
        if role.get("where"):
            meta = f"{meta}  |  {role['where']}"
        story.append(Paragraph(_escape(meta), styles["meta"]))
        for bullet in role["bullets"]:
            story.append(_bullet(bullet, styles))

    story.append(Paragraph("EDUCATION", styles["h"]))
    story.append(_rule())
    for school in resume.get("education_blocks") or []:
        story.append(Paragraph(_escape(school["school"]), styles["role"]))
        story.append(Paragraph(_escape(f"{school['detail']}  |  {school['when']}"), styles["meta"]))
        story.append(Paragraph(_escape("Relevant coursework: " + school["coursework"]), styles["body"]))

    story.append(Paragraph("PROJECTS", styles["h"]))
    story.append(_rule())
    for project in resume["projects"]:
        story.append(Paragraph(_escape(f"{project['title']} — {project['meta']}"), styles["role"]))
        for bullet in project["bullets"]:
            story.append(_bullet(bullet, styles))

    story.append(Paragraph("TECHNICAL SKILLS", styles["h"]))
    story.append(_rule())
    for name, text in resume.get("skill_groups") or SKILL_GROUPS:
        story.append(Paragraph(f"<b>{_escape(name)}:</b> {_escape(text)}", styles["body"]))

    story.append(Paragraph("CERTIFICATIONS", styles["h"]))
    story.append(_rule())
    for line in resume.get("certifications") or CERTIFICATIONS:
        story.append(_bullet(line, styles))

    story.append(Paragraph("LEADERSHIP &amp; ACHIEVEMENTS", styles["h"]))
    story.append(_rule())
    for item in resume.get("leadership") or LEADERSHIP:
        story.append(Paragraph(_escape(item["title"]), styles["role"]))
        for bullet in item["bullets"]:
            story.append(_bullet(bullet, styles))

    story.append(Paragraph("ADDITIONAL INFORMATION", styles["h"]))
    story.append(_rule())
    for line in resume.get("additional") or ADDITIONAL:
        story.append(_bullet(line, styles))
    return story


def _render(resume: dict, body: float) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"{CONTACT['name']} resume",
        author=CONTACT["name"],
    )
    doc.build(_story(resume, body))
    return buffer.getvalue()


def _pages(data: bytes) -> int:
    return len(PdfReader(io.BytesIO(data)).pages)


def write_resume_pdf(resume: dict, path: Path) -> Path:
    """Save a two-page resume. Font size is chosen so the full original content fills two pages."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Try a professional size first, then step down or up until the PDF is two pages.
    chosen = None
    for body in (8.6, 8.3, 8.0, 7.7, 9.0, 9.3, 7.4):
        data = _render(resume, body)
        count = _pages(data)
        if count == 2:
            chosen = data
            break
        # Keep the closest result if no size lands on exactly two pages.
        if chosen is None or abs(count - 2) < abs(_pages(chosen) - 2):
            chosen = data
    path.write_bytes(chosen or _render(resume, 8.3))
    return path
