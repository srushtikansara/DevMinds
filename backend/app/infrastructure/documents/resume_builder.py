import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

RESUME_OUTPUT_DIR = "generated_resumes"
os.makedirs(RESUME_OUTPUT_DIR, exist_ok=True)


def build_resume_docx(content: dict, resume_id: str) -> str:
    doc = Document()

    contact = content.get("contact_info", {})

    # Name
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(contact.get("full_name", "Developer"))
    run.bold = True
    run.font.size = Pt(20)

    # Contact line - only include parts that were actually provided
    contact_parts = [p for p in [
        contact.get("email"),
        contact.get("phone"),
        contact.get("linkedin_url"),
        contact.get("portfolio_url"),
    ] if p]
    if contact_parts:
        contact_line = doc.add_paragraph()
        contact_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_line.add_run("  |  ".join(contact_parts)).font.size = Pt(10)

    doc.add_paragraph()

    # Summary
    doc.add_heading("Summary", level=2)
    doc.add_paragraph(content.get("summary", ""))

    # Skills
    doc.add_heading("Technical Skills", level=2)
    skills = content.get("skills", [])
    doc.add_paragraph("  •  ".join(skills))

    # Experience - grouped by role, with dates
    doc.add_heading("Experience", level=2)
    for role in content.get("experience", []):
        role_heading = doc.add_paragraph()
        run = role_heading.add_run(f"{role.get('title', '')} — {role.get('context', '')}")
        run.bold = True

        date_line = doc.add_paragraph()
        date_run = date_line.add_run(f"{role.get('start_date', '')} - {role.get('end_date', '')}")
        date_run.italic = True
        date_run.font.size = Pt(10)

        for bullet in role.get("bullets", []):
            doc.add_paragraph(bullet, style="List Bullet")

        doc.add_paragraph()  # spacing between roles

    # Education
    education = content.get("education", [])
    if education:
        doc.add_heading("Education", level=2)
        for edu in education:
            edu_line = doc.add_paragraph()
            edu_line.add_run(f"{edu.get('degree', '')} — {edu.get('institution', '')} ({edu.get('graduation_date', '')})")

    output_path = os.path.join(RESUME_OUTPUT_DIR, f"resume_{resume_id}.docx")
    doc.save(output_path)
    return output_path