import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api.js";
import { useJobStatus } from "../hooks/useJobStatus.js";
import { scoreBand } from "../utils/score.js";
import ReviewModal from "./ReviewModal.jsx";
import UploadModal from "./UploadModal.jsx";

function Score({ value }) {
  if (value == null) return <span className="muted">—</span>;
  return <span className={`score ${scoreBand(value)}`}>{value}</span>;
}

export default function FileExplorer() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [activeJob, setActiveJob] = useState(null); // { group, id }
  const [reviewTarget, setReviewTarget] = useState(null); // { group, file }

  const load = useCallback(async () => {
    setError(null);
    try {
      const summaries = await api.listGroups();
      const details = await Promise.all(summaries.map((g) => api.getGroup(g.name)));
      setGroups(details);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const jobStatus = useJobStatus(activeJob?.id, (settled) => {
    setActiveJob(null);
    // Some files may have failed while others succeeded — surface the summary;
    // per-file outcomes show on each row's status badge after reload.
    if (settled?.error) setError(settled.error);
    load();
  });

  const onFix = async (group) => {
    try {
      const { job_id } = await api.remediate(group);
      setActiveJob({ group, id: job_id });
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="muted">Loading your workspace…</p>;

  return (
    <div>
      <div className="row spread" style={{ marginBottom: 16 }}>
        <h2 style={{ color: "var(--text-head)", margin: 0 }}>Your files</h2>
        <button onClick={() => setUploadOpen(true)}>Upload</button>
      </div>

      {error && <p className="error">{error}</p>}

      {groups.length === 0 && (
        <div className="card muted">
          No files yet. Click <strong>Upload</strong> to add a group of lecture materials.
        </div>
      )}

      {groups.map((group) => {
        const busy = activeJob?.group === group.name;
        return (
          <div className="card" key={group.name}>
            <div className="group-header">
              <h3>{group.name}</h3>
              <button onClick={() => onFix(group.name)} disabled={!!activeJob}>
                {busy
                  ? `Fixing… ${jobStatus ? Math.round(jobStatus.progress * 100) : 0}%`
                  : "Fix All"}
              </button>
            </div>
            {busy && jobStatus?.current_file && (
              <p className="muted" style={{ fontSize: 12, margin: "4px 0 8px" }}>
                Processing: <strong>{jobStatus.current_file}</strong> ({jobStatus.files_done + 1} of {jobStatus.files_total})
              </p>
            )}
            <table className="files">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Status</th>
                  <th>Before</th>
                  <th>After</th>
                  <th>Truly fixed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {group.files.map((file) => {
                  const isActive = busy && jobStatus?.current_file === file.name;
                  return (
                  <tr key={file.name} style={isActive ? { background: "var(--surface-raised, #f0f4ff)" } : {}}>
                    <td>{file.name}{isActive && <span className="badge" style={{ marginLeft: 6 }}>fixing…</span>}</td>
                    <td>
                      <span className={`badge ${file.status}`}>{file.status}</span>
                    </td>
                    <td>
                      <Score value={file.pre_fix_score} />
                    </td>
                    <td>
                      <Score value={file.post_fix_score} />
                    </td>
                    <td>
                      <Score value={file.truly_remediated_score} />
                    </td>
                    <td className="row" style={{ gap: 10 }}>
                      <button
                        className="btn-link"
                        onClick={() =>
                          api
                            .download(group.name, file.name, "input")
                            .catch((err) => setError(err.message))
                        }
                      >
                        original
                      </button>
                      {file.has_output && (
                        <>
                          <button
                            className="btn-link"
                            onClick={() =>
                              api
                                .download(group.name, file.name, "output")
                                .catch((err) => setError(err.message))
                            }
                          >
                            remediated
                          </button>
                          <Link
                            to={`/groups/${encodeURIComponent(group.name)}/files/${encodeURIComponent(
                              file.name
                            )}/report`}
                          >
                            report
                          </Link>
                        </>
                      )}
                      {file.file_type === "pptx" && (
                        <button
                          style={{ fontSize: 12, padding: "2px 8px" }}
                          disabled={!!activeJob}
                          onClick={() => setReviewTarget({ group: group.name, file: file.name })}
                        >
                          Review AI
                        </button>
                      )}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}

      {uploadOpen && (
        <UploadModal
          onClose={() => setUploadOpen(false)}
          onUploaded={() => {
            setUploadOpen(false);
            load();
          }}
        />
      )}

      {reviewTarget && (
        <ReviewModal
          group={reviewTarget.group}
          file={reviewTarget.file}
          onClose={() => setReviewTarget(null)}
          onApplied={() => {
            setReviewTarget(null);
            load();
          }}
        />
      )}
    </div>
  );
}
