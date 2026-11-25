# Resume Tailor

Upload a resume and paste a job posting. Claude rewrites the resume for that role, using **only facts from the original**, and shows how well each requirement is covered.

- **Frontend:** React + Vite. Upload or paste a resume, paste the job requirements, then review the tailored resume next to the original.
- **Backend:** Python + FastAPI. Reads PDF, DOCX or TXT resumes, calls Claude with structured output, and exports the result to Word (.docx) or Markdown.

## What you get

- **A tailored resume**: new summary, regrouped skills, and reordered, reworded bullets using the posting's terminology where your experience supports it. Employers, titles and dates stay exactly as written.
- **Requirement coverage**: each key requirement rated *strong*, *partial* or *missing*, with the evidence from your resume.
- **Gaps and advice**: what to do about requirements the resume can't support (mention it in a cover letter, add it if you really have it, or build it).
- **A change log**: what was changed and why.
- **Exports**: an ATS-friendly .docx download, or copy as Markdown.

### Truthfulness

The prompt forbids inventing employers, titles, dates, degrees, certifications, tools, metrics or achievements. Unsupported requirements go into *Gaps* instead of onto the resume. Still, review every line before you send it.

## Quick start

Requirements: Python 3.10+, Node 18+, and an [Anthropic API key](https://console.anthropic.com/).

**Backend**

```bash
cd backend
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows:     .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then put your key in .env
uvicorn app.main:app --port 8001
```

**Frontend** (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5174. To try it quickly, use [`samples/sample-resume.txt`](samples/sample-resume.txt) and paste [`samples/sample-job.txt`](samples/sample-job.txt) (both fictional). A run takes about 30-60 seconds.

### Docker

```bash
docker build -t resume-tailor .
docker run -p 8001:8001 -e ANTHROPIC_API_KEY=sk-ant-... resume-tailor
```

Open http://localhost:8001. The container listens on `$PORT` (default 8001), so it deploys as-is to Render, Railway or Fly.io.

## Configuration (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Model used for the rewrite |
| `CLAUDE_EFFORT` | `medium` | `low` is faster and cheaper; `high` is more thorough |
| `CORS_ORIGINS` | `http://localhost:5174` | Allowed origins (comma-separated) |

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tailor` | Multipart form: `resume_file` *or* `resume_text`, plus `job_text` and optional `notes`. Returns `{original_text, result}` |
| `POST` | `/api/export/docx` | Body: the `result.resume` object. Returns a .docx file |
| `POST` | `/api/export/markdown` | Body: the `result.resume` object. Returns Markdown |

## Project layout

```
backend/app/
  main.py     FastAPI routes and static hosting of the built UI
  extract.py  PDF / DOCX / TXT → plain text
  schema.py   Pydantic models for the structured output (resume + analysis)
  tailor.py   System prompt and the Claude call
  export.py   .docx and Markdown rendering
frontend/src/
  App.jsx     Input form, progress, tailored/original views, analysis panel
  api.js      fetch helpers and the .docx download
```

## Privacy

Resumes are sent to the Anthropic API for processing and are not stored by this app. There is no authentication or rate limiting, so don't expose a deployment publicly without adding them.

## License

MIT
