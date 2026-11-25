"""FastAPI backend for Resume Tailor."""

from __future__ import annotations

import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .export import to_docx, to_markdown  # noqa: E402
from .extract import ExtractError, extract_text  # noqa: E402
from .schema import Resume  # noqa: E402
from .tailor import TailorError, tailor_resume  # noqa: E402

MAX_UPLOAD_MB = 10
MAX_CHARS = 60_000  # far beyond any real resume or posting; guards against huge pastes

app = FastAPI(title="Resume Tailor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5174").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/tailor")
async def tailor(
    job_text: str = Form(...),
    resume_text: str = Form(""),
    notes: str = Form(""),
    resume_file: UploadFile | None = File(None),
):
    if resume_file is not None and resume_file.filename:
        data = await resume_file.read()
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB.")
        try:
            resume_text = extract_text(resume_file.filename, data)
        except ExtractError as exc:
            raise HTTPException(422, str(exc)) from exc

    resume_text, job_text = resume_text.strip(), job_text.strip()
    if len(resume_text) < 50:
        raise HTTPException(422, "Please upload a resume or paste its text.")
    if len(job_text) < 30:
        raise HTTPException(422, "Please paste the job description or requirements.")
    if len(resume_text) > MAX_CHARS or len(job_text) > MAX_CHARS or len(notes) > 4000:
        raise HTTPException(413, "Input is too long.")

    try:
        result = await tailor_resume(resume_text, job_text, notes)
    except TailorError as exc:
        raise HTTPException(502, str(exc)) from exc
    except anthropic.AuthenticationError as exc:
        raise HTTPException(500, "Anthropic API key is missing or invalid.") from exc
    except anthropic.RateLimitError as exc:
        raise HTTPException(429, "Rate limited by the Anthropic API. Try again shortly.") from exc
    except anthropic.APIStatusError as exc:
        raise HTTPException(502, f"Anthropic API error ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:
        raise HTTPException(502, "Could not reach the Anthropic API.") from exc
    except TypeError as exc:  # SDK raises this when no credentials can be resolved
        if "authentication" in str(exc).lower():
            raise HTTPException(500, "No Anthropic credentials. Set ANTHROPIC_API_KEY in backend/.env.") from exc
        raise

    return {"original_text": resume_text, "result": result.model_dump()}


def _filename(resume: Resume, ext: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", resume.name).strip("_") or "resume"
    return f"{base}_tailored.{ext}"


@app.post("/api/export/docx")
def export_docx(resume: Resume):
    return Response(
        to_docx(resume),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{_filename(resume, "docx")}"'},
    )


@app.post("/api/export/markdown")
def export_markdown(resume: Resume):
    return PlainTextResponse(to_markdown(resume))


@app.get("/api/health")
def health():
    return {"ok": True}


# ---- serve the built React app in production ---------------------------------
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        target = DIST / path
        if path and target.is_file() and DIST in target.resolve().parents:
            return FileResponse(target)
        return FileResponse(DIST / "index.html")
