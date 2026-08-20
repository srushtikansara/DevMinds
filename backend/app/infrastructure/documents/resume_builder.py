import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESUME_OUTPUT_DIR = "generated_resumes"
os.makedirs(RESUME_OUTPUT_DIR, exist_ok=True)

ACCENT_COLOR = RGBColor(0x00, 0x00, 0x00)  # ATS-safe: pure black, not a colored accent
FONT_NAME = "Calibri"  # explicit, standard, widely-parsed font


def select_template(target_position: str) -> str:
    """
    Auto-selects a resume template based on target position. Senior/lead-level
    roles typically involve more experience to list, so they default to the
    denser 'compact' template; everything else uses 'modern'. This is an
    explicit, explainable rule, not a black-box guess.
    """
    if not target_position:
        return "modern"
    lowered = target_position.lower()
    senior_keywords = ["senior", "lead", "principal", "staff", "manager", "architect"]
    if any(kw in lowered for kw in senior_keywords):
        return "compact"
    return "modern"


def _set_font(run, size=10, bold=False, italic=False, color=None):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    # ensure the font applies to East Asian/complex-script fallback too
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), FONT_NAME)
    rFonts.set(qn('w:hAnsi'), FONT_NAME)


# ============================================================
# Shared helpers used by the "modern" template
# ============================================================

def add_section_heading(doc, text):
    heading = doc.add_paragraph()
    run = heading.add_run(text.upper())
    _set_font(run, size=11, bold=True, color=ACCENT_COLOR)
    heading.paragraph_format.space_before = Pt(12)
    heading.paragraph_format.space_after = Pt(4)
    p = heading._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return heading


def add_two_column_bullets(doc, items):
    """Renders a list as two visual columns using tab-stops, not a table -
    keeps the document single-column underneath for ATS parser safety."""
    tab_position = Inches(3.25)
    for i in range(0, len(items), 2):
        para = doc.add_paragraph()
        para.paragraph_format.tab_stops.add_tab_stop(tab_position, WD_TAB_ALIGNMENT.LEFT)
        left_run = para.add_run(f"\u2022  {items[i]}")
        _set_font(left_run, size=10)
        if i + 1 < len(items):
            para.add_run("\t")
            right_run = para.add_run(f"\u2022  {items[i + 1]}")
            _set_font(right_run, size=10)


def add_certificates(doc, certificates):
    for cert in certificates:
        p = doc.add_paragraph()
        name_run = p.add_run(cert.get("name", ""))
        _set_font(name_run, size=10, bold=True)
        if cert.get("issuer") or cert.get("date"):
            meta_run = p.add_run(f"  \u2014 {cert.get('issuer', '')} {cert.get('date', '')}")
            _set_font(meta_run, size=9, italic=True, color=RGBColor(0x55, 0x55, 0x55))


def _render_role_entry(doc, role, number=None):
    prefix = f"{number}) " if number else ""
    role_heading = doc.add_paragraph()
    run = role_heading.add_run(f"{prefix}{role.get('title', '')} \u2014 {role.get('context', '')}")
    _set_font(run, size=10, bold=True)

    date_line = doc.add_paragraph()
    date_run = date_line.add_run(f"{role.get('start_date', '')} - {role.get('end_date', '')}")
    _set_font(date_run, size=9, italic=True, color=RGBColor(0x55, 0x55, 0x55))

    for bullet in role.get("bullets", []):
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(bullet)
        _set_font(r, size=10)

    doc.add_paragraph()


# ============================================================
# Template: "modern" (default) - spacious, generous section spacing
# ============================================================

def _build_modern_template(content: dict, resume_id: str) -> str:
    doc = Document()
    contact = content.get("contact_info", {})

    # Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.add_run(contact.get("full_name", "Developer").upper())
    _set_font(run, size=20, bold=True, color=ACCENT_COLOR)

    # Title line (role) under the name
    title = content.get("target_position") or content.get("headline")
    if title:
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(str(title).upper())
        _set_font(title_run, size=12, bold=True)

    # Contact line
    contact_parts = [p for p in [
        contact.get("email"),
        contact.get("phone"),
        contact.get("linkedin_url"),
        contact.get("portfolio_url"),
    ] if p]
    if contact_parts:
        contact_line = doc.add_paragraph()
        contact_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_run = contact_line.add_run("  |  ".join(contact_parts))
        _set_font(contact_run, size=10, color=RGBColor(0x33, 0x33, 0x33))

    # Summary
    add_section_heading(doc, "Professional Summary")
    p = doc.add_paragraph()
    r = p.add_run(content.get("summary", ""))
    _set_font(r, size=10)

    # Education
    education = content.get("education", [])
    if education:
        add_section_heading(doc, "Education")
        for edu in education:
            edu_para = doc.add_paragraph()
            edu_run = edu_para.add_run(f"{edu.get('institution', '')}")
            _set_font(edu_run, size=10, bold=True)
            rest_run = edu_para.add_run(f"  {edu.get('degree', '')} | {edu.get('graduation_date', '')}")
            _set_font(rest_run, size=10)

    # Skills
    skills = content.get("skills", [])
    if skills:
        add_section_heading(doc, "Core Competencies")
        add_two_column_bullets(doc, skills)

    # Projects
    all_entries = content.get("experience", [])
    experience = [e for e in all_entries if e.get("type") == "experience"]
    projects = [e for e in all_entries if e.get("type") == "project"]

    if projects:
        add_section_heading(doc, "Projects")
        for i, role in enumerate(projects, 1):
            _render_role_entry(doc, role, number=i)

    # Professional Experience
    if experience:
        add_section_heading(doc, "Professional Experience")
        for role in experience:
            _render_role_entry(doc, role)

    # Certificates
    certificates = content.get("certificates", [])
    if certificates:
        add_section_heading(doc, "Certificates")
        add_certificates(doc, certificates)

    output_path = os.path.join(RESUME_OUTPUT_DIR, f"resume_{resume_id}.docx")
    doc.save(output_path)
    return output_path


# ============================================================
# Template: "compact" - tighter margins, smaller font, denser
# spacing, auto-selected for senior/lead-level target positions
# ============================================================

def _render_compact_role(doc, role, number=None):
    prefix = f"{number}) " if number else ""
    role_heading = doc.add_paragraph()
    run = role_heading.add_run(f"{prefix}{role.get('title', '')} \u2014 {role.get('context', '')}")
    _set_font(run, size=9, bold=True)
    role_heading.paragraph_format.space_after = Pt(0)

    date_line = doc.add_paragraph()
    date_run = date_line.add_run(f"{role.get('start_date', '')} - {role.get('end_date', '')}")
    _set_font(date_run, size=8, italic=True, color=RGBColor(0x55, 0x55, 0x55))
    date_line.paragraph_format.space_after = Pt(1)

    for bullet in role.get("bullets", []):
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(bullet)
        _set_font(r, size=9)
        p.paragraph_format.space_after = Pt(1)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _build_compact_template(content: dict, resume_id: str) -> str:
    doc = Document()
    contact = content.get("contact_info", {})

    # Tighter page margins for a denser, single-page-optimized layout
    section = doc.sections[0]
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)

    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.add_run(contact.get("full_name", "Developer").upper())
    _set_font(run, size=16, bold=True, color=ACCENT_COLOR)
    name_para.paragraph_format.space_after = Pt(2)

    title = content.get("target_position") or content.get("headline")
    if title:
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(str(title).upper())
        _set_font(title_run, size=10, bold=True)
        title_para.paragraph_format.space_after = Pt(2)

    contact_parts = [p for p in [
        contact.get("email"), contact.get("phone"),
        contact.get("linkedin_url"), contact.get("portfolio_url"),
    ] if p]
    if contact_parts:
        contact_line = doc.add_paragraph()
        contact_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_run = contact_line.add_run("  |  ".join(contact_parts))
        _set_font(contact_run, size=9, color=RGBColor(0x33, 0x33, 0x33))
        contact_line.paragraph_format.space_after = Pt(4)

    def compact_heading(text):
        h = doc.add_paragraph()
        r = h.add_run(text.upper())
        _set_font(r, size=10, bold=True, color=ACCENT_COLOR)
        h.paragraph_format.space_before = Pt(6)
        h.paragraph_format.space_after = Pt(2)
        return h

    compact_heading("Professional Summary")
    p = doc.add_paragraph()
    r = p.add_run(content.get("summary", ""))
    _set_font(r, size=9)
    p.paragraph_format.space_after = Pt(4)

    education = content.get("education", [])
    if education:
        compact_heading("Education")
        for edu in education:
            edu_para = doc.add_paragraph()
            edu_run = edu_para.add_run(f"{edu.get('institution', '')}")
            _set_font(edu_run, size=9, bold=True)
            rest_run = edu_para.add_run(f"  {edu.get('degree', '')} | {edu.get('graduation_date', '')}")
            _set_font(rest_run, size=9)
            edu_para.paragraph_format.space_after = Pt(2)

    skills = content.get("skills", [])
    if skills:
        compact_heading("Core Competencies")
        p = doc.add_paragraph()
        r = p.add_run("  \u2022  ".join(skills))
        _set_font(r, size=9)
        p.paragraph_format.space_after = Pt(4)

    all_entries = content.get("experience", [])
    experience = [e for e in all_entries if e.get("type") == "experience"]
    projects = [e for e in all_entries if e.get("type") == "project"]

    if projects:
        compact_heading("Projects")
        for i, role in enumerate(projects, 1):
            _render_compact_role(doc, role, number=i)

    if experience:
        compact_heading("Professional Experience")
        for role in experience:
            _render_compact_role(doc, role)

    certificates = content.get("certificates", [])
    if certificates:
        compact_heading("Certificates")
        for cert in certificates:
            p = doc.add_paragraph()
            r = p.add_run(f"{cert.get('name', '')}  \u2014 {cert.get('issuer', '')} {cert.get('date', '')}")
            _set_font(r, size=9)
            p.paragraph_format.space_after = Pt(1)

    output_path = os.path.join(RESUME_OUTPUT_DIR, f"resume_{resume_id}.docx")
    doc.save(output_path)
    return output_path


# ============================================================
# Public entry point - dispatches to the correct template
# ============================================================

def build_resume_docx(content: dict, resume_id: str, template: str = None) -> str:
    """
    Builds the resume .docx using the given template, or auto-selects one
    based on content['target_position'] if no template is explicitly given.
    """
    chosen = template or select_template(content.get("target_position", ""))
    if chosen == "compact":
        return _build_compact_template(content, resume_id)
    return _build_modern_template(content, resume_id)