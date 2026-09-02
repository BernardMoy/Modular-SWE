from conftest import read_calls


def test_services_are_reported_in_compose_order(run_appctl, project):
    result = run_appctl("site", "config", "--services", cwd=project)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["database", "web"]


def test_custom_compose_is_applied_after_base(run_appctl, project):
    (project / "override.yml").write_text(
        """services:
  web:
    image: override/web
  worker:
    image: example/worker
"""
    )
    result = run_appctl(
        "site", "config", "--services", "--custom-compose=override.yml", cwd=project
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["database", "web", "worker"]


def test_missing_custom_compose_warns_and_continues(run_appctl, project):
    result = run_appctl(
        "site", "config", "--services", "--custom-compose=missing.yml", cwd=project
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["database", "web"]
    assert "Warning: File: missing.yml does not exist. Falling back to default compose file." in result.stderr


def test_non_compose_override_is_ignored(run_appctl, project):
    (project / "notes.txt").write_text("services:\n  accidental: {}\n")
    result = run_appctl("site", "config", "--services", cwd=project)

    assert result.returncode == 0
    assert "accidental" not in result.stdout


def test_up_uses_detached_mode_and_requested_services(run_appctl, project, fake_runtime):
    result = run_appctl("site", "up", "web", cwd=project)

    assert result.returncode == 0
    calls = read_calls(fake_runtime)
    compose_up = next(call for call in calls if "up" in call)
    assert "-d" in compose_up or "--detach" in compose_up
    assert compose_up[-1] == "web"


def test_down_removes_project_resources(run_appctl, project, fake_runtime):
    result = run_appctl("site", "down", cwd=project)

    assert result.returncode == 0
    compose_down = next(call for call in read_calls(fake_runtime) if "down" in call)
    assert "--volumes" in compose_down or "-v" in compose_down
