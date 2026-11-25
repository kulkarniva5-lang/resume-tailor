import { useEffect, useState } from "react";
import { downloadDocx, getMarkdown, tailorResume } from "./api.js";

const STEPS = [
  "Reading your resume",
  "Picking out the job's key requirements",
  "Matching your experience to each requirement",
  "Rewriting summary, skills and bullets",
  "Checking every claim against the original",
];

export default function App() {
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jobText, setJobText] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null); // { original_text, result }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      setData(await tailorResume({ file, resumeText, jobText, notes }));
      window.scrollTo({ top: 0 });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = (file || resumeText.trim().length >= 50) && jobText.trim().length >= 30 && !loading;

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="logo">✎</span>
          <div>
            <h1>Resume Tailor</h1>
            <p>Rewrite your resume for a specific job, without making anything up.</p>
          </div>
        </div>
        {data && (
          <button className="ghost" onClick={() => setData(null)}>
            ← Edit inputs
          </button>
        )}
      </header>

      {data ? (
        <Result data={data} />
      ) : (
        <form className="inputs" onSubmit={submit}>
          <p className="privacy-note">
            Nothing is saved: your resume is processed in memory and discarded, and results disappear when you close this
            tab.
          </p>
          <section className="card">
            <h2>1. Your resume</h2>
            <FilePicker file={file} setFile={setFile} />
            <div className="or"><span>or paste it</span></div>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your current resume here…"
              disabled={!!file}
              rows={14}
            />
          </section>

          <section className="card">
            <h2>2. Job requirements</h2>
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste the job description or list of requirements…"
              rows={14}
              className="tall"
            />
            <label className="notes-label">
              Notes for the rewrite <span className="muted">(optional)</span>
            </label>
            <input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Keep it to one page. I also used Terraform at my last job."
              maxLength={4000}
            />
          </section>

          <div className="actions">
            {error && <div className="error">{error}</div>}
            <button type="submit" className="primary" disabled={!canSubmit}>
              {loading ? "Tailoring…" : "Tailor my resume"}
            </button>
            {loading && <Progress />}
          </div>
        </form>
      )}

      <footer className="footer">Built by VK</footer>
    </div>
  );
}

function FilePicker({ file, setFile }) {
  return (
    <label
      className={`drop ${file ? "has-file" : ""}`}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
      }}
    >
      <input
        type="file"
        accept=".pdf,.docx,.txt,.md"
        hidden
        onChange={(e) => {
          setFile(e.target.files[0] || null);
          e.target.value = "";
        }}
      />
      {file ? (
        <>
          <strong>{file.name}</strong>
          <button
            type="button"
            className="link"
            onClick={(e) => {
              e.preventDefault();
              setFile(null);
            }}
          >
            Remove
          </button>
        </>
      ) : (
        <>
          <strong>Drop a resume file</strong>
          <span className="muted">PDF, DOCX or TXT · or click to browse</span>
        </>
      )}
    </label>
  );
}

function Progress() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => Math.min(n + 1, STEPS.length - 1)), 9000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="progress">
      <div className="spinner" />
      <span>{STEPS[i]}… this usually takes under a minute.</span>
    </div>
  );
}

function Result({ data }) {
  const { result, original_text } = data;
  const [view, setView] = useState("tailored");
  const [toast, setToast] = useState("");

  const counts = { strong: 0, partial: 0, missing: 0 };
  result.requirements.forEach((r) => (counts[r.status] += 1));
  const total = result.requirements.length || 1;
  const coverage = Math.round(((counts.strong + counts.partial * 0.5) / total) * 100);

  function flash(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 2500);
  }

  return (
    <div className="result">
      <div className="result-main">
        <div className="toolbar">
          <div className="tabs" role="tablist">
            <button className={view === "tailored" ? "on" : ""} onClick={() => setView("tailored")}>
              Tailored
            </button>
            <button className={view === "original" ? "on" : ""} onClick={() => setView("original")}>
              Original
            </button>
          </div>
          <div className="toolbar-actions">
            <button
              className="ghost"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(await getMarkdown(result.resume));
                  flash("Copied as Markdown");
                } catch (e) {
                  flash(e.message || "Copy failed");
                }
              }}
            >
              Copy text
            </button>
            <button
              className="primary small"
              onClick={() => downloadDocx(result.resume).catch((e) => flash(e.message))}
            >
              Download .docx
            </button>
          </div>
        </div>
        {view === "tailored" ? <ResumeView r={result.resume} /> : <pre className="paper original">{original_text}</pre>}
        {toast && <div className="toast">{toast}</div>}
      </div>

      <aside className="analysis">
        <div className="card">
          <div className="eyebrow">Target role</div>
          <h3>{result.target_role}</h3>
          <div className="coverage">
            <div className="meter"><div style={{ width: `${coverage}%` }} /></div>
            <strong>{coverage}%</strong>
          </div>
          <p className="muted small">
            Requirement coverage: {counts.strong} strong · {counts.partial} partial · {counts.missing} missing
          </p>
        </div>

        <div className="card">
          <h4>Requirements</h4>
          <ul className="reqs">
            {result.requirements.map((r, i) => (
              <li key={i}>
                <span className={`pill ${r.status}`}>{r.status}</span>
                <div>
                  <div className="req">{r.requirement}</div>
                  <div className="muted small">{r.evidence}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {result.gaps.length > 0 && (
          <div className="card">
            <h4>Gaps &amp; how to handle them</h4>
            <ul className="plain">
              {result.gaps.map((g, i) => (
                <li key={i}>
                  <strong>{g.requirement}</strong>
                  <div className="muted small">{g.suggestion}</div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="card">
          <h4>What changed</h4>
          <ul className="plain dots">
            {result.changes.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>

        {result.keywords_used.length > 0 && (
          <div className="card">
            <h4>Job keywords now in your resume</h4>
            <div className="chips">
              {result.keywords_used.map((k) => <span key={k} className="chip">{k}</span>)}
            </div>
          </div>
        )}

        <p className="muted small disclaimer">
          Review every line before sending. The rewrite is told to use only facts from your original resume,
          but you are the final check.
        </p>
      </aside>
    </div>
  );
}

function ResumeView({ r }) {
  return (
    <article className="paper">
      <header className="r-head">
        <h2>{r.name}</h2>
        {r.headline && <div className="r-headline">{r.headline}</div>}
        {r.contact.length > 0 && <div className="r-contact">{r.contact.join("  ·  ")}</div>}
      </header>

      {r.summary && (
        <Section title="Summary">
          <p>{r.summary}</p>
        </Section>
      )}

      {r.skills.length > 0 && (
        <Section title="Skills">
          {r.skills.map((g) => (
            <p key={g.category} className="tight">
              <strong>{g.category}:</strong> {g.items.join(", ")}
            </p>
          ))}
        </Section>
      )}

      {r.experience.length > 0 && (
        <Section title="Experience">
          {r.experience.map((role, i) => (
            <div key={i} className="entry">
              <div className="entry-row">
                <strong>{role.title}</strong>
                <span className="muted">{role.dates}</span>
              </div>
              <div className="entry-sub">{[role.company, role.location].filter(Boolean).join(", ")}</div>
              <ul>{role.bullets.map((b, j) => <li key={j}>{b}</li>)}</ul>
            </div>
          ))}
        </Section>
      )}

      {r.projects.length > 0 && (
        <Section title="Projects">
          {r.projects.map((p, i) => (
            <div key={i} className="entry">
              <div className="entry-row">
                <strong>{p.name}</strong>
                {p.subtitle && <span className="muted">{p.subtitle}</span>}
              </div>
              <ul>{p.bullets.map((b, j) => <li key={j}>{b}</li>)}</ul>
            </div>
          ))}
        </Section>
      )}

      {r.education.length > 0 && (
        <Section title="Education">
          {r.education.map((e, i) => (
            <div key={i} className="entry">
              <div className="entry-row">
                <strong>{e.degree}</strong>
                <span className="muted">{e.dates}</span>
              </div>
              <div className="entry-sub">{e.institution}</div>
              {e.details && <p className="tight">{e.details}</p>}
            </div>
          ))}
        </Section>
      )}

      {r.certifications.length > 0 && (
        <Section title="Certifications">
          <ul>{r.certifications.map((c, i) => <li key={i}>{c}</li>)}</ul>
        </Section>
      )}

      {r.extra_sections.filter((s) => s.items.length).map((s) => (
        <Section key={s.heading} title={s.heading}>
          <ul>{s.items.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </Section>
      ))}
    </article>
  );
}

function Section({ title, children }) {
  return (
    <section className="r-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}
