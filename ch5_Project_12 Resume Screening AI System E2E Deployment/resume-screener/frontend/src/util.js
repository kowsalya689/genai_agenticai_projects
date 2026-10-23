export const SEMANTIC = ["required", "responsibilities", "preferred", "role"];
export const SKILLS = ["skills_must", "skills_nice"];

/** Share of the fit score contributed by meaning, skills and experience (each 0..fit_score). */
export function composition(c, weights) {
  const b = c.breakdown;
  const active = Object.keys(weights).filter((k) => b[k] != null);
  const total = active.reduce((s, k) => s + weights[k], 0) || 1;
  const part = (keys) =>
    keys.filter((k) => b[k] != null).reduce((s, k) => s + (weights[k] * b[k]) / total, 0);
  return { meaning: part(SEMANTIC), skills: part(SKILLS), years: part(["years"]) };
}

export function tone(score) {
  if (score >= 70) return "strong";
  if (score >= 50) return "fair";
  return "weak";
}

export function toCSV(candidates) {
  const cols = [
    ["rank", "Rank"], ["name", "Name"], ["fit_score", "Fit score"], ["relative_score", "Relative score"],
    ["email", "Email"], ["phone", "Phone"], ["linkedin", "LinkedIn"], ["github", "GitHub"],
    ["designation", "Designation"], ["location", "Location"], ["years", "Years of experience"],
    ["matched_must", "Matched must-have skills"], ["missing_must", "Missing must-have skills"],
    ["reason", "Reason"], ["file_name", "File"],
  ];
  const esc = (v) => {
    const s = Array.isArray(v) ? v.join("; ") : v ?? "";
    return `"${String(s).replace(/"/g, '""')}"`;
  };
  return [cols.map((c) => esc(c[1])).join(",")]
    .concat(candidates.map((c) => cols.map((k) => esc(c[k[0]])).join(",")))
    .join("\n");
}

export function download(name, text, type = "text/csv") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  URL.revokeObjectURL(url);
}
