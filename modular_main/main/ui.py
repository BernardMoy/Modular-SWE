"""
https://textual.textualize.io/guide/design/
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from typing import Callable

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    RichLog,
    TextArea,
)
from textual.widgets import Select
from textual.reactive import reactive
from textual import on
from typing import Any
from .ui_text_formatters import get_formatted_analyzer_suggestions, write_formatted_human_analyzer_approval, write_formatted_human_question_response


# sort module keys.
# module keys bundle the type (new) together because this follows the same convention of implementation
# order: deleted -> new -> changed -> keep
def _sort_design_modules(name):
    order = {"deleted": 0, "new": 1, "changed": 2, "keep": 3}
    for key in order.keys():
        if name.startswith(f"({key})"):
            return order[key]

    # unrecognised come last
    return 4


class TitleApp(App[None]):
    # Do not call the watcher while the widget tree is being composed.

    # ============= STATES ===============
    stage = reactive("Waiting for workflow", init=False)
    settings = reactive(
        {
            "problem_type": "unknown",
            "problem_name": "unknown",
            "workflow_mode": "unknown",
            "agent": "none",
            "model": "none",
            "checkpoint": 0,
        },
        init=False,
    )
    agent_response = reactive("", init=False)
    design_or_impl = reactive({}, init=False)
    analyzer_suggestions = reactive([], init=False)  # Preserves analyzer result order.
    human_request = reactive({}, init=False)  # the agent question to human
    # ====================================

    # Register the theme
    def on_mount(self):
        self.theme = "textual-dark"
        self.query_one("#selected-file-content", RichLog).write("No files selected.")
        self.watch_human_request(self.human_request)
        self.set_interval(0.1, self._poll_human_request)
        if self.workflow is not None:
            self.call_after_refresh(self._start_workflow)

    CSS_PATH = "ui.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self,
        workspace: Path | None = None,
        workflow: Callable[..., None] | None = None,
    ):
        super().__init__(watch_css=True)
        self.workspace = workspace or Path(
            "agent_workspace"
        )  # workspace is the agent workspace path
        self.workflow = workflow
        self.design_impl_data = self.design_or_impl
        self.analyzer_suggestions_data = self.analyzer_suggestions
        self._analyzer_result_mtime = None

    def _start_workflow(self):
        Thread(
            target=self._run_workflow,
            name="modular-workflow",
            daemon=True,
        ).start()

    # continuously 0.1s poll the human reuqest json file
    # if there are content then update the reactive state
    def _poll_human_request(self) -> None:
        # when human request is continuously being polled, it also polls analyzer result 
        self._poll_analyzer_result()
        request_path = self.workspace / "human_request.json"
        if not request_path.exists():
            if self.human_request:
                self.human_request = {}
            return

        try:
            request_json = json.loads(request_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        if (
            isinstance(request_json, dict)
            and request_json.get("request_id")
            and request_json.get("request_id") != self.human_request.get("request_id")
        ):
            # Assign to the human request reactive state 
            self.human_request = request_json

    # continuously poll the analyzer result file
    # this is required (but not the design)
    # because the analyzer is a blocking operation in the human mode
    # while the agent is waiting for human input.
    def _poll_analyzer_result(self) -> None:
        analyzer_path = self.workspace / "current_analyzer_result.json"

        # if the analyzer file not exist, set none 
        if not analyzer_path.exists():
            self._analyzer_result_mtime = None
            if self.analyzer_suggestions:
                self.analyzer_suggestions = []
            return

        try:
            mtime = analyzer_path.stat().st_mtime_ns
            if mtime == self._analyzer_result_mtime:
                return
            suggestions = get_formatted_analyzer_suggestions(self.workspace)
        except (OSError, json.JSONDecodeError, KeyError):
            # The agent may still be writing the JSON file.
            return

        self._analyzer_result_mtime = mtime
        self._set_analyzer_suggestions(suggestions)

    def _run_workflow(self):
        # Run the blocking workflow outside Textual's UI thread.
        assert self.workflow is not None
        try:
            self.workflow(
                self.update_stage,
                self.update_settings,
                self.update_design_or_impl,
                self.update_agent_response,
                self.update_analyzer_suggestions,
            )
            self.update_stage("Workflow complete")
        except Exception as error:
            raise

    # Reactive state updates follow the same pattern:
    # update_* (thread boundary) -> _set_* (reactive state) -> watch_* (UI).

    # stage
    def update_stage(self, stage: str) -> None:
        self.call_from_thread(self._set_stage, stage)

    def _set_stage(self, stage: str) -> None:
        self.stage = stage

    def watch_stage(self, stage: str) -> None:
        self.query_one("#stage-label", Label).update(f"Stage: {stage}")

    # settings
    def update_settings(self, settings: dict[str, Any]) -> None:
        self.call_from_thread(self._set_settings, settings)

    def _set_settings(self, settings: dict[str, Any]) -> None:
        self.settings = settings

    def watch_settings(self, settings: dict[str, Any]) -> None:
        self.query_one("#settings-label", Label).update(
            f"Problem: {settings.get("problem_name", "unknown")} (checkpoint {settings.get("checkpoint", 0)}) ({settings.get("problem_type", "unknown")}). Agent: {settings.get("agent", "unknown")}. Model: {settings.get("model", "unknown")}. Mode: {settings.get("workflow_mode", "unknown")}."
        )

        # Enable the analyzer table feedback column,
        # the analyzer submit button,
        # and the human questions submit button
        # if the changed setting is human mode.
        # human_mode = settings.get("workflow_mode") == "human"
        # for feedback in self.query("#suggestions TextArea"):
        #     feedback.disabled = not human_mode
        # self.query_one("#analyzer-submit", Button).disabled = not human_mode
        # self.query_one("#human-submit", Button).disabled = not human_mode

    # agent response
    def update_agent_response(self, response: str) -> None:
        self.call_from_thread(self._set_agent_response, response)

    def _set_agent_response(self, response: str) -> None:
        self.agent_response = response

    def watch_agent_response(self, response: str) -> None:
        self.query_one("#agent-response", TextArea).load_text(response)

    # design or implementation
    def update_design_or_impl(self, value: dict[str, Any]) -> None:
        self.call_from_thread(self._set_design_or_impl, value)

    def _set_design_or_impl(self, value: dict[str, Any]) -> None:
        self.design_or_impl = dict(value)

    def watch_design_or_impl(self, value: dict[str, Any]) -> None:
        self.design_impl_data = dict(value)
        files_panel = self.query_one("#files-panel", Vertical)
        files_panel.border_title = f"Modules ({len(self.design_impl_data)})"
        design_list = self.query_one("#design-list", ListView)
        design_list.clear()
        sorted_keys = sorted(
            self.design_impl_data,
            key=_sort_design_modules,
        )
        for file_name in sorted_keys:
            design_list.append(ListItem(Label(file_name)))

    # analyzer suggestions
    def update_analyzer_suggestions(self, value: list[Any]) -> None:
        self.call_from_thread(self._set_analyzer_suggestions, value)

    @staticmethod
    def _normalize_analyzer_suggestion(suggestion: dict[str, Any]) -> dict[str, str]:
        return {
            "status": str(suggestion.get("status", "unresolved")),
            "modules": str(
                suggestion.get("modules", suggestion.get("module_name", "Unknown"))
            ),
            "description": str(suggestion.get("description", "")),
            "feedback": str(suggestion.get("feedback", "")),
        }

    def _set_analyzer_suggestions(self, value: list[Any]) -> None:
        self.analyzer_suggestions = [
            self._normalize_analyzer_suggestion(suggestion) for suggestion in value
        ]

    async def watch_analyzer_suggestions(self, value: list[Any]) -> None:
        # Replace the table rows when a new analyzer result is available
        self.analyzer_suggestions_data = [
            self._normalize_analyzer_suggestion(suggestion) for suggestion in value
        ]
        suggestions = self.query_one("#suggestions", Vertical)

        # Delete the table rows and re-create them
        await suggestions.remove_children()
        await suggestions.mount(
            *[
                self._make_suggestion_row(index, suggestion)
                for index, suggestion in enumerate(self.analyzer_suggestions_data)
            ]
        )

    # the request is the json format of dict given in human_request.json
    def watch_human_request(self, request: dict[str, Any]) -> None:
        suggestions_panel = self.query_one("#suggestions-panel", Vertical)
        request_view = self.query_one("#human-response-view", Vertical)

        # The runner calls this field "type"; accept "kind" as well.
        kind = request.get("kind", request.get("type", ""))
        if not request or not kind:
            # Once human_request.json is deleted, the human request state change to {}, this part is activated 
            # which shows the analyzer suggestions by default 
            suggestions_panel.display = True
            request_view.display = False
            return

        # Questions use the response panel; approvals leave suggestions visible.
        suggestions_panel.display = kind == "approval"
        request_view.display = kind == "question"

        # kind is either question | approval
        # If the kind is question, set human submit button disabled false 
        if kind == "question": 
            self.query_one("#human-submit", Button).disabled = False 

        elif kind == "approval": 
            self.query_one("#analyzer-submit", Button).disabled = False 

        # Replace the text with human question
        self.query_one("#human-question", Label).update(
            str(request.get("question", ""))
        )

        response = self.query_one("#human-response", TextArea)
        response.load_text("")
        response.read_only = False

        # Enable input and the submit button, which is disabled when the human submits 
        # response.disabled = False
        # self.query_one("#human-submit", Button).disabled = False
        # request_view.display = True

    def _make_suggestion_row(
            self, index: int, suggestion: dict[str, Any]
        ) -> Horizontal:
        statuses = ("unresolved", "accepted", "rejected")
        selected_status = suggestion.get("status", "unresolved")
        if selected_status not in statuses:
            selected_status = "unresolved"

        return Horizontal(
            Select(
                [(status, status) for status in statuses],
                value=selected_status,
                allow_blank=False,
                id=f"status-{index}",
            ),
            Label(str(suggestion.get("modules", "Unknown"))),
            Label(str(suggestion.get("description", "Unknown"))),
            TextArea(
                str(suggestion.get("feedback", "")),
                id=f"feedback-{index}",
                classes="human-text",
                disabled=False, 
                placeholder="Feedback..."
            ),
            classes="suggestion-row",
        )

    # Main compose function for the UI
    def compose(self) -> ComposeResult:
        # Top part showing the mode and problem
        yield Label("", id="settings-label")

        # the top bar showing time and command palette search
        yield Header(show_clock=True)

        # The rectangle label above showing the current stage in the multi agent pipeline
        with Container(id="stage"):
            yield Label(f"Stage: {self.stage}", id="stage-label")

        with Container(id="main-content"):
            # The left bar:
            # For design: It shows the list of modules (keep, changed, new) in 3 boxes
            # For implementation: It shows
            with Vertical(id="files-panel", classes="panel") as files_panel:
                files_panel.border_title = f"Modules ({len(self.design_impl_data)})"
                with ListView(
                    id="design-list", initial_index=None
                ):  # Disable the initial selection highlighting

                    # Display the keys sorted: See sort function
                    sorted_keys = sorted(
                        self.design_impl_data.keys(),
                        key=lambda x: _sort_design_modules(x),
                    )
                    for file_name in sorted_keys:
                        yield ListItem(Label(file_name))

            # The right part
            with Vertical(id="right-content"):

                # Right top: Display the selected file (formatted JSON) or code
                with Vertical(
                    id="selected-file-panel", classes="panel"
                ) as selected_panel:
                    selected_panel.border_title = "Selected file"
                    yield RichLog(
                        id="selected-file-content",
                        wrap=True,
                        markup=False,
                    )

                # Right bottom: Suggestions
                with Vertical(
                    id="suggestions-panel", classes="panel"
                ) as suggestions_panel:
                    suggestions_panel.border_title = "Analyzer suggestions"

                    # Suggestions
                    # Table headers
                    with Horizontal(classes="suggestion-header"):
                        yield Label("Status")
                        yield Label("Modules")
                        yield Label("Description")
                        yield Label("Feedback")

                    # Table body
                    with Vertical(id="suggestions"):
                        for index, suggestion in enumerate(
                            self.analyzer_suggestions_data
                        ):
                            yield self._make_suggestion_row(index, suggestion)

                    with Horizontal(id="analyzer-submit-button"):
                        # Keep the feedback field flexible and the submit
                        # button pinned to the right of the same row.
                        yield TextArea(
                            id="analyzer-additional-feedback",
                            classes="human-text",
                            read_only=False,
                            disabled=False,
                            placeholder="Additional feedback...",
                        )
                        yield Button(
                            "Submit",
                            variant="success",
                            id="analyzer-submit",
                            disabled=(self.settings.get("workflow_mode", ""))
                            != "human",
                        )

                # Right bottom: Human questions
                with Vertical(
                    id="human-response-view", classes="panel"
                ) as response_panel:
                    response_panel.border_title = "Human question"
                    yield Label("", id="human-question")
                    yield TextArea(
                        id="human-response",
                        classes="human-text",
                        read_only=False,
                        disabled=False,
                        placeholder="Human response..."
                    )

                    # The submit button for human clarification questions 
                    with Horizontal(id="human-submit-button"):
                        yield Button(
                            "Submit",
                            variant="success",
                            id="human-submit",
                            disabled=(self.settings.get("workflow_mode", ""))
                            != "human",
                        )

        # Footer showing q quit
        yield Footer()

    # Listener only to the design-list (LEFT list)
    @on(ListView.Selected, "#design-list")
    def on_list_view_selected(self, event: ListView.Selected):
        # Obtain the key selected
        selected_key = str(event.item.query_one(Label).content)

        selected_panel = self.query_one("#selected-file-panel", Vertical)
        selected_panel.border_title = selected_key

        # Obtain the processed content and set content
        content = self.design_impl_data.get(selected_key, "Failed to render content.")

        selected_content = self.query_one("#selected-file-content", RichLog)
        selected_content.clear()
        selected_content.write(content)
        selected_content.scroll_home(animate=False, immediate=True)

    # Listener when the human submit (for clarification questions) is pressed
    # Write the result to human_response.json which gets captured inside run_agent.py
    @on(Button.Pressed, "#human-submit")
    def on_human_submit(self) -> None:
        request_id = self.human_request.get("request_id")
        if not request_id:
            return

        # Obtain the response text 
        response = self.query_one("#human-response", TextArea).text

        write_formatted_human_question_response(
            self.workspace, 
            request_id, 
            response
        )

        # Disable the human submit button, which is re-enabled later
        # inside the watch human response function
        self.query_one("#human-submit", Button).disabled = True

    # Listener when the analyzer submit (for human's approval on the analyzer plan) is pressed 
    # Write the result to human_response.json also, after the formatting 
    @on(Button.Pressed, "#analyzer-submit")
    def on_analyzer_submit(self) -> None:
        request_id = self.human_request.get("request_id")
        if not request_id:
            return

        suggestions = []

        # Iterate the index, find the values defined in the tables, 
        # then append to the suggestions list which is written back to analyzer result 
        # This depends on the index: Cant sort the displayed order. to be fixed. 
        for index, suggestion in enumerate(self.analyzer_suggestions_data):
            status = self.query_one(f"#status-{index}", Select).value
            feedback = self.query_one(f"#feedback-{index}", TextArea).text
            suggestions.append(
                {
                    "status": str(status),
                    "modules": str(suggestion.get("modules", "Unknown")),  # unchanged 
                    "description": str(suggestion.get("description", "")),  # unchanged 
                    "feedback": feedback,
                }
            )

        write_formatted_human_analyzer_approval(
            self.workspace, request_id, suggestions
        )
        self.query_one("#analyzer-submit", Button).disabled = True

def run_ui(
    workspace: Path | None = None,
    workflow: Callable[..., None] | None = None,
):
    """Run the UI and, when provided, the workflow alongside it."""
    TitleApp(workspace=workspace, workflow=workflow).run()
