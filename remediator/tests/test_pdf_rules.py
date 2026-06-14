from remediator.handlers.pdf_handler import PdfHandler
from remediator.rules.pdf_rules import audit_pdf


def _check_passed(results, check_id):
    matching = [r for r in results if r.check_id == check_id]
    return bool(matching) and all(r.passed for r in matching)


def _present(results, check_id):
    return any(r.check_id == check_id for r in results)


def test_untagged_pdf_fails_structure_title_language(bad_pdf):
    results = audit_pdf(PdfHandler(bad_pdf))
    assert not _check_passed(results, "D1")  # untagged
    assert not _check_passed(results, "D2")  # no title
    assert not _check_passed(results, "D12")  # no language
    assert _check_passed(results, "D9")  # well-formed
    assert _check_passed(results, "D10")  # not encrypted


def test_image_only_pdf_flags_scanned_and_alt(image_pdf):
    results = audit_pdf(PdfHandler(image_pdf))
    assert not _check_passed(results, "D8")  # scanned / image-only
    assert not _check_passed(results, "D3")  # image with no alt text


def test_text_pdf_is_not_flagged_scanned(bad_pdf):
    results = audit_pdf(PdfHandler(bad_pdf))
    assert not _present(results, "D8")  # has a text layer


def test_encrypted_pdf_detected_and_short_circuits(encrypted_pdf):
    handler = PdfHandler(encrypted_pdf)
    assert handler.encrypted is True
    results = audit_pdf(handler)
    assert not _check_passed(results, "D10")  # encrypted
    # Nothing else is knowable on an encrypted file.
    assert {r.check_id for r in results} == {"D10"}
