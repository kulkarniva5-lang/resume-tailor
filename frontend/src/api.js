async function errorMessage(res) {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* not JSON */
  }
  return `Request failed (${res.status})`;
}

export async function tailorResume({ file, resumeText, jobText, notes }) {
  const form = new FormData();
  if (file) form.append("resume_file", file);
  form.append("resume_text", resumeText || "");
  form.append("job_text", jobText);
  form.append("notes", notes || "");
  const res = await fetch("/api/tailor", { method: "POST", body: form });
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function downloadDocx(resume) {
  const res = await fetch("/api/export/docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
  if (!res.ok) throw new Error(await errorMessage(res));
  const blob = await res.blob();
  const name =
    res.headers.get("Content-Disposition")?.match(/filename="(.+)"/)?.[1] || "resume_tailored.docx";
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export async function getMarkdown(resume) {
  const res = await fetch("/api/export/markdown", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resume),
  });
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.text();
}
