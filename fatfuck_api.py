import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from cv_parser import parse_cv_bytes  # assumes cv_parser.py is in same dir

app = FastAPI(
    title="CV Parser API",
    description="Parses CVs using spaCy and GPT to extract structured information.",
    version="1.0.0"
)

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/parse_cv/", response_model=Dict)
async def parse_cv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        result = parse_cv_bytes(contents, file.filename)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
