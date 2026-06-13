"""Weighted accessibility scoring.

Approximates YuJa Panorama's weighted model (see domain-knowledge.md): more
severe issues lower the score more. Scoring is **per check**, not per element —
a check passes only if every one of its audit results passed.

    score = round(weighted_passes / total_weight * 100)
    severity weights: Severe 3, Major 2, Minor 1, Disabled 0
    Special rule: any remaining Severe violation caps the score at ``severe_cap``.

``placeholder_check_ids`` lets the caller compute the *truly-remediated* score:
checks satisfied only by a placeholder are forced to "failed" so they do not
inflate the honest number.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from remediator.config import ScoringConfig
from remediator.models import (
    SEVERITY_DISABLED,
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_SEVERE,
    AuditResult,
    ScoreBreakdown,
)


def _weights(cfg: ScoringConfig) -> dict[str, int]:
    return {
        SEVERITY_SEVERE: cfg.severe_weight,
        SEVERITY_MAJOR: cfg.major_weight,
        SEVERITY_MINOR: cfg.minor_weight,
        SEVERITY_DISABLED: 0,
    }


def compute_score(
    audit_results: Iterable[AuditResult],
    cfg: ScoringConfig,
    placeholder_check_ids: set[str] | None = None,
) -> ScoreBreakdown:
    """Compute a weighted 0-100 score from a list of audit results."""
    placeholder_check_ids = placeholder_check_ids or set()
    weights = _weights(cfg)

    # Group results by check; a check passes only if all its results passed.
    by_check: dict[str, list[AuditResult]] = defaultdict(list)
    for r in audit_results:
        by_check[r.check_id].append(r)

    total_weight = 0
    weighted_passes = 0
    severe_violation_remains = False

    for check_id, results in by_check.items():
        severity = results[0].severity
        weight = weights.get(severity, 0)
        if weight == 0:  # Disabled checks do not count toward the score
            continue

        passed = all(r.passed for r in results)
        if check_id in placeholder_check_ids:
            passed = False  # truly-remediated: placeholders are not real fixes

        total_weight += weight
        if passed:
            weighted_passes += weight
        elif severity == SEVERITY_SEVERE:
            severe_violation_remains = True

    if total_weight == 0:
        return ScoreBreakdown(score=100, total_weight=0, weighted_passes=0)

    score = round(weighted_passes / total_weight * 100)
    capped = False
    if severe_violation_remains and score > cfg.severe_cap:
        score = cfg.severe_cap
        capped = True

    return ScoreBreakdown(
        score=score,
        total_weight=total_weight,
        weighted_passes=weighted_passes,
        capped=capped,
    )
