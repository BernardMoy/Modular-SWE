from pathlib import Path 
import subprocess 

class BwrapExecutor: 
    # Initialise with an absolute path object of the agent workspace
    def __init__(self, agent_workspace): 
        self.agent_workspace = str(agent_workspace)

    def run(self, argv): 
        cmd = [
            "bwrap", 
            "--bind", self.agent_workspace, "/agent_workspace",
            
            # Make commands and python work
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",

            # Keep the system isolated 
            "--unshare-all", 

            # cd to inside agent workspace
            "--chdir", "/agent_workspace",

            # run additional argv 
            *argv
        ]

        return subprocess.run(
            cmd, 
            check=True
        )