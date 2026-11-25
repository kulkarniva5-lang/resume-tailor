"""Render a tailored resume as a clean, ATS-friendly .docx or Markdown."""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from .schema import Resume

ACCENT = RGBColor(0x1F, 0x3A, 0x5F)


def _rule(paragraph) -> None:
    """Thin bottom border under a section heading."""
    p_pr = paragraph._p.get_or_add_pPr()
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in {"w:val": "single", "w:sz": "6", "w:space": "1", "w:color": "1F3A5F"}.items():
        bottom.set(qn(k), v)
    border.append(bottom)
    p_pr.append(border)


def _heading(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = ACCENT
    _rule(p)


def _line(doc, left: str, right: str = "", bold_left: bool = True, italic: bool = False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(left)
    r.bold = bold_left
    r.italic = italic
    if right:
        p.add_run("\t" + right).italic = True
        # Right-aligned at the text width (612pt page - 2 x 54pt margins).
        p.paragraph_format.tab_stops.add_tab_stop(Pt(504), WD_TAB_ALIGNMENT.RIGHT)
    return p


def _bullets(doc, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(item, style="List Bullet")
        p.paragraph_format.space_after = Pt(1)


def to_docx(r: Resume) -> bytes:
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Pt(42)
        section.left_margin = section.right_margin = Pt(54)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(0)
    run = title.add_run(r.name)
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = ACCENT

    if r.headline:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.add_run(r.headline).font.size = Pt(12)
    if r.contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("  |  ".join(r.contact)).font.size = Pt(9.5)

    if r.summary:
        _heading(doc, "Summary")
        doc.add_paragraph(r.summary)

    if r.skills:
        _heading(doc, "Skills")
        for g in r.skills:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(1)
            p.add_run(f"{g.category}: ").bold = True
            p.add_run(", ".join(g.items))

    if r.experience:
        _heading(doc, "Experience")
        for role in r.experience:
            _line(doc, role.title, role.dates)
            _line(doc, ", ".join(x for x in (role.company, role.location) if x), bold_left=False, italic=True)
            _bullets(doc, role.bullets)

    if r.projects:
        _heading(doc, "Projects")
        for proj in r.projects:
            p = _line(doc, proj.name)
            if proj.subtitle:
                p.add_run(f" — {proj.subtitle}").italic = True
            _bullets(doc, proj.bullets)

    if r.education:
        _heading(doc, "Education")
        for ed in r.education:
            _line(doc, ed.degree, ed.dates)
            _line(doc, ed.institution, bold_left=False, italic=True)
            if ed.details:
                doc.add_paragraph(ed.details)

    if r.certifications:
        _heading(doc, "Certifications")
        _bullets(doc, r.certifications)

    for extra in r.extra_sections:
        if extra.items:
            _heading(doc, extra.heading)
            _bullets(doc, extra.items)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def to_markdown(r: Resume) -> str:
    out = [f"# {r.name}"]
    if r.headline:
        out.append(f"**{r.headline}**")
    if r.contact:
        out.append(" | ".join(r.contact))
    if r.summary:
        out += ["", "## Summary", r.summary]
    if r.skills:
        out += ["", "## Skills"] + [f"- **{g.category}:** {', '.join(g.items)}" for g in r.skills]
    if r.experience:
        out += ["", "## Experience"]
        for role in r.experience:
            where = ", ".join(x for x in (role.company, role.location) if x)
            out += ["", f"### {role.title} — {where}", f"*{role.dates}*"]
            out += [f"- {b}" for b in role.bullets]
    if r.projects:
        out += ["", "## Projects"]
        for p in r.projects:
            out += ["", f"### {p.name}" + (f" — {p.subtitle}" if p.subtitle else "")]
            out += [f"- {b}" for b in p.bullets]
    if r.education:
        out += ["", "## Education"]
        for e in r.education:
            out.append(f"- **{e.degree}**, {e.institution} ({e.dates})" + (f". {e.details}" if e.details else ""))
    if r.certifications:
        out += ["", "## Certifications"] + [f"- {c}" for c in r.certifications]
    for extra in r.extra_sections:
        if extra.items:
            out += ["", f"## {extra.heading}"] + [f"- {i}" for i in extra.items]
    return "\n".join(out) + "\n"
