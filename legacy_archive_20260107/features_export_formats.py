"""
Export Format Implementations
==============================

Additional export formats for ADE documentation:
- HTML Dashboard Export
- JSON Schema Export
- PDF Export (basic)
- Markdown Export
- REDCap Data Dictionary Format

Installation:
    %run features_export_formats.py
"""

import json
import pandas as pd
import re
from typing import List, Dict, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger('ADE.ExportFormats')


# ============================================================================
# HTML DASHBOARD EXPORT
# ============================================================================

class HTMLDashboardExporter:
    """
    Export documentation as an interactive HTML dashboard.

    Creates a single-page application with:
    - Searchable/filterable table of variables
    - Detailed view panels
    - Ontology mapping visualization
    - Quality metrics display
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def export_to_html(self, job_id: str, output_path: str = None) -> str:
        """
        Export job documentation to interactive HTML dashboard.

        Args:
            job_id: The job ID to export
            output_path: Path to save HTML file (auto-generated if None)

        Returns:
            Path to the created HTML file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"dashboard_{job_id}_{timestamp}.html"

        # Get approved items
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

        # Build HTML
        html_content = self._generate_html(items, job_id)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Exported {len(items)} variables to HTML dashboard: {output_path}")
        return output_path

    def _generate_html(self, items: List[Dict], job_id: str) -> str:
        """Generate complete HTML document."""

        # Parse items
        variables_data = []
        for item in items:
            try:
                source = json.loads(item['source_data'])
            except:
                source = {}

            content = item['approved_content'] or item['generated_content']

            var_data = {
                'name': source.get('variable_name', 'Unknown'),
                'data_type': source.get('data_type', 'Unknown'),
                'description': self._extract_brief_description(content),
                'full_content': content,
                'ontologies': self._extract_ontology_badges(content),
                'item_id': item['item_id'],
                'updated_at': item['updated_at']
            }
            variables_data.append(var_data)

        # Build data table rows
        table_rows = []
        for var in variables_data:
            table_rows.append(f"""
                <tr onclick="showDetails('{var['name']}')" style="cursor: pointer;">
                    <td>{var['name']}</td>
                    <td><span class="badge badge-type">{var['data_type']}</span></td>
                    <td>{var['description']}</td>
                    <td>{var['ontologies']}</td>
                    <td>{var['updated_at']}</td>
                </tr>
            """)

        # Build detail panels (hidden by default)
        detail_panels = []
        for var in variables_data:
            detail_panels.append(f"""
                <div id="details-{var['name']}" class="detail-panel" style="display: none;">
                    <h2>{var['name']}</h2>
                    <div class="markdown-content">
                        {self._markdown_to_html(var['full_content'])}
                    </div>
                </div>
            """)

        # Generate JavaScript data
        js_data = json.dumps(variables_data, indent=2)

        # Complete HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Dictionary Dashboard - {job_id}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            margin-bottom: 0.5rem;
        }}

        .header .subtitle {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .search-bar {{
            background: white;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .search-bar input {{
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .stat-card .label {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}

        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }}

        .table-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            overflow: hidden;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: #f8f9fa;
        }}

        th {{
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        .badge-type {{
            background: #e3f2fd;
            color: #1976d2;
        }}

        .badge-ontology {{
            background: #f3e5f5;
            color: #7b1fa2;
            margin-right: 0.25rem;
        }}

        .detail-panel {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-top: 1rem;
        }}

        .detail-panel h2 {{
            color: #667eea;
            margin-bottom: 1rem;
        }}

        .markdown-content {{
            line-height: 1.8;
        }}

        .markdown-content h2 {{
            color: #333;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            font-size: 1.5rem;
        }}

        .markdown-content h3 {{
            color: #555;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            font-size: 1.25rem;
        }}

        .markdown-content p {{
            margin-bottom: 1rem;
        }}

        .markdown-content ul, .markdown-content ol {{
            margin-left: 2rem;
            margin-bottom: 1rem;
        }}

        .markdown-content li {{
            margin-bottom: 0.5rem;
        }}

        .markdown-content code {{
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}

        .markdown-content pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 1rem;
        }}

        .back-button {{
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            margin-bottom: 1rem;
            text-decoration: none;
        }}

        .back-button:hover {{
            background: #5568d3;
        }}

        #tableView {{
            display: block;
        }}

        #detailView {{
            display: none;
        }}

        .no-results {{
            text-align: center;
            padding: 3rem;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Data Dictionary Dashboard</h1>
        <div class="subtitle">Job ID: {job_id} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>

    <div class="container">
        <div id="tableView">
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="🔍 Search variables, descriptions, or ontologies..." onkeyup="filterTable()">
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="label">Total Variables</div>
                    <div class="value" id="totalVars">{len(variables_data)}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Documented</div>
                    <div class="value">{len(variables_data)}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Last Updated</div>
                    <div class="value" style="font-size: 1.2rem;">{items[0]['updated_at'] if items else 'N/A'}</div>
                </div>
            </div>

            <div class="table-container">
                <table id="variablesTable">
                    <thead>
                        <tr>
                            <th>Variable Name</th>
                            <th>Data Type</th>
                            <th>Description</th>
                            <th>Ontology Mappings</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </div>

        <div id="detailView">
            <button class="back-button" onclick="showTable()">← Back to Table</button>
            <div id="detailContent">
                {''.join(detail_panels)}
            </div>
        </div>
    </div>

    <script>
        const variablesData = {js_data};

        function filterTable() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('variablesTable');
            const rows = table.getElementsByTagName('tr');
            let visibleCount = 0;

            for (let i = 1; i < rows.length; i++) {{
                const row = rows[i];
                const text = row.textContent || row.innerText;

                if (text.toUpperCase().indexOf(filter) > -1) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }}

            document.getElementById('totalVars').textContent = visibleCount;
        }}

        function showDetails(varName) {{
            document.getElementById('tableView').style.display = 'none';
            document.getElementById('detailView').style.display = 'block';

            // Hide all detail panels
            const panels = document.querySelectorAll('.detail-panel');
            panels.forEach(panel => panel.style.display = 'none');

            // Show selected panel
            const panel = document.getElementById('details-' + varName);
            if (panel) {{
                panel.style.display = 'block';
            }}

            // Scroll to top
            window.scrollTo(0, 0);
        }}

        function showTable() {{
            document.getElementById('tableView').style.display = 'block';
            document.getElementById('detailView').style.display = 'none';
            window.scrollTo(0, 0);
        }}

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                showTable();
            }}
        }});
    </script>
</body>
</html>"""

        return html

    def _extract_brief_description(self, content: str) -> str:
        """Extract brief description from content."""
        # Look for description section
        match = re.search(r'##?\s*Description:?\s*(.+?)(?:##|\n\n|$)', content, re.DOTALL | re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            # Take first sentence or 150 chars
            first_sentence = desc.split('.')[0]
            return first_sentence[:150] if len(first_sentence) < 150 else first_sentence[:147] + '...'
        return "No description available"

    def _extract_ontology_badges(self, content: str) -> str:
        """Extract and format ontology mappings as HTML badges."""
        badges = []

        if 'OMOP' in content:
            badges.append('<span class="badge badge-ontology">OMOP</span>')
        if 'LOINC' in content:
            badges.append('<span class="badge badge-ontology">LOINC</span>')
        if 'SNOMED' in content:
            badges.append('<span class="badge badge-ontology">SNOMED</span>')
        if 'ICD' in content:
            badges.append('<span class="badge badge-ontology">ICD</span>')

        return ''.join(badges) if badges else '<span style="color: #999;">None</span>'

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (basic conversion)."""
        html = markdown

        # Headers
        html = re.sub(r'###\s+(.+)', r'<h3>\1</h3>', html)
        html = re.sub(r'##\s+(.+)', r'<h2>\1</h2>', html)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Lists
        html = re.sub(r'^\s*-\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)

        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'

        # Code blocks
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        return html


# ============================================================================
# JSON SCHEMA EXPORT
# ============================================================================

@dataclass
class JSONSchemaField:
    """JSON Schema representation of a data dictionary field."""
    name: str
    type: str
    description: str
    enum: Optional[List] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None
    format: Optional[str] = None
    ontology_mappings: Optional[Dict] = None


class JSONSchemaExporter:
    """
    Export documentation as JSON Schema for validation.

    Creates JSON Schema (Draft 7) from data dictionary.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def export_to_json_schema(self, job_id: str, output_path: str = None) -> str:
        """
        Export job documentation to JSON Schema.

        Args:
            job_id: The job ID to export
            output_path: Path to save JSON file (auto-generated if None)

        Returns:
            Path to the created JSON Schema file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"schema_{job_id}_{timestamp}.json"

        # Get approved items
        query = """
        SELECT item_id, source_agent, source_data, generated_content,
               approved_content, status
        FROM ReviewQueue
        WHERE job_id = ? AND status = 'Approved'
        ORDER BY item_id
        """
        items = self.db.execute_query(query, (job_id,))

        if not items:
            raise ValueError(f"No approved items found for job {job_id}")

        # Build schema
        schema = self._build_schema(items, job_id)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Exported {len(items)} fields to JSON Schema: {output_path}")
        return output_path

    def _build_schema(self, items: List[Dict], job_id: str) -> Dict:
        """Build JSON Schema from items."""
        properties = {}
        required = []

        for item in items:
            try:
                source = json.loads(item['source_data'])
            except:
                source = {}

            content = item['approved_content'] or item['generated_content']

            var_name = source.get('variable_name', f'field_{item["item_id"]}')
            data_type = source.get('data_type', 'string')

            # Build field schema
            field_schema = self._build_field_schema(var_name, data_type, content, source)
            properties[var_name] = field_schema

            # Check if required (simple heuristic: not nullable)
            if not source.get('nullable', True):
                required.append(var_name)

        # Complete schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"https://example.com/schemas/{job_id}.json",
            "title": f"Data Dictionary Schema - {job_id}",
            "description": f"JSON Schema for data validation (generated {datetime.now().isoformat()})",
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    def _build_field_schema(self, var_name: str, data_type: str, content: str, source: Dict) -> Dict:
        """Build JSON Schema for a single field."""
        field = {
            "description": self._extract_description(content)
        }

        # Map data types to JSON Schema types
        type_mapping = {
            'integer': 'integer',
            'int': 'integer',
            'float': 'number',
            'double': 'number',
            'numeric': 'number',
            'string': 'string',
            'text': 'string',
            'boolean': 'boolean',
            'bool': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'timestamp': 'string',
        }

        json_type = type_mapping.get(data_type.lower(), 'string')
        field["type"] = json_type

        # Add format for dates
        if data_type.lower() in ['date', 'datetime', 'timestamp']:
            field["format"] = "date-time" if 'time' in data_type.lower() else "date"

        # Extract constraints from content
        constraints = self._extract_constraints(content)

        if json_type in ['integer', 'number']:
            if constraints.get('min') is not None:
                field["minimum"] = constraints['min']
            if constraints.get('max') is not None:
                field["maximum"] = constraints['max']

        # Extract enum values if categorical
        enum_values = self._extract_enum_values(content)
        if enum_values:
            field["enum"] = enum_values

        # Add ontology mappings as custom property
        ontologies = self._extract_ontologies_for_schema(content)
        if ontologies:
            field["x-ontology-mappings"] = ontologies

        return field

    def _extract_description(self, content: str) -> str:
        """Extract description from content."""
        match = re.search(r'##?\s*Description:?\s*(.+?)(?:##|\n\n|$)', content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "No description available"

    def _extract_constraints(self, content: str) -> Dict:
        """Extract numeric constraints from content."""
        constraints = {}

        # Look for range specifications
        range_match = re.search(r'(?:Valid Range|Range):?\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
        if range_match:
            constraints['min'] = float(range_match.group(1))
            constraints['max'] = float(range_match.group(2))

        return constraints

    def _extract_enum_values(self, content: str) -> Optional[List]:
        """Extract enum values from content."""
        # Look for value mappings like "1: Male, 2: Female"
        pattern = r'(?:Valid Values|Values|Coding):?\s*\n((?:\s*[-•\d]+[:\.].*\n?)+)'
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            values_text = match.group(1)
            # Extract numeric codes
            codes = re.findall(r'(\d+)\s*:', values_text)
            if codes:
                return [int(c) for c in codes]

        return None

    def _extract_ontologies_for_schema(self, content: str) -> Dict:
        """Extract ontology mappings for schema."""
        ontologies = {}

        # OMOP
        omop_matches = re.findall(r'OMOP[:\s]+(\d+)', content)
        if omop_matches:
            ontologies['omop_concept_id'] = omop_matches[0]

        # LOINC
        loinc_matches = re.findall(r'LOINC[:\s]+([\d-]+)', content)
        if loinc_matches:
            ontologies['loinc_code'] = loinc_matches[0]

        # SNOMED
        snomed_matches = re.findall(r'SNOMED[:\s]+(\d+)', content)
        if snomed_matches:
            ontologies['snomed_concept_id'] = snomed_matches[0]

        return ontologies if ontologies else None


# ============================================================================
# REDCAP DATA DICTIONARY EXPORT
# ============================================================================

class REDCapExporter:
    """
    Export to REDCap data dictionary format.

    REDCap format is CSV with specific columns:
    - Variable / Field Name
    - Form Name
    - Section Header
    - Field Type
    - Field Label
    - Choices, Calculations, OR Slider Labels
    - Field Note
    - Text Validation Type OR Show Slider Number
    - Text Validation Min
    - Text Validation Max
    - Identifier?
    - Branching Logic (Show field only if...)
    - Required Field?
    - Custom Alignment
    - Question Number (surveys only)
    - Matrix Group Name
    - Matrix Ranking?
    - Field Annotation
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def export_to_redcap(self, job_id: str, output_path: str = None, form_name: str = "data_collection") -> str:
        """
        Export to REDCap data dictionary CSV format.

        Args:
            job_id: The job ID to export
            output_path: Path to save CSV file
            form_name: REDCap form name

        Returns:
            Path to created file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"redcap_dict_{job_id}_{timestamp}.csv"

        # Get approved items
        query = """
        SELECT source_data, generated_content, approved_content
        FROM ReviewQueue
        WHERE job_id = ? AND status = 'Approved'
        ORDER BY item_id
        """
        items = self.db.execute_query(query, (job_id,))

        if not items:
            raise ValueError(f"No approved items found for job {job_id}")

        # Build REDCap rows
        redcap_rows = []
        for item in items:
            try:
                source = json.loads(item['source_data'])
            except:
                source = {}

            content = item['approved_content'] or item['generated_content']
            redcap_row = self._build_redcap_row(source, content, form_name)
            redcap_rows.append(redcap_row)

        # Create DataFrame
        df = pd.DataFrame(redcap_rows)

        # Ensure all required columns exist
        required_columns = [
            'Variable / Field Name',
            'Form Name',
            'Section Header',
            'Field Type',
            'Field Label',
            'Choices, Calculations, OR Slider Labels',
            'Field Note',
            'Text Validation Type OR Show Slider Number',
            'Text Validation Min',
            'Text Validation Max',
            'Identifier?',
            'Branching Logic (Show field only if...)',
            'Required Field?',
            'Custom Alignment',
            'Question Number (surveys only)',
            'Matrix Group Name',
            'Matrix Ranking?',
            'Field Annotation'
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = ''

        # Reorder columns
        df = df[required_columns]

        # Save
        df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(redcap_rows)} fields to REDCap format: {output_path}")
        return output_path

    def _build_redcap_row(self, source: Dict, content: str, form_name: str) -> Dict:
        """Build a single REDCap row."""
        var_name = source.get('variable_name', 'unknown')
        data_type = source.get('data_type', 'text')

        # Extract field label (description)
        field_label = self._extract_field_label(content)

        # Map data type to REDCap field type
        field_type = self._map_to_redcap_type(data_type, content)

        # Extract choices for categorical variables
        choices = self._extract_redcap_choices(content)

        # Extract validation
        validation_type = self._get_validation_type(data_type)

        # Extract min/max
        min_val, max_val = self._extract_min_max(content)

        # Build field note from ontology mappings
        field_note = self._build_field_note(content)

        row = {
            'Variable / Field Name': var_name,
            'Form Name': form_name,
            'Field Type': field_type,
            'Field Label': field_label,
            'Choices, Calculations, OR Slider Labels': choices,
            'Field Note': field_note,
            'Text Validation Type OR Show Slider Number': validation_type,
            'Text Validation Min': min_val,
            'Text Validation Max': max_val,
        }

        return row

    def _extract_field_label(self, content: str) -> str:
        """Extract field label from content."""
        match = re.search(r'Description:?\s*(.+?)(?:\n\n|\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if match:
            label = match.group(1).strip()
            return label[:200]  # REDCap has limits
        return "No description"

    def _map_to_redcap_type(self, data_type: str, content: str) -> str:
        """Map data type to REDCap field type."""
        data_type_lower = data_type.lower()

        # Check for categorical first
        if self._has_enum_values(content):
            return 'radio'  # or 'dropdown'

        type_mapping = {
            'integer': 'text',
            'int': 'text',
            'float': 'text',
            'double': 'text',
            'string': 'text',
            'text': 'notes',
            'boolean': 'yesno',
            'date': 'text',
            'datetime': 'text'
        }

        return type_mapping.get(data_type_lower, 'text')

    def _extract_redcap_choices(self, content: str) -> str:
        """Extract choices in REDCap format: "1, Male | 2, Female"."""
        pattern = r'(?:Valid Values|Values|Coding):?\s*\n((?:\s*[-•\d]+[:\.].*\n?)+)'
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            values_text = match.group(1)
            # Parse "1: Male" format
            choices = []
            for line in values_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Match "1: Male" or "1. Male" or "- 1: Male"
                choice_match = re.match(r'[-•]?\s*(\d+)\s*[:\.]?\s*(.+)', line)
                if choice_match:
                    code = choice_match.group(1)
                    label = choice_match.group(2).strip()
                    choices.append(f"{code}, {label}")

            return ' | '.join(choices) if choices else ''

        return ''

    def _has_enum_values(self, content: str) -> bool:
        """Check if content has enum values."""
        return bool(re.search(r'(?:Valid Values|Values|Coding):', content, re.IGNORECASE))

    def _get_validation_type(self, data_type: str) -> str:
        """Get REDCap validation type."""
        mapping = {
            'integer': 'integer',
            'int': 'integer',
            'float': 'number',
            'double': 'number',
            'date': 'date_ymd',
            'datetime': 'datetime_ymd',
            'email': 'email',
            'phone': 'phone'
        }
        return mapping.get(data_type.lower(), '')

    def _extract_min_max(self, content: str) -> tuple:
        """Extract min and max values."""
        range_match = re.search(r'(?:Valid Range|Range):?\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
        if range_match:
            return range_match.group(1), range_match.group(2)
        return '', ''

    def _build_field_note(self, content: str) -> str:
        """Build field note from ontology mappings."""
        notes = []

        omop = re.search(r'OMOP[:\s]+(\d+)', content)
        if omop:
            notes.append(f"OMOP: {omop.group(1)}")

        loinc = re.search(r'LOINC[:\s]+([\d-]+)', content)
        if loinc:
            notes.append(f"LOINC: {loinc.group(1)}")

        return ' | '.join(notes) if notes else ''


# ============================================================================
# INSTALLATION
# ============================================================================

print("""
╔══════════════════════════════════════════════════════════════════╗
║           EXPORT FORMATS IMPLEMENTATION LOADED                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ HTML Dashboard Export                                        ║
║     - Interactive single-page dashboard                          ║
║     - Searchable/filterable table                                ║
║     - Detailed variable views                                    ║
║                                                                  ║
║  ✅ JSON Schema Export                                           ║
║     - JSON Schema Draft 7 format                                 ║
║     - Data validation support                                    ║
║     - Ontology mappings included                                 ║
║                                                                  ║
║  ✅ REDCap Data Dictionary Export                                ║
║     - Standard REDCap CSV format                                 ║
║     - Field types and validations                                ║
║     - Ready for REDCap import                                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

USAGE EXAMPLES:

1. HTML Dashboard:
   ```python
   html_exporter = HTMLDashboardExporter(db)
   filepath = html_exporter.export_to_html("job-12345")
   # Open in browser to view interactive dashboard
   ```

2. JSON Schema:
   ```python
   schema_exporter = JSONSchemaExporter(db)
   filepath = schema_exporter.export_to_json_schema("job-12345")
   # Use for JSON data validation
   ```

3. REDCap Format:
   ```python
   redcap_exporter = REDCapExporter(db)
   filepath = redcap_exporter.export_to_redcap("job-12345", form_name="my_study")
   # Import into REDCap project
   ```

""")
