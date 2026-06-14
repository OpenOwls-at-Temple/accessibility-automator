import { useState } from "react";
import { api } from "../services/api.js";

// Upload files under a group name (usually a course code). Phase 1: PPTX/PDF.
export default function UploadModal({ onClose, onUploaded, initialGroup = "" }) {
  const [group, setGroup] = useState(initialGroup);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!group.trim() || files.length === 0) {
      setError("Enter a group name and choose at least one file.");
      return;
    }
    setBusy(true);
    try {
      await api.uploadFiles(group.trim(), files);
      onUploaded(group.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Upload files</h3>
        <form onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="group">Group (course code)</label>
            <input
              id="group"
              placeholder="e.g. CIS4526"
              value={group}
              onChange={(e) => setGroup(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="files">Files (.pptx, .pdf)</label>
            <input
              id="files"
              type="file"
              multiple
              accept=".pptx,.pdf"
              onChange={(e) => setFiles(Array.from(e.target.files))}
            />
          </div>
          {error && <p className="error">{error}</p>}
          <div className="row spread" style={{ marginTop: 8 }}>
            <button type="button" className="secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" disabled={busy}>
              {busy ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
