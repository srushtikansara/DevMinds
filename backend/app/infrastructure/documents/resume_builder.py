import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESUME_OUTPUT_DIR = "generated_resumes"
os.makedirs(RESUME_OUTPUT_DIR, exist_ok=True)

FONT = "Times New Roman"
ACCENT = RGBColor(0x1F, 0x3B, 0x5C)


def _set_font(run, size=10, bold=False, italic=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), FONT)
    rFonts.set(qn('w:hAnsi'), FONT)


def _heading(doc, text):
    heading = doc.add_paragraph()
    run = heading.add_run(text.upper())
    _set_font(run, size=13, bold=True, color=ACCENT)
    heading.paragraph_format.space_before = Pt(14)
    heading.paragraph_format.space_after = Pt(4)
    p = heading._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '8')
    bottom.set(qn('w:color'), '1F3B5C')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return heading


def _role_line(doc, title, dates):
    """Title on the left, dates right-aligned on the same line, using a right tab stop."""
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    r1 = p.add_run(title)
    _set_font(r1, size=11, bold=True)
    r2 = p.add_run("\t" + dates)
    _set_font(r2, size=10, bold=True)
    p.paragraph_format.space_after = Pt(2)
    return p


def _render_role_block(doc, role):
    dates = f"{role.get('start_date', '')} - {role.get('end_date', '')}"
    _role_line(doc, role.get("title", ""), dates)
    company_p = doc.add_paragraph()
    company_r = company_p.add_run(role.get("context", ""))
    _set_font(company_r, size=10, bold=True)
    company_p.paragraph_format.space_after = Pt(4)
    for bullet_text in role.get("bullets", []):
        bp = doc.add_paragraph(style="List Bullet")
        bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        br = bp.add_run(bullet_text)
        _set_font(br, size=10)
        bp.paragraph_format.space_after = Pt(2)


def build_resume_docx(content: dict, resume_id: str, template: str = None) -> str:
    """
    Builds the resume .docx. The `template` argument is accepted for backward
    compatibility with existing callers but is currently ignored - there is
    only one, single resume template.
    """
    doc = Document()
    contact = content.get("contact_info", {})

    # Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.add_run(contact.get("full_name", "Developer").upper())
    _set_font(run, size=22, bold=True, color=RGBColor(0x00, 0x00, 0x00))
    name_para.paragraph_format.space_after = Pt(4)

    # Contact line, with a divider rule beneath it
    contact_parts = [p for p in [
        contact.get("location"), contact.get("email"), contact.get("phone"),
        contact.get("linkedin_url"), contact.get("portfolio_url"),
    ] if p]
    if contact_parts:
        contact_line = doc.add_paragraph()
        contact_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_run = contact_line.add_run("   |   ".join(contact_parts))
        _set_font(contact_run, size=10, color=RGBColor(0x33, 0x33, 0x33))
        contact_line.paragraph_format.space_after = Pt(10)
        p = contact_line._p
        pPr = p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '4')
        bottom.set(qn('w:color'), 'CCCCCC')
        pBdr.append(bottom)
        pPr.append(pBdr)

    # Summary
    _heading(doc, "Summary")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(content.get("summary", ""))
    _set_font(r, size=10)
    p.paragraph_format.space_after = Pt(8)

    # Experience / Projects
    all_entries = content.get("experience", [])
    experience = [e for e in all_entries if e.get("type") == "experience"]
    projects = [e for e in all_entries if e.get("type") == "project"]

    if experience:
        _heading(doc, "Work Experience")
        for role in experience:
            _render_role_block(doc, role)

    if projects:
        _heading(doc, "Projects")
        for role in projects:
            _render_role_block(doc, role)

    # Education
    education = content.get("education", [])
    if education:
        _heading(doc, "Education")
        for edu in education:
            p = doc.add_paragraph()
            r1 = p.add_run(f"{edu.get('degree', '')}")
            _set_font(r1, size=10, bold=True)
            r2 = p.add_run(f"  {edu.get('institution', '')} \u00b7 {edu.get('graduation_date', '')}")
            _set_font(r2, size=10)
            p.paragraph_format.space_after = Pt(6)

    # Skills
    skills = content.get("skills", [])
    if skills:
     _heading(doc, "Technical Skills")
    for skill in skills:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(skill)
        _set_font(r, size=10)
        p.paragraph_format.space_after = Pt(1)
    # Certificates
    certificates = content.get("certificates", [])
    if certificates:
        _heading(doc, "Certificates")
        for cert in certificates:
            p = doc.add_paragraph()
            r = p.add_run(f"{cert.get('name', '')}  \u2014 {cert.get('issuer', '')} {cert.get('date', '')}")
            _set_font(r, size=10)
            p.paragraph_format.space_after = Pt(2)

    output_path = os.path.join(RESUME_OUTPUT_DIR, f"resume_{resume_id}.docx")
    doc.save(output_path)
    return output_path