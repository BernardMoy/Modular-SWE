"""Black-box tests for checkpoint 4's grading controls.

The fixtures are generated as temporary workbooks and the public CLI is invoked
in a subprocess.  No implementation modules or private names are imported.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import openpyxl
import pytest
from openpyxl.comments import Comment


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = Path(os.environ.get("SHEETEVAL_IMPLEMENTATION", ROOT / "previous_implementation"))


def _rule(kind="literal", points=1, *, mode=None, depends=None):
    lines = ["rule:", f"  kind: {kind}", f"  points: {points}"]
    if mode is not None:
        lines.append(f"  mode: {mode}")
    if depends is not None:
        lines.append("  depends:")
        lines.extend(f"    - {cell}" for cell in depends)
    return "\n".join(lines)


def make_workbooks(tmp_path, rows, *, min_score=None, threshold_message=None):
    """Create an answer key and submission from (cell, value, annotation, flags)."""
    answer = openpyxl.Workbook()
    manifest = answer.active
    manifest.title = "EvalManifest"
    headers = ["name"]
    if min_score is not None or threshold_message is not None:
        headers += ["min-score", "threshold-message"]
    manifest.append(headers)
    manifest.append(["Quiz"] + ([min_score, threshold_message] if len(headers) > 1 else []))
    sheet = answer.create_sheet("Quiz")
    checklist = answer.create_sheet("Quiz_Checklist")
    checklist.append(["cell-id", "flags"])
    submission = openpyxl.Workbook()
    submission.remove(submission.active)
    submission.create_sheet("EvalManifest")
    sub_sheet = submission.create_sheet("Quiz")

    for cell, expected, annotation, flags, actual in rows:
        sheet[cell] = expected
        if annotation is not None:
            sheet[cell].comment = Comment(annotation, "test")
        checklist.append([cell, flags])
        sub_sheet[cell] = actual

    answer_path = tmp_path / "answer.xlsx"
    submission_path = tmp_path / "submission.xlsx"
    answer.save(answer_path)
    submission.save(submission_path)
    return answer_path, submission_path


def run_cli(answer, submission, *args):
    return subprocess.run(
        [sys.executable, str(IMPLEMENTATION / "sheeteval.py"), str(answer), str(submission), *args],
        cwd=IMPLEMENTATION,
        text=True,
        capture_output=True,
    )


def test_prerequisite_failure_is_gated_and_keeps_possible_points(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "expected", _rule(points=2), "", "wrong"),
        ("B1", "expected", _rule(points=3, depends=["A1"]), "", "expected"),
    ])
    result = run_cli(answer, submission, "--detailed", "--log")
    assert result.returncode == 0
    assert "[INCORRECT] A1 A1: 0 / 2" in result.stdout
    assert "[PREREQ] B1 B1: 0 / 3 (requires A1)" in result.stdout
    assert "LOG Quiz.B1: literal PREREQ" in result.stderr
    assert "Total: 0 / 5" in result.stdout


def test_dependency_requires_an_earlier_correct_rule(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "expected", _rule(points=1), "", "expected"),
        ("B1", "expected", _rule(points=2, depends=["C1"]), "", "expected"),
        ("C1", "expected", _rule(points=4), "", "expected"),
    ])
    result = run_cli(answer, submission, "--detailed")
    assert "[PREREQ] B1 B1: 0 / 2 (requires C1)" in result.stdout
    assert "[CORRECT] C1 C1: 4 / 4" in result.stdout


def test_dependency_on_penalty_pass_satisfies_but_failure_does_not(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=3, mode="penalty"), "", "no"),
        ("B1", "yes", _rule(points=2, depends=["A1"]), "", "yes"),
    ])
    failed = run_cli(answer, submission, "--detailed")
    assert "[INCORRECT] A1 A1: -3 / 0" in failed.stdout
    assert "[PREREQ] B1 B1: 0 / 2 (requires A1)" in failed.stdout
    assert "Total: -3 / 2" in failed.stdout

    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=3, mode="penalty"), "", "yes"),
        ("B1", "yes", _rule(points=2, depends=["A1"]), "", "yes"),
    ])
    passed = run_cli(answer, submission, "--detailed")
    assert "[CORRECT] A1 A1: 0 / 0" in passed.stdout
    assert "[CORRECT] B1 B1: 2 / 2" in passed.stdout


def test_fatal_incorrect_skips_remaining_rules_and_preserves_possible_totals(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "F", "no"),
        ("B1", "yes", _rule(points=3, mode="penalty"), "", "no"),
        ("C1", "yes", _rule(points=4), "", "yes"),
    ])
    result = run_cli(answer, submission, "--detailed", "--log")
    assert "[INCORRECT] A1 A1: 0 / 2" in result.stdout
    assert "[SKIPPED] B1 B1: 0 / 3" in result.stdout
    assert "[SKIPPED] C1 C1: 0 / 4" in result.stdout
    assert "LOG Quiz.B1: literal SKIPPED" in result.stderr
    assert "Total: 0 / 9" in result.stdout


@pytest.mark.parametrize("flags", ["C", "c"])
def test_concealed_rule_hides_cell_case_insensitively(tmp_path, flags):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), flags, "yes"),
        ("B1", "yes", _rule(points=3, depends=["A1"]), "F", "no"),
        ("C1", "yes", _rule(points=4), "", "yes"),
    ])
    result = run_cli(answer, submission, "--detailed")
    assert "[CORRECT] A1 [concealed]: 2 / 2" in result.stdout


def test_combined_fatal_concealed_and_flag_warning(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "fCxZ", "no"),
        ("B1", "yes", _rule(points=1), "", "yes"),
    ])
    result = run_cli(answer, submission, "--detailed")
    assert "[INCORRECT] A1 [concealed]: 0 / 2" in result.stdout
    assert "[SKIPPED] B1 B1: 0 / 1" in result.stdout
    assert "unrecognized" in result.stderr.lower()


def test_concealed_prerequisite_and_concealed_fatal_skip_use_hidden_references(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "F", "no"),
        ("B1", "yes", _rule(points=3, depends=["A1"]), "C", "yes"),
        ("C1", "yes", _rule(points=4), "FC", "yes"),
    ])
    result = run_cli(answer, submission, "--detailed")
    # B1 is gated (and therefore not evaluated); C1 is skipped by A1's fatal halt.
    assert "[PREREQ] B1 [concealed]: 0 / 3 (requires A1)" in result.stdout
    assert "[SKIPPED] C1 [concealed]: 0 / 4" in result.stdout


def test_threshold_replaces_details_and_zeroes_post_threshold_score(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "", "yes"),
        ("B1", "yes", _rule(points=3), "", "no"),
    ], min_score=3, threshold_message="Pass at least three points")
    result = run_cli(answer, submission, "--detailed", "--score-file", str(tmp_path / "score.txt"))
    assert "Sheet 'Quiz':\n  Pass at least three points\nSheet 'Quiz': 0 / 5" in result.stdout
    assert "A1 A1" not in result.stdout
    assert "Assignment Score: 0 / 5" in result.stdout
    assert (tmp_path / "score.txt").read_text() == "0\n"
    report = tmp_path / "report.txt"
    rerun = run_cli(answer, submission, "--detailed", "--report-file", str(report))
    assert rerun.returncode == 0
    assert "Pass at least three points" in report.read_text()
    assert "[CORRECT] A1" not in report.read_text()


def test_threshold_that_is_met_keeps_rule_lines_and_post_threshold_totals(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "", "yes"),
        ("B1", "yes", _rule(points=3), "", "no"),
    ], min_score=2, threshold_message="Must not appear")
    result = run_cli(answer, submission, "--detailed")
    assert "[CORRECT] A1 A1: 2 / 2" in result.stdout
    assert "Must not appear" not in result.stdout
    assert "Assignment Score: 2 / 5" in result.stdout


def test_threshold_message_defaults_and_blank_min_score_disables_threshold(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "", "yes"),
    ], min_score=3, threshold_message="")
    result = run_cli(answer, submission, "--detailed")
    assert "  Minimum score not met." in result.stdout

    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "", "yes"),
    ], min_score="", threshold_message="Should not appear")
    result = run_cli(answer, submission, "--detailed")
    assert "[CORRECT] A1 A1: 2 / 2" in result.stdout
    assert "Should not appear" not in result.stdout


def test_threshold_ignores_manual_rules_and_includes_penalty_failures(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=2), "", "yes"),
        ("B1", "yes", _rule(points=100), "M", "no"),
    ], min_score=3, threshold_message="Not enough")
    result = run_cli(answer, submission, "--detailed")
    assert "Not enough" in result.stdout

    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=5, mode="penalty"), "", "no"),
        ("B1", "yes", _rule(points=1), "", "yes"),
    ], min_score=-5, threshold_message="Should not trigger")
    result = run_cli(answer, submission, "--detailed")
    assert "[INCORRECT] A1 A1: -5 / 0" in result.stdout
    assert "[CORRECT] B1 B1: 1 / 1" in result.stdout
    assert "Should not trigger" not in result.stdout


def test_invalid_min_score_and_cross_sheet_dependency_warn_and_continue(tmp_path):
    answer, submission = make_workbooks(tmp_path, [
        ("A1", "yes", _rule(points=1, depends=["Other!A1"]), "", "yes"),
    ], min_score="not-a-number", threshold_message="No")
    result = run_cli(answer, submission, "--detailed")
    assert result.returncode == 0
    assert "[PREREQ] A1 A1: 0 / 1 (requires Other!A1)" in result.stdout
    assert "warning" in result.stderr.lower()
    assert "numeric" in result.stderr.lower() or "current sheet" in result.stderr.lower()
