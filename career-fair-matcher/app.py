from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import ValidationError

from match import MatchResult, load_roles, match_resume

app = FastAPI(title="Career Fair Matcher")


@app.post("/match", response_model=MatchResult)
def match_endpoint(resume: UploadFile = File(...)):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF.")

    pdf_bytes = resume.file.read()

    try:
        return match_resume(pdf_bytes, load_roles("roles.txt"))
    except (ValidationError, ValueError):
        raise HTTPException(status_code=502, detail="AI returned an unexpected response. Try again.")