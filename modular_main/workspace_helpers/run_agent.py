"""
These helper functions run independently in the bind mounted agent workspace: 
They should not depend on any modules outside of the agent workspace
as they wont be available.
"""
from openai_codex import AsyncCodex, Sandbox, ApprovalMode
import argparse
import asyncio

async def run_agent(agent, model, prompt): 
    # TEMPORARY MOCK 
    # print(
    # """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
    # )

    # return 
    
    # run codex agent 
    if agent == "codex": 
        async with AsyncCodex() as codex: 
            thread = await codex.thread_start(
                model=model, 
                sandbox=Sandbox.full_access, 
                approval_mode=ApprovalMode.deny_all
            )
            result = await thread.run(prompt) 

            # Print the agent's output 
            print(result.final_response)

    # if the agent name does not match, throw an exception
    else: 
        raise Exception(f"Agent {agent} is invalid.")

def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", help="The coding agent being used")
    parser.add_argument("model", help="LLM Model of the coding agent")
    parser.add_argument("prompt", help="Prompt to the agent")
    args = parser.parse_args()

    # Runs the agent with a blocking operation
    # So we can wait for the result to be ready then parse it 
    asyncio.run(run_agent(args.agent, args.model, args.prompt))

# usage: run_agent.py [agent] [model] [prompt]
if __name__ == "__main__": 
    main() 