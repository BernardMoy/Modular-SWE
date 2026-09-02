"""Black-box tests for checkpoint 3's recipe CLI options.

The SDE used here is deliberately tiny and is generated in a temporary
directory.  The tests invoke the public entrypoint in a subprocess; they do
not import planner or renderer implementation details.
"""

from __future__ import annotations

import bz2
import csv
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT = Path(__file__).resolve().parents[1]
ENTRYPOINT = next(
    (PROJECT / directory / "industry.py"
     for directory in ("implementation", "previous_implementation")
     if (PROJECT / directory / "industry.py").is_file()),
    PROJECT / "previous_implementation" / "industry.py",
)


def _write_bz2_csv(root: Path, name: str, fields: list[str], rows: list[dict]):
    with bz2.open(root / name, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture()
def sde(tmp_path: Path) -> Path:
    """A manufacturing recipe and a reaction recipe with distinguishable data."""
    _write_bz2_csv(
        tmp_path,
        "invTypes.csv.bz2",
        ["typeID", "typeName", "groupID", "marketGroupID", "volume", "published"],
        [
            {"typeID": 100, "typeName": "Test Widget", "groupID": 10, "marketGroupID": "", "volume": 1, "published": 1},
            {"typeID": 200, "typeName": "Test Material", "groupID": 20, "marketGroupID": "", "volume": 1, "published": 0},
            {"typeID": 201, "typeName": "Single Unit Material", "groupID": 20, "marketGroupID": "", "volume": 1, "published": 0},
            {"typeID": 400, "typeName": "Test Reaction Product", "groupID": 10, "marketGroupID": "", "volume": 1, "published": 1},
        ],
    )
    _write_bz2_csv(tmp_path, "invGroups.csv.bz2", ["groupID", "groupName", "categoryID"], [
        {"groupID": 10, "groupName": "Products", "categoryID": 6},
        {"groupID": 20, "groupName": "Materials", "categoryID": 4},
    ])
    _write_bz2_csv(tmp_path, "invCategories.csv.bz2", ["categoryID", "categoryName"], [
        {"categoryID": 6, "categoryName": "Manufacture"},
        {"categoryID": 4, "categoryName": "Commodity"},
    ])
    _write_bz2_csv(tmp_path, "invMarketGroups.csv.bz2", ["marketGroupID", "marketGroupName", "parentGroupID"], [])
    _write_bz2_csv(tmp_path, "industryActivity.csv.bz2", ["typeID", "activityID", "time"], [
        # SDE activity time is in seconds; 15,000 seconds renders as 250
        # minutes in the existing CLI output and keeps the example readable.
        {"typeID": 100, "activityID": 1, "time": 15000},
        {"typeID": 400, "activityID": 9, "time": 15000},
    ])
    _write_bz2_csv(tmp_path, "industryActivityProducts.csv.bz2", ["typeID", "productTypeID", "activityID", "quantity"], [
        {"typeID": 100, "productTypeID": 100, "activityID": 1, "quantity": 1},
        {"typeID": 400, "productTypeID": 400, "activityID": 9, "quantity": 1},
    ])
    _write_bz2_csv(tmp_path, "industryActivityMaterials.csv.bz2", ["typeID", "materialTypeID", "activityID", "quantity"], [
        {"typeID": 100, "materialTypeID": 200, "activityID": 1, "quantity": 100},
        {"typeID": 100, "materialTypeID": 201, "activityID": 1, "quantity": 1},
        {"typeID": 400, "materialTypeID": 200, "activityID": 9, "quantity": 100},
    ])
    _write_bz2_csv(tmp_path, "invMetaTypes.csv.bz2", ["typeID", "metaGroupID"], [])
    _write_bz2_csv(tmp_path, "invMetaGroups.csv.bz2", ["metaGroupID", "metaGroupName"], [])
    _write_bz2_csv(tmp_path, "industryActivitySkills.csv.bz2", ["typeID", "activityID", "skillID"], [])
    _write_bz2_csv(tmp_path, "industryActivityProbabilities.csv.bz2", ["typeID", "activityID", "probability"], [])
    (tmp_path / "ship_volumes.yaml").write_text("{}\n", encoding="utf-8")
    return tmp_path


def run_recipe(sde: Path, target: str, *options: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), "recipe", target, "--sde", str(sde), *options],
        cwd=ENTRYPOINT.parent,
        text=True,
        capture_output=True,
    )


def quantities(output: str) -> dict[str, int]:
    result = {}
    for line in output.splitlines():
        if line.startswith("| ") and line.count("|") >= 4 and "Item" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[1].lstrip("-").isdigit():
                result[cells[0]] = int(cells[1])
    return result


def test_defaults_preserve_materials_and_do_not_add_waste_column(sde: Path):
    completed = run_recipe(sde, "Test Widget")

    assert completed.returncode == 0, completed.stderr
    assert quantities(completed.stdout) == {"Test Material": 100, "Single Unit Material": 1}
    assert "| Item | Quantity | Buildable |" in completed.stdout
    assert "Run Time: 250" in completed.stdout


def test_material_efficiency_applies_ceiling_and_waste_is_opt_in(sde: Path):
    completed = run_recipe(sde, "Test Widget", "-me", "5", "--display-waste")

    assert completed.returncode == 0, completed.stderr
    assert quantities(completed.stdout) == {"Test Material": 95, "Single Unit Material": 1}
    assert any("Waste" in line for line in completed.stdout.splitlines() if line.startswith("| Item"))
    material_row = next(line for line in completed.stdout.splitlines() if "Test Material" in line)
    assert [cell.strip() for cell in material_row.strip("|").split("|")][2] == "5"


def test_material_efficiency_short_alias_and_maximum(sde: Path):
    completed = run_recipe(sde, "Test Widget", "--material-efficiency", "10", "-waste")

    assert completed.returncode == 0, completed.stderr
    assert quantities(completed.stdout)["Test Material"] == 90
    assert any("Waste" in line for line in completed.stdout.splitlines() if line.startswith("| Item"))


def test_time_efficiency_alias_reduces_seconds_without_changing_materials(sde: Path):
    completed = run_recipe(sde, "Test Widget", "-te", "20")

    assert completed.returncode == 0, completed.stderr
    assert quantities(completed.stdout) == {"Test Material": 100, "Single Unit Material": 1}
    assert "Run Time: 200" in completed.stdout


def test_waste_flag_at_default_efficiency_displays_zero_waste(sde: Path):
    completed = run_recipe(sde, "Test Widget", "--display-waste")

    assert completed.returncode == 0, completed.stderr
    assert any("Waste" in line for line in completed.stdout.splitlines() if line.startswith("| Item"))
    assert all(
        [cell.strip() for cell in line.strip("|").split("|")][2] == "0"
        for line in completed.stdout.splitlines()
        if line.startswith("| Test ")
    )


def test_material_efficiency_does_not_apply_to_reactions(sde: Path):
    completed = run_recipe(sde, "Test Reaction Product", "--material-efficiency", "10", "--time-efficiency", "20")

    assert completed.returncode == 0, completed.stderr
    assert quantities(completed.stdout) == {"Test Material": 100}
    assert "Run Time: 200" in completed.stdout


@pytest.mark.parametrize(
    "option, value",
    [
        ("--material-efficiency", "-1"),
        ("--material-efficiency", "11"),
        ("--material-efficiency", "1.5"),
        ("--time-efficiency", "-2"),
        ("--time-efficiency", "22"),
        ("--time-efficiency", "1"),
        ("--time-efficiency", "19"),
        ("--time-efficiency", "3"),
        ("--time-efficiency", "1.5"),
    ],
)
def test_efficiency_values_outside_required_domains_are_rejected(sde: Path, option: str, value: str):
    completed = run_recipe(sde, "Test Widget", option, value)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr
    assert "Traceback" not in completed.stderr
