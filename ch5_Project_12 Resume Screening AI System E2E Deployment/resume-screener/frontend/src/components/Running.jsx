import { useEffect, useState } from "react";

const STAGES = ["Reading files", "Splitting sections", "Embedding text", "Scoring and ranking"];

export default function Running({ model }) {
  const [t, setT] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setT((x) => x + 1), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="running" role="status">
      <div className="bar"><i /></div>
      <h2>Screening resumes</h2>
      <p>{STAGES.join(" · ")}</p>
      <p className="muted">
        {t}s elapsed.{" "}
        {model !== "hashing" && "The first run with a new model downloads it, which can take a few minutes."}
      </p>
    </div>
  );
}
