import { useEffect, useMemo, useRef, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { getModels, getSamples, screen } from "./api";
import SetupPanel from "./components/SetupPanel.jsx";
import Results from "./components/Results.jsx";
import EmptyState from "./components/EmptyState.jsx";
import Running from "./components/Running.jsx";

function initialTheme() {
  try {
    const saved = localStorage.getItem("theme");
    if (saved) return saved;
  } catch {}
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState(initialTheme);
  const [samples, setSamples] = useState({ jds: [], resumes: [] });
  const [models, setModels] = useState({ default: "bge-large", models: [] });
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [useSamples, setUseSamples] = useState(false);
  const [topK, setTopK] = useState(5);
  const [model, setModel] = useState("bge-large");
  const [phase, setPhase] = useState("idle"); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const resultsRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch {}
  }, [theme]);

  useEffect(() => {
    getSamples().then(setSamples).catch(() => {});
    getModels().then((m) => { setModels(m); setModel(m.default); }).catch(() => {});
  }, []);

  const resumeCount = resumes.length + (useSamples ? samples.resumes.length : 0);
  const hasJd = jdText.trim().split(/\s+/).filter(Boolean).length >= 15 || !!jdFile;
  const canRun = hasJd && resumeCount > 0 && phase !== "running";

  async function run() {
    setPhase("running");
    setError("");
    try {
      const data = await screen({ jdText, jdFile, resumes, useSamples, topK, model });
      setResult(data);
      setPhase("done");
      requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (e) {
      setError(e.message || "Something went wrong.");
      setPhase("error");
    }
  }

  const props = {
    samples, models, jdText, setJdText, jdFile, setJdFile, resumes, setResumes,
    useSamples, setUseSamples, topK, setTopK, model, setModel, resumeCount, canRun, run,
    running: phase === "running",
  };

  return (
    <>
      <header className="topbar">
        <div className="wordmark" aria-label="Shortlist">
          <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="var(--cobalt)" />
            <rect x="7" y="9" width="18" height="3.5" rx="1.75" fill="#fff" />
            <rect x="7" y="15" width="13" height="3.5" rx="1.75" fill="#fff" opacity=".8" />
            <rect x="7" y="21" width="8" height="3.5" rx="1.75" fill="#fff" opacity=".6" />
          </svg>
          <span>Shortlist</span>
        </div>
        <button className="icon-btn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}>
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      <main className="shell">
        <SetupPanel {...props} />
        <section className="stage" ref={resultsRef} aria-live="polite">
          {phase === "idle" && <EmptyState />}
          {phase === "running" && <Running model={model} />}
          {phase === "error" && (
            <div className="alert" role="alert">
              <strong>Screening stopped.</strong> {error}
            </div>
          )}
          {phase === "done" && result && <Results result={result} />}
        </section>
      </main>
    </>
  );
}
