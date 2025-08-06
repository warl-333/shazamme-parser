# fatfuck_api.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from cv_parser import parse_cv_bytes  # make sure this exists

app = FastAPI(
    title="CV Parser API",
    description="Parses CVs using spaCy and GPT to extract structured information.",
    version="1.0.0"
)

# Optional: allow frontend JS to access the API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with specific frontend URL for production
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


@app.get("/")
async def root():
    return {"message": "It works!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("fatfuck_api:app", host="0.0.0.0", port=port)
