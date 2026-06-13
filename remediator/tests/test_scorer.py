from remediator.config import ScoringConfig
from remediator.models import (
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_SEVERE,
    AuditResult,
)
from remediator.scorer import compute_score

CFG = ScoringConfig()


def _r(check_id, severity, passed):
    return AuditResult(check_id, severity, passed, "ref")


def test_all_pass_is_100():
    results = [_r("P1", SEVERITY_MAJOR, True), _r("P6", SEVERITY_MINOR, True)]
    assert compute_score(results, CFG).score == 100


def test_weighted_average():
    # P1 major (w=2) fails, P6 minor (w=1) passes -> 1/3 -> 33
    results = [_r("P1", SEVERITY_MAJOR, False), _r("P6", SEVERITY_MINOR, True)]
    assert compute_score(results, CFG).score == 33


def test_check_fails_if_any_element_fails():
    # Two P3 results; one fails -> the whole P3 check fails.
    results = [_r("P3", SEVERITY_MAJOR, True), _r("P3", SEVERITY_MAJOR, False)]
    breakdown = compute_score(results, CFG)
    assert breakdown.score == 0


def test_severe_violation_caps_score():
    results = [_r("P11", SEVERITY_SEVERE, False)] + [
        _r(f"M{i}", SEVERITY_MAJOR, True) for i in range(10)
    ]
    breakdown = compute_score(results, CFG)
    assert breakdown.capped is True
    assert breakdown.score == CFG.severe_cap


def test_disabled_checks_excluded():
    from remediator.models import SEVERITY_DISABLED

    results = [_r("P1", SEVERITY_MAJOR, True), _r("P13", SEVERITY_DISABLED, False)]
    # P13 is weight 0 -> excluded -> score stays 100.
    assert compute_score(results, CFG).score == 100


def test_placeholder_forces_failure():
    results = [_r("P2", SEVERITY_MAJOR, True), _r("P6", SEVERITY_MINOR, True)]
    # Treat P2 as placeholder -> 1/3 -> 33.
    assert compute_score(results, CFG, placeholder_check_ids={"P2"}).score == 33
