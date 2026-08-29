"""
These helper functions run independently in the bind mounted agent workspace:
They should not depend on any modules outside of the agent workspace
as they wont be available.
"""

from openai_codex import AsyncCodex, Sandbox, ApprovalMode
import argparse
import asyncio
import json
import uuid
from pathlib import Path
from opencode_ai import AsyncOpencode

# when the run_agent command is called, the agent summary and log will be written to the json below
AGENT_REPORT_JSON = "agent_report.json"
HUMAN_REQUEST_JSON = "human_request.json"
HUMAN_RESPONSE_JSON = "human_response.json"


async def _wait_for_human_response(kind: str, question: str) -> str:
    request_path = Path(HUMAN_REQUEST_JSON)
    response_path = Path(HUMAN_RESPONSE_JSON)
    request_id = uuid.uuid4().hex

    response_path.unlink(missing_ok=True)

    # Write the human question / approval to the human request.json
    with open(HUMAN_REQUEST_JSON, 'w') as f: 
        f.write(
            json.dump(
                {"request_id": request_id, "type": kind, "question": question}, f, indent=2
            )
        )

    try:
        # Continuously poll response path JSON for a human response.
        while True:
            if response_path.exists():
                try:
                    response = json.loads(response_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    response = None

                if (
                    isinstance(response, dict)
                    and response.get("request_id") == request_id
                ):
                    return str(response.get("response", ""))

            await asyncio.sleep(0.1)
    finally:
        request_path.unlink(missing_ok=True)
        response_path.unlink(missing_ok=True)


# Reads the agent workspace / analyzer result, remove all unresolved suggestions and quit
# So that the DA loop would not continue
def _remove_unresolved_suggestions():
    analyzer_result = Path("current_analyzer_result.json")

    with open(analyzer_result, "r") as f:
        data = json.load(f)

        data = [entry for entry in data if entry.get("status") != "unresolved"]

        with open(analyzer_result, "w") as f:
            json.dump(data, f, indent=2)


async def run_agent(agent, model, prompt):
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
                approval_mode=ApprovalMode.deny_all,
            )

            result = await thread.run(prompt)

            # Handle human questions asked by the agent
            # By re-assigning the variable 'result'
            while True:
                response = result.final_response

                # Identify questions asked by codex to humans: They are always in the form "HUMAN_QUESTION: <question>"
                if response.strip().startswith("HUMAN_QUESTION:"):
                    # Strip the prefix to get the question
                    question = response.removeprefix("HUMAN_QUESTION:").strip()

                    human_response = await _wait_for_human_response(
                        "question", question
                    )

                    # if human response == q, quit
                    if human_response.strip() == "q":
                        break

                    print("Response recorded.")

                    # Call the agent in the same thread again to continue the conversation
                    # with the human response added to the context
                    new_prompt = f"""The human has responded to your previous question: 
{human_response}

Continue your task or ask another question in the format HUMAN_QUESTION: <question>. 
"""
                    # Re-assign the result variable
                    result = await thread.run(new_prompt)

                elif response.strip().startswith("HUMAN_APPROVE:"):
                    # strip the prefix
                    question = response.removeprefix("HUMAN_APPROVE:").strip()

                    human_response = await _wait_for_human_response(
                        "approval", question
                    )

                    # if human response == a, quit
                    if human_response.strip() == "a":
                        break

                    # if human response == q, remove suggestions and quit
                    elif human_response.strip() == "q":
                        _remove_unresolved_suggestions()
                        break

                    else:
                        print("Response recorded.")

                    # Call the agent in the same thread again to continue the conversation
                    # with the human response added to the context
                    new_prompt = f"""The human has provided feedback for the suggestions: 
{human_response}

Continue your task.
"""
                    # Re-assign the result variable
                    result = await thread.run(new_prompt)

                else:
                    break

            # Print the agent's output to be captured later
            print(result.final_response)

            # Obtain the token usage from last and total
            last_dict = (
                result.usage.last.model_dump()
                if hasattr(result.usage.last, "model_dump")
                else vars(result.usage.last)
            )
            total_dict = (
                result.usage.total.model_dump()
                if hasattr(result.usage.total, "model_dump")
                else vars(result.usage.total)
            )

            for item in result.items:
                # Add the all fields metadata to the log array
                data = (
                    item.model_dump()
                    if hasattr(item, "model_dump")
                    else (
                        vars(item) if hasattr(item, "__dict__") else {"raw": str(item)}
                    )
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
                        if not change.get("kind"):
                            continue
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
                "changed_files_count": len(
                    set(added_files + updated_files + deleted_files)
                ),  # unique across add / update / delete
                "files_read": read_files,
                "files_read_count": len(set(read_files)),
            }

            # clear the agent report json
            # Write the summary and log (full data) to the json

            # As in overall_metrics (under metrics/) the "log" attribute must be present
            # so metrics can be analyzed from the coding session.
            with open(AGENT_REPORT_JSON, "w") as f:
                json.dump(
                    {"summary": summary, "tokens": total_dict, "log": log},
                    f,
                    indent=2,
                    default=str,
                )

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
            model_id=model,  # the offical docs example: opencode/gpt-5.1-codex (provider_id/model_id)
            parts=[{"type": "text", "text": prompt}],
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
