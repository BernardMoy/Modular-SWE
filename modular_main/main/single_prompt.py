PROMPT = """I am testing a software engineering workflow. When asking human questions, start with the format "HUMAN_QUESTION: <Question>"

Write a function that sorts a list of integers using merge sort. 

Then you encountered some ambiguity that you need to ask the human: Should the list be sorted ascending or descending? 

Ask this question, then you will obtain the answer where you can perform the task and print out the code. 
"""

import subprocess 
from ..workspace_helpers.run_agent import run_agent
from ..settings import MODEL, AGENT
import asyncio 

def workflow(): 
    print("[1/2] Agent sign in")
    subprocess.run([
            "python", "-m", "modular_main.login"
        ], check=True)

    print("[2/2] Run prompt")
    result = asyncio.run(run_agent(AGENT, MODEL, PROMPT))
    # print(result)  # ignored: In the actual bwrap executor it works because it captures agent outputs 

if __name__ == "__main__": 
    workflow() 