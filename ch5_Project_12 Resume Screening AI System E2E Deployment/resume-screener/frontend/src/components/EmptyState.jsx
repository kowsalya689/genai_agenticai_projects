const JD_STEPS = ["Read the file", "Clean the text", "Split into sections", "Embed each section", "Store the vectors"];
const CV_STEPS = ["Read each file", "Clean the text", "Split into sections", "Embed each section", "Compare with the JD"];
const END_STEPS = ["Score", "Rank", "Pull out names and contacts", "Show the table"];

function Lane({ title, steps }) {
  return (
    <div className="lane">
      <h3>{title}</h3>
      <ol>{steps.map((s) => <li key={s}>{s}</li>)}</ol>
    </div>
  );
}

export default function EmptyState() {
  return (
    <div className="empty">
      <h1>Rank resumes by what they say, not by the keywords they repeat.</h1>
      <p className="lede">
        Add a job description and a stack of resumes. Each resume is compared with the role section by section,
        so a Spark engineer is not lost because they wrote “PySpark”.
      </p>
      <div className="lanes">
        <Lane title="Job description" steps={JD_STEPS} />
        <Lane title="Every resume" steps={CV_STEPS} />
      </div>
      <div className="lane end">
        <h3>Then</h3>
        <ol className="inline">{END_STEPS.map((s) => <li key={s}>{s}</li>)}</ol>
      </div>
      <p className="fair">
        Names, contact details and gender never affect the score. Use blind review to hide them while you read.
      </p>
    </div>
  );
}
