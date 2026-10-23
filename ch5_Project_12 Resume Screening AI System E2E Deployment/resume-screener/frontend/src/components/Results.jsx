import { useMemo, useState } from "react";
import { AlertTriangle, Download, Eye, EyeOff, List, Table2 } from "lucide-react";
import { download, toCSV } from "../util";
import CandidateRow from "./CandidateRow.jsx";
import CandidateTable from "./CandidateTable.jsx";

export default function Results({ result }) {
  const { meta, candidates, errors } = result;
  const [view, setView] = useState("ledger");
  const [blind, setBlind] = useState(false);
  const [openId, setOpenId] = useState(candidates[0]?.file_name ?? null);
  const [showRest, setShowRest] = useState(false);

  const short = useMemo(() => candidates.filter((c) => c.shortlisted), [candidates]);
  const rest = useMemo(() => candidates.filter((c) => !c.shortlisted), [candidates]);
  const jd = meta.jd;

  const rowProps = (c, i) => ({ c, i, weights: meta.weights, blind, jd,
    open: openId === c.file_name, onToggle: () => setOpenId(openId === c.file_name ? null : c.file_name) });

  return (
    <div className="results">
      {meta.fallback_note && (
        <div className="alert warn" role="status">
          <AlertTriangle size={16} aria-hidden="true" /> {meta.fallback_note}
        </div>
      )}

      <div className="results-head">
        <div>
          <h1>
            {short.length} of {candidates.length} shortlisted
            {jd.title ? <span className="for"> for {jd.title}</span> : null}
          </h1>
          <p className="muted">
            Scored with {meta.model} in {(meta.elapsed_ms / 1000).toFixed(1)}s.
            {jd.min_years != null && <> Role asks for {jd.min_years}{jd.max_years ? `–${jd.max_years}` : "+"} years.</>}
          </p>
        </div>
        <div className="tools">
          <div className="seg" role="group" aria-label="View">
            <button aria-pressed={view === "ledger"} onClick={() => setView("ledger")}><List size={15} /> Ranked</button>
            <button aria-pressed={view === "table"} onClick={() => setView("table")}><Table2 size={15} /> Table</button>
          </div>
          <button className="btn ghost" aria-pressed={blind} onClick={() => setBlind(!blind)}>
            {blind ? <EyeOff size={15} /> : <Eye size={15} />} Blind review
          </button>
          <button className="btn ghost" onClick={() => download("shortlist.csv", toCSV(short))}>
            <Download size={15} /> Export CSV
          </button>
        </div>
      </div>

      {jd.must_skills.length > 0 && (
        <div className="jd-skills">
          <span className="muted">Must-have skills read from the JD</span>
          <ul className="chips">{jd.must_skills.map((s) => <li key={s} className="chip">{s}</li>)}</ul>
        </div>
      )}

      <div className="legend" aria-hidden="true">
        <span><i className="sw meaning" />Meaning match</span>
        <span><i className="sw skills" />Skills covered</span>
        <span><i className="sw years" />Experience</span>
      </div>

      {view === "ledger" ? (
        <ol className="ledger">
          {short.map((c, i) => <CandidateRow key={c.file_name} {...rowProps(c, i)} />)}
        </ol>
      ) : (
        <CandidateTable rows={short} blind={blind} />
      )}

      {rest.length > 0 && (
        <div className="rest">
          <button className="link" aria-expanded={showRest} onClick={() => setShowRest(!showRest)}>
            {showRest ? "Hide" : "Show"} {rest.length} not shortlisted
          </button>
          {showRest && (view === "ledger" ? (
            <ol className="ledger dim" start={short.length + 1}>
              {rest.map((c, i) => <CandidateRow key={c.file_name} {...rowProps(c, short.length + i)} />)}
            </ol>
          ) : <CandidateTable rows={rest} blind={blind} />)}
        </div>
      )}

      {errors.length > 0 && (
        <div className="alert" role="alert">
          <strong>{errors.length} file{errors.length > 1 ? "s" : ""} could not be read.</strong>
          <ul>{errors.map((e) => <li key={e.file_name}>{e.file_name}: {e.error}</li>)}</ul>
        </div>
      )}
      <p className="muted foot">
        Fit score is an absolute 0–100 measure of how well a resume covers the role. It is not rescaled within the batch.
      </p>
    </div>
  );
}
