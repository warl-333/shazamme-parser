import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import openai
import fitz  # PyMuPDF
import docx  # python-docx
from io import BytesIO
import json

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
                    "content": (
                        f"Extract and summarise the following structured information from the provided CV text. Please return the results in **clean, structured, JSON-style format** with the following top-level fields: "
                        f"1. **contact_info**: - full_name - email_addresses (list) - phone_numbers (list) - address: - street - city - state_or_province - postal_code - country - links (LinkedIn, portfolio, GitHub, etc.) 2. **professional_summary**: (Short about me or objective paragraph) 3. **work_experience**: (List of past jobs, each with the following) - job_title - company - location (city, country) - start_date (ISO format: YYYY-MM-DD or partial if unavailable) - end_date (or present) - responsibilities (bullet points) - achievements (metrics, awards, key results) 4. **education**: (List of degrees/certifications) - degree - institution - location (city, country) - start_date - end_date - honors_or_gpa 5. **skills**: - programming_languages - frameworks - tools - spoken_languages - other_skills 6. **certifications**: - name - issuer - issue_date - expiry_date (if any) 7. **languages**: - name - proficiency_level (e.g. native, fluent, professional) 8. **awards_and_memberships**: - name - issuer - date 9. **publications_and_patents**: - title - venue_or_office - date 10. **projects**: - title - description - technologies_used - dates Use null for any fields not found. Do not hallucinate or assume information. Prioritize accuracy and structured output. \n\n{full_text}"
                    )
                }],
                temperature=0.3,
            )
            gpt_summary = response.choices[0].message.content.strip()

            # Remove markdown code block if present
            if gpt_summary.startswith("```json"):
                gpt_summary = gpt_summary[len("```json"):].strip()
            if gpt_summary.endswith("```"):
                gpt_summary = gpt_summary[:-3].strip()

            # Parse JSON string into Python dict
            parsed_json = json.loads(gpt_summary)

            # Compact JSON string (no newlines or spaces)
            gpt_summary_compact = json.dumps(parsed_json, separators=(',', ':'))

            return {
                "gpt_summary": gpt_summary_compact
            }

        except Exception as e:
            # GPT summarization or JSON parsing failed
            raise HTTPException(status_code=500, detail=f"GPT summarization failed: {str(e)}")

    except Exception as e:
        # Catch all other errors (file read, extraction, etc.)
        raise HTTPException(status_code=500, detail=str(e))


# Optional manual runner for local testing
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("shazamme_parser:app", host="0.0.0.0", port=port)
