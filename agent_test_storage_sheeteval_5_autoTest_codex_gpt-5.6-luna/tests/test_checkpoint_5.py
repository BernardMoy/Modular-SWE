"""Black-box tests for checkpoint 5's additional rule kinds.

The tests invoke the documented command-line entry point in a subprocess.  The
workbooks are generated in pytest's temporary directory so no repository data
or fixed filesystem paths are required.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import openpyxl
import pytest


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = Path(
    os.environ.get("SHEETEVAL_IMPLEMENTATION", ROOT / "previous_implementation")
)


def annotation(rule: str) -> str:
    normalized = "\n".join(line.strip() for line in rule.strip().splitlines())
    return "rule:\n" + textwrap.indent(normalized, "  ")


def make_workbooks(tmp_path: Path, rows, *, cells=None, min_score=None, threshold_message=None):
    """Create an answer key and submission containing one evaluated sheet."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    cells = cells or {}
    answer = openpyxl.Workbook()
    answer.active.title = "EvalManifest"
    manifest = answer["EvalManifest"]
    manifest.append(["name", "min-score", "threshold-message"])
    manifest.append(["Sheet1", min_score, threshold_message])
    sheet = answer.create_sheet("Sheet1")
    checklist = answer.create_sheet("Sheet1_Checklist")
    checklist.append(["cell-id", "flags"])
    for cell_id, flags in rows:
        checklist.append([cell_id, flags])
    for cell_id, spec in cells.items():
        value = spec.get("answer")
        sheet[cell_id] = value
        if "annotation" in spec:
            sheet[cell_id].comment = openpyxl.comments.Comment(spec["annotation"], "test")

    submission = openpyxl.Workbook()
    submission.active.title = "Sheet1"
    sub_sheet = submission["Sheet1"]
    for cell_id, spec in cells.items():
        if "submission" in spec:
            sub_sheet[cell_id] = spec["submission"]

    answer_path = tmp_path / "answer.xlsx"
    submission_path = tmp_path / "submission.xlsx"
    answer.save(answer_path)
    submission.save(submission_path)
    return answer_path, submission_path


def run_cli(answer_path, submission_path, *args):
    result = subprocess.run(
        [sys.executable, str(IMPLEMENTATION / "sheeteval.py"), str(answer_path), str(submission_path), *args],
        cwd=IMPLEMENTATION,
        text=True,
        capture_output=True,
    )
    return result


def grade(tmp_path, rule, *, answer="", submission=None, cell="C1", flags=None, cells=None, **kwargs):
    cells = cells or {cell: {"answer": answer, "submission": submission, "annotation": annotation(rule)}}
    if cell not in cells:
        cells[cell] = {"answer": answer, "submission": submission, "annotation": annotation(rule)}
    else:
        cells[cell].setdefault("annotation", annotation(rule))
    answer_path, submission_path = make_workbooks(
        tmp_path,
        [(cell, flags)],
        cells=cells,
        **kwargs,
    )
    return run_cli(answer_path, submission_path, "--detailed")


def assert_total(result, text):
    assert result.returncode == 0, result.stderr
    assert f"Total: {text}" in result.stdout


def test_boolean_accepts_only_the_explicit_truthy_values(tmp_path):
    cases = [(True, True), (2, True), (-1.5, True), ("TRUE", True), ("yes", True),
             ("Yes", True), (False, False), (0, False), ("true ", False), ("1", False),
             ("y", False), (None, False)]
    for index, (value, expected) in enumerate(cases):
        result = grade(tmp_path / str(index), "kind: boolean\n  points: 2", answer=value, submission=value)
        assert_total(result, "2 / 2" if expected else "0 / 2")
        assert "Warning:" not in result.stderr


def test_reference_uses_submission_values_to_evaluate_answer_formula(tmp_path):
    result = grade(
        tmp_path,
        "kind: reference\n  points: 3",
        answer="=A1+B1",
        submission=7,
        cells={"C1": {"answer": "=A1+B1", "submission": 7}, "A1": {"answer": 2, "submission": 3}, "B1": {"answer": 5, "submission": 4}},
    )
    assert_total(result, "3 / 3")


def test_reference_uses_submitted_formula_result_and_alternates_in_order(tmp_path):
    rule = "kind: reference\n  points: 1\n  alternates: [D1, E1]"
    cells = {
        "C1": {"answer": "=A1+B1", "submission": "=A1*B1"},
        "D1": {"answer": "=A1*B1"},
        "E1": {"answer": "=A1-B1"},
        "A1": {"answer": 2, "submission": 3},
        "B1": {"answer": 5, "submission": 4},
    }
    cells["C1"]["annotation"] = annotation(rule)
    answer_path, submission_path = make_workbooks(tmp_path, [("C1", None)], cells=cells)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "1 / 1")


def test_reference_expr_requires_a_submission_formula(tmp_path):
    result = grade(tmp_path, "kind: reference_expr\n  points: 2", answer="=A1+B1", submission=7)
    assert_total(result, "0 / 2")
    assert result.stderr == ""


def test_reference_expr_compares_evaluated_submission_formula(tmp_path):
    cells = {"C1": {"answer": "=A1+B1", "submission": "=A1*B1"}, "A1": {"answer": 2, "submission": 3}, "B1": {"answer": 5, "submission": 4}}
    cells["C1"]["annotation"] = annotation("kind: reference_expr\npoints: 1")
    answer_path, submission_path = make_workbooks(tmp_path, [("C1", None)], cells=cells)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "1 / 1")


@pytest.mark.parametrize("kind", ["reference", "reference_expr"])
def test_formula_rule_without_answer_formula_warns_and_scores_zero(tmp_path, kind):
    result = grade(tmp_path, f"kind: {kind}\n  points: 2", answer=7, submission=7)
    assert_total(result, "0 / 2")
    assert "answer key has no formula" in result.stderr


@pytest.mark.parametrize("formula", ["=UNSUPPORTED(A1)", "=A1+A1"])
def test_reference_formula_evaluation_errors_warn_and_score_zero(tmp_path, formula):
    if formula == "=A1+A1":
        cells = {"C1": {"answer": formula, "submission": 1}, "A1": {"answer": "=C1", "submission": "=C1"}}
    else:
        cells = {"C1": {"answer": formula, "submission": 1}, "A1": {"answer": 2, "submission": 2}}
    cells["C1"]["annotation"] = annotation("kind: reference\npoints: 2")
    answer_path, submission_path = make_workbooks(tmp_path, [("C1", None)], cells=cells)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "0 / 2")
    assert "Warning:" in result.stderr


def test_result_compares_designated_target_and_applies_numeric_tolerance(tmp_path):
    rule = "kind: result\n  points: 4\n  target: D10\n  tolerance: 0.1"
    # Put the expected value at the target cell, not at the graded cell.
    # Recreate with an explicit target in the workbook.
    answer_path, submission_path = make_workbooks(
        tmp_path / "target", [("C1", None)],
        cells={"C1": {"answer": 0, "submission": 10.09}, "D10": {"answer": 10}},
    )
    # Add the annotation after construction to keep the helper's cell map simple.
    book = openpyxl.load_workbook(answer_path)
    book["Sheet1"]["C1"].comment = openpyxl.comments.Comment(annotation(rule), "test")
    book.save(answer_path)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "4 / 4")


def test_result_alternate_target_and_non_numeric_exact_equality(tmp_path):
    rule = "kind: result\n  points: 2\n  target: D1\n  alternates: [E1]"
    answer_path, submission_path = make_workbooks(
        tmp_path, [("C1", None)],
        cells={"C1": {"answer": "wrong", "submission": "approved"}, "D1": {"answer": "nope"}, "E1": {"answer": "approved"}},
    )
    book = openpyxl.load_workbook(answer_path)
    book["Sheet1"]["C1"].comment = openpyxl.comments.Comment(annotation(rule), "test")
    book.save(answer_path)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "2 / 2")


def test_result_without_target_is_warned_and_excluded_from_maximum(tmp_path):
    result = grade(tmp_path, "kind: result\n  points: 5", answer=1, submission=1)
    assert_total(result, "0 / 0")
    assert "target" in result.stderr.lower()


def test_result_missing_target_warns_and_scores_zero(tmp_path):
    rule = "kind: result\n  points: 5\n  target: Z99"
    answer_path, submission_path = make_workbooks(tmp_path, [("C1", None)], cells={"C1": {"answer": 1, "submission": 1}})
    book = openpyxl.load_workbook(answer_path)
    book["Sheet1"]["C1"].comment = openpyxl.comments.Comment(annotation(rule), "test")
    book.save(answer_path)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "0 / 5")
    assert "Z99" in result.stderr


def test_invalid_alternate_coordinate_warns_but_primary_result_can_pass(tmp_path):
    rule = "kind: result\n  points: 2\n  target: D1\n  alternates: [not-a-cell]"
    answer_path, submission_path = make_workbooks(
        tmp_path, [("C1", None)],
        cells={"C1": {"answer": 0, "submission": 8}, "D1": {"answer": 8}},
    )
    book = openpyxl.load_workbook(answer_path)
    book["Sheet1"]["C1"].comment = openpyxl.comments.Comment(annotation(rule), "test")
    book.save(answer_path)
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "2 / 2")
    assert "not-a-cell" in result.stderr.lower()


def test_penalty_and_concealed_fatal_rules_have_public_report_semantics(tmp_path):
    cells = {
        "A1": {"answer": True, "submission": False},
        "B1": {"answer": 2, "submission": 9},
        "C1": {"answer": True, "submission": True},
    }
    rules = {
        "A1": "kind: boolean\npoints: 3\nmode: penalty",
        "B1": "kind: result\npoints: 4\ntarget: B1",
        "C1": "kind: boolean\npoints: 5",
    }
    answer_path, submission_path = make_workbooks(
        tmp_path,
        [("A1", None), ("B1", "F"), ("C1", "C")],
        cells={cell: {**spec, "annotation": annotation(rules[cell])} for cell, spec in cells.items()},
    )
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "-3 / 5")
    assert "[INCORRECT] B1 B1: 0 / 4" in result.stdout
    assert "[SKIPPED] C1 [concealed]: 0 / 5" in result.stdout


def test_new_kinds_obey_penalty_tolerance_dependency_fatal_concealed_and_threshold(tmp_path):
    cells = {
        "A1": {"answer": 1, "submission": 0},
        "B1": {"answer": "=A1+1", "submission": 0},
        "C1": {"answer": 3, "submission": 4},
        "D1": {"answer": True, "submission": False},
    }
    rules = {
        "A1": "kind: boolean\n  points: 2\n  mode: penalty",
        "B1": "kind: reference\n  points: 2\n  depends: [A1]",
        "C1": "kind: result\n  points: 3\n  target: C1",
        "D1": "kind: boolean\n  points: 4",
    }
    answer_path, submission_path = make_workbooks(
        tmp_path, [(cell, "F" if cell == "C1" else ("C" if cell == "D1" else None)) for cell in rules],
        cells={cell: {**spec, "annotation": annotation(rules[cell])} for cell, spec in cells.items()},
        min_score=10, threshold_message="Not enough",
    )
    result = run_cli(answer_path, submission_path, "--detailed")
    assert_total(result, "0 / 9")
    assert "Not enough" in result.stdout
    assert "[concealed]" not in result.stdout  # threshold suppresses event details
