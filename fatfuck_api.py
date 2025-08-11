import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import openai
import fitz  # PyMuPDF
import docx  # python-docx
from io import BytesIO

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="CV Parser API (GPT only)",
    description="Parses uploaded CVs (PDF or DOCX) and summarizes using GPT.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extract text from PDF
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

# Extract text from DOCX
def extract_text_from_docx(docx_bytes: bytes) -> str:
    file_stream = BytesIO(docx_bytes)
    document = docx.Document(file_stream)
    return "\n".join([para.text for para in document.paragraphs])

@app.post("/parse_cv/", response_model=Dict)
async def parse_cv(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Determine file type
        if file.filename.lower().endswith(".pdf"):
            full_text = extract_text_from_pdf(contents)
        elif file.filename.lower().endswith(".docx"):
            full_text = extract_text_from_docx(contents)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload a .pdf or .docx file.")

        # GPT Summary
        try:
            response = openai.chat.completions.create(
                model="gpt-4.1-2025-04-14",  # or your chosen model
                messages=[{
                    "role": "user",
                    "content": ("""
You are an AI CV parser. Extract the following fields from the CV text below
and return them as a **single valid JSON object**. Do not include any text
outside the JSON. For missing fields, use an empty string ("") or empty list ([]).

Required JSON schema:

{{
  "contact": {{
    "full_name": "",
    "emails": [],
    "phones": [],
    "address": {{
      "street": "",
      "city": "",
      "state": "",
      "country": "",
      "postcode": ""
    }},
    "links": []
  }},
  "summary": "",
  "work_experience": [
    {{
      "job_title": "",
      "employer": "",
      "start_date": "",
      "end_date": "",
      "location": {{
        "city": "",
        "country": ""
      }},
      "responsibilities": [],
      "achievements": []
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "start_date": "",
      "end_date": "",
      "location": {{
        "city": "",
        "country": ""
      }},
      "honors_gpa": ""
    }}
  ],
  "skills": [],
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "date_earned": "",
      "expiry_date": ""
    }}
  ],
  "languages": [
    {{
      "name": "",
      "proficiency": ""
    }}
  ],
  "awards": [
    {{
      "name": "",
      "issuer": "",
      "date": ""
    }}
  ],
  "publications": [
    {{
      "title": "",
      "venue": "",
      "date": ""
    }}
  ],
  "projects": [
    {{
      "title": "",
      "description": "",
      "technologies": [],
      "dates": ""
    }}
  ]
}}

Rules:
- Escape all newline characters inside strings as \\n.
- Dates must be in ISO format (YYYY-MM-DD) if available.
- Keep arrays even if empty.
- Do not include comments or explanations.

CV text:
\"\"\"{full_text}\"\"\"
""" 
                    )
                }],
                temperature=0.3,
            )
            gpt_summary = response.choices[0].message.content.strip()
        except Exception as e:
            gpt_summary = f"GPT summarization failed: {str(e)}"

        return {
            "gpt_summary": gpt_summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional manual runner for local testing
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("fatfuck_api:app", host="0.0.0.0", port=port)
