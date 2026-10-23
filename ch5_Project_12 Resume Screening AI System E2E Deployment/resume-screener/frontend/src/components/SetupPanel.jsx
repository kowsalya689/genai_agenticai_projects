import { useRef, useState } from "react";
import { FileText, Minus, Plus, Upload, X } from "lucide-react";

export default function SetupPanel(p) {
  const jdInput = useRef(null);
  const resumeInput = useRef(null);
  const [drag, setDrag] = useState(false);
  const maxK = Math.max(1, p.resumeCount || 50);

  function addResumes(list) {
    const ok = Array.from(list).filter((f) => /\.(pdf|docx|txt)$/i.test(f.name));
    const names = new Set(p.resumes.map((f) => f.name + f.size));
    p.setResumes([...p.resumes, ...ok.filter((f) => !names.has(f.name + f.size))]);
  }

  async function pickJd(file) {
    if (!file) return;
    if (/\.txt$|\.md$/i.test(file.name)) {
      p.setJdText(await file.text());
      p.setJdFile(null);
    } else {
      p.setJdFile(file);
      p.setJdText("");
    }
  }

  return (
    <aside className="setup">
      <div className="block">
        <div className="block-head">
          <h2>Job description</h2>
          <button className="link" onClick={() => jdInput.current?.click()}>Upload file</button>
          <input ref={jdInput} type="file" hidden accept=".txt,.md,.pdf,.docx"
            onChange={(e) => pickJd(e.target.files[0])} />
        </div>

        {p.jdFile ? (
          <div className="file-pill">
            <FileText size={16} /> <span>{p.jdFile.name}</span>
            <button className="icon-btn sm" onClick={() => p.setJdFile(null)} aria-label="Remove job description file">
              <X size={14} />
            </button>
          </div>
        ) : (
          <textarea value={p.jdText} onChange={(e) => p.setJdText(e.target.value)} rows={9}
            placeholder="Paste the job description, or upload a file. Sections such as required skills, responsibilities and years of experience are picked up automatically."
            aria-label="Job description text" />
        )}

        {p.samples.jds.length > 0 && (
          <div className="samples">
            <span className="muted">Try a sample</span>
            {p.samples.jds.map((jd) => (
              <button key={jd.id} className="chip-btn" onClick={() => { p.setJdText(jd.text); p.setJdFile(null); }}>
                {jd.label.replace(/^JD\d+ /, "")}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="block">
        <div className="block-head">
          <h2>Resumes</h2>
          <span className="count">{p.resumeCount}</span>
        </div>

        <div className={"drop" + (drag ? " over" : "")}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); addResumes(e.dataTransfer.files); }}>
          <Upload size={20} aria-hidden="true" />
          <p>Drop PDF, DOCX or TXT files here</p>
          <button className="btn ghost" onClick={() => resumeInput.current?.click()}>Choose files</button>
          <input ref={resumeInput} type="file" multiple hidden accept=".pdf,.docx,.txt"
            onChange={(e) => { addResumes(e.target.files); e.target.value = ""; }} />
        </div>

        {p.samples.resumes.length > 0 && (
          <label className="check">
            <input type="checkbox" checked={p.useSamples} onChange={(e) => p.setUseSamples(e.target.checked)} />
            <span>Include the {p.samples.resumes.length} sample resumes</span>
          </label>
        )}

        {p.resumes.length > 0 && (
          <ul className="files">
            {p.resumes.map((f, i) => (
              <li key={f.name + f.size}>
                <FileText size={14} aria-hidden="true" />
                <span title={f.name}>{f.name}</span>
                <button className="icon-btn sm" aria-label={`Remove ${f.name}`}
                  onClick={() => p.setResumes(p.resumes.filter((_, j) => j !== i))}>
                  <X size={14} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="block row2">
        <div>
          <label htmlFor="k" className="label">Shortlist size</label>
          <div className="stepper">
            <button className="icon-btn sm" aria-label="Fewer" onClick={() => p.setTopK(Math.max(1, p.topK - 1))}>
              <Minus size={14} />
            </button>
            <input id="k" type="number" min={1} max={maxK} value={p.topK}
              onChange={(e) => p.setTopK(Math.max(1, Math.min(maxK, Number(e.target.value) || 1)))} />
            <button className="icon-btn sm" aria-label="More" onClick={() => p.setTopK(Math.min(maxK, p.topK + 1))}>
              <Plus size={14} />
            </button>
          </div>
        </div>
        <div>
          <label htmlFor="m" className="label">Embedding model</label>
          <select id="m" value={p.model} onChange={(e) => p.setModel(e.target.value)}>
            {(p.models.models.length ? p.models.models : [{ key: p.model, label: p.model, available: true }]).map((m) => (
              <option key={m.key} value={m.key}>{m.label}{m.available === false ? " (unavailable)" : ""}</option>
            ))}
          </select>
        </div>
      </div>

      <button className="btn primary run" disabled={!p.canRun} onClick={p.run}>
        {p.running ? "Screening…" : "Rank resumes"}
      </button>
      {!p.canRun && !p.running && (
        <p className="hint">
          {p.resumeCount === 0 ? "Add at least one resume." : "Add a job description."}
        </p>
      )}
    </aside>
  );
}
