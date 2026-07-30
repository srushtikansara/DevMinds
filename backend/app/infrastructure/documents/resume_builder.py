import os
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESUME_OUTPUT_DIR = "generated_resumes"
os.makedirs(RESUME_OUTPUT_DIR, exist_ok=True)

ACCENT_COLOR = RGBColor(0x2E, 0x3B, 0x4E)


def add_section_heading(doc, text):
    heading = doc.add_paragraph()
    run = heading.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = ACCENT_COLOR
    heading.paragraph_format.space_before = Pt(12)
    heading.paragraph_format.space_after = Pt(4)
    p = heading._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:color'), '2E3B4E')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return heading


def _render_role_entry(doc, role, number=None):
    prefix = f"{number}) " if number else ""
    role_heading = doc.add_paragraph()
    run = role_heading.add_run(f"{prefix}{role.get('title', '')} — {role.get('context', '')}")
    run.bold = True

    date_line = doc.add_paragraph()
    date_run = date_line.add_run(f"{role.get('start_date', '')} - {role.get('end_date', '')}")
    date_run.italic = True
    date_run.font.size = Pt(9)
    date_run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)

    for bullet in role.get("bullets", []):
        doc.add_paragraph(bullet, style="List Bullet")

    doc.add_paragraph()


def build_resume_docx(content: dict, resume_id: str) -> str:
    doc = Document()
    contact = content.get("contact_info", {})

    # Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.add_run(contact.get("full_name", "Developer").upper())
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = ACCENT_COLOR

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
        contact_run.font.size = Pt(10)
        contact_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Summary
    add_section_heading(doc, "Profile")
    doc.add_paragraph(content.get("summary", ""))

    # Education
    education = content.get("education", [])
    if education:
        add_section_heading(doc, "Education")
        for edu in education:
            edu_para = doc.add_paragraph()
            edu_run = edu_para.add_run(f"{edu.get('institution', '')}")
            edu_run.bold = True
            edu_para.add_run(f"  {edu.get('degree', '')} | {edu.get('graduation_date', '')}")

    # Skills
    add_section_heading(doc, "Technical Skills")
    skills = content.get("skills", [])
    doc.add_paragraph("  •  ".join(skills))

    # Experience and Projects — split, rendered only once
    all_entries = content.get("experience", [])
    experience = [e for e in all_entries if e.get("type") == "experience"]
    projects = [e for e in all_entries if e.get("type") == "project"]

    if experience:
        add_section_heading(doc, "Experience")
        for role in experience:
            _render_role_entry(doc, role)

    if projects:
        add_section_heading(doc, "Projects")
        for i, role in enumerate(projects, 1):
            _render_role_entry(doc, role, number=i)

    output_path = os.path.join(RESUME_OUTPUT_DIR, f"resume_{resume_id}.docx")
    doc.save(output_path)
    return output_path