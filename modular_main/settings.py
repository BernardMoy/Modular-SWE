"""
Settings to be configured before running the main workflow. 
It is located here instead of passed as parameters as this allows the settings to be shared by different files
without the need to pass data to many descendents (prop drilling)
"""

from typing import Literal

# Coding agent name: Codex / claude code, or opencode (free, but is unreliable) 
AGENT: Literal["codex", "opencode"] = "codex"

# The model used according to the selected coding agent 
MODEL: Literal[
    "gpt-5.4-nano",
    "gpt-5.4-mini", 
    "gpt-5.6-luna",
    "Nemotron 3 Ultra Free",
    "Big Pickle",
    "DeepSeek V4 Flash Free",
] = "gpt-5.6-luna"

# Workflow modes for the modular workflow. 
# noDesign: Directly implement all modules at once
# auto: Multi-agent loop, but without the human steps. Feedback loops stop beyond a certain threshold. Used for automatic evaluation.
# human: The full workflow with human-in-the-loop. 
# autoNoMetric: auto mode, but without providing the implementation metrics. For ablation study 
# autoTest: Test-driven development modification to have the agent write black box tests first prior to implementation. 
# autoByLayer: auto mode, but the implementation is done layer by layer using a BFS of the dependency graph. 
WORKFLOW_MODE: Literal[
    "noDesign", "autoNoMetric", "auto", "human", "autoByLayer", "autoTest" 
] = "human"

# Problem type: Either "custom" for custom problems or "scb" for SlopCodeBench problems
PROBLEM_TYPE: Literal["custom", "scb"] = "custom"

# Whether or not UI is enabled
UI_ENABLED = True

# Sign in method: either "api" or "chatgpt", currently tailored to the codex sign in methods. 
# api means use openai api key - access models such as gpt 5.4 nano 
SIGN_IN_METHOD: Literal["api", "chatgpt"] = "chatgpt" 

# Whether or not in demo mode. 
# If demo is true, then the UI would flow deterministically: 
# 1. Show current design viewing and current deps graph 
# 2. Answer human question 
# 3. Show analyzer suggestions, and how you would modify it 
DEMO_MODE = True