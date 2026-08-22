from typing import Literal 

# For the coding agent: Codex / Claude Code 
AGENT: Literal["codex", "opencode"] = "codex"
MODEL: Literal[
                "gpt-5.4", 
                "gpt-5.6-luna",
                
                "Nemotron 3 Ultra Free", 
                "Big Pickle", 
                "DeepSeek V4 Flash Free"
               ] = "gpt-5.6-luna"

# For the modular workflow. 
# noDesign: Directly implement all modules at once (reference) 
# auto: D-A loop analyzer makes suggestions automatically using the agent's thinking; no human is involved. 
# human: D-A loop analyzer would ask human questions if it encounters ambiguity / contextual uncertainty / contrasting metrics. 
WORKFLOW_MODE: Literal[
    "noDesign", 
    "autoNoMetric", 
    "autoTest"
    "auto", 
    "human"
    ] = "autoTest"

# Unused: 
# allAtOnce: DA loop, then implement all modules at once following the design 
# byLayer: BFS, then code modules in the same layer within the same prompt 
# byModule: BFS and one prompt per module. Modules in the same layer are coded in parallel

# Problem type: Either "custom" or "scb" 
PROBLEM_TYPE: Literal["custom", "scb"] = "scb"