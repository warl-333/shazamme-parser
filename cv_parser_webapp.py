from fastapi import FastAPI, UploadFile, File, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security.api_key import APIKeyHeader
import os

from parser_utils import parse_cv_bytes
from db import init_db, AsyncSessionLocal
from models import ParsedCV
from sqlalchemy.future import select

app = FastAPI()

# commented out HTTPS Redirect Middleware
#@app.middleware("http")
#async def redirect_http_to_https(request: Request, call_next):
 #   if request.url.scheme != "https":
#        url = request.url.replace(scheme="https")
#        return RedirectResponse(url)
 #   return await call_next(request)

# API Key Auth
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("API_KEY", "dev-key")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# Save to DB
from sqlalchemy.orm import sessionmaker

async def save_parsed_cv(data: dict):
    async with AsyncSessionLocal() as session:
        cv = ParsedCV(
            filename=data["filename"],
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            skills=";".join(data["skills"]),
            text_preview=data["text_preview"]
        )
        session.add(cv)
        await session.commit()
        await session.refresh(cv)
        return cv.id

@app.post("/parse_cv/", dependencies=[Depends(get_api_key)])
async def parse_cv(file: UploadFile = File(...)):
    parsed = parse_cv_bytes(await file.read(), file.filename)
    parsed_id = await save_parsed_cv(parsed)
    parsed["id"] = parsed_id
    return parsed

@app.post("/parse_cvs/", dependencies=[Depends(get_api_key)])
async def parse_cvs(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        parsed = parse_cv_bytes(await file.read(), file.filename)
        parsed_id = await save_parsed_cv(parsed)
        parsed["id"] = parsed_id
        results.append(parsed)
    return results

# Startup: create DB tables
@app.on_event("startup")
async def startup():
    await init_db()
