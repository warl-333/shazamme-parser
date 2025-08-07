import os
import openai
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Optional: Enable CORS if calling from a frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Upload a PDF to extract content using GPT."}

@app.post("/parse_pdf/")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Read and extract text from the PDF
        contents = await file.read()
        doc = fitz.open(stream=contents, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF.")

        # Send to OpenAI GPT
        response = openai.chat.completions.create(
                model="gpt-4.1-2025-04-14",  # Replace with your available model
                messages=[{
                    "role": "user",
                    "content": (
                        f"Summarise the following CV text. Extract and list: "
                        f"name, email, phone, degrees, skills, location, universities.\n\n{full_text}"
                    )}]
        )

        return {"result": response["choices"][0]["message"]["content"]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("fatfuck_api:app", host="0.0.0.0", port=port)
