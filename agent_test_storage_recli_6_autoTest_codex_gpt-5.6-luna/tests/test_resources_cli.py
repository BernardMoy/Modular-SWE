from conftest import read_calls


def test_project_creation_creates_volume_with_project_metadata(run_appctl, project, fake_runtime):
    result = run_appctl("site", "create", "demo", cwd=project)

    assert result.returncode == 0
    volume_call = next(call for call in read_calls(fake_runtime) if call and call[0] == "volume")
    assert "create" in volume_call
    assert any("label" in item or "appctl" in item for item in volume_call)


def test_project_creation_skips_volume_marked_skip_volume(run_appctl, project, fake_runtime):
    (project / "appctl.yml").write_text(
        """services: {web: {image: example/web}}
volumes:
  cache:
    skip_volume: true
"""
    )
    result = run_appctl("site", "create", "demo", cwd=project)

    assert result.returncode == 0
    assert not any("cache" in call for call in read_calls(fake_runtime))


def test_network_connect_reports_success(run_appctl, project, fake_runtime):
    result = run_appctl("site", "network", "connect", "web", cwd=project)

    assert result.returncode == 0
    assert "web" in result.stdout


def test_network_connect_failure_is_an_error(run_appctl, project, fake_runtime, monkeypatch):
    monkeypatch.setenv("RUNTIME_EXIT_CODE", "1")
    result = run_appctl("site", "network", "connect", "web", cwd=project)

    assert result.returncode != 0
    assert result.stderr == "There was some error connecting to web.\n"


def test_network_disconnect_failure_warns_without_halting(run_appctl, project, fake_runtime, monkeypatch):
    monkeypatch.setenv("RUNTIME_EXIT_CODE", "1")
    result = run_appctl("site", "network", "disconnect", "web", cwd=project)

    assert result.returncode == 0
    assert "Warning: Error in disconnecting from Docker network of web" in result.stderr


def test_network_remove_targets_the_named_network(run_appctl, project, fake_runtime):
    result = run_appctl("site", "network", "remove", "frontend", cwd=project)

    assert result.returncode == 0
    assert any(
        call and call[0] == "network" and "rm" in call and "frontend" in call
        for call in read_calls(fake_runtime)
    )

