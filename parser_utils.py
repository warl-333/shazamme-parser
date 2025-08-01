def parse_cv_bytes(content: bytes, filename: str) -> dict:
    # Replace with actual NLP logic later
    text = content.decode(errors="ignore")
    return {
        "filename": filename,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "skills": ["Python", "FastAPI", "SQL"],
        "text_preview": text[:500]
    }
