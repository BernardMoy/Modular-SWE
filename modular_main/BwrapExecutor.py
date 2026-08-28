from pathlib import Path
import subprocess

venv = Path(".venv")
codex_auth = Path.home() / ".codex" / "auth.json"


class BwrapExecutor:
    # Initialise with an absolute path object of the agent workspace
    def __init__(self, agent_workspace):
        self.agent_workspace = str(agent_workspace)

    def run(self, argv):
        cmd = [
            "bwrap",
            # bind mount the agent workspace and the venv
            "--bind",
            self.agent_workspace,
            "/agent_workspace",
            "--ro-bind",
            venv,
            "/.venv",
            # Make commands and python work
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/bin",
            "/bin",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            # Make network requests work
            "--ro-bind",
            "/etc/ssl",
            "/etc/ssl",
            "--ro-bind",
            "/etc/resolv.conf",
            "/etc/resolv.conf",
            # Codex auth so it wont 401 unauthorised
            "--ro-bind",
            str(codex_auth),
            str(codex_auth),
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            # Keep the system isolated
            "--unshare-all",
            # Allow coding agents API calls
            "--share-net",
            # Activate the venv by changing the PATH
            "--setenv",
            "PATH",
            "/.venv/bin:/usr/bin:/bin",
            # cd to inside agent workspace
            "--chdir",
            "/agent_workspace",
            # run additional argv
            *argv,
        ]

        try:
            # There needs to be a way to allow the LLM agent to produce output, capture it, and use it somewhere else.
            # The LLM agent needs to be called from the command line (python -m ...)
            # So realistic ways to do this would be
            # 1. Capture the stdout output where the LLM output is printed to the terminal
            # 2. Let the LLM write to a shared file, and read from there after it returns
            # The first option is currently used for its simplicity.
            # Capture the output of the LLM through stdout
            result = subprocess.run(
                cmd, check=True, text=True
            )  # capture_output=True is ignored - it blocks agent ask questions
            return result.stdout

        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr) from e
