"""Black-box tests for the industry recipe CLI.

The SDE used here is deliberately small and created at runtime.  Tests invoke
the documented command through a subprocess; they do not import the entrypoint
or rely on implementation details.
"""

from __future__ import annotations

import bz2
import csv
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "implementation" / "industry.py"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with bz2.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def sde(tmp_path: Path) -> Path:
    """A miniature SDE containing manufacturing, reaction, and edge cases."""
    _write_csv(
        tmp_path / "invTypes.csv.bz2",
        ["typeID", "typeName", "groupID", "marketGroupID", "volume", "published", "metaGroupID"],
        [
            {"typeID": 100, "typeName": "Test Ship", "groupID": 10, "marketGroupID": 40, "volume": "123.4", "published": "1", "metaGroupID": ""},
            {"typeID": 101, "typeName": "Widget", "groupID": 11, "marketGroupID": 42, "volume": "2.5", "published": "1", "metaGroupID": ""},
            {"typeID": 102, "typeName": "Alpha", "groupID": 12, "marketGroupID": "", "volume": "1", "published": "1", "metaGroupID": ""},
            {"typeID": 103, "typeName": "beta", "groupID": 12, "marketGroupID": "", "volume": "1", "published": "1", "metaGroupID": ""},
            {"typeID": 104, "typeName": "Hidden Product", "groupID": 11, "marketGroupID": "", "volume": "1", "published": "0", "metaGroupID": ""},
            {"typeID": 105, "typeName": "Widget Blueprint", "groupID": 20, "marketGroupID": "", "volume": "1", "published": "1", "metaGroupID": ""},
            {"typeID": 106, "typeName": "Reaction Product", "groupID": 12, "marketGroupID": "", "volume": "0.01", "published": "1", "metaGroupID": ""},
            {"typeID": 107, "typeName": "Reaction Blueprint", "groupID": 20, "marketGroupID": "", "volume": "1", "published": "1", "metaGroupID": ""},
            {"typeID": 108, "typeName": "Unpublished Material", "groupID": 12, "marketGroupID": "", "volume": "1", "published": "0", "metaGroupID": ""},
            {"typeID": 109, "typeName": "Tech Three Product", "groupID": 11, "marketGroupID": "", "volume": "1", "published": "1", "metaGroupID": "3"},
        ],
    )
    _write_csv(tmp_path / "invGroups.csv.bz2", ["groupID", "groupName", "categoryID"], [
        {"groupID": 10, "groupName": "Ships", "categoryID": 6},
        {"groupID": 11, "groupName": "Widgets", "categoryID": 7},
        {"groupID": 12, "groupName": "Materials", "categoryID": 8},
        {"groupID": 20, "groupName": "Blueprints", "categoryID": 9},
    ])
    _write_csv(tmp_path / "invCategories.csv.bz2", ["categoryID", "categoryName"], [
        {"categoryID": 6, "categoryName": "Ship"},
        {"categoryID": 7, "categoryName": "Commodity"},
        {"categoryID": 8, "categoryName": "Material"},
        {"categoryID": 9, "categoryName": "Blueprint"},
    ])
    _write_csv(tmp_path / "invMarketGroups.csv.bz2", ["marketGroupID", "marketGroupName", "parentGroupID"], [
        {"marketGroupID": 40, "marketGroupName": "Ships", "parentGroupID": ""},
        {"marketGroupID": 41, "marketGroupName": "Combat Ships", "parentGroupID": 40},
        {"marketGroupID": 42, "marketGroupName": "Widgets", "parentGroupID": 41},
    ])
    _write_csv(tmp_path / "invMetaTypes.csv.bz2", ["typeID", "metaGroupID"], [
        {"typeID": 101, "metaGroupID": 2},
        {"typeID": 109, "metaGroupID": 3},
    ])
    _write_csv(tmp_path / "invMetaGroups.csv.bz2", ["metaGroupID", "metaGroupName"], [
        {"metaGroupID": 2, "metaGroupName": "Tech II"},
        {"metaGroupID": 3, "metaGroupName": "Tech III"},
    ])
    _write_csv(tmp_path / "industryActivity.csv.bz2", ["typeID", "activityID", "time"], [
        {"typeID": 100, "activityID": 1, "time": 600},
        {"typeID": 101, "activityID": 1, "time": 61},
        {"typeID": 105, "activityID": 1, "time": 999},
        {"typeID": 102, "activityID": 1, "time": 60},
        {"typeID": 106, "activityID": 11, "time": 180},
        {"typeID": 107, "activityID": 11, "time": 180},
        {"typeID": 109, "activityID": 1, "time": 1},
    ])
    _write_csv(tmp_path / "industryActivityProducts.csv.bz2", ["typeID", "activityID", "productTypeID", "quantity"], [
        {"typeID": 100, "activityID": 1, "productTypeID": 100, "quantity": 1},
        {"typeID": 101, "activityID": 1, "productTypeID": 101, "quantity": 3},
        {"typeID": 102, "activityID": 1, "productTypeID": 102, "quantity": 1},
        {"typeID": 105, "activityID": 1, "productTypeID": 101, "quantity": 3},
        {"typeID": 106, "activityID": 11, "productTypeID": 106, "quantity": 10},
        {"typeID": 107, "activityID": 11, "productTypeID": 106, "quantity": 10},
        {"typeID": 109, "activityID": 1, "productTypeID": 109, "quantity": 1},
    ])
    _write_csv(tmp_path / "industryActivityMaterials.csv.bz2", ["typeID", "activityID", "materialTypeID", "quantity"], [
        {"typeID": 100, "activityID": 1, "materialTypeID": 101, "quantity": 12000},
        {"typeID": 101, "activityID": 1, "materialTypeID": 102, "quantity": 2000},
        {"typeID": 101, "activityID": 1, "materialTypeID": 103, "quantity": 1500},
        {"typeID": 101, "activityID": 1, "materialTypeID": 104, "quantity": 9999999},
        {"typeID": 106, "activityID": 11, "materialTypeID": 102, "quantity": 5},
        {"typeID": 106, "activityID": 11, "materialTypeID": 108, "quantity": 7},
    ])
    for name, fields in {
        "industryActivitySkills.csv.bz2": ["typeID", "activityID", "skillID", "level"],
        "industryActivityProbabilities.csv.bz2": ["typeID", "activityID", "productTypeID", "probability"],
        "ramActivities.csv.bz2": ["activityID", "activityName"],
    }.items():
        _write_csv(tmp_path / name, fields, [])
    (tmp_path / "ship_volumes.yaml").write_text("Ships: 15000.00\n", encoding="utf-8")
    return tmp_path


def run_cli(sde: Path, name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), "recipe", name, "--sde", str(sde)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_product_report_uses_metadata_packaged_ship_volume_and_sorted_materials(sde: Path) -> None:
    result = run_cli(sde, "Test Ship")
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith(
        "ITEM: Test Ship (100)\n"
        "Group: Ship > Ships\n"
        "Market Group: Ships\n"
        "Tech Level: Tech I\n"
        "Volume: 15000.00\n\n"
        "Recipe:\n"
        "Activity: Manufacturing\n"
        "Output Quantity: 1\n"
        "Run Time: 10\n"
        "| Item | Quantity | Buildable |\n"
        "|:-:|:---:|---|\n"
        "| Widget | 12000 | Yes |\n"
    )


def test_blueprint_resolves_to_its_product_and_ceils_time(sde: Path) -> None:
    result = run_cli(sde, "Widget Blueprint")
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith(
        "ITEM: Widget (101)\nGroup: Commodity > Widgets\nMarket Group: Ships > Combat Ships > Widgets\n"
        "Tech Level: Tech I\nVolume: 2.5\n\nRecipe:\nActivity: Manufacturing\n"
        "Output Quantity: 3\nRun Time: 2\n| Item | Quantity | Buildable |\n|:-:|:---:|---|\n"
        "| Alpha | 2000 | Yes |\n| beta | 1500 | No |\n| Hidden Product | 9999999 | No |\n"
    )


def test_reaction_report_and_default_none_market_group(sde: Path) -> None:
    result = run_cli(sde, "Reaction Product")
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith(
        "ITEM: Reaction Product (106)\nGroup: Material > Materials\nMarket Group: None\nTech Level: Tech I\n"
        "Volume: 0.01\n\nRecipe:\nActivity: Reactions\nOutput Quantity: 10\nRun Time: 3\n"
        "| Item | Quantity | Buildable |\n|:-:|:---:|---|\n| Alpha | 5 | Yes |\n"
        "| Unpublished Material | 7 | No |\n"
    )


@pytest.mark.parametrize(
    ("name", "level"),
    [("Widget", "Tech II"), ("Tech Three Product", "Tech III")],
)
def test_known_meta_groups_are_rendered_as_tech_levels(sde: Path, name: str, level: str) -> None:
    result = run_cli(sde, name)
    assert result.returncode == 0, result.stderr
    assert f"Tech Level: {level}\n" in result.stdout


@pytest.mark.parametrize("query", ["test ship", "Test Ship ", "Missing Product", "Hidden Product"])
def test_name_matching_is_exact_and_only_published_targets_are_valid(sde: Path, query: str) -> None:
    result = run_cli(sde, query)
    assert result.returncode != 0
