"""
https://textual.textualize.io/guide/design/
"""

from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Callable

from textual.app import App, ComposeResult
from textual.message import Message
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, TextArea, Label, ListItem, ListView
from textual.widgets import Select
from textual import on

# data
lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
design_data = {"module_1": "Content1 " + lorem, "module_2": "Content2 " + lorem}
impl_data = {"file_1": "Content1 " + lorem, "package.file_2": "Content2 " + lorem}
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
WorkflowRunner = Callable[[StageCallback], None]


class StageChanged(Message):
    """A workflow stage update posted from the background thread."""

    def __init__(self, stage: str) -> None:
        super().__init__()
        self.stage = stage


class TitleApp(App[None]):
    # Register the theme
    def on_mount(self) -> None:
        self.theme = "textual-dark"
        if self.workflow is not None:
            self.call_after_refresh(self._start_workflow)

    CSS_PATH = "ui.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self,
        workspace: Path | None = None,
        workflow: WorkflowRunner | None = None,
    ) -> None:
        super().__init__(watch_css=True)
        self.workspace = workspace or Path(
            "agent_workspace"
        )  # workspace is the agent workspace path
        self.workflow = workflow
        self.design_impl_data = design_data
        self.analyzer_suggestions_data = analyzer_suggestions_data

    def _start_workflow(self) -> None:
        Thread(
            target=self._run_workflow,
            name="modular-workflow",
            daemon=True,
        ).start()

    def _run_workflow(self) -> None:
        """Run the blocking workflow outside Textual's UI thread."""
        assert self.workflow is not None
        try:
            self.workflow(self.update_stage)
            self.update_stage("Workflow complete")
        except Exception as error:
            self.update_stage(f"Failed: {error}")
            raise

    def update_stage(self, stage: str) -> None:
        """Post a stage update safely from the workflow worker thread."""
        self.post_message(StageChanged(stage))

    def on_stage_changed(self, message: StageChanged) -> None:
        stage_label = self.query_one("#stage-label", Label)
        stage_label.update(f"Stage: {message.stage}")

    def compose(self) -> ComposeResult:
        # Top part showing the mode and problem
        yield Label("Problem: XXX. Problem type: XXX. Mode: XXX.", id="top-label")

        # the top bar showing time and command palette search
        yield Header(show_clock=True)

        # The rectangle label above showing the current stage in the multi agent pipeline
        with Container(id="stage"):
            yield Label("Stage: Waiting for workflow", id="stage-label")

        with Container(id="main-content"):
            # The left bar:
            # For design: It shows the list of modules (keep, changed, new) in 3 boxes
            # For implementation: It shows
            with Vertical(classes="panel") as files_panel:
                files_panel.border_title = "Modules"
                with ListView(
                    id="design-list", initial_index=None
                ):  # Disable the initial selection highlighting
                    for file_name in self.design_impl_data.keys():
                        yield ListItem(Label(file_name))

            # The right part
            with Vertical(id="right-content"):

                # Right top: Display the selected file (formatted JSON) or code
                with Vertical(classes="panel") as selected_panel:
                    selected_panel.border_title = "Selected file"
                    yield TextArea(
                        "No files selected.",  # default value, to be overridden
                        id="selected-file-content",
                        read_only=True,
                        show_cursor=False,
                        highlight_cursor_line=False,
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

    # Listener only to the design-list
    @on(ListView.Selected, "#design-list")
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Obtain the key selected
        selected_key = str(event.item.query_one(Label).content)

        # Obtain the processed content and set content
        content = str(self.design_impl_data[selected_key])

        selected_content = self.query_one("#selected-file-content", TextArea)
        selected_content.load_text(content)
        selected_content.scroll_home(animate=False, immediate=True)
        selected_content.refresh(layout=True)


def run_ui(
    workspace: Path | None = None,
    workflow: WorkflowRunner | None = None,
) -> None:
    """Run the UI and, when provided, the workflow alongside it."""
    TitleApp(workspace=workspace, workflow=workflow).run()
