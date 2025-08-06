import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
print("Starting FastAPI app...")

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "It works!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("fatfuck_api:app", host="0.0.0.0", port=port)