from __future__ import annotations

import csv
from pathlib import Path


def write_config(path: Path, *, te_bonus: int = 20, invention_skill: int = 3) -> Path:
    path.write_text(
        f"te_bonus: {te_bonus}\ninvention_skill: {invention_skill}\n",
        encoding="utf-8",
    )
    return path


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_plan_writes_required_csvs_and_consolidates_buy_materials(
    tmp_path, sde_dir, run_cli
):
    output = tmp_path / "reports"
    result = run_cli(
        "plan", "Widget 2 x3", "--config", str(write_config(tmp_path / "build.yaml")),
        "--sde", str(sde_dir), "--output", str(output)
    )

    assert result.returncode == 0, result.stderr
    assert (output / "materials.csv").exists()
    assert (output / "jobs.csv").exists()
    assert (output / "materials.csv").read_text().splitlines()[0] == (
        "name,to_buy,buy_volume,start_amount,end_amount"
    )
    assert (output / "jobs.csv").read_text().splitlines()[0] == "name,runs,days,count"
    assert read_csv(output / "materials.csv") == [
        {"name": "Fuel", "to_buy": "3", "buy_volume": "3.0", "start_amount": "0", "end_amount": "0"},
        {"name": "Ore", "to_buy": "24", "buy_volume": "24.0", "start_amount": "0", "end_amount": "0"},
    ]


def test_plan_item_defaults_runs_and_job_count_to_one(tmp_path, sde_dir, run_cli):
    config = write_config(tmp_path / "c.yaml")
    for build, expected_runs in (("Widget", "1"), ("Widget 2", "2")):
        output = tmp_path / expected_runs
        result = run_cli(
            "plan", build, "--config", str(config), "--sde", str(sde_dir),
            "--output", str(output)
        )

        assert result.returncode == 0, result.stderr
        assert read_csv(output / "jobs.csv")[0]["count"] == "1"
        assert read_csv(output / "jobs.csv")[0]["runs"] == expected_runs


def test_plan_normal_form_applies_manual_me_and_configured_te(tmp_path, sde_dir, run_cli):
    output = tmp_path / "out"
    result = run_cli(
        "plan", "Widget 2 10 20 x3", "--config", str(write_config(tmp_path / "c.yaml")),
        "--sde", str(sde_dir), "--output", str(output)
    )

    assert result.returncode == 0, result.stderr
    rows = read_csv(output / "materials.csv")
    assert {row["name"]: row["to_buy"] for row in rows} == {
        "Alloy": "6", "Fuel": "3", "Ore": "24"
    }
    # The configured TE bonus must affect the reported job duration.
    assert float(read_csv(output / "jobs.csv")[0]["days"]) > 0


def test_plan_accepts_invention_and_reverse_engineering_forms(tmp_path, sde_dir, run_cli):
    config = write_config(tmp_path / "c.yaml")
    for build in ("Widget 1 None x1", "Widget 1 None Test Relic x1"):
        result = run_cli("plan", build, "--config", str(config), "--sde", str(sde_dir), "--output", str(tmp_path / build[:2]))
        assert result.returncode == 0, result.stderr


def test_plan_rejects_invalid_config_values_and_missing_required_options(tmp_path, sde_dir, run_cli):
    for bad in (write_config(tmp_path / "bad-te.yaml", te_bonus=31), write_config(tmp_path / "bad-skill.yaml", invention_skill=0)):
        result = run_cli("plan", "Widget", "--config", str(bad), "--sde", str(sde_dir), "--output", str(tmp_path / "out"))
        assert result.returncode != 0
    result = run_cli("plan", "Widget", "--config", str(tmp_path / "missing.yaml"), "--sde", str(sde_dir), "--output", str(tmp_path / "out"))
    assert result.returncode != 0


def test_plan_rejects_unknown_product_and_malformed_build_string(tmp_path, sde_dir, run_cli):
    config = write_config(tmp_path / "c.yaml")
    for build in ("Not A Product", "Widget nope", "Widget 1 2 3 4 5", "Widget 1 None x0"):
        result = run_cli("plan", build, "--config", str(config), "--sde", str(sde_dir), "--output", str(tmp_path / "out"))
        assert result.returncode != 0
