import { useEffect, useState } from "react";
import { api } from "../services/api.js";
import { scoreBand } from "../utils/score.js";

function ScoreBox({ label, value }) {
  return (
    <div className="score-box">
      <div className={`num ${scoreBand(value)}`}>{value ?? "—"}</div>
      <div className="muted">{label}</div>
    </div>
  );
}

function FixList({ items, emptyText, acknowledged, onAck }) {
  if (items.length === 0) return <p className="muted">{emptyText}</p>;
  return (
    <ul className="fix-list">
      {items.map((fix, i) => (
        <li key={`${fix.check_id}-${fix.element_ref}-${i}`}>
          <span>
            <code>{fix.check_id}</code> — {fix.element_ref}
            <br />
            <span className="muted">{fix.detail}</span>
          </span>
          {onAck &&
            (acknowledged.has(fix.check_id + fix.element_ref) ? (
              <span className="badge complete">acknowledged</span>
            ) : (
              <button className="secondary" onClick={() => onAck(fix)}>
                Acknowledge
              </button>
            ))}
        </li>
      ))}
    </ul>
  );
}

// Honest report (domain-knowledge.md): two scores, and placeholders kept
// separate from genuine fixes so they are never presented as real.
export default function ReportViewer({ group, name }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [acknowledged, setAcknowledged] = useState(new Set());

  useEffect(() => {
    api
      .getReport(group, name)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [group, name]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <p className="muted">Loading report…</p>;

  const fixes = report.fixes || [];
  const genuine = fixes.filter((f) => f.action === "auto_fixed" || f.action === "ai_fixed");
  const placeholders = fixes.filter((f) => f.action === "placeholder");
  const manual = fixes.filter((f) => f.action === "not_fixed");
  const scores = report.scores || {};

  const onAck = async (fix) => {
    try {
      await api.signoff(group, name, fix.check_id);
      setAcknowledged((prev) => new Set(prev).add(fix.check_id + fix.element_ref));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h1 style={{ color: "var(--text-head)" }}>{report.file_name}</h1>
      <div className="scores">
        <ScoreBox label="Before" value={scores.pre_fix?.score} />
        <ScoreBox label="After (checker)" value={scores.post_fix_checker_passing?.score} />
        <ScoreBox label="Truly remediated" value={scores.truly_remediated?.score} />
      </div>
      <p className="muted">
        The gap between “checker” and “truly remediated” is the work that still needs a
        human. The real score is confirmed when you re-upload to Canvas.
      </p>

      <div className="card">
        <h3 style={{ color: "var(--text-head)" }}>Genuinely fixed ({genuine.length})</h3>
        <FixList items={genuine} emptyText="No automatic fixes were needed." />
      </div>

      <div className="card">
        <h3 style={{ color: "var(--text-head)" }}>
          Needs human follow-up — placeholders ({placeholders.length})
        </h3>
        <FixList
          items={placeholders}
          emptyText="No placeholders — every item was genuinely fixed."
          acknowledged={acknowledged}
          onAck={onAck}
        />
      </div>

      <div className="card">
        <h3 style={{ color: "var(--text-head)" }}>
          Needs manual fix — report only ({manual.length})
        </h3>
        <FixList items={manual} emptyText="Nothing requires a manual fix." />
      </div>
    </div>
  );
}
