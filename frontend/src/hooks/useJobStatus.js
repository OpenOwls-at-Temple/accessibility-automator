// Poll a remediation job until it finishes. Mirrors the backend's
// background-job + polling model (~2s interval; see architecture-planning.md).

import { useEffect, useRef, useState } from "react";
import { api } from "../services/api.js";

export function useJobStatus(jobId, onSettled) {
  const [status, setStatus] = useState(null);
  const onSettledRef = useRef(onSettled);
  onSettledRef.current = onSettled;

  useEffect(() => {
    if (!jobId) return undefined;
    let active = true;
    let timer;

    const tick = async () => {
      try {
        const next = await api.getJob(jobId);
        if (!active) return;
        setStatus(next);
        if (next.status === "done" || next.status === "error") {
          onSettledRef.current?.(next);
          return;
        }
      } catch {
        // transient error — keep polling
      }
      if (active) timer = setTimeout(tick, 2000);
    };

    timer = setTimeout(tick, 500);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [jobId]);

  return status;
}
