import { useState } from "react";
import { api } from "../services/api.js";
import { useJobStatus } from "../hooks/useJobStatus.js";

export default function ReviewModal({ group, file, onClose, onApplied }) {
  const [step, setStep] = useState("idle"); // idle | scanning | reviewing | applying | done
  const [suggestions, setSuggestions] = useState([]);
  const [edited, setEdited] = useState({});
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);

  useJobStatus(jobId, () => {
    setStep("done");
    setJobId(null);
    onApplied();
  });

  const scan = async () => {
    setStep("scanning");
    setError(null);
    try {
      const items = await api.scanFile(group, file);
      if (items.length === 0) {
        setError("No AI suggestions needed — this file has no missing alt text or slide titles.");
        setStep("idle");
        return;
      }
      const initialEdits = {};
      items.forEach((s) => {
        initialEdits[`${s.check_id}|${s.element_ref}`] = s.draft_text;
      });
      setSuggestions(items);
      setEdited(initialEdits);
      setStep("reviewing");
    } catch (err) {
      setError(err.message);
      setStep("idle");
    }
  };

  const apply = async () => {
    setStep("applying");
    setError(null);
    try {
      const payload = suggestions.map((s) => ({
        check_id: s.check_id,
        element_ref: s.element_ref,
        approved_text: edited[`${s.check_id}|${s.element_ref}`] ?? s.draft_text,
      }));
      const { job_id } = await api.applyReview(group, file, payload);
      setJobId(job_id);
    } catch (err) {
      setError(err.message);
      setStep("reviewing");
    }
  };

  const typeLabel = (type) => (type === "slide_title" ? "Slide title" : "Alt text");

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Review AI suggestions for ${file}`}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
      }}
    >
      <div
        style={{
          background: "var(--surface, #fff)", borderRadius: 8, padding: 28,
          width: "min(680px, 95vw)", maxHeight: "85vh", overflowY: "auto",
          boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Review AI Suggestions — {file}</h2>
        <p style={{ color: "var(--text-muted, #666)", marginTop: 0 }}>
          The AI generated draft alt text and slide titles. Edit anything that looks wrong,
          then click <strong>Apply</strong> to write the approved text into the remediated file.
        </p>

        {error && <p className="error">{error}</p>}

        {step === "idle" && (
          <p className="muted">Click <strong>Scan</strong> to generate AI suggestions for this file.</p>
        )}

        {step === "scanning" && <p className="muted">Scanning file and generating suggestions…</p>}

        {step === "reviewing" && suggestions.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 20 }}>
            {suggestions.map((s) => {
              const key = `${s.check_id}|${s.element_ref}`;
              return (
                <div
                  key={key}
                  style={{
                    border: "1px solid var(--border, #ddd)", borderRadius: 6, padding: 14,
                    background: s.is_placeholder ? "var(--surface-warn, #fffbe6)" : "var(--surface-ok, #f0fff4)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>
                      {typeLabel(s.suggestion_type)} — {s.element_ref}
                    </span>
                    {s.is_placeholder && (
                      <span className="badge" style={{ fontSize: 11 }}>AI unavailable — please edit</span>
                    )}
                  </div>
                  <textarea
                    rows={2}
                    value={edited[key] ?? s.draft_text}
                    onChange={(e) => setEdited((prev) => ({ ...prev, [key]: e.target.value }))}
                    style={{
                      width: "100%", resize: "vertical", fontFamily: "inherit",
                      padding: "6px 8px", borderRadius: 4, border: "1px solid var(--border, #ccc)",
                      boxSizing: "border-box",
                    }}
                    aria-label={`Edit ${typeLabel(s.suggestion_type)} for ${s.element_ref}`}
                  />
                </div>
              );
            })}
          </div>
        )}

        {step === "applying" && <p className="muted">Applying your approved suggestions…</p>}
        {step === "done" && <p style={{ color: "green" }}>Done! File has been remediated with your approved text.</p>}

        <div className="row" style={{ gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onClose} disabled={step === "scanning" || step === "applying"}>
            Close
          </button>
          {step === "idle" && (
            <button onClick={scan}>Scan for AI Suggestions</button>
          )}
          {step === "reviewing" && (
            <button onClick={apply}>Apply Approved Text</button>
          )}
        </div>
      </div>
    </div>
  );
}
