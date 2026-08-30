from __future__ import annotations

from .models import RunRecord


def classify(record: RunRecord) -> str:
    if record.error:
        text = record.error.lower()
        if "timeout" in text:
            return "timeout"
        if "max_steps" in text:
            return "max-steps"
        if "api" in text or "connection" in text or "rate" in text or "status" in text:
            return "api-error"
        return "runner-error"
    if not record.passed:
        reason = str(record.grader_details.get("reason", ""))
        if "missing" in reason or "does not exist" in reason:
            return "incomplete-artifact"
        if "syntaxerror" in reason or "assert" in reason or "failed" in reason:
            return "execution-misalignment"
        return "grader-fail"
    return "pass"
