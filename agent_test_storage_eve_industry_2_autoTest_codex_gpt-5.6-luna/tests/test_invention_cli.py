"""Black-box tests for the checkpoint 2 invention CLI.

The tests deliberately invoke the executable in a subprocess and construct a
small SDE in a temporary directory.  No implementation modules are imported.
"""

from __future__ import annotations

import bz2
import csv
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = next(
    candidate
    for candidate in (ROOT / "implementation" / "industry.py", ROOT / "previous_implementation" / "industry.py", ROOT / "industry.py")
    if candidate.exists()
)


def _bz2_csv(directory: Path, name: str, columns: list[str], rows: list[dict]):
    with bz2.open(directory / f"{name}.csv.bz2", "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def sde(tmp_path: Path) -> Path:
    """A minimal, self-contained SDE with deliberately unsorted source rows."""
    _bz2_csv(tmp_path, "invTypes", ["typeID", "typeName", "groupID", "marketGroupID", "volume", "published"], [
        {"typeID": 100, "typeName": "Charge", "groupID": 10, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 101, "typeName": "Advanced Ammo", "groupID": 11, "marketGroupID": 103, "volume": 1, "published": 1},
        {"typeID": 102, "typeName": "Barrage L", "groupID": 11, "marketGroupID": 103, "volume": 1, "published": 1},
        {"typeID": 103, "typeName": "Barrage L Blueprint", "groupID": 99, "marketGroupID": "", "volume": 0, "published": 1},
        {"typeID": 104, "typeName": "Nuclear L", "groupID": 11, "marketGroupID": 103, "volume": 1, "published": 1},
        {"typeID": 105, "typeName": "Nuclear L Blueprint", "groupID": 99, "marketGroupID": "", "volume": 0, "published": 1},
        {"typeID": 106, "typeName": "Proteus", "groupID": 20, "marketGroupID": 203, "volume": 1, "published": 1},
        {"typeID": 107, "typeName": "Proteus Blueprint", "groupID": 99, "marketGroupID": "", "volume": 0, "published": 1},
        {"typeID": 108, "typeName": "Intact Hull Section", "groupID": 30, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 109, "typeName": "Wrecked Hull Section", "groupID": 30, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 110, "typeName": "Datacore - Zeta Physics", "groupID": 40, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 111, "typeName": "Datacore - Alpha Engineering", "groupID": 40, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 112, "typeName": "Encryption Methods", "groupID": 41, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 113, "typeName": "Zeta Physics", "groupID": 41, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 114, "typeName": "Alpha Engineering", "groupID": 41, "marketGroupID": "", "volume": 1, "published": 1},
        {"typeID": 999, "typeName": "Unpublished Thing", "groupID": 11, "marketGroupID": 103, "volume": 1, "published": 0},
    ])
    _bz2_csv(tmp_path, "invGroups", ["groupID", "groupName", "categoryID"], [
        {"groupID": 11, "groupName": "Advanced Autocannon Ammo", "categoryID": 1},
        {"groupID": 20, "groupName": "Strategic Cruiser", "categoryID": 6},
        {"groupID": 30, "groupName": "Relic", "categoryID": 6},
        {"groupID": 40, "groupName": "Datacore", "categoryID": 7},
        {"groupID": 41, "groupName": "Skill", "categoryID": 16},
        {"groupID": 99, "groupName": "Blueprint", "categoryID": 9},
    ])
    _bz2_csv(tmp_path, "invCategories", ["categoryID", "categoryName"], [
        {"categoryID": 1, "categoryName": "Charge"}, {"categoryID": 6, "categoryName": "Ship"},
        {"categoryID": 7, "categoryName": "Commodity"}, {"categoryID": 9, "categoryName": "Blueprint"},
        {"categoryID": 16, "categoryName": "Skill"},
    ])
    _bz2_csv(tmp_path, "invMarketGroups", ["marketGroupID", "marketGroupName", "parentGroupID"], [
        {"marketGroupID": 103, "marketGroupName": "Advanced", "parentGroupID": 102},
        {"marketGroupID": 101, "marketGroupName": "Ammunition", "parentGroupID": ""},
        {"marketGroupID": 102, "marketGroupName": "Projectile", "parentGroupID": 101},
        {"marketGroupID": 203, "marketGroupName": "Strategic", "parentGroupID": 202},
        {"marketGroupID": 202, "marketGroupName": "Cruisers", "parentGroupID": 201},
        {"marketGroupID": 201, "marketGroupName": "Ships", "parentGroupID": ""},
    ])
    _bz2_csv(tmp_path, "industryActivity", ["typeID", "activityID", "time"], [
        {"typeID": 105, "activityID": 8, "time": 67800}, {"typeID": 107, "activityID": 7, "time": 3599},
        {"typeID": 103, "activityID": 1, "time": 60},
    ])
    _bz2_csv(tmp_path, "industryActivityProducts", ["typeID", "activityID", "productTypeID", "quantity"], [
        {"typeID": 105, "activityID": 8, "productTypeID": 103, "quantity": 1},
        {"typeID": 107, "activityID": 7, "productTypeID": 106, "quantity": 1},
        {"typeID": 103, "activityID": 1, "productTypeID": 102, "quantity": 10},
    ])
    _bz2_csv(tmp_path, "industryActivityMaterials", ["typeID", "activityID", "materialTypeID", "quantity"], [
        {"typeID": 105, "activityID": 8, "materialTypeID": 110, "quantity": 1},
        {"typeID": 105, "activityID": 8, "materialTypeID": 111, "quantity": 1},
        {"typeID": 105, "activityID": 8, "materialTypeID": 112, "quantity": 1},
        {"typeID": 107, "activityID": 7, "materialTypeID": 110, "quantity": 3},
        {"typeID": 107, "activityID": 7, "materialTypeID": 111, "quantity": 3},
        {"typeID": 107, "activityID": 7, "materialTypeID": 113, "quantity": 1},
    ])
    _bz2_csv(tmp_path, "industryActivityProbabilities", ["typeID", "activityID", "probability"], [
        {"typeID": 102, "activityID": 8, "probability": 0.4},
    ])
    _bz2_csv(tmp_path, "industryActivitySkills", ["typeID", "activityID", "skillID", "level"], [
        {"typeID": 105, "activityID": 8, "skillID": 112, "level": 1},
        {"typeID": 105, "activityID": 8, "skillID": 114, "level": 1},
        {"typeID": 107, "activityID": 7, "skillID": 112, "level": 1},
        {"typeID": 107, "activityID": 7, "skillID": 113, "level": 1},
    ])
    _bz2_csv(tmp_path, "invMetaTypes", ["typeID", "metaGroupID"], [
        {"typeID": 102, "metaGroupID": 2}, {"typeID": 106, "metaGroupID": 3},
    ])
    _bz2_csv(tmp_path, "invMetaGroups", ["metaGroupID", "metaGroupName"], [
        {"metaGroupID": 2, "metaGroupName": "Tech II"}, {"metaGroupID": 3, "metaGroupName": "Tech III"},
    ])
    _bz2_csv(tmp_path, "ramActivities", ["activityID", "activityName"], [
        {"activityID": 7, "activityName": "Reverse Engineering"}, {"activityID": 8, "activityName": "Invention"},
    ])
    (tmp_path / "ship_volumes.yaml").write_text("Strategic Cruiser: 1000\n", encoding="utf-8")
    return tmp_path


def run_cli(sde: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), "invention", *args, "--sde", str(sde)],
        cwd=ENTRYPOINT.parent,
        text=True,
        capture_output=True,
    )


def test_tech_ii_report_is_canonical_and_resolves_product_or_blueprint(sde: Path):
    product = run_cli(sde, "Barrage L")
    blueprint = run_cli(sde, "Barrage L Blueprint")
    assert product.returncode == 0, product.stderr
    assert product.stdout == blueprint.stdout
    assert product.stdout.endswith(
        """ITEM: Barrage L (102)\nGroup: Charge > Advanced Autocannon Ammo\nMarket Group: Ammunition > Projectile > Advanced\nTech Level: Tech II\n\nInvention:\nBase: Nuclear L Blueprint (105)\nDatacores: Datacore - Alpha Engineering, Datacore - Zeta Physics\nRequired Per Run: 1\nSkills: Alpha Engineering, Encryption Methods, Zeta Physics\nTime: 1130\nProbabilities:\n| Decryptor                       | Probability | Runs | ME | TE |\n|---------------------------------|-------------|------|----|----|\n| Accelerant Decryptor            | 70.00       | 11   | 4  | 14 |\n| Attainment Decryptor            | 100.00      | 14   | 1  | 8  |\n| Augmentation Decryptor          | 42.00       | 19   | 0  | 6  |\n| None                            | 58.33       | 10   | 2  | 4  |\n| Optimized Attainment Decryptor  | 100.00      | 12   | 3  | 2  |\n| Optimized Augmentation Decryptor| 52.50       | 17   | 4  | 4  |\n| Parity Decryptor                | 87.50       | 13   | 3  | 2  |\n| Process Decryptor               | 64.17       | 10   | 5  | 10 |\n| Symmetry Decryptor              | 58.33       | 12   | 3  | 12 |"""
    )


def test_skill_changes_probability_and_defaults_to_five(sde: Path):
    default = run_cli(sde, "Barrage L")
    explicit = run_cli(sde, "Barrage L", "--skill", "3")
    assert "| None                            | 58.33" in default.stdout
    assert "| None                            | 51.00" in explicit.stdout


def test_tech_iii_has_relic_rows_sorted_by_quality_then_decryptor(sde: Path):
    result = run_cli(sde, "Proteus")
    assert result.returncode == 0, result.stderr
    assert "Tech Level: Tech III\n\nInvention:\n" in result.stdout
    assert "Base:" not in result.stdout
    assert "Required Per Run: 3" in result.stdout
    assert "Time: 60" in result.stdout
    rows = [line for line in result.stdout.splitlines() if line.startswith("| ")][2:]
    assert len(rows) == 27
    assert all("Intact Hull Section" in row for row in rows[:9])
    assert all("Wrecked Hull Section" in row for row in rows[18:])
    assert rows[0].split("|")[2].strip() == "None"
    assert rows[1].split("|")[2].strip() == "Accelerant Decryptor"
    assert "| Intact Hull Section          | None" in result.stdout
    assert "| Intact Hull Section          | None                            | 37.92" in result.stdout


@pytest.mark.parametrize("skill", ["0", "6", "1.5", "five", ""])
def test_skill_must_be_one_integer_through_five(sde: Path, skill: str):
    args = ("Barrage L", "--skill", skill) if skill else ("Barrage L", "--skill")
    result = run_cli(sde, *args)
    assert result.returncode != 0


def test_unknown_unpublished_and_non_invention_targets_are_errors(sde: Path):
    for target in ("Missing", "Unpublished Thing", "Nuclear L"):
        result = run_cli(sde, target)
        assert result.returncode != 0
        assert result.stderr


def test_missing_sde_directory_is_an_error(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "invention", "Barrage L", "--sde", str(tmp_path / "missing")],
        cwd=ENTRYPOINT.parent, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert result.stderr
