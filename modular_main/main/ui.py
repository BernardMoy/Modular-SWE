"""
https://textual.textualize.io/guide/design/
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from threading import Thread
from typing import Callable

import cairosvg
from PIL import Image as PILImage
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
from textual_image.widget import Image as TerminalImage
from typing import Any
from .ui_text_formatters import (
    get_formatted_analyzer_suggestions,
    write_formatted_human_analyzer_approval,
    write_formatted_human_question_response,
)


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
    requirements = reactive({}, init=False)
    deps_graph = reactive({}, init=False) 
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
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+q", "quit_workflow", "Stop workflow and quit"),
    ]

    def __init__(
        self,
        workspace: Path | None = None,
        workflow: Callable[..., None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ):
        super().__init__(watch_css=True)
        self.workspace = workspace or Path(
            "agent_workspace"
        )  # workspace is the agent workspace path
        self.workflow = workflow
        self.on_quit = on_quit
        self.design_impl_data = self.design_or_impl
        self.requirements_data = self.requirements
        self.deps_graph_data = self.deps_graph
        self.analyzer_suggestions_data = self.analyzer_suggestions
        self._analyzer_result_mtime = None
        self._deps_graph_base_image = None
        self._deps_graph_zoom = 1.0
        self._deps_graph_fit_size = None

    def action_quit_workflow(self) -> None:
        """Stop the external agent process, then close the UI."""
        if self.on_quit is not None:
            self.on_quit()
        self.exit()

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
                self.update_requirements,
                self.update_deps_graph,
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

    # requirements
    def update_requirements(self, value: dict[str, Any]) -> None:
        self.call_from_thread(self._set_requirements, value)

    def _set_requirements(self, value: dict[str, Any]) -> None:
        self.requirements = dict(value)

    def watch_requirements(self, value: dict[str, Any]) -> None:
        self.requirements_data = dict(value)
        requirements_list = self.query_one("#requirements-list", ListView)
        requirements_list.clear()
        for file_name in self.requirements_data:
            requirements_list.append(ListItem(Label(file_name)))

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
        design_impl_list = self.query_one("#design-impl-list", ListView)
        design_impl_list.clear()
        sorted_keys = sorted(
            self.design_impl_data,
            key=_sort_design_modules,
        )
        for file_name in sorted_keys:
            design_impl_list.append(ListItem(Label(file_name)))

    # dependency graphs
    def update_deps_graph(self, value: dict[str, Any]) -> None:
        self.call_from_thread(self._set_deps_graph, value)

    def _set_deps_graph(self, value: dict[str, Any]) -> None:
        self.deps_graph = dict(value)

    def watch_deps_graph(self, value: dict[str, Any]) -> None:
        self.deps_graph_data = dict(value)

        graph_list = self.query_one("#deps-graph-list", ListView)
        graph_list.clear()

        for graph_name in self.deps_graph_data:
            graph_list.append(ListItem(Label(graph_name)))

        self._render_deps_graph(self.deps_graph_data.get("Current graph"))

    # Render a dependency graph image from its path
    def _render_deps_graph(self, graph_path: str | Path | None) -> None:
        image_widget = self.query_one("#deps-graph-image", TerminalImage)
        if graph_path is None:
            image_widget.image = None
            self._deps_graph_base_image = None
            return

        try:
            png_data = cairosvg.svg2png(url=str(graph_path))
            image = PILImage.open(BytesIO(png_data)).copy()
        except (OSError, ValueError, cairosvg.CairoError):
            # The workflow may still be writing the SVG.
            return

        self._deps_graph_base_image = image
        self._deps_graph_fit_size = None
        self._apply_deps_graph_zoom()

    def _apply_deps_graph_zoom(self) -> None:
        """Apply the selected zoom while preserving the image aspect ratio."""
        image_widget = self.query_one("#deps-graph-image", TerminalImage)
        if self._deps_graph_base_image is None:
            image_widget.image = None
            return

        base_image = self._deps_graph_base_image
        if self._deps_graph_zoom == 1.0:
            image_widget.styles.width = "auto"
            image_widget.styles.height = "auto"
            image_widget.image = base_image
            if image_widget.size.width and image_widget.size.height:
                self._deps_graph_fit_size = (
                    image_widget.size.width,
                    image_widget.size.height,
                )
            return

        if self._deps_graph_fit_size is None:
            self._deps_graph_fit_size = (
                max(1, image_widget.size.width),
                max(1, image_widget.size.height),
            )

        fit_width, fit_height = self._deps_graph_fit_size
        image_widget.styles.width = max(1, round(fit_width * self._deps_graph_zoom))
        image_widget.styles.height = max(1, round(fit_height * self._deps_graph_zoom))

        width = max(1, round(base_image.width * self._deps_graph_zoom))
        height = max(1, round(base_image.height * self._deps_graph_zoom))
        image_widget.image = base_image.resize(
            (width, height), PILImage.Resampling.LANCZOS
        )

    @on(Button.Pressed, "#deps-graph-zoom-in")
    def on_deps_graph_zoom_in(self) -> None:
        self._deps_graph_zoom = min(self._deps_graph_zoom * 1.25, 4.0)
        self._apply_deps_graph_zoom()

    @on(Button.Pressed, "#deps-graph-zoom-out")
    def on_deps_graph_zoom_out(self) -> None:
        self._deps_graph_zoom = max(self._deps_graph_zoom / 1.25, 0.25)
        self._apply_deps_graph_zoom()

    @on(Button.Pressed, "#deps-graph-zoom-reset")
    def on_deps_graph_zoom_reset(self) -> None:
        self._deps_graph_zoom = 1.0
        self._apply_deps_graph_zoom()


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
            suggestions_panel.display = (
                True  # show analyzer + disable button (Will be enabled later with Q)
            )
            self.query_one("#analyzer-submit", Button).disabled = True
            request_view.display = False  # Hide human
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
                placeholder="Feedback...",
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
            with Vertical(id="left-content"):
                # Left top:
                # For design and impl: Show module names
                with Vertical(id="files-panel", classes="panel") as files_panel:
                    files_panel.border_title = f"Modules ({len(self.design_impl_data)})"
                    with ListView(
                        id="design-impl-list", initial_index=None
                    ):  # Disable the initial selection highlighting

                        # Display the keys sorted: See sort function
                        sorted_keys = sorted(
                            self.design_impl_data.keys(),
                            key=lambda x: _sort_design_modules(x),
                        )
                        for file_name in sorted_keys:
                            yield ListItem(Label(file_name))

                # Left bottom: Deps graph section
                with Vertical(
                    id="deps-graph-panel", classes="panel"
                ) as deps_graph_panel:
                    deps_graph_panel.border_title = f"Dependency graphs"
                    with ListView(
                        id="deps-graph-list", initial_index=None
                    ):  # Disable the initial selection highlighting

                        # Display the keys sorted: See sort function
                        sorted_keys = sorted(
                            self.deps_graph_data.keys(),
                            key=lambda x: _sort_design_modules(x),
                        )

                        for file_name in sorted_keys:
                            yield ListItem(Label(file_name))

                # Left bottom: Requirements document section
                with Vertical(
                    id="requirements-panel", classes="panel"
                ) as requirements_panel:
                    requirements_panel.border_title = f"Requirements document"
                    with ListView(
                        id="requirements-list", initial_index=None
                    ):  # Disable the initial selection highlighting

                        # Display the keys sorted: See sort function
                        sorted_keys = sorted(
                            self.design_impl_data.keys(),
                            key=lambda x: _sort_design_modules(x),
                        )

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
                        auto_scroll=False,
                    )

                # Right top: SVG
                with Vertical(
                    id="deps-graph-preview-panel", classes="panel"
                ) as deps_graph_preview_panel:
                    deps_graph_preview_panel.border_title = "Dependency graph"
                    deps_graph_preview_panel.display = False # Turn off display initially 

                    with Horizontal(id="deps-graph-controls"):
                        yield Button("-", id="deps-graph-zoom-out")
                        yield Button("Reset", id="deps-graph-zoom-reset")
                        yield Button("+", id="deps-graph-zoom-in")
                    yield TerminalImage(id="deps-graph-image")

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
                            disabled=True # disabled initially 
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
                        placeholder="Human response...",
                    )

                    # The submit button for human clarification questions
                    with Horizontal(id="human-submit-button"):
                        yield Button(
                            "Submit",
                            variant="success",
                            id="human-submit",
                            disabled=True 
                        )

        # Footer showing q quit
        yield Footer()

    # The three left-side lists share one selection. Selecting an item in one
    # list clears the selection in the other two.
    @on(ListView.Selected)
    def on_list_view_selected(self, event: ListView.Selected):
        list_ids = ("design-impl-list", "deps-graph-list", "requirements-list")
        selected_list_id = event.list_view.id
        if selected_list_id not in list_ids:
            return

        for list_id in list_ids:
            if list_id != selected_list_id:
                self.query_one(f"#{list_id}", ListView).index = None

    # Display the selected module in the right-side selected-file panel.
    @on(ListView.Selected, "#design-impl-list")
    def on_design_list_selected(self, event: ListView.Selected):
        # Obtain the key selected
        selected_key = str(event.item.query_one(Label).content)

        selected_panel = self.query_one("#selected-file-panel", Vertical)
        selected_panel.border_title = selected_key

        # Obtain the processed content and set content
        content = self.design_impl_data.get(selected_key, "Failed to render content.")

        selected_content = self.query_one("#selected-file-content", RichLog)
        selected_content.clear()
        selected_content.write(content, scroll_end=False)
        selected_content.scroll_home(animate=False, immediate=True)

        # Turn on display for the selected file and turn off for deps graph 
        self.query_one("#selected-file-panel", Vertical).display = True 
        self.query_one("#deps-graph-preview-panel", Vertical).display = False 

    # Display the selected requirements document.
    @on(ListView.Selected, "#requirements-list")
    def on_requirements_list_selected(self, event: ListView.Selected):
        selected_key = str(event.item.query_one(Label).content)
        selected_panel = self.query_one("#selected-file-panel", Vertical)
        selected_panel.border_title = selected_key

        selected_content = self.query_one("#selected-file-content", RichLog)
        selected_content.clear()
        selected_content.write(
            self.requirements_data.get(selected_key, "Failed to render content."),
            scroll_end=False,
        )
        selected_content.scroll_home(animate=False, immediate=True)

        # Turn on display for the selected file and turn off for deps graph 
        self.query_one("#selected-file-panel", Vertical).display = True 
        self.query_one("#deps-graph-preview-panel", Vertical).display = False 


    # Display the selected dependency graph.
    @on(ListView.Selected, "#deps-graph-list")
    def on_deps_graph_list_selected(self, event: ListView.Selected):
        selected_label = str(event.item.query_one(Label).content)

        # Obtain the graph path (svg) from the selected label 
        if selected_label:
            graph_path = self.deps_graph_data.get(selected_label)
            self._render_deps_graph(graph_path) 

            # Turn on display for deps grpah and turn off for selected file 
            self.query_one("#selected-file-panel", Vertical).display = False
            self.query_one("#deps-graph-preview-panel", Vertical).display = True
            

    # Listener when the human submit (for clarification questions) is pressed
    # Write the result to human_response.json which gets captured inside run_agent.py
    @on(Button.Pressed, "#human-submit")
    def on_human_submit(self) -> None:
        request_id = self.human_request.get("request_id")
        if not request_id:
            return

        # Obtain the response text
        response = self.query_one("#human-response", TextArea).text

        write_formatted_human_question_response(self.workspace, request_id, response)

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

        # Obtain the additional feedback field
        additional_feedback = self.query_one(
            "#analyzer-additional-feedback", TextArea
        ).text

        write_formatted_human_analyzer_approval(
            self.workspace,
            request_id,
            suggestions,
            additional_feedback,
        )

        # Clear the analyzer additional feedback + feedback-{index} text fields
        self.query_one("#analyzer-additional-feedback", TextArea).load_text("")
        for index in range(len(self.analyzer_suggestions_data)):
            feedback = self.query_one(f"#feedback-{index}", TextArea)
            feedback.load_text("")

        self.query_one("#analyzer-submit", Button).disabled = True


def run_ui(
    workspace: Path | None = None,
    workflow: Callable[..., None] | None = None,
    on_quit: Callable[[], None] | None = None,
):
    """Run the UI and, when provided, the workflow alongside it."""
    TitleApp(workspace=workspace, workflow=workflow, on_quit=on_quit).run()
