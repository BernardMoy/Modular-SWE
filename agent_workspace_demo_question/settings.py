from typing import Literal

# For the coding agent: Codex / Claude Code
AGENT: Literal["codex", "opencode"] = "codex"
MODEL: Literal[
    "gpt-5.4-nano",
    "gpt-5.4-mini", 
    "gpt-5.6-luna",
    "Nemotron 3 Ultra Free",
    "Big Pickle",
    "DeepSeek V4 Flash Free",
] = "gpt-5.6-luna"

# For the modular workflow.
# noDesign: Directly implement all modules at once (reference)
# auto: D-A loop analyzer makes suggestions automatically using the agent's thinking; no human is involved.
# human: D-A loop analyzer would ask human questions if it encounters ambiguity / contextual uncertainty / contrasting metrics.
WORKFLOW_MODE: Literal[
    "noDesign", "autoNoMetric", "auto", "human", "autoByLayer", "autoTest"  # USED ONLY [4] noDesign, auto, autoNoMetric, autoByLayer   # "autoAggressive", 
] = "human"

# Unused:
# allAtOnce: DA loop, then implement all modules at once following the design
# byLayer: BFS, then code modules in the same layer within the same prompt
# byModule: BFS and one prompt per module. Modules in the same layer are coded in parallel

# Problem type: Either "custom" or "scb"
PROBLEM_TYPE: Literal["custom", "scb"] = "custom"

# Whether or not UI is enabled
UI_ENABLED = True

# Sign in method: either "api" or "chatgpt"
# api means use openai api key - access models such as gpt 5.4 nano 
# chatgpt only supports the models visible under /models when running codex in the terminal 
SIGN_IN_METHOD: Literal["api", "chatgpt"] = "chatgpt" 

# If demo is true, then the UI would flow deterministically: 
# 1. Show current design viewing and current deps graph 
# 2. Answer human question 
# 3. Show analyzer suggestions, and how you would modify it 
DEMO_MODE = False 