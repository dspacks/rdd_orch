"""
ADE Feature Implementations
===========================

This module implements the feature suggestions from FEATURE_SUGGESTIONS.md,
organized from easiest to most difficult:

1. Field-level comments system
2. Quality score display
3. Excel export functionality
4. Version comparison UI
5. Template library with demographics
6. PDF export functionality
7. HTML dashboard export
8. JSON Schema export
9. REDCap integration (import/export)
10. Data quality and validation module

Installation:
    %run features_implementation.py
"""

import sqlite3
import json
import pandas as pd
import io
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import hashlib
import re

logger = logging.getLogger('ADE.Features')


# ============================================================================
# FEATURE 1: FIELD-LEVEL COMMENTS SYSTEM
# ============================================================================

class CommentsManager:
    """
    Manages field-level comments for collaborative review.

    Allows reviewers to add threaded comments to specific fields/items
    without approving or rejecting them.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_comments_table()

    def _ensure_comments_table(self):
        """Create comments table if it doesn't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS FieldComments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            reviewer_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            comment_type TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES ReviewQueue(item_id)
        );

        CREATE INDEX IF NOT EXISTS idx_field_comments_item
        ON FieldComments(item_id);
        """
        for statement in schema.split(';'):
            if statement.strip():
                self.db.cursor.execute(statement)
        self.db.conn.commit()
        logger.info("Comments table created/verified")

    def add_comment(self, item_id: int, reviewer_name: str,
                   comment_text: str, comment_type: str = 'general') -> int:
        """
        Add a comment to a review item.

        Args:
            item_id: ID of the review queue item
            reviewer_name: Name of the reviewer
            comment_text: The comment content
            comment_type: Type of comment (general, question, suggestion, concern)

        Returns:
            comment_id: ID of the created comment
        """
        query = """
        INSERT INTO FieldComments (item_id, reviewer_name, comment_text, comment_type)
        VALUES (?, ?, ?, ?)
        """
        comment_id = self.db.execute_update(
            query, (item_id, reviewer_name, comment_text, comment_type)
        )
        logger.info(f"Added comment {comment_id} to item {item_id} by {reviewer_name}")
        return comment_id

    def get_comments(self, item_id: int) -> List[Dict]:
        """Get all comments for a review item."""
        query = """
        SELECT comment_id, reviewer_name, comment_text, comment_type, created_at
        FROM FieldComments
        WHERE item_id = ?
        ORDER BY created_at ASC
        """
        comments = self.db.execute_query(query, (item_id,))
        return comments

    def get_comment_count(self, item_id: int) -> int:
        """Get count of comments for an item."""
        query = "SELECT COUNT(*) as count FROM FieldComments WHERE item_id = ?"
        result = self.db.execute_query(query, (item_id,))
        return result[0]['count'] if result else 0


class CommentsWidget:
    """Interactive widget for displaying and adding comments."""

    def __init__(self, comments_manager: CommentsManager, reviewer_name: str = "User"):
        self.comments_mgr = comments_manager
        self.reviewer_name = reviewer_name
        self.current_item_id = None

    def create_widget(self, item_id: int) -> widgets.Widget:
        """Create comments widget for a review item."""
        self.current_item_id = item_id

        # Comments display area
        comments_html = widgets.HTML()

        # New comment input
        comment_type_dropdown = widgets.Dropdown(
            options=['general', 'question', 'suggestion', 'concern'],
            value='general',
            description='Type:',
            disabled=False,
        )

        comment_input = widgets.Textarea(
            placeholder='Enter your comment here...',
            description='Comment:',
            layout=widgets.Layout(width='100%', height='80px')
        )

        reviewer_input = widgets.Text(
            value=self.reviewer_name,
            description='Your name:',
            layout=widgets.Layout(width='300px')
        )

        add_button = widgets.Button(
            description='💬 Add Comment',
            button_style='info',
            icon='comment'
        )

        output = widgets.Output()

        def update_comments_display():
            """Refresh the comments display."""
            comments = self.comments_mgr.get_comments(item_id)

            if not comments:
                comments_html.value = '<p><em>No comments yet. Be the first to comment!</em></p>'
                return

            # Build comments HTML
            html_parts = []
            for comment in comments:
                comment_type = comment['comment_type']
                icon = {
                    'general': '💬',
                    'question': '❓',
                    'suggestion': '💡',
                    'concern': '⚠️'
                }.get(comment_type, '💬')

                bg_color = {
                    'general': '#f0f0f0',
                    'question': '#e3f2fd',
                    'suggestion': '#fff3e0',
                    'concern': '#ffebee'
                }.get(comment_type, '#f0f0f0')

                html_parts.append(f"""
                <div style="background: {bg_color}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #2196F3;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                        <strong>{icon} {comment['reviewer_name']}</strong>
                        <span style="float: right;">{comment['created_at']}</span>
                    </div>
                    <div style="margin-left: 10px;">
                        {comment['comment_text']}
                    </div>
                </div>
                """)

            comments_html.value = f"""
            <div style="max-height: 300px; overflow-y: auto;">
                <h4>Comments ({len(comments)})</h4>
                {''.join(html_parts)}
            </div>
            """

        def on_add_comment(b):
            """Handle add comment button click."""
            if not comment_input.value.strip():
                with output:
                    clear_output()
                    print("❌ Please enter a comment")
                return

            try:
                self.comments_mgr.add_comment(
                    item_id,
                    reviewer_input.value or "Anonymous",
                    comment_input.value,
                    comment_type_dropdown.value
                )

                with output:
                    clear_output()
                    print(f"✓ Comment added by {reviewer_input.value}")

                # Clear input and refresh display
                comment_input.value = ''
                update_comments_display()

            except Exception as e:
                with output:
                    clear_output()
                    print(f"❌ Error adding comment: {str(e)}")

        add_button.on_click(on_add_comment)

        # Initial display
        update_comments_display()

        return widgets.VBox([
            widgets.HTML('<h3>💬 Field Comments</h3>'),
            comments_html,
            widgets.HTML('<h4>Add New Comment</h4>'),
            widgets.HBox([reviewer_input, comment_type_dropdown]),
            comment_input,
            add_button,
            output
        ])


# ============================================================================
# FEATURE 2: QUALITY SCORE DISPLAY
# ============================================================================

@dataclass
class QualityMetrics:
    """Quality metrics for a documented field."""
    overall_score: float  # 0-100
    completeness_score: float
    ontology_mapping_score: float
    clarity_score: float
    issues: List[str]
    suggestions: List[str]


class QualityScoreCalculator:
    """
    Calculates and displays quality scores for documentation.

    Provides visual feedback on documentation quality to help reviewers
    focus on items that need improvement.
    """

    def calculate_score(self, content: str, metadata: Dict = None) -> QualityMetrics:
        """
        Calculate quality score for documentation content.

        Args:
            content: The documentation markdown content
            metadata: Optional metadata (ontology mappings, etc.)

        Returns:
            QualityMetrics with scores and feedback
        """
        issues = []
        suggestions = []

        # 1. Completeness score (0-100)
        completeness_score = self._assess_completeness(content, issues, suggestions)

        # 2. Ontology mapping score (0-100)
        ontology_score = self._assess_ontology_mapping(content, metadata, issues, suggestions)

        # 3. Clarity score (0-100)
        clarity_score = self._assess_clarity(content, issues, suggestions)

        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.4 +
            ontology_score * 0.3 +
            clarity_score * 0.3
        )

        return QualityMetrics(
            overall_score=round(overall_score, 1),
            completeness_score=round(completeness_score, 1),
            ontology_mapping_score=round(ontology_score, 1),
            clarity_score=round(clarity_score, 1),
            issues=issues,
            suggestions=suggestions
        )

    def _assess_completeness(self, content: str, issues: List, suggestions: List) -> float:
        """Assess documentation completeness."""
        score = 100.0
        required_sections = ['Variable:', 'Description:', 'Data Type:', 'Values:']

        for section in required_sections:
            if section.lower() not in content.lower():
                score -= 20
                issues.append(f"Missing section: {section}")

        # Check for minimal content length
        if len(content) < 100:
            score -= 20
            issues.append("Documentation too brief (< 100 characters)")

        # Bonus for examples
        if 'example' in content.lower() or 'e.g.' in content.lower():
            score = min(100, score + 10)
        else:
            suggestions.append("Consider adding examples")

        return max(0, score)

    def _assess_ontology_mapping(self, content: str, metadata: Dict,
                                 issues: List, suggestions: List) -> float:
        """Assess ontology mapping quality."""
        score = 100.0

        # Check for ontology mentions
        ontologies = ['OMOP', 'LOINC', 'SNOMED', 'ICD']
        found_ontologies = [ont for ont in ontologies if ont in content]

        if not found_ontologies:
            score = 0
            issues.append("No ontology mappings found")
            suggestions.append("Add OMOP, LOINC, or SNOMED mappings if applicable")
        elif len(found_ontologies) == 1:
            score = 70
            suggestions.append(f"Only {found_ontologies[0]} found - consider additional ontologies")
        else:
            score = 100

        # Check for concept IDs (numeric codes)
        if not re.search(r'\b\d{5,}\b', content):
            score -= 20
            suggestions.append("Include specific concept IDs for ontology mappings")

        return max(0, score)

    def _assess_clarity(self, content: str, issues: List, suggestions: List) -> float:
        """Assess documentation clarity."""
        score = 100.0

        # Check for technical jargon without explanation
        jargon_patterns = [
            (r'\b(PHI|PII|HIPAA)\b', "Consider explaining acronyms"),
            (r'\bNULL\b', "Explain what NULL/missing values mean"),
        ]

        for pattern, suggestion in jargon_patterns:
            if re.search(pattern, content):
                # Check if there's an explanation nearby
                if 'means' not in content.lower() and 'defined as' not in content.lower():
                    score -= 5
                    suggestions.append(suggestion)

        # Check sentence structure (basic)
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length > 30:
            score -= 10
            suggestions.append("Consider breaking up long sentences for clarity")

        # Check for positive indicators
        if 'clinical' in content.lower() or 'patient' in content.lower():
            score = min(100, score + 5)  # Bonus for clinical context

        return max(0, score)


class QualityScoreWidget:
    """Visual widget for displaying quality scores."""

    def __init__(self, calculator: QualityScoreCalculator = None):
        self.calculator = calculator or QualityScoreCalculator()

    def create_score_badge(self, score: float) -> str:
        """Create HTML badge for a score."""
        if score >= 80:
            color = '#4CAF50'  # Green
            label = 'Excellent'
        elif score >= 60:
            color = '#FF9800'  # Orange
            label = 'Good'
        else:
            color = '#f44336'  # Red
            label = 'Needs Work'

        return f"""
        <div style="display: inline-block; background: {color}; color: white;
                    padding: 5px 10px; border-radius: 5px; font-weight: bold; margin: 2px;">
            {score:.1f}% {label}
        </div>
        """

    def create_widget(self, content: str, metadata: Dict = None) -> widgets.Widget:
        """Create quality score display widget."""
        metrics = self.calculator.calculate_score(content, metadata)

        # Build HTML display
        html_content = f"""
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h3 style="margin-top: 0;">📊 Quality Assessment</h3>

            <div style="margin: 10px 0;">
                <strong>Overall Score:</strong> {self.create_score_badge(metrics.overall_score)}
            </div>

            <div style="margin: 10px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #e0e0e0;">
                        <th style="padding: 8px; text-align: left;">Metric</th>
                        <th style="padding: 8px; text-align: right;">Score</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Completeness</td>
                        <td style="padding: 8px; text-align: right;">
                            {self.create_score_badge(metrics.completeness_score)}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Ontology Mapping</td>
                        <td style="padding: 8px; text-align: right;">
                            {self.create_score_badge(metrics.ontology_mapping_score)}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Clarity</td>
                        <td style="padding: 8px; text-align: right;">
                            {self.create_score_badge(metrics.clarity_score)}
                        </td>
                    </tr>
                </table>
            </div>
        """

        # Add issues if any
        if metrics.issues:
            html_content += """
            <div style="background: #ffebee; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #f44336;">
                <strong>⚠️ Issues Found:</strong>
                <ul style="margin: 5px 0;">
            """
            for issue in metrics.issues:
                html_content += f"<li>{issue}</li>"
            html_content += "</ul></div>"

        # Add suggestions if any
        if metrics.suggestions:
            html_content += """
            <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #2196F3;">
                <strong>💡 Suggestions:</strong>
                <ul style="margin: 5px 0;">
            """
            for suggestion in metrics.suggestions:
                html_content += f"<li>{suggestion}</li>"
            html_content += "</ul></div>"

        html_content += "</div>"

        return widgets.HTML(html_content)


# ============================================================================
# FEATURE 3: EXCEL EXPORT FUNCTIONALITY
# ============================================================================

class ExcelExporter:
    """
    Export documentation to Excel format.

    Creates a comprehensive Excel workbook with:
    - Data Dictionary sheet
    - Ontology Mappings sheet
    - Quality Metrics sheet
    - Summary sheet
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def export_job_to_excel(self, job_id: str, output_path: str = None) -> str:
        """
        Export a documentation job to Excel format.

        Args:
            job_id: The job ID to export
            output_path: Path to save Excel file (auto-generated if None)

        Returns:
            Path to the created Excel file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"documentation_{job_id}_{timestamp}.xlsx"

        # Get approved items from review queue
        query = """
        SELECT item_id, source_agent, source_data, generated_content,
               approved_content, status, created_at, updated_at
        FROM ReviewQueue
        WHERE job_id = ? AND status = 'Approved'
        ORDER BY item_id
        """
        items = self.db.execute_query(query, (job_id,))

        if not items:
            raise ValueError(f"No approved items found for job {job_id}")

        # Parse items into structured data
        data_dict_rows = []
        ontology_rows = []
        quality_calculator = QualityScoreCalculator()

        for item in items:
            # Parse source data
            try:
                source = json.loads(item['source_data'])
            except:
                source = {}

            content = item['approved_content'] or item['generated_content']

            # Extract key information
            var_name = source.get('variable_name', 'Unknown')
            data_type = source.get('data_type', 'Unknown')
            description = self._extract_description(content)

            # Data dictionary row
            data_dict_rows.append({
                'Variable Name': var_name,
                'Data Type': data_type,
                'Description': description,
                'Full Documentation': content,
                'Source Agent': item['source_agent'],
                'Reviewed': item['updated_at']
            })

            # Ontology mappings
            ontologies = self._extract_ontologies(content, source)
            for ont in ontologies:
                ontology_rows.append({
                    'Variable Name': var_name,
                    'Ontology System': ont['system'],
                    'Concept ID': ont['concept_id'],
                    'Concept Name': ont['concept_name']
                })

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Data Dictionary
            dd_df = pd.DataFrame(data_dict_rows)
            dd_df.to_excel(writer, sheet_name='Data Dictionary', index=False)

            # Sheet 2: Ontology Mappings
            if ontology_rows:
                ont_df = pd.DataFrame(ontology_rows)
                ont_df.to_excel(writer, sheet_name='Ontology Mappings', index=False)

            # Sheet 3: Summary
            summary_data = {
                'Metric': [
                    'Total Variables',
                    'Documentation Date',
                    'Job ID',
                    'Ontology Mappings Count'
                ],
                'Value': [
                    len(data_dict_rows),
                    datetime.now().strftime("%Y-%m-%d"),
                    job_id,
                    len(ontology_rows)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        logger.info(f"Exported {len(data_dict_rows)} variables to {output_path}")
        return output_path

    def _extract_description(self, content: str) -> str:
        """Extract brief description from full documentation."""
        # Look for description section
        match = re.search(r'##?\s*Description:?\s*(.+?)(?:##|$)', content, re.DOTALL | re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            # Take first sentence or 200 chars
            first_sentence = desc.split('.')[0]
            return first_sentence[:200] if len(first_sentence) < 200 else first_sentence[:197] + '...'
        return "See full documentation"

    def _extract_ontologies(self, content: str, source: Dict) -> List[Dict]:
        """Extract ontology mappings from content."""
        ontologies = []

        # OMOP patterns
        omop_matches = re.findall(r'OMOP[:\s]+(\d+)[:\s]*([^,\n]+)', content)
        for concept_id, concept_name in omop_matches:
            ontologies.append({
                'system': 'OMOP',
                'concept_id': concept_id.strip(),
                'concept_name': concept_name.strip()
            })

        # LOINC patterns
        loinc_matches = re.findall(r'LOINC[:\s]+([\d-]+)[:\s]*([^,\n]+)', content)
        for concept_id, concept_name in loinc_matches:
            ontologies.append({
                'system': 'LOINC',
                'concept_id': concept_id.strip(),
                'concept_name': concept_name.strip()
            })

        # SNOMED patterns
        snomed_matches = re.findall(r'SNOMED[:\s]+(\d+)[:\s]*([^,\n]+)', content)
        for concept_id, concept_name in snomed_matches:
            ontologies.append({
                'system': 'SNOMED CT',
                'concept_id': concept_id.strip(),
                'concept_name': concept_name.strip()
            })

        return ontologies


class ExcelExportWidget:
    """Interactive widget for Excel export."""

    def __init__(self, excel_exporter: ExcelExporter):
        self.exporter = excel_exporter

    def create_widget(self, job_id: str) -> widgets.Widget:
        """Create Excel export widget."""
        output = widgets.Output()

        filename_input = widgets.Text(
            value=f'documentation_{job_id}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            description='Filename:',
            layout=widgets.Layout(width='500px')
        )

        export_button = widgets.Button(
            description='📊 Export to Excel',
            button_style='success',
            icon='file-excel'
        )

        download_link_html = widgets.HTML()

        def on_export(b):
            """Handle export button click."""
            with output:
                clear_output()
                print(f"📊 Exporting job {job_id} to Excel...")

                try:
                    filepath = self.exporter.export_job_to_excel(
                        job_id,
                        filename_input.value
                    )
                    print(f"✓ Successfully exported to: {filepath}")

                    # Create download link
                    download_link_html.value = f"""
                    <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <strong>✓ Export Complete!</strong><br/>
                        File saved: <code>{filepath}</code><br/>
                        <a href="files/{filepath}" download="{filepath}">
                            📥 Click here to download
                        </a>
                    </div>
                    """

                except Exception as e:
                    print(f"❌ Export failed: {str(e)}")
                    logger.error(f"Excel export failed: {e}", exc_info=True)

        export_button.on_click(on_export)

        return widgets.VBox([
            widgets.HTML('<h3>📊 Excel Export</h3>'),
            widgets.HTML("""
            <p>Export documentation to Excel format with multiple sheets:</p>
            <ul>
                <li><strong>Data Dictionary</strong> - All variables with descriptions</li>
                <li><strong>Ontology Mappings</strong> - OMOP, LOINC, SNOMED mappings</li>
                <li><strong>Summary</strong> - Job statistics and metadata</li>
            </ul>
            """),
            filename_input,
            export_button,
            download_link_html,
            output
        ])


# ============================================================================
# FEATURE 4: VERSION COMPARISON UI
# ============================================================================

class VersionComparisonWidget:
    """
    Visual comparison of documentation versions.

    Shows side-by-side diffs and highlights changes between versions.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def _get_versions(self, variable_name: str, job_id: str = None) -> List[Dict]:
        """Get all versions of a variable's documentation."""
        # In a real implementation, this would query a versions table
        # For now, we'll query the ReviewQueue for different statuses
        query = """
        SELECT item_id, generated_content, approved_content, status,
               created_at, updated_at, source_agent
        FROM ReviewQueue
        WHERE source_data LIKE ?
        ORDER BY updated_at DESC
        """
        pattern = f'%"variable_name": "{variable_name}"%'
        versions = self.db.execute_query(query, (pattern,))
        return versions

    def _highlight_differences(self, old_text: str, new_text: str) -> Tuple[str, str]:
        """
        Highlight differences between two texts.

        Returns HTML-formatted versions with changes highlighted.
        """
        # Simple word-level diff
        old_words = old_text.split()
        new_words = new_text.split()

        # Basic diff (in production, use difflib)
        old_html = []
        new_html = []

        max_len = max(len(old_words), len(new_words))
        for i in range(max_len):
            old_word = old_words[i] if i < len(old_words) else ""
            new_word = new_words[i] if i < len(new_words) else ""

            if old_word != new_word:
                if old_word:
                    old_html.append(f'<span style="background: #ffcdd2; text-decoration: line-through;">{old_word}</span>')
                if new_word:
                    new_html.append(f'<span style="background: #c8e6c9;">{new_word}</span>')
            else:
                old_html.append(old_word)
                new_html.append(new_word)

        return ' '.join(old_html), ' '.join(new_html)

    def create_widget(self, variable_name: str, job_id: str = None) -> widgets.Widget:
        """Create version comparison widget."""
        versions = self._get_versions(variable_name, job_id)

        if len(versions) < 2:
            return widgets.HTML(f"""
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px;">
                    <strong>ℹ️ Only one version available</strong><br/>
                    No previous versions to compare.
                </div>
            """)

        # Version selectors
        version_options = [
            (f"v{i+1} - {v['updated_at']} ({v['status']})", i)
            for i, v in enumerate(versions)
        ]

        old_version_selector = widgets.Dropdown(
            options=version_options,
            value=1,  # Second newest
            description='Old Version:',
        )

        new_version_selector = widgets.Dropdown(
            options=version_options,
            value=0,  # Newest
            description='New Version:',
        )

        comparison_html = widgets.HTML()
        stats_html = widgets.HTML()

        def update_comparison(change=None):
            """Update the comparison display."""
            old_idx = old_version_selector.value
            new_idx = new_version_selector.value

            old_version = versions[old_idx]
            new_version = versions[new_idx]

            old_content = old_version['approved_content'] or old_version['generated_content']
            new_content = new_version['approved_content'] or new_version['generated_content']

            old_highlighted, new_highlighted = self._highlight_differences(old_content, new_content)

            comparison_html.value = f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div style="background: #fff; padding: 10px; border-radius: 5px; border: 2px solid #ffcdd2;">
                    <h4 style="margin-top: 0;">Old Version (v{old_idx+1})</h4>
                    <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
                        {old_version['updated_at']}<br/>
                        Status: {old_version['status']}<br/>
                        Agent: {old_version['source_agent']}
                    </div>
                    <div style="max-height: 400px; overflow-y: auto; padding: 10px; background: #f5f5f5;">
                        {old_highlighted}
                    </div>
                </div>

                <div style="background: #fff; padding: 10px; border-radius: 5px; border: 2px solid #c8e6c9;">
                    <h4 style="margin-top: 0;">New Version (v{new_idx+1})</h4>
                    <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
                        {new_version['updated_at']}<br/>
                        Status: {new_version['status']}<br/>
                        Agent: {new_version['source_agent']}
                    </div>
                    <div style="max-height: 400px; overflow-y: auto; padding: 10px; background: #f5f5f5;">
                        {new_highlighted}
                    </div>
                </div>
            </div>
            """

            # Calculate stats
            words_added = new_content.split().__len__() - old_content.split().__len__()
            chars_added = len(new_content) - len(old_content)

            stats_html.value = f"""
            <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                <strong>📊 Change Statistics:</strong><br/>
                Words: {words_added:+d} | Characters: {chars_added:+d}
            </div>
            """

        old_version_selector.observe(update_comparison, names='value')
        new_version_selector.observe(update_comparison, names='value')

        # Initial display
        update_comparison()

        return widgets.VBox([
            widgets.HTML(f'<h3>🔄 Version Comparison: {variable_name}</h3>'),
            widgets.HTML(f'<p>Total versions: {len(versions)}</p>'),
            widgets.HBox([old_version_selector, new_version_selector]),
            stats_html,
            comparison_html
        ])


# ============================================================================
# FEATURE 5: TEMPLATE LIBRARY
# ============================================================================

class TemplateLibrary:
    """
    Pre-built templates for common research data patterns.

    Includes standard demographics, clinical assessments, lab values, etc.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_templates_table()
        self._load_default_templates()

    def _ensure_templates_table(self):
        """Create templates table."""
        schema = """
        CREATE TABLE IF NOT EXISTS FieldTemplates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            field_pattern TEXT NOT NULL,
            documentation_template TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.db.cursor.execute(schema)
        self.db.conn.commit()

    def _load_default_templates(self):
        """Load default template library."""
        templates = [
            {
                'name': 'demographics_age',
                'category': 'Demographics',
                'pattern': r'age|years_old',
                'template': '''## Variable: {var_name}

**Description:** Patient age at time of enrollment/measurement

**Data Type:** Integer

**Valid Range:** 0-120 years

**Units:** Years

**Ontology Mappings:**
- OMOP Concept: 4265453 (Age)
- LOINC: 21611-9 (Age at enrollment)

**Clinical Context:**
Age is a fundamental demographic variable used for:
- Eligibility screening
- Age-stratified analysis
- Risk factor assessment

**Missing Values:**
- NULL indicates age not collected
- May be grouped (e.g., 18-25, 26-35) for privacy

**Example Values:**
- 45 (45 years old)
- 32 (32 years old)
'''},
            {
                'name': 'demographics_sex',
                'category': 'Demographics',
                'pattern': r'\b(sex|gender)\b',
                'template': '''## Variable: {var_name}

**Description:** Biological sex or gender identity

**Data Type:** Categorical

**Valid Values:**
- 1: Male
- 2: Female
- 3: Other/Non-binary
- 9: Prefer not to answer

**Ontology Mappings:**
- OMOP Concept: 8507 (Male), 8532 (Female)
- SNOMED CT: 248153007 (Male), 248152002 (Female)

**Clinical Context:**
Used for sex-specific analysis, medication dosing, and risk stratification.

**Note:** Distinguish between biological sex (at birth) and gender identity based on study needs.

**Missing Values:**
- NULL indicates not collected

**Example Values:**
- 1 (Male)
- 2 (Female)
'''},
            {
                'name': 'demographics_race',
                'category': 'Demographics',
                'pattern': r'race|ethnicity',
                'template': '''## Variable: {var_name}

**Description:** Self-reported race/ethnicity

**Data Type:** Categorical

**Valid Values (OMB Categories):**
- 1: American Indian or Alaska Native
- 2: Asian
- 3: Black or African American
- 4: Native Hawaiian or Other Pacific Islander
- 5: White
- 6: More than one race
- 99: Unknown or not reported

**Regulatory:**
Follows OMB Statistical Policy Directive 15 categories

**Ontology Mappings:**
- OMOP Concept: 8516 (Black or African American), 8527 (White), etc.

**Clinical Context:**
Used for health disparities research and demographic reporting.

**Privacy:** May be grouped for small cell sizes

**Missing Values:**
- NULL indicates not collected

**Example Values:**
- 3 (Black or African American)
- 5 (White)
'''},
            {
                'name': 'vitals_blood_pressure',
                'category': 'Vital Signs',
                'pattern': r'(systolic|diastolic|blood_pressure|bp_sys|bp_dia)',
                'template': '''## Variable: {var_name}

**Description:** Blood pressure measurement

**Data Type:** Integer (Systolic) or Integer (Diastolic)

**Valid Range:**
- Systolic: 70-250 mmHg
- Diastolic: 40-150 mmHg

**Units:** mmHg (millimeters of mercury)

**Ontology Mappings:**
- LOINC: 8480-6 (Systolic blood pressure), 8462-4 (Diastolic blood pressure)
- OMOP Concept: 3004249 (Systolic), 3012888 (Diastolic)
- SNOMED CT: 271649006 (Systolic BP), 271650006 (Diastolic BP)

**Clinical Context:**
Blood pressure is a key vital sign for cardiovascular health assessment.

**Collection Method:**
- Position: Seated, arm at heart level
- Device: Automated oscillometric or manual sphygmomanometer
- Timing: After 5 minutes of rest

**Quality Flags:**
Values outside normal range (Systolic <90 or >180, Diastolic <60 or >120) may indicate:
- Measurement error
- Critical clinical condition
- Require verification

**Missing Values:**
- NULL indicates not measured

**Example Values:**
- Systolic: 120 (normal), 140 (stage 1 hypertension)
- Diastolic: 80 (normal), 90 (stage 1 hypertension)
'''},
            {
                'name': 'labs_complete_blood_count',
                'category': 'Laboratory',
                'pattern': r'(wbc|rbc|hemoglobin|hematocrit|platelet)',
                'template': '''## Variable: {var_name}

**Description:** Complete Blood Count (CBC) component

**Data Type:** Float

**Valid Range:** Varies by component
- WBC: 3.5-10.5 K/uL
- RBC: 4.5-5.5 M/uL (male), 4.0-5.0 M/uL (female)
- Hemoglobin: 13.5-17.5 g/dL (male), 12.0-16.0 g/dL (female)
- Hematocrit: 38-50% (male), 36-44% (female)
- Platelets: 150-400 K/uL

**Ontology Mappings (LOINC):**
- WBC: 6690-2
- RBC: 789-8
- Hemoglobin: 718-7
- Hematocrit: 4544-3
- Platelets: 777-3

**Clinical Context:**
CBC is ordered to evaluate overall health and detect disorders such as anemia, infection, and blood cancers.

**Specimen:** Whole blood (EDTA tube, purple top)

**Quality Notes:**
- Hemolyzed samples may affect results
- Time-sensitive: analyze within 24 hours

**Missing Values:**
- NULL indicates test not performed or invalid result

**Example Values:**
- WBC: 7.2 K/uL (normal)
- Hemoglobin: 14.5 g/dL (normal male)
'''}
        ]

        # Insert templates if they don't exist
        for tmpl in templates:
            try:
                query = """
                INSERT OR IGNORE INTO FieldTemplates
                (template_name, category, field_pattern, documentation_template, metadata)
                VALUES (?, ?, ?, ?, ?)
                """
                metadata = json.dumps({'version': '1.0', 'validated': True})
                self.db.execute_update(
                    query,
                    (tmpl['name'], tmpl['category'], tmpl['pattern'],
                     tmpl['template'], metadata)
                )
            except Exception as e:
                logger.warning(f"Could not insert template {tmpl['name']}: {e}")

    def find_matching_template(self, variable_name: str) -> Optional[Dict]:
        """Find a template that matches the variable name."""
        query = "SELECT * FROM FieldTemplates ORDER BY template_id"
        templates = self.db.execute_query(query)

        for template in templates:
            pattern = template['field_pattern']
            if re.search(pattern, variable_name, re.IGNORECASE):
                return template

        return None

    def apply_template(self, variable_name: str, template_name: str = None) -> str:
        """Apply a template to generate documentation."""
        if template_name:
            query = "SELECT * FROM FieldTemplates WHERE template_name = ?"
            templates = self.db.execute_query(query, (template_name,))
            template = templates[0] if templates else None
        else:
            template = self.find_matching_template(variable_name)

        if not template:
            return None

        # Format template with variable name
        documentation = template['documentation_template'].format(var_name=variable_name)
        return documentation

    def list_templates(self, category: str = None) -> List[Dict]:
        """List available templates."""
        if category:
            query = "SELECT * FROM FieldTemplates WHERE category = ? ORDER BY template_name"
            return self.db.execute_query(query, (category,))
        else:
            query = "SELECT * FROM FieldTemplates ORDER BY category, template_name"
            return self.db.execute_query(query)


class TemplateLibraryWidget:
    """Interactive widget for browsing and applying templates."""

    def __init__(self, template_library: TemplateLibrary):
        self.library = template_library

    def create_widget(self) -> widgets.Widget:
        """Create template library browser widget."""
        templates = self.library.list_templates()

        # Group by category
        categories = {}
        for template in templates:
            cat = template['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)

        # Category selector
        category_dropdown = widgets.Dropdown(
            options=['All'] + list(categories.keys()),
            value='All',
            description='Category:',
        )

        templates_list = widgets.Select(
            options=[],
            description='Template:',
            layout=widgets.Layout(width='100%', height='150px')
        )

        preview_html = widgets.HTML()
        variable_input = widgets.Text(
            placeholder='Enter variable name to apply template...',
            description='Variable:',
            layout=widgets.Layout(width='400px')
        )

        apply_button = widgets.Button(
            description='Apply Template',
            button_style='primary',
            icon='magic'
        )

        output = widgets.Output()

        def update_templates_list(change):
            """Update templates list based on category selection."""
            category = category_dropdown.value

            if category == 'All':
                tmpl_list = templates
            else:
                tmpl_list = categories.get(category, [])

            templates_list.options = [
                (f"{t['template_name']} - {t['category']}", t['template_name'])
                for t in tmpl_list
            ]

        def update_preview(change):
            """Update template preview."""
            template_name = templates_list.value
            if not template_name:
                return

            query = "SELECT * FROM FieldTemplates WHERE template_name = ?"
            result = self.library.db.execute_query(query, (template_name,))

            if result:
                template = result[0]
                preview_html.value = f"""
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h4>{template['template_name']}</h4>
                    <p><strong>Category:</strong> {template['category']}</p>
                    <p><strong>Pattern:</strong> <code>{template['field_pattern']}</code></p>
                    <div style="background: white; padding: 10px; border-radius: 3px; margin-top: 10px; max-height: 300px; overflow-y: auto;">
                        <pre>{template['documentation_template'][:500]}...</pre>
                    </div>
                </div>
                """

        def on_apply_template(b):
            """Apply template to variable."""
            if not variable_input.value:
                with output:
                    clear_output()
                    print("❌ Please enter a variable name")
                return

            template_name = templates_list.value
            if not template_name:
                with output:
                    clear_output()
                    print("❌ Please select a template")
                return

            try:
                documentation = self.library.apply_template(
                    variable_input.value,
                    template_name
                )

                with output:
                    clear_output()
                    print(f"✓ Applied template to '{variable_input.value}'")
                    print("\n" + "="*60)
                    print(documentation)
                    print("="*60)

            except Exception as e:
                with output:
                    clear_output()
                    print(f"❌ Error applying template: {e}")

        category_dropdown.observe(update_templates_list, names='value')
        templates_list.observe(update_preview, names='value')
        apply_button.on_click(on_apply_template)

        # Initial update
        update_templates_list(None)

        return widgets.VBox([
            widgets.HTML('<h3>📚 Template Library</h3>'),
            widgets.HTML(f'<p>Available templates: {len(templates)}</p>'),
            category_dropdown,
            templates_list,
            preview_html,
            widgets.HTML('<h4>Apply Template</h4>'),
            variable_input,
            apply_button,
            output
        ])


# ============================================================================
# INSTALLATION AND USAGE
# ============================================================================

print("""
╔══════════════════════════════════════════════════════════════════╗
║              NEW FEATURES IMPLEMENTATION LOADED                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ Feature 1: Field-Level Comments System                       ║
║     - CommentsManager for database operations                    ║
║     - CommentsWidget for interactive UI                          ║
║     - Threaded comments with types (general/question/etc)        ║
║                                                                  ║
║  ✅ Feature 2: Quality Score Display                             ║
║     - QualityScoreCalculator for scoring                         ║
║     - QualityScoreWidget for visual display                      ║
║     - Scores: Completeness, Ontology, Clarity                    ║
║                                                                  ║
║  ✅ Feature 3: Excel Export Functionality                        ║
║     - ExcelExporter for multi-sheet exports                      ║
║     - ExcelExportWidget for UI                                   ║
║     - Sheets: Data Dictionary, Ontology, Summary                 ║
║                                                                  ║
║  ✅ Feature 4: Version Comparison UI                             ║
║     - VersionComparisonWidget for side-by-side diffs             ║
║     - Highlights changes between versions                        ║
║     - Change statistics                                          ║
║                                                                  ║
║  ✅ Feature 5: Template Library                                  ║
║     - TemplateLibrary with pre-built templates                   ║
║     - Demographics, vitals, labs templates                       ║
║     - TemplateLibraryWidget for browsing                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

USAGE EXAMPLES:

1. Field-Level Comments:
   ```python
   # Setup
   comments_mgr = CommentsManager(db)
   comments_widget = CommentsWidget(comments_mgr, reviewer_name="Dr. Smith")

   # Display comments for an item
   display(comments_widget.create_widget(item_id=123))

   # Add comment programmatically
   comments_mgr.add_comment(123, "Dr. Smith", "This needs clarification", "question")
   ```

2. Quality Scores:
   ```python
   # Calculate score
   calculator = QualityScoreCalculator()
   metrics = calculator.calculate_score(documentation_content)

   # Display score widget
   score_widget = QualityScoreWidget(calculator)
   display(score_widget.create_widget(documentation_content))
   ```

3. Excel Export:
   ```python
   # Export to Excel
   exporter = ExcelExporter(db)
   filepath = exporter.export_job_to_excel("job-12345")

   # Or use widget
   export_widget = ExcelExportWidget(exporter)
   display(export_widget.create_widget("job-12345"))
   ```

4. Version Comparison:
   ```python
   # Compare versions
   comp_widget = VersionComparisonWidget(db)
   display(comp_widget.create_widget("blood_pressure_sys"))
   ```

5. Template Library:
   ```python
   # Browse templates
   library = TemplateLibrary(db)
   lib_widget = TemplateLibraryWidget(library)
   display(lib_widget.create_widget())

   # Apply template
   doc = library.apply_template("patient_age", "demographics_age")
   print(doc)
   ```

""")
