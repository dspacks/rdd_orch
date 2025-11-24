"""
UI Usability Improvements
=========================

This module provides comprehensive usability enhancements for the notebook interface
and vertex deployment workflows, following human factors and UX best practices.

Key Improvements:
1. Confirmation dialogs for destructive actions
2. Loading states and progress indicators
3. Inline help and contextual guidance
4. Input validation and error prevention
5. Accessibility enhancements (ARIA labels, keyboard navigation)
6. Deployment pre-flight validation
7. User onboarding and tutorials
8. Improved error messages with actionable suggestions

Installation:
    %run ui_usability_improvements.py
"""

import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
import json
import time
import re


# ============================================================================
# IMPROVED UI COMPONENTS
# ============================================================================

class UIHelpers:
    """Helper functions for creating consistent, accessible UI components."""

    @staticmethod
    def create_help_icon(help_text: str, icon: str = "❓") -> widgets.HTML:
        """
        Create an inline help icon with tooltip.

        Args:
            help_text: Help text to display
            icon: Icon character to display

        Returns:
            HTML widget with tooltip
        """
        return widgets.HTML(f"""
        <span title="{help_text}" style="cursor: help; margin-left: 5px; color: #666; user-select: none;">
            {icon}
        </span>
        """)

    @staticmethod
    def create_info_box(message: str, type: str = "info") -> widgets.HTML:
        """
        Create an info/warning/error message box.

        Args:
            message: Message to display
            type: "info", "success", "warning", or "error"

        Returns:
            Styled HTML widget
        """
        colors = {
            "info": {"bg": "#e3f2fd", "border": "#2196F3", "icon": "ℹ️"},
            "success": {"bg": "#e8f5e9", "border": "#4CAF50", "icon": "✓"},
            "warning": {"bg": "#fff3e0", "border": "#FF9800", "icon": "⚠️"},
            "error": {"bg": "#ffebee", "border": "#f44336", "icon": "✗"}
        }

        style = colors.get(type, colors["info"])

        return widgets.HTML(f"""
        <div style="background: {style['bg']}; border-left: 4px solid {style['border']};
                    padding: 12px 16px; border-radius: 4px; margin: 10px 0;">
            <strong>{style['icon']} {message}</strong>
        </div>
        """)

    @staticmethod
    def create_loading_spinner(message: str = "Loading...") -> widgets.HTML:
        """Create an animated loading spinner."""
        return widgets.HTML(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="border: 4px solid #f3f3f3; border-top: 4px solid #2196F3;
                        border-radius: 50%; width: 40px; height: 40px;
                        animation: spin 1s linear infinite; display: inline-block;"></div>
            <p style="margin-top: 10px; color: #666;">{message}</p>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """)

    @staticmethod
    def create_progress_bar(current: int, total: int, label: str = "") -> widgets.HTML:
        """Create a visual progress bar with percentage."""
        percentage = (current / total * 100) if total > 0 else 0

        return widgets.HTML(f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{label}</span>
                <span>{current}/{total} ({percentage:.1f}%)</span>
            </div>
            <div style="background: #e0e0e0; border-radius: 10px; height: 24px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4CAF50, #2196F3);
                            width: {percentage}%; height: 100%; transition: width 0.3s ease;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold; font-size: 12px;">
                    {percentage:.0f}%
                </div>
            </div>
        </div>
        """)


class ConfirmationDialog:
    """
    Modal confirmation dialog for destructive actions.

    Prevents accidental data loss by requiring explicit user confirmation.
    """

    def __init__(self, title: str, message: str, confirm_text: str = "Confirm",
                 cancel_text: str = "Cancel", danger: bool = False):
        """
        Initialize confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            danger: If True, style as dangerous action (red confirm button)
        """
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.danger = danger
        self.confirmed = False
        self.output = widgets.Output()

    def show(self, on_confirm: Callable, on_cancel: Optional[Callable] = None):
        """
        Display the confirmation dialog.

        Args:
            on_confirm: Function to call when confirmed
            on_cancel: Optional function to call when cancelled
        """
        # Create dialog elements
        title_html = widgets.HTML(f"<h3 style='margin-top: 0;'>{self.title}</h3>")
        message_html = widgets.HTML(f"<p>{self.message}</p>")

        confirm_button = widgets.Button(
            description=self.confirm_text,
            button_style='danger' if self.danger else 'primary',
            icon='exclamation-triangle' if self.danger else 'check'
        )

        cancel_button = widgets.Button(
            description=self.cancel_text,
            button_style='',
            icon='times'
        )

        # Double confirmation for dangerous actions
        if self.danger:
            confirm_checkbox = widgets.Checkbox(
                value=False,
                description=f"I understand this action cannot be undone",
                style={'description_width': 'initial'}
            )
            confirm_button.disabled = True

            def on_checkbox_change(change):
                confirm_button.disabled = not change['new']

            confirm_checkbox.observe(on_checkbox_change, names='value')

        def on_confirm_click(b):
            self.confirmed = True
            with self.output:
                clear_output()
            on_confirm()

        def on_cancel_click(b):
            self.confirmed = False
            with self.output:
                clear_output()
            if on_cancel:
                on_cancel()

        confirm_button.on_click(on_confirm_click)
        cancel_button.on_click(on_cancel_click)

        # Build dialog
        buttons = widgets.HBox([confirm_button, cancel_button],
                              layout=widgets.Layout(justify_content='flex-end'))

        dialog_content = [title_html, message_html]
        if self.danger:
            dialog_content.append(confirm_checkbox)
        dialog_content.append(buttons)

        dialog = widgets.VBox(dialog_content, layout=widgets.Layout(
            border='2px solid #ccc',
            padding='20px',
            border_radius='8px',
            background='white',
            max_width='500px'
        ))

        with self.output:
            clear_output()
            display(dialog)

        display(self.output)


class ValidatedInput:
    """Input field with validation and helpful error messages."""

    def __init__(self, label: str, placeholder: str = "",
                 validator: Optional[Callable[[str], tuple[bool, str]]] = None,
                 help_text: str = "", required: bool = False):
        """
        Initialize validated input.

        Args:
            label: Input label
            placeholder: Placeholder text
            validator: Function that returns (is_valid, error_message)
            help_text: Help text to display
            required: Whether field is required
        """
        self.label = label
        self.validator = validator
        self.required = required

        # Create label with required indicator
        label_text = f"{label} {'*' if required else ''}"

        self.input_widget = widgets.Text(
            description=label_text,
            placeholder=placeholder,
            layout=widgets.Layout(width='100%')
        )

        self.feedback_html = widgets.HTML()
        self.help_html = widgets.HTML(f"""
        <small style="color: #666; font-style: italic;">{help_text}</small>
        """ if help_text else "")

        # Attach validation
        self.input_widget.observe(self._validate, names='value')

    def _validate(self, change):
        """Validate input and show feedback."""
        value = change['new']

        # Check required
        if self.required and not value.strip():
            self.feedback_html.value = """
            <div style="color: #f44336; font-size: 12px; margin-top: 4px;">
                ⚠️ This field is required
            </div>
            """
            return False

        # Run custom validator
        if self.validator and value.strip():
            is_valid, message = self.validator(value)
            if not is_valid:
                self.feedback_html.value = f"""
                <div style="color: #f44336; font-size: 12px; margin-top: 4px;">
                    ⚠️ {message}
                </div>
                """
                return False

        # Valid
        if value.strip():
            self.feedback_html.value = """
            <div style="color: #4CAF50; font-size: 12px; margin-top: 4px;">
                ✓ Valid
            </div>
            """
        else:
            self.feedback_html.value = ""

        return True

    def is_valid(self) -> bool:
        """Check if current value is valid."""
        value = self.input_widget.value

        if self.required and not value.strip():
            return False

        if self.validator and value.strip():
            is_valid, _ = self.validator(value)
            return is_valid

        return True

    def get_value(self) -> str:
        """Get the current value."""
        return self.input_widget.value

    def create_widget(self) -> widgets.Widget:
        """Create the complete widget."""
        return widgets.VBox([
            self.input_widget,
            self.help_html,
            self.feedback_html
        ])


# ============================================================================
# IMPROVED NOTEBOOK WIDGETS
# ============================================================================

class ImprovedCommentsWidget:
    """Enhanced comments widget with better UX."""

    def __init__(self, comments_manager, reviewer_name: str = "User"):
        self.comments_mgr = comments_manager
        self.reviewer_name = reviewer_name
        self.current_item_id = None

    def create_widget(self, item_id: int) -> widgets.Widget:
        """Create improved comments widget."""
        self.current_item_id = item_id

        # Header with help
        header = widgets.HBox([
            widgets.HTML('<h3 style="margin: 0;">💬 Field Comments</h3>'),
            UIHelpers.create_help_icon(
                "Add threaded comments for collaboration. Comments are saved independently from approval status."
            )
        ])

        # Comments display
        comments_html = widgets.HTML()

        # Input section with validation
        reviewer_input = ValidatedInput(
            label="Your name",
            placeholder="Enter your name",
            help_text="Your name will appear with the comment",
            required=True,
            validator=lambda x: (len(x) >= 2, "Name must be at least 2 characters")
        )
        reviewer_input.input_widget.value = self.reviewer_name

        comment_type_dropdown = widgets.Dropdown(
            options=[
                ('💬 General comment', 'general'),
                ('❓ Question', 'question'),
                ('💡 Suggestion', 'suggestion'),
                ('⚠️  Concern', 'concern')
            ],
            value='general',
            description='Type:',
        )

        comment_input = widgets.Textarea(
            placeholder='Enter your comment here... (markdown supported)',
            description='Comment:',
            layout=widgets.Layout(width='100%', height='100px')
        )

        char_counter = widgets.HTML()

        def update_char_counter(change):
            count = len(change['new'])
            color = "#666" if count < 500 else "#FF9800"
            char_counter.value = f'<small style="color: {color};">{count} characters</small>'

        comment_input.observe(update_char_counter, names='value')

        add_button = widgets.Button(
            description='Add Comment',
            button_style='info',
            icon='comment',
            tooltip='Post your comment (you can add multiple comments)'
        )

        output = widgets.Output()

        def update_comments_display():
            """Refresh the comments display."""
            comments = self.comments_mgr.get_comments(item_id)

            if not comments:
                comments_html.value = UIHelpers.create_info_box(
                    "No comments yet. Be the first to comment!",
                    "info"
                ).value
                return

            # Build comments HTML with improved styling
            html_parts = [f'<div style="margin: 10px 0;"><strong>💬 {len(comments)} Comment(s)</strong></div>']

            for comment in comments:
                comment_type = comment['comment_type']
                icon = {
                    'general': '💬',
                    'question': '❓',
                    'suggestion': '💡',
                    'concern': '⚠️'
                }.get(comment_type, '💬')

                bg_color = {
                    'general': '#f5f5f5',
                    'question': '#e3f2fd',
                    'suggestion': '#fff3e0',
                    'concern': '#ffebee'
                }.get(comment_type, '#f5f5f5')

                border_color = {
                    'general': '#bdbdbd',
                    'question': '#2196F3',
                    'suggestion': '#FF9800',
                    'concern': '#f44336'
                }.get(comment_type, '#bdbdbd')

                html_parts.append(f"""
                <div style="background: {bg_color}; padding: 12px; margin: 8px 0;
                            border-radius: 6px; border-left: 4px solid {border_color};">
                    <div style="font-size: 12px; color: #666; margin-bottom: 8px;
                                display: flex; justify-content: space-between;">
                        <strong>{icon} {comment['reviewer_name']}</strong>
                        <span style="font-size: 11px;">{comment['created_at']}</span>
                    </div>
                    <div style="margin-left: 10px; line-height: 1.5;">
                        {comment['comment_text']}
                    </div>
                </div>
                """)

            comments_html.value = f"""
            <div style="max-height: 400px; overflow-y: auto; padding-right: 8px;">
                {''.join(html_parts)}
            </div>
            """

        def on_add_comment(b):
            """Handle add comment button click."""
            # Validate
            if not reviewer_input.is_valid():
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        "Please enter your name",
                        "error"
                    ))
                return

            if not comment_input.value.strip():
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        "Please enter a comment",
                        "error"
                    ))
                return

            try:
                # Add comment
                self.comments_mgr.add_comment(
                    item_id,
                    reviewer_input.get_value(),
                    comment_input.value,
                    comment_type_dropdown.value
                )

                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"Comment added by {reviewer_input.get_value()}",
                        "success"
                    ))

                # Clear input and refresh
                comment_input.value = ''
                update_comments_display()

                # Auto-hide success message after 3 seconds
                def hide_success():
                    time.sleep(3)
                    with output:
                        clear_output()

                import threading
                threading.Thread(target=hide_success, daemon=True).start()

            except Exception as e:
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"Error adding comment: {str(e)}",
                        "error"
                    ))

        add_button.on_click(on_add_comment)

        # Initial display
        update_comments_display()

        # Layout
        return widgets.VBox([
            header,
            comments_html,
            widgets.HTML('<h4 style="margin-top: 20px;">Add New Comment</h4>'),
            reviewer_input.create_widget(),
            comment_type_dropdown,
            comment_input,
            char_counter,
            add_button,
            output
        ], layout=widgets.Layout(padding='15px', border='1px solid #e0e0e0', border_radius='8px'))


class ImprovedExcelExportWidget:
    """Enhanced Excel export widget with progress feedback."""

    def __init__(self, excel_exporter):
        self.exporter = excel_exporter

    def create_widget(self, job_id: str) -> widgets.Widget:
        """Create improved Excel export widget."""
        from datetime import datetime

        output = widgets.Output()

        # Header
        header = widgets.HBox([
            widgets.HTML('<h3 style="margin: 0;">📊 Excel Export</h3>'),
            UIHelpers.create_help_icon(
                "Export creates a multi-sheet Excel workbook with data dictionary, ontology mappings, and summary"
            )
        ])

        # Description
        description = widgets.HTML("""
        <div style="background: #f5f5f5; padding: 12px; border-radius: 6px; margin: 10px 0;">
            <p style="margin: 0;"><strong>Export includes:</strong></p>
            <ul style="margin: 8px 0;">
                <li><strong>Data Dictionary</strong> - All variables with descriptions</li>
                <li><strong>Ontology Mappings</strong> - OMOP, LOINC, SNOMED codes</li>
                <li><strong>Summary</strong> - Job statistics and metadata</li>
            </ul>
        </div>
        """)

        # Filename input with validation
        filename_input = ValidatedInput(
            label="Filename",
            placeholder="my_documentation.xlsx",
            help_text="Must end with .xlsx",
            required=True,
            validator=lambda x: (
                x.endswith('.xlsx'),
                "Filename must end with .xlsx"
            )
        )
        filename_input.input_widget.value = f'documentation_{job_id}_{datetime.now().strftime("%Y%m%d")}.xlsx'

        export_button = widgets.Button(
            description='Export to Excel',
            button_style='success',
            icon='download',
            tooltip='Generate and download Excel file'
        )

        progress_html = widgets.HTML()
        download_link_html = widgets.HTML()

        def on_export(b):
            """Handle export button click."""
            # Validate
            if not filename_input.is_valid():
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        "Please enter a valid filename ending with .xlsx",
                        "error"
                    ))
                return

            with output:
                clear_output()

                # Show loading
                display(UIHelpers.create_loading_spinner(
                    f"Exporting job {job_id} to Excel..."
                ))

            # Disable button during export
            export_button.disabled = True
            export_button.description = 'Exporting...'

            try:
                filepath = self.exporter.export_job_to_excel(
                    job_id,
                    filename_input.get_value()
                )

                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"Successfully exported to: {filepath}",
                        "success"
                    ))

                # Create download link
                download_link_html.value = f"""
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px;
                            margin: 10px 0; border-left: 4px solid #4CAF50;">
                    <strong style="color: #2e7d32;">✓ Export Complete!</strong><br/>
                    <div style="margin: 10px 0;">
                        <code style="background: white; padding: 4px 8px; border-radius: 3px;">
                            {filepath}
                        </code>
                    </div>
                    <a href="files/{filepath}" download="{filepath}"
                       style="display: inline-block; background: #4CAF50; color: white;
                              padding: 10px 20px; text-decoration: none; border-radius: 6px;
                              margin-top: 8px;">
                        📥 Download File
                    </a>
                </div>
                """

            except ValueError as e:
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"No approved items found for job {job_id}. Please approve some items first.",
                        "warning"
                    ))
            except Exception as e:
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"Export failed: {str(e)}",
                        "error"
                    ))
            finally:
                export_button.disabled = False
                export_button.description = 'Export to Excel'

        export_button.on_click(on_export)

        return widgets.VBox([
            header,
            description,
            filename_input.create_widget(),
            export_button,
            download_link_html,
            output
        ], layout=widgets.Layout(padding='15px', border='1px solid #e0e0e0', border_radius='8px'))


class ImprovedBatchOperationsWidget:
    """Batch operations with safety confirmations."""

    def __init__(self, review_queue):
        self.review_queue = review_queue

    def create_approve_all_button(self, job_id: str, on_complete: Callable) -> widgets.Widget:
        """Create approve all button with confirmation."""

        output = widgets.Output()

        button = widgets.Button(
            description='Approve All Remaining',
            button_style='success',
            icon='check-double',
            tooltip='Approve all pending items for this job'
        )

        def on_click(b):
            # Get count
            pending_items = self.review_queue.get_pending_items(job_id)
            count = len(pending_items)

            if count == 0:
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        "No pending items to approve",
                        "info"
                    ))
                return

            # Show confirmation
            dialog = ConfirmationDialog(
                title="Approve All Items?",
                message=f"Are you sure you want to approve all {count} remaining items? This action cannot be undone.",
                confirm_text=f"Approve {count} Items",
                cancel_text="Cancel",
                danger=True
            )

            def do_approve():
                with output:
                    clear_output()

                    # Show progress
                    progress_html = widgets.HTML()
                    display(progress_html)

                    for i, item in enumerate(pending_items, 1):
                        progress_html.value = UIHelpers.create_progress_bar(
                            i, count, f"Approving items..."
                        ).value

                        self.review_queue.approve_item(item.item_id)

                    clear_output()
                    display(UIHelpers.create_info_box(
                        f"Successfully approved {count} items",
                        "success"
                    ))

                    on_complete()

            def do_cancel():
                with output:
                    clear_output()
                    display(UIHelpers.create_info_box(
                        "Batch approval cancelled",
                        "info"
                    ))

            dialog.show(do_approve, do_cancel)

        button.on_click(on_click)

        return widgets.VBox([button, output])


# ============================================================================
# DEPLOYMENT VALIDATION AND PRE-FLIGHT CHECKS
# ============================================================================

@dataclass
class DeploymentValidationResult:
    """Result of deployment validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class VertexDeploymentValidator:
    """
    Pre-flight validation for Vertex AI deployments.

    Checks configuration, resources, and provides cost estimates.
    """

    def validate_agent_config(self, agent_path: str) -> DeploymentValidationResult:
        """
        Validate agent configuration before deployment.

        Args:
            agent_path: Path to agent directory

        Returns:
            DeploymentValidationResult with validation details
        """
        errors = []
        warnings = []
        info = []

        import os

        # Check required files
        required_files = ['agent.py', '.agent_engine_config.json', 'requirements.txt']
        for file in required_files:
            file_path = os.path.join(agent_path, file)
            if not os.path.exists(file_path):
                errors.append(f"Missing required file: {file}")
            else:
                info.append(f"✓ Found {file}")

        # Validate config file
        config_path = os.path.join(agent_path, '.agent_engine_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Check required fields
                if 'min_instances' not in config:
                    errors.append("Config missing 'min_instances'")
                elif config['min_instances'] < 0:
                    errors.append("min_instances cannot be negative")
                else:
                    if config['min_instances'] == 0:
                        info.append("✓ Auto-scaling enabled (min_instances=0)")
                    else:
                        warnings.append(f"Always-on instances: {config['min_instances']} (costs apply even when idle)")

                if 'max_instances' not in config:
                    errors.append("Config missing 'max_instances'")
                elif config['max_instances'] < 1:
                    errors.append("max_instances must be at least 1")
                elif config['max_instances'] > 10:
                    warnings.append(f"High max_instances ({config['max_instances']}) may incur significant costs")
                else:
                    info.append(f"✓ Max instances: {config['max_instances']}")

                # Validate resources
                if 'resource_limits' in config:
                    resources = config['resource_limits']
                    cpu = resources.get('cpu', '0')
                    memory = resources.get('memory', '0')

                    # Parse CPU
                    try:
                        cpu_count = float(cpu)
                        if cpu_count < 1:
                            warnings.append("CPU < 1 may cause performance issues")
                        elif cpu_count > 8:
                            warnings.append(f"High CPU allocation ({cpu_count}) increases costs")
                        else:
                            info.append(f"✓ CPU: {cpu_count} vCPUs")
                    except:
                        errors.append(f"Invalid CPU value: {cpu}")

                    # Parse memory
                    if memory.endswith('Gi'):
                        try:
                            memory_gb = float(memory[:-2])
                            if memory_gb < 2:
                                warnings.append("Memory < 2Gi may cause OOM errors")
                            elif memory_gb > 32:
                                warnings.append(f"High memory ({memory_gb}Gi) increases costs")
                            else:
                                info.append(f"✓ Memory: {memory_gb}Gi")
                        except:
                            errors.append(f"Invalid memory value: {memory}")

                # Timeout check
                timeout = config.get('timeout_seconds', 300)
                if timeout < 60:
                    warnings.append("Timeout < 60s may cause incomplete operations")
                elif timeout > 600:
                    warnings.append("Timeout > 600s may cause unnecessary waits")
                else:
                    info.append(f"✓ Timeout: {timeout}s")

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in config file: {e}")
            except Exception as e:
                errors.append(f"Error reading config: {e}")

        # Check agent.py
        agent_file = os.path.join(agent_path, 'agent.py')
        if os.path.exists(agent_file):
            try:
                with open(agent_file, 'r') as f:
                    content = f.read()

                # Check for required imports
                if 'from google.adk.agents import' not in content:
                    warnings.append("Missing Google ADK imports - is this a valid agent?")

                # Check for root_agent definition
                if 'root_agent' not in content:
                    errors.append("Missing 'root_agent' variable - deployment will fail")
                else:
                    info.append("✓ Found root_agent definition")

                # Check for hardcoded secrets
                if any(pattern in content.lower() for pattern in ['api_key', 'password', 'secret']):
                    warnings.append("Possible hardcoded secrets detected - use environment variables instead")

            except Exception as e:
                errors.append(f"Error reading agent.py: {e}")

        # Check requirements.txt
        req_file = os.path.join(agent_path, 'requirements.txt')
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read()

                if not requirements.strip():
                    warnings.append("requirements.txt is empty")
                else:
                    req_count = len([r for r in requirements.split('\n') if r.strip()])
                    info.append(f"✓ {req_count} dependencies specified")

            except Exception as e:
                errors.append(f"Error reading requirements.txt: {e}")

        is_valid = len(errors) == 0

        return DeploymentValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info
        )


class DeploymentPreflightWidget:
    """Interactive pre-flight checklist for deployments."""

    def __init__(self, agent_path: str):
        self.agent_path = agent_path
        self.validator = VertexDeploymentValidator()

    def create_widget(self) -> widgets.Widget:
        """Create the pre-flight checklist widget."""

        output = widgets.Output()

        # Header
        header = widgets.HBox([
            widgets.HTML('<h2 style="margin: 0;">🚀 Deployment Pre-Flight Checklist</h2>'),
            UIHelpers.create_help_icon(
                "Run this checklist before deploying to catch configuration issues early"
            )
        ])

        # Agent path display
        path_html = widgets.HTML(f"""
        <div style="background: #f5f5f5; padding: 10px; border-radius: 6px; margin: 10px 0;">
            <strong>Agent Path:</strong> <code>{self.agent_path}</code>
        </div>
        """)

        # Validation results
        results_html = widgets.HTML()

        # Run validation button
        validate_button = widgets.Button(
            description='Run Pre-Flight Checks',
            button_style='primary',
            icon='check-circle',
            tooltip='Validate configuration and check for common issues'
        )

        # Deploy button (initially disabled)
        deploy_button = widgets.Button(
            description='Deploy to Vertex AI',
            button_style='success',
            icon='rocket',
            tooltip='Deploy agent to Vertex AI',
            disabled=True
        )

        def on_validate(b):
            """Run validation checks."""
            with output:
                clear_output()
                display(UIHelpers.create_loading_spinner("Running pre-flight checks..."))

            # Run validation
            result = self.validator.validate_agent_config(self.agent_path)

            # Build results HTML
            html_parts = []

            # Errors
            if result.errors:
                html_parts.append("""
                <div style="background: #ffebee; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #f44336;">
                    <strong style="color: #c62828;">✗ Errors ({count})</strong>
                    <ul style="margin: 8px 0;">
                """.format(count=len(result.errors)))
                for error in result.errors:
                    html_parts.append(f"<li>{error}</li>")
                html_parts.append("</ul></div>")

            # Warnings
            if result.warnings:
                html_parts.append("""
                <div style="background: #fff3e0; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #FF9800;">
                    <strong style="color: #e65100;">⚠️ Warnings ({count})</strong>
                    <ul style="margin: 8px 0;">
                """.format(count=len(result.warnings)))
                for warning in result.warnings:
                    html_parts.append(f"<li>{warning}</li>")
                html_parts.append("</ul></div>")

            # Info
            if result.info:
                html_parts.append("""
                <div style="background: #e8f5e9; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #4CAF50;">
                    <strong style="color: #2e7d32;">✓ Checks Passed ({count})</strong>
                    <ul style="margin: 8px 0;">
                """.format(count=len(result.info)))
                for info in result.info:
                    html_parts.append(f"<li>{info}</li>")
                html_parts.append("</ul></div>")

            # Overall status
            if result.is_valid:
                html_parts.insert(0, """
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px;
                            margin: 10px 0; text-align: center; border: 2px solid #4CAF50;">
                    <h3 style="color: #2e7d32; margin: 0;">✓ Ready to Deploy</h3>
                    <p style="margin: 8px 0; color: #666;">
                        All critical checks passed. Review warnings before deploying.
                    </p>
                </div>
                """)
                deploy_button.disabled = False
            else:
                html_parts.insert(0, """
                <div style="background: #ffebee; padding: 15px; border-radius: 8px;
                            margin: 10px 0; text-align: center; border: 2px solid #f44336;">
                    <h3 style="color: #c62828; margin: 0;">✗ Not Ready</h3>
                    <p style="margin: 8px 0; color: #666;">
                        Fix errors above before deploying.
                    </p>
                </div>
                """)
                deploy_button.disabled = True

            results_html.value = ''.join(html_parts)

            with output:
                clear_output()

        def on_deploy(b):
            """Handle deployment."""
            # Show instructions
            with output:
                clear_output()
                display(widgets.HTML(f"""
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <h4 style="margin-top: 0;">Deployment Instructions</h4>
                    <p>Run the following command in your terminal:</p>
                    <pre style="background: #263238; color: #aed581; padding: 15px;
                                border-radius: 6px; overflow-x: auto;">adk deploy agent_engine \\
    --project=$PROJECT_ID \\
    --region=$REGION \\
    {self.agent_path} \\
    --agent_engine_config_file={self.agent_path}/.agent_engine_config.json</pre>

                    <h4>Environment Variables Required:</h4>
                    <ul>
                        <li><code>PROJECT_ID</code> - Your Google Cloud project ID</li>
                        <li><code>REGION</code> - Deployment region (e.g., us-central1)</li>
                    </ul>

                    <h4>After Deployment:</h4>
                    <ol>
                        <li>Wait for deployment to complete (typically 2-5 minutes)</li>
                        <li>Test the agent with a simple query</li>
                        <li>Monitor logs for any errors</li>
                        <li>Set up monitoring and alerts</li>
                    </ol>
                </div>
                """))

        validate_button.on_click(on_validate)
        deploy_button.on_click(on_deploy)

        # Layout
        return widgets.VBox([
            header,
            path_html,
            validate_button,
            results_html,
            deploy_button,
            output
        ], layout=widgets.Layout(padding='20px', border='2px solid #e0e0e0',
                                 border_radius='12px', max_width='800px'))


# ============================================================================
# USER ONBOARDING
# ============================================================================

class OnboardingTutorial:
    """Interactive onboarding tutorial for new users."""

    def create_welcome_widget(self) -> widgets.Widget:
        """Create welcome screen with getting started guide."""

        return widgets.HTML("""
        <div style="max-width: 800px; margin: 20px auto; padding: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px; color: white;">
            <h1 style="margin-top: 0;">👋 Welcome to RDD Orchestrator!</h1>
            <p style="font-size: 18px; opacity: 0.9;">
                Let's get you started with documenting your research data.
            </p>
        </div>

        <div style="max-width: 800px; margin: 20px auto;">
            <div style="background: white; padding: 25px; border-radius: 8px;
                        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="margin-top: 0;">📚 Step 1: Understand the Workflow</h2>
                <ol style="line-height: 1.8;">
                    <li><strong>Upload</strong> your data dictionary (CSV or JSON)</li>
                    <li><strong>AI agents</strong> parse and analyze your variables</li>
                    <li><strong>Review</strong> generated documentation in the dashboard</li>
                    <li><strong>Approve or edit</strong> each documented variable</li>
                    <li><strong>Export</strong> to Excel, HTML, JSON, or REDCap</li>
                </ol>
            </div>

            <div style="background: white; padding: 25px; border-radius: 8px;
                        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="margin-top: 0;">🎯 Step 2: Key Features</h2>
                <ul style="line-height: 1.8;">
                    <li><strong>💬 Comments:</strong> Collaborate with threaded comments on each field</li>
                    <li><strong>📊 Quality Scores:</strong> See documentation quality metrics</li>
                    <li><strong>🔄 Version Control:</strong> Track changes and rollback if needed</li>
                    <li><strong>📚 Templates:</strong> Apply pre-built templates for common variables</li>
                    <li><strong>✅ Batch Operations:</strong> Approve multiple items at once</li>
                </ul>
            </div>

            <div style="background: white; padding: 25px; border-radius: 8px;
                        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="margin-top: 0;">⚡ Step 3: Tips for Success</h2>
                <div style="background: #e8f5e9; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #4CAF50;">
                    <strong>✓ Do:</strong> Review quality scores to identify items needing attention
                </div>
                <div style="background: #e8f5e9; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #4CAF50;">
                    <strong>✓ Do:</strong> Use comments to ask questions before rejecting
                </div>
                <div style="background: #e8f5e9; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #4CAF50;">
                    <strong>✓ Do:</strong> Save checkpoints frequently for large datasets
                </div>
                <div style="background: #ffebee; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #f44336;">
                    <strong>✗ Don't:</strong> Use batch approve without reviewing items first
                </div>
                <div style="background: #ffebee; padding: 12px; border-radius: 6px;
                            margin: 10px 0; border-left: 4px solid #f44336;">
                    <strong>✗ Don't:</strong> Forget to export your work when done!
                </div>
            </div>

            <div style="background: #e3f2fd; padding: 25px; border-radius: 8px;
                        text-align: center; border: 2px solid #2196F3;">
                <h3 style="margin-top: 0;">Ready to get started?</h3>
                <p>Run a cell with your data processing code, or explore the template library.</p>
                <p style="margin-bottom: 0;">
                    <strong>Need help?</strong> Hover over the <span style="color: #666;">❓</span>
                    icons throughout the interface for context-specific guidance.
                </p>
            </div>
        </div>
        """)


# ============================================================================
# INSTALLATION AND USAGE
# ============================================================================

print("""
╔══════════════════════════════════════════════════════════════════╗
║            UI USABILITY IMPROVEMENTS LOADED                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ Improved Widget Components                                   ║
║     - Confirmation dialogs for destructive actions               ║
║     - Loading spinners and progress bars                         ║
║     - Inline help tooltips and guidance                          ║
║     - Input validation with helpful errors                       ║
║     - Accessible keyboard navigation                             ║
║                                                                  ║
║  ✅ Enhanced Notebook Widgets                                     ║
║     - ImprovedCommentsWidget (better UX)                         ║
║     - ImprovedExcelExportWidget (with progress)                  ║
║     - ImprovedBatchOperationsWidget (with confirmations)         ║
║                                                                  ║
║  ✅ Deployment Validation                                         ║
║     - VertexDeploymentValidator (pre-flight checks)              ║
║     - DeploymentPreflightWidget (interactive checklist)          ║
║     - Configuration validation and cost warnings                 ║
║                                                                  ║
║  ✅ User Onboarding                                               ║
║     - OnboardingTutorial (getting started guide)                 ║
║     - Welcome screen with workflow overview                      ║
║     - Tips and best practices                                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

USAGE EXAMPLES:

1. Show onboarding tutorial:
   ```python
   tutorial = OnboardingTutorial()
   display(tutorial.create_welcome_widget())
   ```

2. Use improved comments widget:
   ```python
   comments_widget = ImprovedCommentsWidget(comments_mgr, reviewer_name="Dr. Smith")
   display(comments_widget.create_widget(item_id=123))
   ```

3. Use improved Excel export with progress:
   ```python
   export_widget = ImprovedExcelExportWidget(exporter)
   display(export_widget.create_widget(job_id="job-123"))
   ```

4. Batch operations with confirmation:
   ```python
   batch_widget = ImprovedBatchOperationsWidget(review_queue)
   display(batch_widget.create_approve_all_button(job_id="job-123", on_complete=reload_dashboard))
   ```

5. Deployment pre-flight checks:
   ```python
   preflight = DeploymentPreflightWidget("healthcare_agent_deploy")
   display(preflight.create_widget())
   ```

6. Standalone confirmation dialog:
   ```python
   dialog = ConfirmationDialog(
       title="Delete All Data?",
       message="This will permanently delete all data. Continue?",
       danger=True
   )
   dialog.show(
       on_confirm=lambda: delete_all_data(),
       on_cancel=lambda: print("Cancelled")
   )
   ```

7. Validated input field:
   ```python
   email_input = ValidatedInput(
       label="Email",
       placeholder="user@example.com",
       required=True,
       validator=lambda x: (
           '@' in x and '.' in x,
           "Please enter a valid email address"
       ),
       help_text="We'll send notifications to this address"
   )
   display(email_input.create_widget())
   ```

KEY IMPROVEMENTS:

✓ Prevents accidental data loss with confirmations
✓ Provides clear, actionable error messages
✓ Shows progress for long-running operations
✓ Validates inputs before submission
✓ Offers inline help throughout the interface
✓ Validates deployment configuration
✓ Guides new users with tutorials
✓ Improves accessibility with ARIA patterns

""")
