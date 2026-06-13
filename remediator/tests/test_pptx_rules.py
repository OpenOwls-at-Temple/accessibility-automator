from remediator.config import ScoringConfig
from remediator.handlers.pptx_handler import PptxHandler
from remediator.rules.pptx_rules import audit_pptx
from remediator.scorer import compute_score


def _check_passed(results, check_id):
    matching = [r for r in results if r.check_id == check_id]
    return bool(matching) and all(r.passed for r in matching)


def _present(results, check_id):
    return any(r.check_id == check_id for r in results)


def test_bad_deck_fails_expected_checks(bad_pptx):
    results = audit_pptx(PptxHandler(bad_pptx))
    assert not _check_passed(results, "P1")  # no document title
    assert not _check_passed(results, "P2")  # untitled slide
    assert not _check_passed(results, "P3")  # image without alt text
    assert not _check_passed(results, "P5")  # table without header row
    assert not _check_passed(results, "P6")  # no language set


def test_good_deck_passes_present_checks(good_pptx):
    results = audit_pptx(PptxHandler(good_pptx))
    assert _check_passed(results, "P1")
    assert _check_passed(results, "P2")
    assert _check_passed(results, "P3")
    assert _check_passed(results, "P5")
    assert _check_passed(results, "P6")


def test_good_deck_scores_100(good_pptx):
    results = audit_pptx(PptxHandler(good_pptx))
    assert compute_score(results, ScoringConfig()).score == 100


def test_integrity_checks_present_and_pass(good_pptx):
    results = audit_pptx(PptxHandler(good_pptx))
    assert _check_passed(results, "P11")  # well-formed
    assert _check_passed(results, "P12")  # not encrypted
    assert _check_passed(results, "P13")  # modern .pptx


def test_bad_deck_scores_below_good(bad_pptx, good_pptx):
    bad = compute_score(audit_pptx(PptxHandler(bad_pptx)), ScoringConfig()).score
    good = compute_score(audit_pptx(PptxHandler(good_pptx)), ScoringConfig()).score
    assert bad < good == 100
