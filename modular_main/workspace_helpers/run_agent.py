"""
These helper functions run independently in the bind mounted agent workspace: 
They should not depend on any modules outside of the agent workspace
as they wont be available.
"""
from openai_codex import AsyncCodex, Sandbox, ApprovalMode
import argparse
import asyncio
import json 
from opencode_ai import AsyncOpencode

# when the run_agent command is called, the agent summary and log will be written to the json below 
AGENT_REPORT_JSON = "agent_report.json" 


async def run_agent(agent, model, prompt): 
    # TEMPORARY MOCK 
    # print(
    # """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
    # )

    log = []
    read_files = [] 
    added_files = [] 
    updated_files = [] 
    deleted_files = [] 

    # run codex agent 
    if agent == "codex": 
        async with AsyncCodex() as codex: 
            thread = await codex.thread_start(
                model=model, 
                sandbox=Sandbox.full_access, 
                approval_mode=ApprovalMode.deny_all
            )
            result = await thread.run(prompt) 

            # Print the agent's output to be captured later 
            print(result.final_response)

            for item in result.items:
                # Add the all fields metadata to the log array 
                data = item.model_dump() if hasattr(item, "model_dump") else (
                    vars(item) if hasattr(item, "__dict__") else {"raw": str(item)}
                )
                log.append(data)

                # For edits (add / update / delete) 
                # this is indicated in the kind - type field inside changes 
                # their type = fileChange if "changes" is present 

                # If there is a changes: key, then extract the path inside 
                # To record a file edit
                if data.get("changes") and data.get("type") == "fileChange":
                    # add all the changed file paths to the edited files  
                    for change in data["changes"]:
                        if not change.get("kind"): continue 
                        if change["kind"].get("type") == "add": 
                            added_files.append(change.get("path"))
                        if change["kind"].get("type") == "update": 
                            updated_files.append(change.get("path"))
                        if change["kind"].get("type") == "delete": 
                            deleted_files.append(change.get("path"))

                # For read: 
                # there is a command key with type = "read" 

                # For list a directory, 
                # there is a command key with type = "search" (NOT SURE, CHECK!)
                elif data.get("command_actions"):
                    for command_action in data["command_actions"]: 
                        if command_action["type"] == "read": 
                            if "path" in command_action: 
                                read_files.append(command_action["path"])

            # The list of added / updated / deleted files are in time order. 
            summary = {
                "added_files": added_files, 
                "added_files_count": len(set(added_files)),  # unique only 
                "updated_files": updated_files, 
                "updated_files_count": len(set(updated_files)), 
                "deleted_files": deleted_files, 
                "deleted_files_count": len(set(deleted_files)), 
                "changed_files_count": len(set(added_files + updated_files + deleted_files)), # unique across add / update / delete 
                "files_read": read_files,
                "files_read_count": len(set(read_files)),
            }

            # clear the agent report json 
            # Write the summary and log (full data) to the json
            with open(AGENT_REPORT_JSON, "w") as f:
                json.dump({"summary": summary, "log": log}, f, indent=2, default=str)

    # run opencode agent 
    # https://github.com/anomalyco/opencode-sdk-python/blob/main/api.md
    # generate the base url by running `opencode serve` in a separate terminal

    # It would hit timeout after the implementation is completed and i have no idea why. 
    # See curl -N http://127.0.0.1:4096/event
    # server heartbeat events remains, those causes the timeout to occur 
    elif agent == "opencode": 
        client = AsyncOpencode(base_url="http://127.0.0.1:4096")  
        session = await client.session.create() 

        # runs the chat 
        result = await client.session.chat(
            id=session.id, 
            provider_id="opencode",  # free ones only (opencode Zen)
            model_id=model,   # the offical docs example: opencode/gpt-5.1-codex (provider_id/model_id)
            parts=[{"type": "text", "text": prompt}]
        )

        print(result) 

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
