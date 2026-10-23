export default function CandidateTable({ rows, blind }) {
  const hide = (v) => (blind ? "Hidden" : v || "—");
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank</th><th>Name</th><th className="num">Fit</th><th>Email</th><th>Phone</th>
            <th>LinkedIn</th><th>GitHub</th><th className="num">Years</th><th>Matched skills</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.file_name}>
              <td className="num">{c.rank}</td>
              <th scope="row">{blind ? `Candidate ${String(c.rank).padStart(2, "0")}` : c.name}</th>
              <td className="num"><b>{Math.round(c.fit_score)}</b></td>
              <td>{hide(c.email)}</td>
              <td>{hide(c.phone)}</td>
              <td>{hide(c.linkedin)}</td>
              <td>{hide(c.github)}</td>
              <td className="num">{c.years ?? "—"}</td>
              <td>{c.matched_must.join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
