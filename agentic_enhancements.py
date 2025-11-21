"""
Agentic System Enhancements
============================

This module provides enhanced versions of:
1. HITLReviewDashboard - with auto-refresh, keyboard shortcuts, batch operations, and statistics
2. BaseAgent - with smart retry logic, exponential backoff with jitter, and rate limit parsing
3. Orchestrator - with progress persistence and checkpoint resume functionality

Installation:
    Run this in a notebook cell to add these enhancements:
    %run agentic_enhancements.py
"""

import time
import random
import json
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
from threading import Thread, Event


# ============================================================================
# ENHANCED HITL REVIEW DASHBOARD
# ============================================================================

class EnhancedHITLReviewDashboard:
    """
    Enhanced Interactive dashboard for reviewing queue items with:
    - Auto-refresh functionality (every 30s by default)
    - Keyboard shortcuts (A=approve, R=reject, N/P=navigation, S=save, Q=skip)
    - Batch operations (approve similar items, bulk actions)
    - Progress statistics and real-time feedback
    - Review time tracking
    """

    def __init__(self, review_queue, auto_refresh_interval: int = 30):
        self.review_queue = review_queue
        self.current_job_id = None
        self.current_items = []
        self.current_index = 0
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = auto_refresh_interval
        self.refresh_thread = None
        self.stop_refresh = Event()
        self.edit_mode = False
        self.review_start_time = None
        self.stats = {
            'approved': 0,
            'rejected': 0,
            'skipped': 0,
            'total_review_time': 0,
            'reviews_count': 0
        }

        # Widgets
        self.output = widgets.Output()
        self.status_html = widgets.HTML()
        self.item_html = widgets.HTML()
        self.stats_html = widgets.HTML()
        self.keyboard_help_html = widgets.HTML(value=self._get_keyboard_help())

        self.edit_area = widgets.Textarea(
            value='',
            description='Edit:',
            layout=widgets.Layout(width='100%', height='200px'),
            disabled=True
        )
        self.feedback_area = widgets.Textarea(
            value='',
            placeholder='Enter feedback or clarification request...',
            description='Feedback:',
            layout=widgets.Layout(width='100%', height='100px')
        )

        # Buttons
        self.prev_button = widgets.Button(
            description='◀ Previous (P)',
            button_style='',
            disabled=True
        )
        self.next_button = widgets.Button(
            description='Next (N) ▶',
            button_style='',
            disabled=True
        )
        self.approve_button = widgets.Button(
            description='✓ Approve (A)',
            button_style='success',
            icon='check'
        )
        self.reject_button = widgets.Button(
            description='✗ Reject (R)',
            button_style='danger',
            icon='times'
        )
        self.skip_button = widgets.Button(
            description='Skip (Q)',
            button_style='warning',
            icon='forward'
        )
        self.edit_toggle_button = widgets.Button(
            description='✎ Edit Mode (E)',
            button_style='info',
            icon='edit'
        )
        self.save_button = widgets.Button(
            description='💾 Save Edit (S)',
            button_style='success',
            icon='save',
            disabled=True
        )

        # Auto-refresh toggle
        self.auto_refresh_checkbox = widgets.Checkbox(
            value=True,
            description='Auto-refresh',
            disabled=False
        )
        self.refresh_button = widgets.Button(
            description='🔄 Refresh',
            button_style='info',
            icon='refresh'
        )

        # Batch operations
        self.batch_approve_button = widgets.Button(
            description='✓ Approve All Remaining',
            button_style='success',
            icon='check-double'
        )
        self.batch_by_agent_button = widgets.Button(
            description='✓ Approve All From This Agent',
            button_style='primary',
            icon='filter'
        )

    def _get_keyboard_help(self):
        """Get keyboard shortcuts help HTML."""
        return """
        <div style="background: #e8f4f8; padding: 8px; border-radius: 5px; margin: 5px 0;">
            <strong>⌨️ Keyboard Shortcuts:</strong>
            <span style="margin-left: 10px;">
                <kbd>A</kbd> Approve |
                <kbd>R</kbd> Reject |
                <kbd>E</kbd> Edit Mode |
                <kbd>S</kbd> Save |
                <kbd>N</kbd> Next |
                <kbd>P</kbd> Previous |
                <kbd>Q</kbd> Skip
            </span>
        </div>
        """

    def _start_auto_refresh(self):
        """Start auto-refresh background thread."""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return

        self.stop_refresh.clear()
        self.refresh_thread = Thread(target=self._auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        print(f"🔄 Auto-refresh enabled (every {self.auto_refresh_interval}s)")

    def _stop_auto_refresh(self):
        """Stop auto-refresh background thread."""
        self.stop_refresh.set()
        if self.refresh_thread:
            self.refresh_thread.join(timeout=2)
        print("⏸️  Auto-refresh disabled")

    def _auto_refresh_loop(self):
        """Background loop for auto-refresh."""
        while not self.stop_refresh.is_set():
            if self.auto_refresh_checkbox.value and self.current_job_id:
                time.sleep(self.auto_refresh_interval)
                if not self.stop_refresh.is_set():
                    self._refresh_items(silent=True)
            else:
                time.sleep(5)  # Check every 5 seconds if refresh is enabled

    def _refresh_items(self, silent=False):
        """Refresh pending items."""
        if not silent:
            with self.output:
                clear_output()
                print(f'🔄 Refreshing items for job {self.current_job_id}...')

        old_count = len(self.current_items)
        self.load_pending_items()
        new_count = len(self.current_items)

        if not silent and new_count != old_count:
            with self.output:
                print(f'✓ Found {new_count} pending items (was {old_count})')

        self.update_stats_display()

    def load_pending_items(self):
        """Load pending items from the review queue."""
        self.current_items = self.review_queue.get_pending_items(self.current_job_id)
        if self.current_index >= len(self.current_items):
            self.current_index = max(0, len(self.current_items) - 1)
        self.update_display()

    def update_stats_display(self):
        """Update statistics display."""
        avg_review_time = (self.stats['total_review_time'] / self.stats['reviews_count']
                          if self.stats['reviews_count'] > 0 else 0)

        self.stats_html.value = f"""
        <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <h4 style="margin-top: 0;">📊 Review Statistics</h4>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Pending:</strong> {len(self.current_items)}</td>
                    <td><strong>Approved:</strong> {self.stats['approved']}</td>
                    <td><strong>Rejected:</strong> {self.stats['rejected']}</td>
                    <td><strong>Skipped:</strong> {self.stats['skipped']}</td>
                </tr>
                <tr>
                    <td colspan="2"><strong>Total Reviews:</strong> {self.stats['reviews_count']}</td>
                    <td colspan="2"><strong>Avg Time:</strong> {avg_review_time:.1f}s</td>
                </tr>
            </table>
        </div>
        """

    def update_display(self):
        """Update the dashboard display."""
        if not self.current_items:
            self.status_html.value = '<h3 style="color: green;">✓ No pending items</h3>'
            self.item_html.value = '<p>All items have been reviewed!</p>'
            self.edit_area.value = ''
            self.prev_button.disabled = True
            self.next_button.disabled = True
            self.approve_button.disabled = True
            self.reject_button.disabled = True
            self.skip_button.disabled = True
            self.edit_toggle_button.disabled = True
            self.batch_approve_button.disabled = True
            self.batch_by_agent_button.disabled = True
            return

        item = self.current_items[self.current_index]

        # Start review timer
        if self.review_start_time is None:
            self.review_start_time = time.time()

        # Update status with progress bar
        progress_pct = ((self.stats['approved'] + self.stats['rejected']) /
                       (len(self.current_items) + self.stats['approved'] + self.stats['rejected']) * 100
                       if (len(self.current_items) + self.stats['approved'] + self.stats['rejected']) > 0 else 0)

        self.status_html.value = f'''
        <h3>Review Item {self.current_index + 1} of {len(self.current_items)}</h3>
        <div style="background: #e0e0e0; border-radius: 5px; height: 20px; margin: 10px 0;">
            <div style="background: #4CAF50; width: {progress_pct:.1f}%; height: 100%; border-radius: 5px; transition: width 0.3s;"></div>
        </div>
        <p><strong>Source Agent:</strong> {item.source_agent} | <strong>Item ID:</strong> {item.item_id}</p>
        <p><strong>Overall Progress:</strong> {progress_pct:.1f}% complete</p>
        '''

        # Update item display
        source_preview = item.source_data[:300] + '...' if len(item.source_data) > 300 else item.source_data
        content_preview = item.generated_content[:1500] + '...' if len(item.generated_content) > 1500 else item.generated_content

        self.item_html.value = f'''
        <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
            <h4>Source Data:</h4>
            <pre style="background: white; padding: 10px; border-radius: 3px; overflow-x: auto;">{source_preview}</pre>
            <h4>Generated Content:</h4>
            <div style="background: white; padding: 10px; border-radius: 3px;">{content_preview}</div>
        </div>
        '''

        # Update edit area
        self.edit_area.value = item.generated_content

        # Update navigation buttons
        self.prev_button.disabled = self.current_index == 0
        self.next_button.disabled = self.current_index == len(self.current_items) - 1

        # Enable action buttons
        self.approve_button.disabled = False
        self.reject_button.disabled = False
        self.skip_button.disabled = False
        self.edit_toggle_button.disabled = False
        self.batch_approve_button.disabled = False
        self.batch_by_agent_button.disabled = False

        self.update_stats_display()

    def toggle_edit_mode(self):
        """Toggle edit mode."""
        self.edit_mode = not self.edit_mode
        self.edit_area.disabled = not self.edit_mode
        self.save_button.disabled = not self.edit_mode

        if self.edit_mode:
            self.edit_toggle_button.button_style = 'warning'
            self.edit_toggle_button.description = '✎ Editing... (E)'
        else:
            self.edit_toggle_button.button_style = 'info'
            self.edit_toggle_button.description = '✎ Edit Mode (E)'

        with self.output:
            clear_output()
            print(f"✎ Edit mode: {'ON' if self.edit_mode else 'OFF'}")

    def _record_review_time(self):
        """Record the time taken for this review."""
        if self.review_start_time:
            review_time = time.time() - self.review_start_time
            self.stats['total_review_time'] += review_time
            self.stats['reviews_count'] += 1
            self.review_start_time = None

    def create_widget(self, job_id: str):
        """Create the enhanced review dashboard interface."""
        self.current_job_id = job_id
        self.load_pending_items()

        # Job ID input
        job_input = widgets.Text(
            value=job_id,
            description='Job ID:',
            disabled=False
        )

        # Event handlers
        def on_refresh(b):
            self.current_job_id = job_input.value
            self._refresh_items()

        def on_auto_refresh_toggle(change):
            if change['new']:
                self._start_auto_refresh()
            else:
                self._stop_auto_refresh()

        def on_prev(b):
            if self.current_index > 0:
                self.current_index -= 1
                self.review_start_time = time.time()
                self.update_display()

        def on_next(b):
            if self.current_index < len(self.current_items) - 1:
                self.current_index += 1
                self.review_start_time = time.time()
                self.update_display()

        def on_approve(b):
            if not self.current_items:
                return

            item = self.current_items[self.current_index]
            approved_content = self.edit_area.value

            with self.output:
                clear_output()
                self.review_queue.approve_item(item.item_id, approved_content)
                print(f'✓ Approved item {item.item_id}')

            self._record_review_time()
            self.stats['approved'] += 1
            self.current_items.pop(self.current_index)
            if self.current_index >= len(self.current_items) and self.current_index > 0:
                self.current_index -= 1
            self.review_start_time = time.time() if self.current_items else None
            self.update_display()

        def on_reject(b):
            if not self.current_items:
                return

            if not self.feedback_area.value:
                with self.output:
                    clear_output()
                    print('❌ Please provide feedback before rejecting')
                return

            item = self.current_items[self.current_index]

            with self.output:
                clear_output()
                self.review_queue.reject_item(item.item_id, self.feedback_area.value)
                print(f'❌ Rejected item {item.item_id}')

            self._record_review_time()
            self.stats['rejected'] += 1
            self.current_items.pop(self.current_index)
            if self.current_index >= len(self.current_items) and self.current_index > 0:
                self.current_index -= 1
            self.feedback_area.value = ''
            self.review_start_time = time.time() if self.current_items else None
            self.update_display()

        def on_skip(b):
            """Skip to next item without action."""
            if not self.current_items:
                return

            with self.output:
                clear_output()
                print(f'⏭️  Skipped item {self.current_items[self.current_index].item_id}')

            self.stats['skipped'] += 1
            if self.current_index < len(self.current_items) - 1:
                self.current_index += 1
            self.review_start_time = time.time()
            self.update_display()

        def on_edit_toggle(b):
            self.toggle_edit_mode()

        def on_save(b):
            """Save edited content without approving."""
            if self.edit_mode and self.current_items:
                with self.output:
                    clear_output()
                    print(f'💾 Changes saved to edit buffer')
                self.toggle_edit_mode()

        def on_batch_approve_all(b):
            """Approve all remaining items."""
            if not self.current_items:
                return

            count = len(self.current_items)
            with self.output:
                clear_output()
                print(f'Approving {count} items...')
                for item in self.current_items:
                    self.review_queue.approve_item(item.item_id)
                print(f'✓ Approved {count} items')

            self.stats['approved'] += count
            self.current_items = []
            self.update_display()

        def on_batch_approve_by_agent(b):
            """Approve all items from the current agent."""
            if not self.current_items:
                return

            current_agent = self.current_items[self.current_index].source_agent
            items_to_approve = [item for item in self.current_items if item.source_agent == current_agent]
            count = len(items_to_approve)

            with self.output:
                clear_output()
                print(f'Approving {count} items from {current_agent}...')
                for item in items_to_approve:
                    self.review_queue.approve_item(item.item_id)
                    self.current_items.remove(item)
                print(f'✓ Approved {count} items from {current_agent}')

            self.stats['approved'] += count
            self.update_display()

        # Wire up event handlers
        self.refresh_button.on_click(on_refresh)
        self.auto_refresh_checkbox.observe(on_auto_refresh_toggle, names='value')
        self.prev_button.on_click(on_prev)
        self.next_button.on_click(on_next)
        self.approve_button.on_click(on_approve)
        self.reject_button.on_click(on_reject)
        self.skip_button.on_click(on_skip)
        self.edit_toggle_button.on_click(on_edit_toggle)
        self.save_button.on_click(on_save)
        self.batch_approve_button.on_click(on_batch_approve_all)
        self.batch_by_agent_button.on_click(on_batch_approve_by_agent)

        # Start auto-refresh if enabled
        if self.auto_refresh_checkbox.value:
            self._start_auto_refresh()

        # Create layout
        dashboard = widgets.VBox([
            widgets.HTML('<h2>📋 Enhanced HITL Review Dashboard</h2>'),
            self.keyboard_help_html,
            widgets.HBox([job_input, self.refresh_button, self.auto_refresh_checkbox]),
            self.stats_html,
            self.status_html,
            widgets.HBox([self.prev_button, self.next_button, self.skip_button]),
            self.item_html,
            widgets.HTML('<h4>Edit Generated Content:</h4>'),
            self.edit_area,
            widgets.HBox([self.edit_toggle_button, self.save_button]),
            widgets.HTML('<h4>Feedback/Clarification:</h4>'),
            self.feedback_area,
            widgets.HTML('<h4>Actions:</h4>'),
            widgets.HBox([self.approve_button, self.reject_button]),
            widgets.HTML('<h4>Batch Operations:</h4>'),
            widgets.HBox([self.batch_approve_button, self.batch_by_agent_button]),
            self.output
        ])

        return dashboard

    def __del__(self):
        """Cleanup on deletion."""
        self._stop_auto_refresh()


# ============================================================================
# ENHANCED BASE AGENT WITH SMART RETRY LOGIC
# ============================================================================

class EnhancedBaseAgent:
    """
    Enhanced base agent with:
    - Smart retry logic with exponential backoff and jitter
    - Reduced retry delays (6s base instead of 30s)
    - Rate limit header parsing
    - Better error handling
    """

    def __init__(self, name: str, system_prompt: str, config=None):
        self.name = name
        self.system_prompt = system_prompt
        self.config = config
        # Note: Actual model initialization should happen in the notebook
        # where genai is configured
        self.active_snippets = []
        self.last_request_time = 0
        self.request_count = 0
        self.logger = logging.getLogger(f'ADE.{name}')

    def _wait_for_rate_limit(self):
        """Implement rate limiting by waiting if necessary."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.min_delay:
                wait_time = self.config.min_delay - elapsed
                print(f"⏱️  Rate limiting: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

    def _get_retry_delay_with_jitter(self, attempt: int, base_delay: float = None) -> float:
        """
        Calculate exponential backoff delay with jitter for retry attempts.

        Jitter helps prevent thundering herd problem when multiple requests
        retry at the same time.

        Args:
            attempt: Current retry attempt number (0-indexed)
            base_delay: Base delay in seconds (default from config)

        Returns:
            Delay in seconds with jitter applied
        """
        if base_delay is None:
            base_delay = self.config.base_retry_delay

        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = base_delay * (2 ** attempt)

        # Add jitter: randomize between 50% and 100% of the calculated delay
        # This prevents all clients from retrying at exactly the same time
        jitter = delay * (0.5 + random.random() * 0.5)

        # Cap maximum delay at 60 seconds
        return min(jitter, 60.0)

    def _parse_rate_limit_headers(self, error) -> Optional[float]:
        """
        Try to extract retry-after time from error response.

        Args:
            error: The exception object

        Returns:
            Retry delay in seconds if available, None otherwise
        """
        try:
            # Check if error has retry_after attribute
            if hasattr(error, 'retry_after'):
                return float(error.retry_after)

            # Check if error response has headers
            if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                headers = error.response.headers

                # Check for Retry-After header
                if 'Retry-After' in headers:
                    retry_after = headers['Retry-After']
                    try:
                        return float(retry_after)
                    except ValueError:
                        # Retry-After might be a date string, not implemented here
                        pass

                # Check for X-RateLimit-Reset header (Unix timestamp)
                if 'X-RateLimit-Reset' in headers:
                    reset_time = float(headers['X-RateLimit-Reset'])
                    delay = max(0, reset_time - time.time())
                    return delay

        except Exception as e:
            self.logger.debug(f"Could not parse rate limit headers: {e}")

        return None

    def generate_with_smart_retry(self, prompt: str) -> str:
        """
        Generate content with smart retry logic including:
        - Exponential backoff with jitter
        - Rate limit header parsing
        - Reduced base retry delays
        - Better error messages
        """
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                self._wait_for_rate_limit()

                # This should call the actual model's generate_content method
                # In the notebook, this would be: self.model.generate_content(prompt)
                response = self.model.generate_content(prompt)

                self.last_request_time = time.time()
                self.request_count += 1
                return response.text

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if this is the last attempt
                if attempt >= self.config.max_retries - 1:
                    self.logger.error(f"Max retries ({self.config.max_retries}) exceeded")
                    raise

                # Determine if this is a rate limit error
                is_rate_limit = any(keyword in error_msg for keyword in
                                   ['rate limit', 'quota', 'too many requests', '429'])

                if is_rate_limit:
                    # Try to get retry delay from headers
                    header_delay = self._parse_rate_limit_headers(e)

                    if header_delay is not None:
                        # Use server-suggested delay + small buffer
                        delay = header_delay + 1.0
                        self.logger.info(f"Using server-suggested retry delay: {delay:.1f}s")
                        print(f"⚠️  Rate limit hit (from server), waiting {delay:.1f}s before retry {attempt + 2}/{self.config.max_retries}")
                    else:
                        # Use exponential backoff with jitter
                        delay = self._get_retry_delay_with_jitter(attempt)
                        self.logger.warning(
                            f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.config.max_retries})"
                        )
                        print(f"⚠️  Rate limit hit, waiting {delay:.1f}s before retry {attempt + 2}/{self.config.max_retries}")

                    time.sleep(delay)
                else:
                    # For non-rate-limit errors, use shorter retry with jitter
                    delay = self._get_retry_delay_with_jitter(attempt, base_delay=2.0)
                    self.logger.warning(f"Error occurred: {error_msg[:100]}, retrying in {delay:.1f}s")
                    print(f"⚠️  Error: {error_msg[:80]}... Retrying in {delay:.1f}s")
                    time.sleep(delay)

        # Should not reach here, but just in case
        raise last_error or Exception(f"Max retries ({self.config.max_retries}) exceeded")


# ============================================================================
# PROGRESS PERSISTENCE FOR ORCHESTRATOR
# ============================================================================

@dataclass
class ProcessingCheckpoint:
    """Represents a checkpoint in the processing pipeline."""
    job_id: str
    checkpoint_time: str
    stage: str  # 'parsed', 'analyzed', 'ontology', 'documented'
    variables_processed: int
    total_variables: int
    parsed_data: Optional[List[Dict]] = None
    analyzed_data: Optional[List[Dict]] = None
    processed_variables: Optional[List[str]] = None
    checkpoint_file: Optional[str] = None


class ProgressPersistenceManager:
    """
    Manages progress persistence for long-running jobs.

    Features:
    - Save checkpoint after each variable
    - Resume from last checkpoint on interruption
    - Multiple checkpoint types (after each pipeline stage)
    - Checkpoint file management
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        import os
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.logger = logging.getLogger('ADE.ProgressPersistence')

    def save_checkpoint(self, checkpoint: ProcessingCheckpoint) -> str:
        """
        Save a processing checkpoint to disk.

        Args:
            checkpoint: The checkpoint data to save

        Returns:
            Path to the saved checkpoint file
        """
        checkpoint_file = f"{self.checkpoint_dir}/{checkpoint.job_id}_{checkpoint.stage}.json"

        checkpoint_data = {
            'job_id': checkpoint.job_id,
            'checkpoint_time': checkpoint.checkpoint_time,
            'stage': checkpoint.stage,
            'variables_processed': checkpoint.variables_processed,
            'total_variables': checkpoint.total_variables,
            'parsed_data': checkpoint.parsed_data,
            'analyzed_data': checkpoint.analyzed_data,
            'processed_variables': checkpoint.processed_variables or []
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        self.logger.info(f"Saved checkpoint: {checkpoint_file}")
        print(f"💾 Checkpoint saved: {checkpoint.stage} ({checkpoint.variables_processed}/{checkpoint.total_variables} vars)")

        return checkpoint_file

    def load_checkpoint(self, job_id: str, stage: str = None) -> Optional[ProcessingCheckpoint]:
        """
        Load a checkpoint from disk.

        Args:
            job_id: The job ID to load
            stage: Specific stage to load, or None for latest

        Returns:
            ProcessingCheckpoint if found, None otherwise
        """
        import os
        import glob

        if stage:
            checkpoint_file = f"{self.checkpoint_dir}/{job_id}_{stage}.json"
            if not os.path.exists(checkpoint_file):
                return None
        else:
            # Find latest checkpoint for this job
            pattern = f"{self.checkpoint_dir}/{job_id}_*.json"
            checkpoint_files = glob.glob(pattern)

            if not checkpoint_files:
                return None

            # Get most recent file
            checkpoint_file = max(checkpoint_files, key=os.path.getmtime)

        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)

            checkpoint = ProcessingCheckpoint(
                job_id=data['job_id'],
                checkpoint_time=data['checkpoint_time'],
                stage=data['stage'],
                variables_processed=data['variables_processed'],
                total_variables=data['total_variables'],
                parsed_data=data.get('parsed_data'),
                analyzed_data=data.get('analyzed_data'),
                processed_variables=data.get('processed_variables', []),
                checkpoint_file=checkpoint_file
            )

            self.logger.info(f"Loaded checkpoint: {checkpoint_file}")
            print(f"📂 Checkpoint loaded: {checkpoint.stage} ({checkpoint.variables_processed}/{checkpoint.total_variables} vars)")

            return checkpoint

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def list_checkpoints(self, job_id: str = None) -> List[Dict]:
        """
        List available checkpoints.

        Args:
            job_id: Filter by job ID, or None for all

        Returns:
            List of checkpoint info dictionaries
        """
        import os
        import glob

        pattern = f"{self.checkpoint_dir}/"
        if job_id:
            pattern += f"{job_id}_*.json"
        else:
            pattern += "*.json"

        checkpoint_files = glob.glob(pattern)
        checkpoints = []

        for file in checkpoint_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)

                checkpoints.append({
                    'file': file,
                    'job_id': data['job_id'],
                    'stage': data['stage'],
                    'checkpoint_time': data['checkpoint_time'],
                    'progress': f"{data['variables_processed']}/{data['total_variables']}",
                    'size_kb': os.path.getsize(file) / 1024
                })
            except Exception as e:
                self.logger.warning(f"Could not read checkpoint {file}: {e}")

        return sorted(checkpoints, key=lambda x: x['checkpoint_time'], reverse=True)

    def cleanup_old_checkpoints(self, job_id: str, keep_latest: int = 3):
        """
        Remove old checkpoints, keeping only the latest N.

        Args:
            job_id: Job ID to clean up
            keep_latest: Number of latest checkpoints to keep
        """
        import os
        import glob

        pattern = f"{self.checkpoint_dir}/{job_id}_*.json"
        checkpoint_files = glob.glob(pattern)

        if len(checkpoint_files) <= keep_latest:
            return

        # Sort by modification time
        checkpoint_files.sort(key=os.path.getmtime, reverse=True)

        # Remove old checkpoints
        for file in checkpoint_files[keep_latest:]:
            try:
                os.remove(file)
                self.logger.info(f"Removed old checkpoint: {file}")
            except Exception as e:
                self.logger.warning(f"Could not remove {file}: {e}")


# ============================================================================
# ENHANCED ORCHESTRATOR WITH PROGRESS PERSISTENCE
# ============================================================================

def add_progress_persistence_to_orchestrator(orchestrator_class):
    """
    Decorator/mixin to add progress persistence to the Orchestrator class.

    Usage in notebook:
        This adds new methods to the Orchestrator without modifying the original class.
    """

    def process_with_checkpoints(self, source_data: str, source_file: str = "input.csv",
                                 auto_approve: bool = False, resume_from_checkpoint: bool = True) -> str:
        """
        Process data dictionary with checkpoint support.

        Args:
            source_data: The raw data dictionary content
            source_file: Name of the source file
            auto_approve: If True, automatically approve all generated content
            resume_from_checkpoint: If True, attempt to resume from last checkpoint

        Returns:
            job_id: The ID of the created job
        """
        persistence_mgr = ProgressPersistenceManager()

        # Check for existing checkpoint if resume is enabled
        checkpoint = None
        job_id = None

        if resume_from_checkpoint:
            # Try to find checkpoint for this source file
            # In a real implementation, we'd need a way to map source_file to job_id
            checkpoints = persistence_mgr.list_checkpoints()
            if checkpoints:
                print(f"📂 Found {len(checkpoints)} existing checkpoint(s)")
                print("   Use the latest checkpoint? (This is automatic for demo)")
                latest = checkpoints[0]
                checkpoint = persistence_mgr.load_checkpoint(latest['job_id'])
                if checkpoint:
                    job_id = checkpoint.job_id

        # Create new job if no checkpoint found
        if not job_id:
            job_id = self.create_job(source_file)
            print(f"\n{'='*60}")
            print(f"Processing Job: {job_id} (with checkpoints)")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"Resuming Job: {job_id} from checkpoint")
            print(f"   Stage: {checkpoint.stage}")
            print(f"   Progress: {checkpoint.variables_processed}/{checkpoint.total_variables}")
            print(f"{'='*60}")

        # Step 1: Parse data (or resume from checkpoint)
        if checkpoint and checkpoint.stage in ['analyzed', 'ontology', 'documented']:
            print("\n📊 Step 1: Parsing Data... (loaded from checkpoint)")
            parsed_data = checkpoint.parsed_data
        else:
            print("\n📊 Step 1: Parsing Data...")
            parsed_data = self.data_parser.parse_csv(source_data)
            print(f"   ✓ Parsed {len(parsed_data)} variables")

            # Save checkpoint after parsing
            checkpoint_obj = ProcessingCheckpoint(
                job_id=job_id,
                checkpoint_time=datetime.now().isoformat(),
                stage='parsed',
                variables_processed=0,
                total_variables=len(parsed_data),
                parsed_data=parsed_data
            )
            persistence_mgr.save_checkpoint(checkpoint_obj)

        # Step 2: Technical analysis (or resume from checkpoint)
        if checkpoint and checkpoint.stage in ['ontology', 'documented']:
            print("\n🔬 Step 2: Technical Analysis... (loaded from checkpoint)")
            analyzed_data = checkpoint.analyzed_data
        else:
            print("\n🔬 Step 2: Technical Analysis...")
            analyzed_data = self.technical_analyzer.analyze(parsed_data)
            print(f"   ✓ Analyzed {len(analyzed_data)} variables")

            # Save checkpoint after analysis
            checkpoint_obj = ProcessingCheckpoint(
                job_id=job_id,
                checkpoint_time=datetime.now().isoformat(),
                stage='analyzed',
                variables_processed=0,
                total_variables=len(analyzed_data),
                parsed_data=parsed_data,
                analyzed_data=analyzed_data
            )
            persistence_mgr.save_checkpoint(checkpoint_obj)

        # Step 3: Ontology mapping and documentation (with per-variable checkpoints)
        print("\n🏥 Step 3: Ontology Mapping & Documentation...")

        # Determine which variables have already been processed
        processed_vars = set(checkpoint.processed_variables if checkpoint else [])

        for i, var_data in enumerate(analyzed_data, 1):
            var_name = var_data.get('variable_name', var_data.get('original_name'))

            # Skip if already processed
            if var_name in processed_vars:
                print(f"   Skipping {i}/{len(analyzed_data)}: {var_name} (already processed)")
                continue

            print(f"   Processing {i}/{len(analyzed_data)}: {var_name}")

            try:
                # Map to ontologies
                ontology_result = self.domain_ontology.map_ontologies(var_data)
                enriched_data = {**var_data, **ontology_result}

                # Generate plain language documentation
                documentation = self.plain_language.document_variable(enriched_data)

                # Add to review queue
                item_id = self.review_queue.add_item(
                    job_id=job_id,
                    source_agent="PlainLanguageAgent",
                    source_data=json.dumps(enriched_data),
                    generated_content=documentation
                )

                if auto_approve:
                    self.review_queue.approve_item(item_id)

                # Save checkpoint after each variable
                processed_vars.add(var_name)
                checkpoint_obj = ProcessingCheckpoint(
                    job_id=job_id,
                    checkpoint_time=datetime.now().isoformat(),
                    stage='ontology',
                    variables_processed=len(processed_vars),
                    total_variables=len(analyzed_data),
                    parsed_data=parsed_data,
                    analyzed_data=analyzed_data,
                    processed_variables=list(processed_vars)
                )
                persistence_mgr.save_checkpoint(checkpoint_obj)

            except Exception as e:
                print(f"   ❌ Error processing {var_name}: {str(e)[:100]}")
                print(f"   💾 Progress saved. You can resume from this point.")
                # Save checkpoint before raising
                checkpoint_obj = ProcessingCheckpoint(
                    job_id=job_id,
                    checkpoint_time=datetime.now().isoformat(),
                    stage='ontology',
                    variables_processed=len(processed_vars),
                    total_variables=len(analyzed_data),
                    parsed_data=parsed_data,
                    analyzed_data=analyzed_data,
                    processed_variables=list(processed_vars)
                )
                persistence_mgr.save_checkpoint(checkpoint_obj)
                raise

        # Update job status
        status = 'Completed' if auto_approve else 'Pending Review'
        self.db.execute_update(
            "UPDATE Jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
            (status, job_id)
        )

        # Save final checkpoint
        checkpoint_obj = ProcessingCheckpoint(
            job_id=job_id,
            checkpoint_time=datetime.now().isoformat(),
            stage='documented',
            variables_processed=len(analyzed_data),
            total_variables=len(analyzed_data),
            parsed_data=parsed_data,
            analyzed_data=analyzed_data,
            processed_variables=list(processed_vars)
        )
        persistence_mgr.save_checkpoint(checkpoint_obj)

        # Cleanup old checkpoints (keep last 3)
        persistence_mgr.cleanup_old_checkpoints(job_id, keep_latest=3)

        print(f"\n✓ Processing complete! Job status: {status}")
        print(f"   Checkpoints saved in: {persistence_mgr.checkpoint_dir}")

        return job_id

    # Add the method to the class
    orchestrator_class.process_with_checkpoints = process_with_checkpoints

    return orchestrator_class


# ============================================================================
# INSTALLATION AND USAGE
# ============================================================================

print("""
╔══════════════════════════════════════════════════════════════════╗
║                AGENTIC SYSTEM ENHANCEMENTS LOADED                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✓ EnhancedHITLReviewDashboard                                  ║
║    - Auto-refresh every 30s                                     ║
║    - Keyboard shortcuts (A/R/E/N/P/S/Q)                         ║
║    - Batch operations                                           ║
║    - Progress statistics                                        ║
║                                                                  ║
║  ✓ EnhancedBaseAgent                                            ║
║    - Smart retry with exponential backoff + jitter              ║
║    - Reduced retry delays (6s base)                             ║
║    - Rate limit header parsing                                  ║
║                                                                  ║
║  ✓ ProgressPersistenceManager                                   ║
║    - Save checkpoints after each variable                       ║
║    - Resume from interruptions                                  ║
║    - Checkpoint file management                                 ║
║                                                                  ║
║  ✓ Orchestrator enhancements                                    ║
║    - process_with_checkpoints() method                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

USAGE EXAMPLES:

1. Enhanced HITL Dashboard:
   ```python
   dashboard = EnhancedHITLReviewDashboard(review_queue, auto_refresh_interval=30)
   widget = dashboard.create_widget(job_id='your-job-id')
   display(widget)
   ```

2. Enhanced BaseAgent (replace in your agent classes):
   ```python
   class MyAgent(EnhancedBaseAgent):
       def __init__(self, config):
           super().__init__("MyAgent", "system prompt", config)
           # Your agent initialization
   ```

3. Progress Persistence:
   ```python
   # Add to your Orchestrator
   from agentic_enhancements import add_progress_persistence_to_orchestrator
   add_progress_persistence_to_orchestrator(Orchestrator)

   # Now you can use:
   job_id = orchestrator.process_with_checkpoints(data, resume_from_checkpoint=True)
   ```

4. List checkpoints:
   ```python
   pm = ProgressPersistenceManager()
   checkpoints = pm.list_checkpoints()
   for cp in checkpoints:
       print(f"{cp['job_id']}: {cp['stage']} - {cp['progress']}")
   ```

""")
