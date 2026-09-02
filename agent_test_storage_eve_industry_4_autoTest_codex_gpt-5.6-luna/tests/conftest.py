from __future__ import annotations

import bz2
import csv
import io
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def sde_dir(tmp_path: Path) -> Path:
    """A small, self-contained SDE with one product and two recipes."""
    sde_root = tmp_path / "sde"
    sde_root.mkdir()
    rows = {
        "invTypes.csv.bz2": [
            {"typeID": "100", "typeName": "Widget", "groupID": "1", "published": "1", "volume": "1"},
            {"typeID": "101", "typeName": "Widget Blueprint", "groupID": "2", "published": "1", "volume": "1"},
            {"typeID": "200", "typeName": "Alloy", "groupID": "3", "published": "1", "volume": "2"},
            {"typeID": "201", "typeName": "Fuel", "groupID": "4", "published": "1", "volume": "1"},
            {"typeID": "202", "typeName": "Ore", "groupID": "5", "published": "1", "volume": "1"},
            {"typeID": "300", "typeName": "Datacore - Test Engineering", "groupID": "6", "published": "1", "volume": "0.1"},
            {"typeID": "301", "typeName": "Test Encryption Methods", "groupID": "7", "published": "1", "volume": "0.1"},
            {"typeID": "400", "typeName": "Test Decryptor", "groupID": "8", "published": "1", "volume": "0.1"},
            {"typeID": "500", "typeName": "Widget BPC", "groupID": "2", "published": "1", "volume": "1"},
        ],
        "invGroups.csv.bz2": [
            {"groupID": "1", "groupName": "Products", "categoryID": "1"},
            {"groupID": "2", "groupName": "Blueprints", "categoryID": "2"},
            {"groupID": "3", "groupName": "Materials", "categoryID": "3"},
            {"groupID": "4", "groupName": "Materials", "categoryID": "3"},
            {"groupID": "5", "groupName": "Materials", "categoryID": "3"},
            {"groupID": "6", "groupName": "Datacores", "categoryID": "3"},
            {"groupID": "7", "groupName": "Skills", "categoryID": "3"},
            {"groupID": "8", "groupName": "Decryptors", "categoryID": "3"},
        ],
        "invCategories.csv.bz2": [{"categoryID": "1", "categoryName": "Items"}, {"categoryID": "2", "categoryName": "Blueprints"}, {"categoryID": "3", "categoryName": "Materials"}],
        "invMarketGroups.csv.bz2": [],
        "industryActivity.csv.bz2": [
            {"typeID": "101", "activityID": "1", "time": "600"},
            {"typeID": "200", "activityID": "1", "time": "300"},
            {"typeID": "101", "activityID": "8", "time": "120"},
            {"typeID": "101", "activityID": "7", "time": "180"},
        ],
        "industryActivityProducts.csv.bz2": [
            {"typeID": "101", "productTypeID": "100", "activityID": "1", "quantity": "1"},
            {"typeID": "200", "productTypeID": "200", "activityID": "1", "quantity": "1"},
            {"typeID": "101", "productTypeID": "500", "activityID": "8", "quantity": "1"},
            {"typeID": "101", "productTypeID": "500", "activityID": "7", "quantity": "1"},
        ],
        "industryActivityMaterials.csv.bz2": [
            {"typeID": "101", "materialTypeID": "200", "activityID": "1", "quantity": "2"},
            {"typeID": "101", "materialTypeID": "201", "activityID": "1", "quantity": "1"},
            {"typeID": "200", "materialTypeID": "202", "activityID": "1", "quantity": "4"},
            {"typeID": "101", "materialTypeID": "300", "activityID": "8", "quantity": "2"},
            {"typeID": "101", "materialTypeID": "301", "activityID": "8", "quantity": "1"},
        ],
        "industryActivitySkills.csv.bz2": [{"typeID": "101", "activityID": "8", "skillID": "301"}],
        "industryActivityProbabilities.csv.bz2": [{"typeID": "101", "activityID": "8", "probability": "0.4"}],
        "invMetaTypes.csv.bz2": [],
        "invMetaGroups.csv.bz2": [],
    }
    for filename, values in rows.items():
        fields = sorted({key for row in values for key in row}) or ["value"]
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(values)
        (sde_root / filename).write_bytes(bz2.compress(stream.getvalue().encode()))
    (sde_root / "ship_volumes.yaml").write_text("{}\n", encoding="utf-8")
    return sde_root


@pytest.fixture
def run_cli():
    def run(*args: str):
        return subprocess.run(
            [sys.executable, "industry.py", *args],
            cwd=Path(__file__).parents[1] / "implementation",
            text=True,
            capture_output=True,
        )

    return run
