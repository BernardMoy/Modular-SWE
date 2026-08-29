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

# sort module keys. 
# module keys bundle the type (new) together because this follows the same convention of implementation
# order: deleted -> new -> changed -> keep 
def _sort_design_modules(name): 
    order = {
        "deleted": 0, 
        "new": 1, 
        "changed": 2, 
        "keep": 3
    }
    for key in order.keys(): 
        if name.startswith(f"({key})"): 
            return order[key] 

    # unrecognised come last 
    return 4 

# data
# lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
# design_data = {"module_1": "Content1 " + lorem, "module_2": "Content2 " + lorem}
# impl_data = {"file_1": "Content1 " + lorem, "package.file_2": "Content2 " + lorem}
analyzer_suggestions_data = [
    {
        "module_name": "hmock_routing",
        "description": "Keep hmock_routing focused on route shape matching by extracting the full behavior expectation check into hmock_conditions or a small matcher function owned by the condition layer. hmock_routing should produce candidate route matches with path parameters and delegate condition evaluation through a narrow boolean API, so route parsing remains independently testable and future condition syntax changes do not require edits in routing.",
        "status": "accepted",
    },
    {
        "module_name": "hmock_template_renderer",
        "description": "Extract block-boundary traversal from hmock_template_renderer into one private helper API, such as collect_block(tokens, start, stop_tags) returning the nested body tokens, stop tag, and next index. Use that helper from both if and range rendering instead of maintaining separate depth-scanning logic in _find_matching_end, _collect_block, and _skip_if_tail. Keep expression evaluation, range variable binding, and output concatenation in hmock_template_renderer so the refactor removes duplicate traversal rules without creating a new renderer abstraction or leaking token internals outside the template package.",
        "status": "unresolved",
    },
]


StageCallback = Callable[[str], None]
SettingsCallback = Callable[[dict[str, Any]], None]
WorkflowRunner = Callable[[StageCallback], None]


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
    analyzer_suggestions = reactive([], init=False)
    # ====================================

    # Register the theme
    def on_mount(self):
        self.theme = "textual-dark"
        self.query_one("#selected-file-content", RichLog).write(
            "No files selected."
        )
        if self.workflow is not None:
            self.call_after_refresh(self._start_workflow)

    CSS_PATH = "ui.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self,
        workspace: Path | None = None,
        workflow: WorkflowRunner | None = None,
    ):
        super().__init__(watch_css=True)
        self.workspace = workspace or Path(
            "agent_workspace"
        )  # workspace is the agent workspace path
        self.workflow = workflow
        self.design_impl_data = self.design_or_impl
        self.analyzer_suggestions_data = analyzer_suggestions_data

    def _start_workflow(self):
        Thread(
            target=self._run_workflow,
            name="modular-workflow",
            daemon=True,
        ).start()

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

    # Setters and getters for reactive state values
    # stage
    def update_stage(self, stage):
        self.call_from_thread(self._set_stage, stage)

    def _set_stage(self, stage):
        self.stage = stage

    def watch_stage(self, stage):
        self.query_one("#stage-label", Label).update(f"Stage: {stage}")

    # settings
    def update_settings(self, settings):
        self.call_from_thread(self._set_settings, settings)

    def _set_settings(self, settings):
        self.settings = settings

    def watch_settings(self, settings):
        self.query_one("#settings-label", Label).update(
            f"Problem: {settings.get("problem_name", "unknown")} (checkpoint {settings.get("checkpoint", 0)}) ({settings.get("problem_type", "unknown")}). Agent: {settings.get("agent", "unknown")}. Model: {settings.get("model", "unknown")}."
        )

    # agent response
    def update_agent_response(self, response: str) -> None:
        self.call_from_thread(self._set_agent_response, response)

    def _set_agent_response(self, response: str) -> None:
        self.agent_response = response

    def watch_agent_response(self, response: str) -> None:
        self.query_one("#agent-response", TextArea).load_text(response)

    # design or impl / dict
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
        for file_name in self.design_impl_data:
            design_list.append(ListItem(Label(file_name)))

    # analyzer suggestions
    def update_analyzer_suggestions(self, value: list[Any]) -> None:
        self.call_from_thread(self._set_analyzer_suggestions, value)

    def _set_analyzer_suggestions(self, value: list[Any]) -> None:
        self.analyzer_suggestions = list(value)

    def watch_analyzer_suggestions(self, value: list[Any]) -> None:
        self.query_one("#analyzer-suggestions", TextArea).load_text(
            json.dumps(value, indent=2, default=str)
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
                    sorted_keys = sorted(self.design_impl_data.keys(), key=lambda x: _sort_design_modules(x))
                    for file_name in sorted_keys:
                        yield ListItem(Label(file_name))

            # The right part
            with Vertical(id="right-content"):

                # Right top: Display the selected file (formatted JSON) or code
                with Vertical(classes="panel") as selected_panel:
                    selected_panel.border_title = "Selected file"
                    yield RichLog(
                        id="selected-file-content",
                        wrap=True,
                        markup=False,
                    )

                # Right bottom: Suggestions or agent output
                with Vertical(classes="panel") as suggestions_panel:
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
                            with Horizontal(classes="suggestion-row"):
                                # Status dropdown
                                statuses = ("unresolved", "accepted", "rejected")
                                selected_status = suggestion.get("status", "unresolved")
                                if selected_status not in statuses:
                                    selected_status = "unresolved"
                                yield Select(
                                    [(status, status) for status in statuses],
                                    value=selected_status,
                                    allow_blank=False,  # default to unresolved
                                    id=f"status-{index}",
                                )

                                yield Label(
                                    str(suggestion.get("module_name", "Unknown"))
                                )
                                yield Label(
                                    str(suggestion.get("description", "Unknown"))
                                )

                                # Multi line user input for feedback
                                yield TextArea(
                                    id=f"feedback-{index}", classes="human-text"
                                )

                    # The submit button: Only available in the human mode
                    # Else, it is disabled
                    with Horizontal(id="submit-button"):
                        yield Button(
                            "Submit", variant="success", id="submit", disabled=False
                        )

        # Footer showing q quit
        yield Footer()

    # Listener only to the design-list (LEFT list) 
    @on(ListView.Selected, "#design-list")
    def on_list_view_selected(self, event: ListView.Selected):
        # Obtain the key selected
        selected_key = str(event.item.query_one(Label).content)

        # Obtain the processed content and set content
        content = self.design_impl_data.get(
            selected_key, "Failed to render content."
        )

        selected_content = self.query_one("#selected-file-content", RichLog)
        selected_content.clear()
        selected_content.write(content)
        selected_content.scroll_home(animate=False, immediate=True)


def run_ui(
    workspace: Path | None = None,
    workflow: WorkflowRunner | None = None,
):
    """Run the UI and, when provided, the workflow alongside it."""
    TitleApp(workspace=workspace, workflow=workflow).run()
