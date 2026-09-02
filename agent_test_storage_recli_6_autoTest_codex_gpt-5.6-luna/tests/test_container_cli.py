from conftest import read_calls


def test_missing_runtime_has_actionable_error(run_appctl, project, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent")
    result = run_appctl("site", "up", cwd=project)

    assert result.returncode != 0
    assert result.stderr == (
        "Error: Container runtime is not installed. Please install the container runtime to run AppCtl.\n"
    )


def test_running_container_is_not_started_again(run_appctl, project, fake_runtime, monkeypatch):
    monkeypatch.setenv("RUNTIME_CONTAINER_STATE", "running")
    result = run_appctl("site", "start", "web", cwd=project)

    assert result.returncode == 0
    calls = read_calls(fake_runtime)
    assert not any(call and call[0] == "start" for call in calls)


def test_exited_container_is_started(run_appctl, project, fake_runtime, monkeypatch):
    monkeypatch.setenv("RUNTIME_CONTAINER_STATE", "exited")
    result = run_appctl("site", "start", "web", cwd=project)

    assert result.returncode == 0
    assert any(call and call[0] == "start" for call in read_calls(fake_runtime))


def test_missing_container_is_created(run_appctl, project, fake_runtime, monkeypatch):
    monkeypatch.setenv("RUNTIME_CONTAINER_STATE", "missing")
    result = run_appctl("site", "start", "web", cwd=project)

    assert result.returncode == 0
    assert any(call and call[0] == "create" and "web" in call for call in read_calls(fake_runtime))


def test_stop_restart_are_addressed_to_the_named_container(run_appctl, project, fake_runtime):
    assert run_appctl("site", "stop", "web", cwd=project).returncode == 0
    assert run_appctl("site", "restart", "web", cwd=project).returncode == 0

    calls = read_calls(fake_runtime)
    stop = next(call for call in calls if call and call[0] == "stop")
    restart = next(call for call in calls if call and call[0] == "restart")
    assert "web" in stop
    assert "web" in restart


def test_exec_skip_tty_disables_tty_allocation(run_appctl, project, fake_runtime):
    result = run_appctl("site", "exec", "--skip-tty", "web", "echo", "hello", cwd=project)

    assert result.returncode == 0
    exec_call = next(call for call in read_calls(fake_runtime) if "exec" in call)
    assert "-t" not in exec_call and "--tty" not in exec_call


def test_exec_forwards_user_shell_and_shell_wrapper(run_appctl, project, fake_runtime):
    result = run_appctl(
        "site", "exec", "web", "--user=1000", "--shell=/bin/bash",
        "--shell-wrapper", "printf", "ok", cwd=project
    )

    assert result.returncode == 0
    exec_call = next(call for call in read_calls(fake_runtime) if "exec" in call)
    assert "1000" in exec_call
    assert "/bin/bash" in exec_call
    assert "printf" in exec_call and "ok" in exec_call
