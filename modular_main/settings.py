from typing import Literal 

# For the coding agent: Codex / Claude Code 
AGENT: Literal["codex", "opencode"] = "codex"
MODEL: Literal[
                "gpt-5.5", 
                "Nemotron 3 Ultra Free", "Big Pickle", "DeepSeek V4 Flash Free"
               ] = "gpt-5.5"

# For the modular workflow. 
# noDesign: Directly implement all modules at once (reference) 
# allAtOnce: DA loop, then implement all modules at once following the design 
# byLayer: BFS, then code modules in the same layer within the same prompt 
# byModule: BFS and one prompt per module. Modules in the same layer are coded in parallel
WORKFLOW_MODE: Literal[
    "noDesign", 
    "allAtOnce", 
    "byLayer", 
    "byModule", 
    "5aspects"
    ] = "5aspects"
