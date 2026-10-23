import { useState } from "react";
import { Check, ChevronDown, Copy, Github, Linkedin, Mail, Phone, X } from "lucide-react";
import { composition, tone } from "../util";

const LABELS = {
  required: "Required skills", responsibilities: "Responsibilities", preferred: "Nice-to-have", role: "Role summary",
  skills_must: "Must-have skill coverage", skills_nice: "Nice-to-have coverage", years: "Years of experience",
};
const SECTION = { required: "Required", responsibilities: "Duties", preferred: "Nice-to-have", role: "Role" };

function Copy1({ value, label }) {
  const [done, setDone] = useState(false);
  return (
    <button className="icon-btn sm" aria-label={`Copy ${label}`}
      onClick={async () => { try { await navigator.clipboard.writeText(value); setDone(true); setTimeout(() => setDone(false), 1200); } catch {} }}>
      {done ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
}

function Contact({ icon: Icon, label, value, href }) {
  if (!value) return null;
  return (
    <li>
      <Icon size={15} aria-hidden="true" />
      <a href={href} target={href?.startsWith("http") ? "_blank" : undefined} rel="noreferrer">{value}</a>
      <Copy1 value={value} label={label} />
    </li>
  );
}

export default function CandidateRow({ c, i, weights, blind, open, onToggle }) {
  const comp = composition(c, weights);
  const fit = c.fit_score || 1;
  const id = `row-${i}`;
  const name = blind ? `Candidate ${String(c.rank).padStart(2, "0")}` : c.name;
  const url = (v) => (v.startsWith("http") ? v : `https://${v}`);

  return (
    <li className={"cand " + tone(c.fit_score)} style={{ "--i": i }}>
      <button className="cand-main" aria-expanded={open} aria-controls={id} onClick={onToggle}>
        <span className="rank">{c.rank}</span>
        <span className="who">
          <strong>{name}</strong>
          <span className="muted">
            {[c.designation, c.years != null ? `${c.years} yrs` : null, !blind && c.location].filter(Boolean).join(" · ")}
          </span>
        </span>
        <span className="meter" role="img"
          aria-label={`Fit ${c.fit_score}. Meaning ${comp.meaning.toFixed(0)}, skills ${comp.skills.toFixed(0)}, experience ${comp.years.toFixed(0)}`}>
          <span className="track">
            <span className="fill" style={{ width: `${c.fit_score}%` }}>
              <i className="part meaning" style={{ flexGrow: comp.meaning }} />
              <i className="part skills" style={{ flexGrow: comp.skills }} />
              <i className="part years" style={{ flexGrow: comp.years }} />
            </span>
          </span>
        </span>
        <span className="score"><b>{Math.round(c.fit_score)}</b></span>
        <ChevronDown size={18} className="chev" aria-hidden="true" />
      </button>

      <div className="skills-line">
        {c.matched_must.slice(0, 6).map((s) => <span key={s} className="chip ok">{s}</span>)}
        {c.matched_must.length > 6 && <span className="chip plain">+{c.matched_must.length - 6}</span>}
        {c.missing_must.slice(0, 3).map((s) => <span key={s} className="chip miss">{s}</span>)}
      </div>

      <div className={"detail" + (open ? " open" : "")} id={id}>
        <div className="detail-inner">
          <div className="detail-grid">
            <section>
              <h4>Why it ranks here</h4>
              <p>{c.reason}</p>

              {c.missing_must.length > 0 && (
                <p className="gap"><X size={14} aria-hidden="true" /> Missing: {c.missing_must.join(", ")}</p>
              )}

              <h4>Contact</h4>
              {blind ? (
                <p className="muted">Hidden during blind review.</p>
              ) : (
                <ul className="contact">
                  <Contact icon={Mail} label="email" value={c.email} href={`mailto:${c.email}`} />
                  <Contact icon={Phone} label="phone" value={c.phone} href={`tel:${c.phone.replace(/[^\d+]/g, "")}`} />
                  <Contact icon={Linkedin} label="LinkedIn" value={c.linkedin} href={c.linkedin && url(c.linkedin)} />
                  <Contact icon={Github} label="GitHub" value={c.github} href={c.github && url(c.github)} />
                  {!c.email && !c.phone && <li className="muted">No contact details found in this file.</li>}
                </ul>
              )}

              <h4>Score breakdown</h4>
              <dl className="bd">
                {Object.entries(c.breakdown).filter(([, v]) => v != null).map(([k, v]) => (
                  <div key={k}>
                    <dt>{LABELS[k]}</dt>
                    <dd><span className="mini"><i style={{ width: `${v}%` }} /></span><b>{v}</b></dd>
                  </div>
                ))}
              </dl>
            </section>

            <section>
              <h4>Closest matches to the role</h4>
              {c.evidence.length === 0 && <p className="muted">No close passages found.</p>}
              {c.evidence.map((e, k) => (
                <figure key={k} className="ev">
                  <figcaption>{SECTION[e.jd_section]} in the JD</figcaption>
                  <blockquote className="jd">{e.jd_chunk}</blockquote>
                  <figcaption>From the resume’s {e.resume_section} · similarity {e.sim.toFixed(2)}</figcaption>
                  <blockquote className="cv">{e.resume_chunk}</blockquote>
                </figure>
              ))}
            </section>
          </div>
        </div>
      </div>
    </li>
  );
}
