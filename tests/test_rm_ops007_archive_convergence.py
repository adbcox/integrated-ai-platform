from framework.rm_ops007_archive_convergence import evidence_allows_archive


def test_evidence_allows_archive_on_passed_validation():
    ok, reason = evidence_allows_archive(
        {
            "validation": {"validation_status": "passed"},
            "execution": {"execution_status": "complete"},
        }
    )
    assert ok is True
    assert reason == "evidence_sufficient"


def test_evidence_blocks_archive_when_execution_not_started():
    ok, reason = evidence_allows_archive(
        {
            "validation": {"validation_status": "passed"},
            "execution": {"execution_status": "not_started"},
        }
    )
    assert ok is False
    assert reason == "execution_status=not_started"


def test_evidence_blocks_archive_without_any_readiness_signal():
    ok, reason = evidence_allows_archive(
        {
            "validation": {"validation_status": "not_started"},
            "execution": {"execution_status": "complete"},
            "archive_readiness": {"ready": False},
        }
    )
    assert ok is False
    assert reason == "insufficient_validation_or_readiness_evidence"
