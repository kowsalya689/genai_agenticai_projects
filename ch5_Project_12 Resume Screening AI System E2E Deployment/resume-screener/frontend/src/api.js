export async function getSamples() {
  const r = await fetch("/api/samples");
  if (!r.ok) throw new Error("Could not load sample data");
  return r.json();
}

export async function getModels() {
  const r = await fetch("/api/models");
  if (!r.ok) throw new Error("Could not load models");
  return r.json();
}

export async function screen({ jdText, jdFile, resumes, useSamples, topK, model }) {
  const fd = new FormData();
  fd.append("jd_text", jdText || "");
  if (jdFile) fd.append("jd_file", jdFile);
  resumes.forEach((f) => fd.append("resumes", f));
  fd.append("use_sample_resumes", String(useSamples));
  fd.append("top_k", String(topK));
  fd.append("model", model);
  const r = await fetch("/api/screen", { method: "POST", body: fd });
  if (!r.ok) {
    let msg = `Request failed (${r.status})`;
    try {
      const j = await r.json();
      if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}
