"""Black-box tests for checkpoint 2 scoring and reporting behaviour."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "implementation" / "sheeteval.py"


def make_workbooks(tmp_path: Path, rules, *, submission_values=None, manifest=None):
    """Create minimal answer-key/submission workbooks for a CLI invocation."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = manifest or ["Answers"]
    submission_values = submission_values or {}

    answer = openpyxl.Workbook()
    answer.remove(answer.active)
    manifest_sheet = answer.create_sheet("EvalManifest")
    manifest_sheet.append(["name"])
    for name in manifest:
        manifest_sheet.append([name])

    submission = openpyxl.Workbook()
    submission.remove(submission.active)
    for name in manifest:
        answer_sheet = answer.create_sheet(name)
        submission_sheet = submission.create_sheet(name)
        for cell_ref, value, annotation, *flags in rules.get(name, []):
            answer_sheet[cell_ref] = value
            if annotation is not None:
                answer_sheet[cell_ref].comment = openpyxl.comments.Comment(
                    annotation, "test"
                )
            submission_sheet[cell_ref] = submission_values.get(
                (name, cell_ref), value
            )

        checklist = answer.create_sheet(f"{name}_Checklist")
        checklist.append(["id", "flags"])
        for cell_ref, _value, _annotation, *flags in rules.get(name, []):
            checklist.append([cell_ref, flags[0] if flags else None])

    answer_path = tmp_path / "answer.xlsx"
    submission_path = tmp_path / "submission.xlsx"
    answer.save(answer_path)
    submission.save(submission_path)
    return answer_path, submission_path


def run_cli(answer_path, submission_path, *args):
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), str(answer_path), str(submission_path), *args],
        cwd=ENTRYPOINT.parent,
        text=True,
        capture_output=True,
    )


def annotation(*, points=1, tolerance=None, alternates=None, mode=None, kind="literal"):
    fields = [f"kind: {kind}", f"points: {points}"]
    if tolerance is not None:
        fields.append(f"tolerance: {tolerance}")
    if alternates is not None:
        fields.append("alternates: [" + ", ".join(alternates) + "]")
    if mode is not None:
        fields.append(f"mode: {mode}")
    return "rule:\n  " + "\n  ".join(fields)


def test_tolerance_is_inclusive_and_exact_matching_remains_default(tmp_path):
    rules = {
        "Answers": [
            ("A1", 10, annotation(points=1, tolerance=0.5)),
            ("A2", 10, annotation(points=1)),
        ]
    }
    answer, submission = make_workbooks(
        tmp_path,
        rules,
        submission_values={("Answers", "A1"): 10.5, ("Answers", "A2"): 10.1},
    )

    result = run_cli(answer, submission)

    assert result.returncode == 0
    assert result.stdout.strip() == "Assignment Score: 1 / 2"


@pytest.mark.parametrize("actual", [9.499999, 10.500001])
def test_tolerance_uses_absolute_difference_without_rounding(tmp_path, actual):
    rules = {"Answers": [("A1", 10, annotation(points=2, tolerance=0.5))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): actual}
    )

    result = run_cli(answer, submission)

    assert result.returncode == 0
    assert result.stdout.strip() == "Assignment Score: 0 / 2"


def test_tolerance_only_replaces_equality_when_both_values_are_numeric(tmp_path):
    rules = {"Answers": [("A1", "10", annotation(points=1, tolerance=1))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): "10.5"}
    )

    result = run_cli(answer, submission)

    assert result.stdout.strip() == "Assignment Score: 0 / 1"


def test_alternates_try_primary_then_listed_order_and_stop_after_first_match(tmp_path):
    rules = {
        "Answers": [
            ("A1", "primary", annotation(points=3, alternates=["not-a-cell", "B1"])),
            ("B1", "second", None),
        ]
    }
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): "second"}
    )
    # The first alternate is malformed; B1 is the later valid match.
    # Also verify a successful primary match prevents later alternate processing.
    result = run_cli(answer, submission)
    assert result.returncode == 0
    assert result.stdout.strip() == "Assignment Score: 3 / 3"
    assert "not-a-cell" in result.stderr

    primary_rules = {"Answers": [("A1", "primary", annotation(alternates=["not-a-cell"]))]}
    answer, submission = make_workbooks(
        tmp_path / "primary", primary_rules,
        submission_values={("Answers", "A1"): "primary"},
    )
    result = run_cli(answer, submission)
    assert result.stdout.strip() == "Assignment Score: 1 / 1"
    assert "not-a-cell" not in result.stderr


def test_malformed_alternate_warns_and_does_not_make_matching_rule_fail(tmp_path):
    rules = {"Answers": [("A1", "expected", annotation(alternates=["not-a-cell"]))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): "expected"}
    )

    result = run_cli(answer, submission)

    assert result.returncode == 0
    assert result.stdout.strip() == "Assignment Score: 1 / 1"
    # The primary value matches, so alternate processing is not entered.
    assert "not-a-cell" not in result.stderr


def test_alternate_uses_the_primary_rule_tolerance(tmp_path):
    rules = {
        "Answers": [
            ("A1", 0, annotation(points=2, tolerance=0.5, alternates=["B1"])),
            ("B1", 10, None),
        ]
    }
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): 10.5}
    )
    result = run_cli(answer, submission)
    assert result.stdout.strip() == "Assignment Score: 2 / 2"


@pytest.mark.parametrize(
    ("mode", "points", "actual", "expected_score", "expected_max"),
    [("penalty", 2, "wrong", "-2", "0"),
     ("penalty", 2, "right", "0", "0"),
     ("penalty", -2, "wrong", "-2", "0"),
     ("award", 2, "right", "2", "2")],
)
def test_penalty_sign_and_max_possible_semantics(
    tmp_path, mode, points, actual, expected_score, expected_max
):
    rules = {"Answers": [("A1", "right", annotation(points=points, mode=mode))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): actual}
    )
    result = run_cli(answer, submission)
    assert result.stdout.strip() == f"Assignment Score: {expected_score} / {expected_max}"


def test_invalid_mode_warns_and_defaults_to_award(tmp_path):
    rules = {"Answers": [("A1", "right", annotation(points=2, mode="mystery"))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): "wrong"}
    )
    result = run_cli(answer, submission)
    assert result.stdout.strip() == "Assignment Score: 0 / 2"
    assert "mystery" in result.stderr
    assert "award" in result.stderr.lower()


def test_negative_tolerance_is_ignored_with_warning(tmp_path):
    rules = {"Answers": [("A1", 10, annotation(points=1, tolerance=-1))]}
    answer, submission = make_workbooks(
        tmp_path, rules, submission_values={("Answers", "A1"): 10.1}
    )
    result = run_cli(answer, submission)
    assert result.stdout.strip() == "Assignment Score: 0 / 1"
    assert "negative" in result.stderr.lower()
    assert "tolerance" in result.stderr.lower()


def test_report_has_manifest_sheet_order_checklist_order_and_numeric_formatting(tmp_path):
    rules = {
        "Second": [("B2", 1, annotation(points=2.75)), ("A1", 2, annotation(points=1, mode="penalty"))],
        "First": [("C3", 4, annotation(points=2)), ("D4", 5, annotation(points=3), "manual"),
                  ("E5", 6, annotation(points=4, kind="unknown"))],
    }
    answer, submission = make_workbooks(
        tmp_path, rules, manifest=["Second", "First"],
        submission_values={("Second", "A1"): 0, ("First", "C3"): 0},
    )
    report = tmp_path / "report.txt"
    result = run_cli(answer, submission, "--report-file", str(report))

    assert result.returncode == 0
    assert report.read_text(encoding="utf-8") == (
        "Sheet 'Second':\n"
        "  [CORRECT] B2 B2: 2.75 / 2.75\n"
        "  [INCORRECT] A1 A1: -1 / 1\n"
        "Sheet 'Second': 1.75 / 2.75\n"
        "\n"
        "Sheet 'First':\n"
        "  [INCORRECT] C3 C3: 0 / 2\n"
        "Sheet 'First': 0 / 2\n"
        "\n"
        "Total: 1.75 / 4.75\n"
    )


def test_detailed_stdout_is_report_content_then_final_assignment_summary(tmp_path):
    rules = {"Answers": [("A1", 1, annotation(points=1)), ("B2", 2, annotation(points=2))]}
    answer, submission = make_workbooks(tmp_path, rules)
    report = tmp_path / "report.txt"
    score_file = tmp_path / "score"
    result = run_cli(
        answer, submission, "--detailed", "--report-file", str(report),
        "--score-file", str(score_file)
    )
    assert result.returncode == 0
    report_lines = report.read_text(encoding="utf-8").splitlines()
    assert result.stdout.splitlines() == report_lines + ["Assignment Score: 3 / 3"]
    assert score_file.read_text(encoding="utf-8") == "3\n"


def test_report_file_write_failure_is_cli_error(tmp_path):
    rules = {"Answers": [("A1", 1, annotation())]}
    answer, submission = make_workbooks(tmp_path, rules)
    result = run_cli(answer, submission, "--report-file", str(tmp_path / "missing" / "report.txt"))
    assert result.returncode == 1
    assert result.stdout == ""
    assert "error" in result.stderr.lower()
