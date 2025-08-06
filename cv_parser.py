import os

import sys
import re
from io import BytesIO
from collections import Counter
import fitz
try:
    import fitz
    print("Imported fitz")
except ImportError:
    try:
        import pymupdf
        print("Imported pymupdf")
    except ImportError as e:
        print("Failed to import:", e)

import pandas as pd

# Load skills from second column (index 1) without headers
import pandas as pd

def load_skills_column(filepath):
    skills = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:  # Make sure there is a second column
                skills.append(parts[1].strip().lower())
    return set(skills)

# Load your skills
KNOWN_SKILLS = load_skills_column("skills-dataset.csv")

# File handling

from docx import Document

# NLP
import spacy
from spacy.cli import download

try:
    nlp = spacy.load("en_core_web_trf")
except OSError:
    download("en_core_web_trf")
    nlp = spacy.load("en_core_web_trf")
from spacy.matcher import PhraseMatcher

# OpenAI GPT
import openai
openai.api_key = os.environ.get("OPENAI_API_KEY")
# Load NLP model
nlp = spacy.load("en_core_web_trf")

# Predefined keyword lists
degree_keywords = [
    "bachelor of science", "bachelor of science honours", "bachelor of science (honours)",
    "bachelor of arts", "master of science", "doctor of philosophy", "phd", "mba",
    "b.sc", "bsc", "ba", "ma", "m.sc", "m.a", "doctorate"
]
university_keywords = [
    "University of Sydney", "Harvard", "MIT", "Stanford",
    "University of Melbourne", "Monash University", "University"
]
skills_list = [
    "Python", "R", "SQL", "Java", "C++", "Machine Learning", "Data Science",
    "Pandas", "NumPy", "FastAPI", "Flask", "Django", "Git", "Linux", "Docker"
]

# Matchers
degree_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
degree_matcher.add("DEGREE", [nlp.make_doc(d) for d in degree_keywords])

skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
skill_matcher.add("SKILL", [nlp.make_doc(s) for s in skills_list])

# --- Cleaning ---
def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# --- Extraction ---
def extract_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and 2 <= len(line.split()) <= 4 and not any(c.isdigit() for c in line) and "@" not in line:
            return line
    return ""

def extract_email(text):
    emails = re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", text)
    return emails[0] if emails else ""

def extract_phone(text):
    phones = re.findall(r"(?:(?:\+?\d{1,3})?[-.\s(]*\d{2,4}[-.\s)]*\d{2,4}[-.\s]*\d{2,4})", text)
    return phones[0] if phones else ""

def extract_degrees(text):
    doc = nlp(clean_text(text))
    degrees = set()
    for chunk in doc.noun_chunks:
        if any(k in chunk.text.lower() for k in ["bachelor", "master", "phd", "doctor", "mba"]):
            if 2 <= len(chunk.text.split()) <= 6:
                degrees.add(chunk.text.strip())
    for ent in doc.ents:
        if ent.label_ == "WORK_OF_ART" and any(x in ent.text.lower() for x in ["bachelor", "master", "phd", "doctor", "mba"]):
            degrees.add(ent.text.strip())
    return sorted(degrees)

def extract_universities(text):
    doc = nlp(clean_text(text))
    return sorted(set(ent.text.strip() for ent in doc.ents if ent.label_ == "ORG" and "university" in ent.text.lower()))

def extract_location(text):
    doc = nlp(clean_text(text))
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return Counter(locations).most_common(1)[0][0] if locations else ""

DEGREE_KEYWORDS = {"bachelor", "master", "phd", "msc", "bsc", "doctorate", "honours", "degree"}

def is_invalid_skill(phrase):
    lowered = phrase.lower()
    return (
        any(keyword in lowered for keyword in DEGREE_KEYWORDS) or
        len(phrase.split()) > 5 or
        phrase.istitle()  # likely a proper name
    )

def is_potential_skill(phrase: str) -> bool:
    return phrase.lower().strip() in KNOWN_SKILLS

def extract_skills(text):
    doc = nlp(text)
    found = set()

    # PhraseMatcher matches
    matches = skill_matcher(doc)
    for _, start, end in matches:
        span = doc[start:end].text.strip().lower()
        if is_potential_skill(span):
            found.add(span)

    # Noun chunks (optional, if they match known skills)
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        if 1 <= len(phrase.split()) <= 4 and is_potential_skill(phrase):
            found.add(phrase)

    return sorted(found)
# --- GPT Fusion ---
def parse_cv_with_gpt(full_text: str, filename: str) -> dict:
    # spaCy analysis
    spacy_data = {
        "filename": filename,
        "name": extract_name(full_text),
        "email": extract_email(full_text),
        "phone": extract_phone(full_text),
        "skills": extract_skills(full_text),
        "degrees": extract_degrees(full_text),
        "universities": extract_universities(full_text),
        "location": extract_location(full_text),
    }

    # GPT summary
    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[{
                "role": "user",
                "content": (
                    f"Summarise the following CV text. Extract and list: "
                    f"name, email, phone, degrees, skills, location, universities.\n\n{full_text}"
                )
            }],
            temperature=0.3,
        )
        gpt_summary = response.choices[0].message.content.strip()
    except Exception as e:
        gpt_summary = f"GPT summarization failed: {str(e)}"

    return {
        **spacy_data,
      
        "gpt_summary": gpt_summary,
    }

# --- File reading ---
def parse_cv_bytes(file_bytes: bytes, filename: str) -> dict:
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text("text")
        elif filename.lower().endswith(".docx"):
            document = Document(BytesIO(file_bytes))
            for para in document.paragraphs:
                text += para.text + "\n"
        else:
            return {"error": "Unsupported file format"}
    except Exception as e:
        return {"error": f"File parsing error: {str(e)}"}

    return parse_cv_with_gpt(text, filename)

# Example usage
if __name__ == "__main__":
    filepath = "sample_resume.pdf"
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    result = parse_cv_bytes(file_bytes, filepath)
    from pprint import pprint
    pprint(result)
