from remediator.config import load_config
from remediator.handlers.pdf_handler import PdfHandler, get_language, get_title
from remediator.models import ACTION_NOT_FIXED
from remediator.pipeline import remediate_file
from remediator.rules.pdf_rules import audit_pdf


def _check_passed(results, check_id):
    matching = [r for r in results if r.check_id == check_id]
    return bool(matching) and all(r.passed for r in matching)


def test_metadata_fixes_applied_and_score_improves(bad_pdf, tmp_path):
    out = tmp_path / "bad_a11y.pdf"
    report = remediate_file(bad_pdf, out, cfg=load_config(), provider=None)

    assert report.post_fix_score > report.pre_fix_score
    post = audit_pdf(PdfHandler(out))
    assert _check_passed(post, "D2")  # title now set
    assert _check_passed(post, "D12")  # language now set

    # The title/language are actually written into the output file.
    pdf = PdfHandler(out).pdf
    assert get_title(pdf)
    assert get_language(pdf) == "en-US"


def test_untagged_structure_is_reported_not_faked(bad_pdf, tmp_path):
    out = tmp_path / "bad_a11y.pdf"
    report = remediate_file(bad_pdf, out, cfg=load_config(), provider=None)

    d1 = [f for f in report.fixes if f.check_id == "D1"]
    assert d1 and d1[0].action == ACTION_NOT_FIXED  # honest: not silently "fixed"
    # Untagged structure remains a failure after remediation.
    assert not _check_passed(audit_pdf(PdfHandler(out)), "D1")


def test_scanned_pdf_capped_low_after_fix(image_pdf, tmp_path):
    out = tmp_path / "scanned_a11y.pdf"
    report = remediate_file(image_pdf, out, cfg=load_config(), provider=None)
    # A remaining Severe issue (D8) caps the score even after metadata fixes.
    assert report.post_fix.capped is True
    assert report.post_fix_score <= load_config().scoring.severe_cap


def test_encrypted_pdf_copied_through_and_reported(encrypted_pdf, tmp_path):
    out = tmp_path / "enc_a11y.pdf"
    report = remediate_file(encrypted_pdf, out, cfg=load_config(), provider=None)

    assert out.exists()  # original copied through, never lost
    assert report.post_fix_score <= load_config().scoring.severe_cap
    d10 = [f for f in report.fixes if f.check_id == "D10"]
    assert d10 and d10[0].action == ACTION_NOT_FIXED


def test_original_pdf_is_never_modified(bad_pdf, tmp_path):
    out = tmp_path / "bad_a11y.pdf"
    remediate_file(bad_pdf, out, cfg=load_config(), provider=None)
    # Input still has no title after remediation.
    assert not get_title(PdfHandler(bad_pdf).pdf)
