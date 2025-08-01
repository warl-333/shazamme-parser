import fitz  # PyMuPDF
from io import BytesIO
from docx import Document
import re

def extract_email(text):
    emails = re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", text)
    return emails[0] if emails else ""

def extract_phone(text):
    phones = re.findall(r"(?:(?:\+?\d{1,3})?[-.\s(]*\d{2,4}[-.\s)]*\d{2,4}[-.\s]*\d{2,4})", text)
    return phones[0] if phones else ""

def extract_name(text):
    # Heuristic: first non-empty line with 2-4 words, no digits or '@'
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and 2 <= len(line.split()) <= 4 and not any(c.isdigit() for c in line) and "@" not in line:
            return line
    return ""

def extract_skills(text):
    known_skills = [
        "Python", "R", "SQL", "Java", "C++", "Machine Learning", "Data Science",
        "Pandas", "NumPy", "FastAPI", "Flask", "Django", "Git", "Linux", "Docker"
    ]
    text_lower = text.lower()
    return [skill for skill in known_skills if skill.lower() in text_lower]

def parse_cv_bytes(file_bytes: bytes, filename: str) -> dict:
    text = ""

    try:
        if filename.lower().endswith(".pdf"):
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    text += page_text
            print(f"Extracted text length: {len(text)}")
        elif filename.lower().endswith(".docx"):
            document = Document(BytesIO(file_bytes))
            for para in document.paragraphs:
                text += para.text + "\n"
        else:
            text = "Unsupported file format"
    except Exception as e:
        text = f"Error parsing file: {str(e)}"

    print("---- EXTRACTED TEXT PREVIEW ----")
    print(text[:1000])

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)

    return {
        "filename": filename,
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "text_preview": text[:1000]  # first 1000 chars
    }
