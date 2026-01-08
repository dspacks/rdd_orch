import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import pandas as pd
import io
import logging
from typing import Optional, List
from ..review_queue import ReviewQueueManager

logger = logging.getLogger('ADE.UI.Widgets')

class DocumentUploader:
    """Enhanced DocumentUploader with file size validation and improved Excel handling."""
    
    MAX_FILE_SIZE_MB = 50
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    MAX_SHEETS = 20

    def __init__(self):
        self.uploaded_data = None
        self.uploaded_files = {}
        self.processed_text = {}
        self.upload_output = widgets.Output()

    def create_widget(self):
        upload_button = widgets.Button(
            description='📤 Upload Document(s)',
            button_style='primary',
            icon='upload',
            layout=widgets.Layout(width='250px')
        )
        status_label = widgets.HTML(value='<p>No files uploaded</p>')
        
        # File upload logic (using google.colab.files if available, or ipywidgets FileUpload)
        # Note: 'google.colab.files' only works in Colab. For standard Jupyter, we use widgets.FileUpload.
        # But the notebook used `files.upload()` which suggests Colab context.
        # We will use widgets.FileUpload for better compatibility if possible, or fallback.
        # Given the environment is 'windows', this is likely local Jupyter.
        # So `widgets.FileUpload` is better.
        
        self.file_upload = widgets.FileUpload(
            accept='.pdf,.docx,.xlsx,.xls,.csv,.json,.txt',
            multiple=True
        )

        def on_upload_change(change):
            with self.upload_output:
                clear_output()
                uploaded_files = change['new'] # This returns a list or dict depending on version
                
                # Handling FileUpload value format differences (widgets <8 vs >=8)
                if isinstance(uploaded_files, dict):
                    # version < 8
                    file_items = uploaded_files.items()
                else:
                    # version >= 8 (list of dicts)
                    file_items = [(f['name'], f['content']) for f in uploaded_files]

                results = []
                for filename, content in file_items:
                    # memoryview to bytes
                    if memoryview and isinstance(content, memoryview):
                        content = content.tobytes()
                    
                    try:
                        self._validate_file_size(content, filename)
                        file_type, data = self._process_file(filename, content)
                        
                        summary = f"✅ {filename} ({file_type})"
                        if isinstance(data, pd.DataFrame):
                            summary += f" - {len(data)} rows"
                        results.append(summary)
                        print(summary)
                    except Exception as e:
                        results.append(f"❌ {filename}: {str(e)}")
                        print(f"Error {filename}: {e}")

                status_label.value = "<br>".join(results)

        self.file_upload.observe(on_upload_change, names='value')

        return widgets.VBox([
            widgets.HTML("<h3>📄 Upload Documents</h3>"),
            self.file_upload,
            status_label,
            self.upload_output
        ])

    def _validate_file_size(self, content, filename):
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large ({size_mb:.1f} MB). Max {self.MAX_FILE_SIZE_MB} MB.")

    def _process_file(self, filename: str, content: bytes):
        file_lower = filename.lower()
        if file_lower.endswith(('.xlsx', '.xls')):
            self.uploaded_data = pd.read_excel(io.BytesIO(content))
            return 'Excel', self.uploaded_data
        elif file_lower.endswith('.csv'):
            self.uploaded_data = pd.read_csv(io.BytesIO(content))
            return 'CSV', self.uploaded_data
        elif file_lower.endswith('.json'):
            self.uploaded_data = pd.read_json(io.BytesIO(content))
            return 'JSON', self.uploaded_data
        # Simplified for other types
        return 'Other', None

class BatchOperationsWidget:
    """Enhanced batch operations widget with confirmation dialogs."""

    def __init__(self, review_queue):
        self.review_queue = review_queue
        self.output = widgets.Output()

    def create_widget(self, job_id: str):
        stats_html = widgets.HTML()
        confirm_output = widgets.Output()

        def update_stats():
            pending = self.review_queue.get_pending_items(job_id)
            approved = len(self.review_queue.get_approved_items(job_id))
            stats_html.value = f"<b>Pending:</b> {len(pending)} | <b>Approved:</b> {approved}"
            return len(pending)

        approve_btn = widgets.Button(description='✓ Approve All Pending', button_style='success')
        reject_btn = widgets.Button(description='✗ Reject All Pending', button_style='danger')
        feedback_area = widgets.Textarea(placeholder='Rejection reason...')

        def confirm(action, count, callback):
            with confirm_output:
                clear_output()
                yes = widgets.Button(description='Yes, Proceed', button_style='warning')
                no = widgets.Button(description='Cancel')
                
                def on_yes(b):
                    with confirm_output: clear_output()
                    callback()
                    update_stats()
                
                def on_no(b):
                    with confirm_output: clear_output(); print("Cancelled.")

                yes.on_click(on_yes)
                no.on_click(on_no)
                display(widgets.VBox([
                    widgets.HTML(f"<b>Are you sure you want to {action} {count} items?</b>"),
                    widgets.HBox([yes, no])
                ]))

        def on_approve(b):
            count = update_stats()
            if count > 0:
                def do_approve():
                    pk = self.review_queue.get_pending_items(job_id)
                    for i in pk: self.review_queue.approve_item(i.item_id)
                    with self.output: print(f"Approved {len(pk)} items.")
                confirm("approve", count, do_approve)

        def on_reject(b):
            if not feedback_area.value:
                with self.output: print("Provide feedback!")
                return
            count = update_stats()
            if count > 0:
                def do_reject():
                    pk = self.review_queue.get_pending_items(job_id)
                    for i in pk: self.review_queue.reject_item(i.item_id, feedback_area.value)
                    with self.output: print(f"Rejected {len(pk)} items.")
                confirm("reject", count, do_reject)

        approve_btn.on_click(on_approve)
        reject_btn.on_click(on_reject)
        update_stats()

        return widgets.VBox([
            widgets.HTML("<h3>⚡ Batch Operations</h3>"),
            stats_html,
            approve_btn,
            widgets.HTML("<b>Batch Reject:</b>"),
            feedback_area,
            reject_btn,
            confirm_output,
            self.output
        ])

class ClarificationWidget:
    """Widget for managing clarifications."""
    def __init__(self, review_queue):
        self.review_queue = review_queue
        self.output = widgets.Output()

    def create_widget(self, job_id: str):
        # Simplified implementation
        return widgets.HTML("<p>Clarification Widget Placeholder</p>")

class ExportWidget:
    """Widget for exporting documentation."""
    def __init__(self, assembler, review_queue):
        self.assembler = assembler
        self.review_queue = review_queue
        self.output = widgets.Output()

    def create_widget(self, job_id: str):
        btn = widgets.Button(description="Export Markdown", button_style='success')
        
        def on_click(b):
            with self.output:
                clear_output()
                doc = self.assembler.assemble(job_id)
                print(doc[:500] + "...")
                # In local Jupyter, we can write to file
                with open(f"{job_id}_doc.md", "w") as f:
                    f.write(doc)
                print(f"Saved to {job_id}_doc.md")

        btn.on_click(on_click)
        return widgets.VBox([
            widgets.HTML("<h3>💾 Export</h3>"),
            btn,
            self.output
        ])
