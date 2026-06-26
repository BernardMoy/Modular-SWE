from pathlib import Path 
import subprocess 

venv = Path(".venv")

class BwrapExecutor: 
    # Initialise with an absolute path object of the agent workspace
    def __init__(self, agent_workspace): 
        self.agent_workspace = str(agent_workspace)

    def run(self, argv):
        cmd = [
            "bwrap", 

            # bind mount the agent workspace and the venv 
            "--bind", self.agent_workspace, "/agent_workspace",
            "--ro-bind", venv, "/.venv",
            
            # Make commands and python work
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",

            # Keep the system isolated 
            "--unshare-all", 

            # Allow coding agents API calls 
            "--share-net",

            # Activate the venv by changing the PATH
            "--setenv", "PATH", "/.venv/bin:/usr/bin:/bin",

            # cd to inside agent workspace
            "--chdir", "/agent_workspace",

            # run additional argv 
            *argv
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result.stdout
        
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr) from e