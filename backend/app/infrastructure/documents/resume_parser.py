import pdfplumber
from docx import Document

def extract_text_from_pdf(file_path:str) -> str:
    
    text_parts=[]
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:   
            page_text= page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)

                
def extract_text_from_docx(file_path:str) -> str:
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

def extract_resume_text(file_path:str,filename:str) ->str:
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif filename.lower().endswith("'docx"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type - only .pdf and .docx are supported")