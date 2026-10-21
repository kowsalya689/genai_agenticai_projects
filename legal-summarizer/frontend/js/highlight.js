// Splits a summary into plain text, verified facts (numbers/dates found in the source) and flagged facts/terms
// (reported by the server's faithfulness check as NOT in the source). Pure functions, no DOM.

const MON = "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)";
const DMY = `\\d{1,2}(?:st|nd|rd|th)?\\s+(?:day\\s+of\\s+)?${MON}\\.?,?\\s+\\d{4}`;
const MDY = `${MON}\\.?\\s+\\d{1,2}(?:st|nd|rd|th)?,?\\s+\\d{4}`;
const NUM = "\\d[\\d,]*(?:\\.\\d+)?%?";
const FACT_RE = () => new RegExp(`\\b(?:${DMY}|${MDY})\\b|${NUM}`, "gi");
const DMY_RE = new RegExp(`^(\\d{1,2})(?:st|nd|rd|th)?\\s+(?:day\\s+of\\s+)?(${MON})\\.?,?\\s+(\\d{4})$`, "i");
const MDY_RE = new RegExp(`^(${MON})\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(\\d{4})$`, "i");
const MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
const WORD_RE = /([A-Za-z][A-Za-z'&-]*)/;

const pad = (n, w) => String(n).padStart(w, "0");
const iso = (y, m, d) => `${pad(y, 4)}-${pad(m, 2)}-${pad(d, 2)}`;

export function parseDateIso(s) {
  let m = DMY_RE.exec(s);
  if (m) return iso(+m[3], MONTHS.indexOf(m[2].slice(0, 3).toLowerCase()) + 1, +m[1]);
  m = MDY_RE.exec(s);
  if (m) return iso(+m[3], MONTHS.indexOf(m[1].slice(0, 3).toLowerCase()) + 1, +m[2]);
  return null;
}

export function buildSegments(text, faith = {}) {
  const badNums = new Set(faith.unsupported_numbers || []);
  const badDates = new Set(faith.unsupported_dates || []);
  const badTerms = new Set(faith.unsupported_terms || []);
  const out = [];
  const pushPlain = (chunk) => {
    // within plain text, flag any word the server reported as missing from the source
    for (const part of chunk.split(WORD_RE)) {
      if (!part) continue;
      out.push({ text: part, kind: badTerms.has(part) ? "flag" : "plain" });
    }
  };
  let last = 0, m;
  const re = FACT_RE();
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) pushPlain(text.slice(last, m.index));
    const raw = m[0];
    const date = parseDateIso(raw);
    const digitRuns = (raw.match(/\d[\d,]*(?:\.\d+)?/g) || []).map((n) => n.replace(/,/g, ""));
    const flagged = (date && badDates.has(date)) || digitRuns.some((n) => badNums.has(n));
    out.push({ text: raw, kind: flagged ? "flag" : "fact" });
    last = m.index + raw.length;
  }
  if (last < text.length) pushPlain(text.slice(last));
  return out;
}
