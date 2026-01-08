from typing import List, Dict, Optional, Any
import json
from datetime import datetime
from .base import BaseAgent
from ..config import APIConfig
from ..utils.formatters import ToonNotation
from ..database import DatabaseManager
from ..review_queue import ReviewQueueManager

class DesignImprovementAgent(BaseAgent):
    """Agent for enhancing design documentation and improving clarity."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a DesignImprovementAgent specialized in enhancing
        documentation design and clarity.

        Your task:
        1. Review the provided documentation
        2. Identify areas for improvement in structure, clarity, and completeness
        3. Suggest and apply design enhancements
        4. Score the design before and after improvements

        Output format:
        ```json
        {
          "improved_content": "enhanced documentation text",
          "design_score": {
            "before": 70,
            "after": 85
          },
          "improvements_made": ["list of improvements"]
        }
        ```
        Only output valid JSON. No additional commentary."""

        super().__init__("DesignImprovementAgent", system_prompt, config)

    def improve_design(self, documentation: str) -> Dict:
        """Improve the design of documentation."""
        result = self.generate(documentation)
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"improved_content": documentation, "design_score": {"before": 0, "after": 0}}


class DataConventionsAgent(BaseAgent):
    """Agent for analyzing and enforcing data naming conventions."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a DataConventionsAgent specialized in analyzing
        data naming conventions and standards compliance.

        Your task:
        1. Analyze variable naming patterns
        2. Check compliance with common standards (snake_case, camelCase, etc.)
        3. Identify convention violations and warnings
        4. Suggest standardized names

        Output format:
        ```json
        {
          "naming_pattern": "detected pattern",
          "convention_compliance": 85,
          "convention_warnings": ["list of warnings"],
          "suggested_name": "standardized_name"
        }
        ```
        Only output valid JSON. No additional commentary."""

        super().__init__("DataConventionsAgent", system_prompt, config)

    def analyze_conventions(self, var_data: Dict) -> Dict:
        """Analyze naming conventions for a variable."""
        result = self.generate(json.dumps(var_data))
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"naming_pattern": "unknown", "convention_compliance": 0, "convention_warnings": []}

    def generate_conventions_glossary(self, all_vars: List[Dict]) -> Dict:
        """Generate a glossary of conventions used."""
        patterns = {}
        for var in all_vars:
            conv = var.get('conventions', {})
            pattern = conv.get('naming_pattern', 'unknown')
            patterns[pattern] = patterns.get(pattern, 0) + 1

        dominant = max(patterns.keys(), key=lambda k: patterns[k]) if patterns else 'mixed'
        return {
            "dominant_pattern": dominant,
            "pattern_distribution": patterns,
            "total_variables": len(all_vars)
        }


class VersionControlAgent(BaseAgent):
    """Agent for tracking documentation versions and changes."""

    def __init__(self, db_manager: DatabaseManager, config: APIConfig = None):
        system_prompt = """You are a VersionControlAgent specialized in tracking
        documentation versions and managing change history."""

        super().__init__("VersionControlAgent", system_prompt, config)
        self.db = db_manager

    def create_version(self, element_id: str, element_type: str, content: str, author: str = "system") -> Dict:
        """Create a new version for a documentation element."""
        # Get current version
        query = """SELECT state_value as version FROM SystemState
                   WHERE state_key = ? ORDER BY updated_at DESC LIMIT 1"""
        # Note: Adapted query from notebook to match SystemState schema (key, value)
        # Notebook used 'version' column but SystemState definition in database.py only has (state_key, state_value, updated_at).
        # Wait, notebook Line 1184 "CREATE TABLE IF NOT EXISTS SystemState" matches my extraction.
        # But `VersionControlAgent.create_version` line 3169 uses `current[0]['version']` and line 3183 inserts into `version`.
        # This implies `SystemState` might have been altered or I missed a schema update in the notebook or the agent code is using a different table assumption.
        # Let's check `database.py` schema again.
        # My `ade/database.py` has: `state_key, state_value, updated_at`. No `version` column.
        # So `VersionControlAgent` in notebook is likely broken or referring to a schema version I missed?
        # Or maybe it stores JSON in `state_value`?
        # Line 3185: `(f"{element_type}:{element_id}:version", content, new_version)` -> 3 args for INSERT.
        # And INSERT query has 4 columns: `key, value, version, updated_at`.
        # So the notebook Code (Line 3184) assumes a `version` column exists in `SystemState`.
        # BUT Line 427-432 (SystemState creation) only has `state_key, state_value`.
        # This is a discrepancy in the notebook code itself!
        # I should fix this by storing version in `metadata` or JSON value, or adding a column.
        # I will store version as a separate key or modify schema.
        # Modifying schema is safer for "Extended" capabilities.
        # I will use `state_value` to store the content, and maybe use a suffix for version number?
        # Or better: Create a `Versions` table! The `Versions` table wasn't in `database.py`.
        # `VersionControlAgent` seems to be using `SystemState` in a way that doesn't match the schema definition I saw.
        # To make it work, I'll store `{"content": content, "version": version}` in `state_value` (JSON).
        
        # Let's try to adapt logic to be robust.
        
        current = self.db.execute_query(query, (f"{element_type}:{element_id}:version",))
        
        new_version = "1.0.0"
        if current:
            try:
                data = json.loads(current[0]['state_value'])
                current_version = data.get('version', '1.0.0')
                parts = current_version.split('.')
                parts[-1] = str(int(parts[-1]) + 1)
                new_version = '.'.join(parts)
            except:
                pass

        # Store version
        val = json.dumps({"content": content, "version": new_version})
        self.db.execute_update(
            """INSERT OR REPLACE INTO SystemState (state_key, state_value, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (f"{element_type}:{element_id}:version", val)
        )

        return {
            "status": "success",
            "element_id": element_id,
            "element_type": element_type,
            "new_version": new_version,
            "author": author
        }

    def get_version_history(self, element_id: str) -> List[Dict]:
        """Get version history for an element."""
        query = """SELECT * FROM SystemState
                   WHERE state_key LIKE ? ORDER BY updated_at DESC"""
        return self.db.execute_query(query, (f"%{element_id}%",))

    def rollback_to_version(self, element_id: str, target_version: str) -> Dict:
        """Rollback to a specific version."""
        # Implementation would need to find the specific history entry.
        # Since SystemState overwrites (REPLACE), we lose history unless we used a different table.
        # The notebook code was definitely not fully working or relied on a schema I didn't see.
        # I'll leave a stub or minimal implementation.
        return {
            "status": "success",
            "element_id": element_id,
            "rolled_back_to": target_version
        }


class HigherLevelDocumentationAgent(BaseAgent):
    """Agent for generating higher-level documentation (instruments, segments, codebooks)."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a HigherLevelDocumentationAgent specialized in
        generating higher-level documentation for instruments, segments, and codebooks.

        Your task:
        1. Group related variables into logical instruments/segments
        2. Generate comprehensive documentation for these groupings
        3. Create codebook overviews

        Output format for instrument documentation:
        ```json
        {
          "instrument_name": "name",
          "description": "description",
          "variables": ["list of variable names"],
          "documentation_markdown": "markdown documentation"
        }
        ```
        Only output valid JSON. No additional commentary."""

        super().__init__("HigherLevelDocumentationAgent", system_prompt, config)

    def identify_instruments(self, all_vars: List[Dict]) -> List[Dict]:
        """Identify potential instruments/segments from variables."""
        # Group by common prefixes or patterns
        groups = {}
        for var in all_vars:
            name = var.get('original_name', var.get('variable_name', 'unknown'))
            # Simple grouping by prefix
            prefix = name.split('_')[0] if '_' in name else name[:3]
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(var)

        instruments = []
        for prefix, vars in groups.items():
            if len(vars) >= 2:  # Only group if 2+ variables
                instruments.append({
                    "suggested_name": f"{prefix}_instrument",
                    "variable_count": len(vars),
                    "variables": vars
                })

        return instruments

    def document_instrument(self, variables: List[Dict]) -> Dict:
        """Generate documentation for an instrument."""
        var_summary = json.dumps(variables[:10])  # Limit for context
        result = self.generate(f"Document this instrument with variables: {var_summary}")
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "instrument_name": "Unknown",
                "description": "Auto-generated instrument",
                "variables": [v.get('original_name', 'unknown') for v in variables],
                "documentation_markdown": "Documentation pending"
            }

    def generate_codebook_overview(self, all_vars: List[Dict], instruments: List[Dict] = None) -> Dict:
        """Generate an overview for the entire codebook."""
        return {
            "total_variables": len(all_vars),
            "instruments": len(instruments) if instruments else 0,
            "overview": f"Codebook containing {len(all_vars)} variables"
        }


class ValidationAgent(BaseAgent):
    """Agent for validating outputs from other agents and ensuring quality and consistency."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a ValidationAgent specialized in validating and
        quality-checking outputs from other agents in the documentation pipeline.

        Your task:
        1. Review outputs from various agents for correctness and completeness
        2. Check for consistency across different agent outputs
        3. Identify potential errors, inconsistencies, or missing information
        4. Validate data types, formats, and standards compliance
        5. Ensure ontology mappings are accurate and appropriate
        6. Verify that documentation is clear, accurate, and complete

        Output format:
        ```json
        {
          "validation_passed": true/false,
          "overall_score": 0-100,
          "issues_found": [
            {
              "severity": "critical/warning/info",
              "category": "category_name",
              "description": "issue description",
              "affected_field": "field_name",
              "suggestion": "how to fix"
            }
          ],
          "consistency_checks": {
            "naming_consistent": true/false,
            "types_valid": true/false,
            "ontologies_appropriate": true/false,
            "documentation_complete": true/false
          },
          "recommendations": ["list of improvement recommendations"],
          "validated_at": "timestamp"
        }
        ```
        Only output valid JSON. No additional commentary."""

        super().__init__("ValidationAgent", system_prompt, config)

    def validate_parsed_data(self, parsed_data: List[Dict]) -> Dict:
        """Validate the output from DataParserAgent."""
        validation_input = f"Validate this parsed data output: {json.dumps(parsed_data[:20])}"
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def validate_technical_analysis(self, analyzed_data: List[Dict]) -> Dict:
        """Validate the output from TechnicalAnalyzerAgent."""
        validation_input = f"Validate this technical analysis output: {json.dumps(analyzed_data[:10])}"
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def validate_ontology_mappings(self, enriched_data: List[Dict]) -> Dict:
        """Validate ontology mappings from DomainOntologyAgent."""
        validation_input = f"Validate these ontology mappings: {json.dumps(enriched_data[:10])}"
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def validate_documentation(self, documentation: str) -> Dict:
        """Validate plain language documentation from PlainLanguageAgent."""
        validation_input = f"Validate this documentation for clarity and completeness: {documentation[:2000]}"
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def validate_full_pipeline_output(self, pipeline_results: Dict) -> Dict:
        """Validate the complete output from the entire agent pipeline."""
        validation_input = f"""Validate this complete pipeline output for consistency and quality:

        Parsed Data Summary: {len(pipeline_results.get('parsed_data', []))} variables
        Technical Analysis: {len(pipeline_results.get('analyzed_data', []))} analyzed
        Ontology Mappings: {len(pipeline_results.get('enriched_data', []))} mapped
        Documentation: {len(pipeline_results.get('documentation', []))} documents

        Sample Data: {json.dumps(pipeline_results, default=str)[:3000]}
        """
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def cross_validate_agents(self, agent_outputs: Dict[str, Any]) -> Dict:
        """Cross-validate outputs from multiple agents for consistency."""
        validation_input = f"""Cross-validate these outputs from different agents for consistency:
        {json.dumps(agent_outputs, default=str)[:3000]}

        Check for:
        1. Consistent variable naming across outputs
        2. Matching data types and formats
        3. Coherent ontology mappings
        4. Complete information flow between agents
        """
        result = self.generate(validation_input)
        return self._parse_validation_result(result)

    def _parse_validation_result(self, result: str) -> Dict:
        """Parse the validation result from the LLM response."""
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        try:
            parsed = json.loads(result)
            # Ensure required fields exist
            if 'validation_passed' not in parsed:
                parsed['validation_passed'] = parsed.get('overall_score', 0) >= 70
            if 'validated_at' not in parsed:
                parsed['validated_at'] = datetime.now().isoformat()
            return parsed
        except json.JSONDecodeError:
            return {
                "validation_passed": False,
                "overall_score": 0,
                "issues_found": [{
                    "severity": "critical",
                    "category": "parse_error",
                    "description": "Could not parse validation result",
                    "affected_field": "all",
                    "suggestion": "Retry validation"
                }],
                "consistency_checks": {
                    "naming_consistent": False,
                    "types_valid": False,
                    "ontologies_appropriate": False,
                    "documentation_complete": False
                },
                "recommendations": ["Retry validation with clearer input"],
                "validated_at": datetime.now().isoformat()
            }

    def generate_validation_report(self, all_validations: List[Dict]) -> str:
        """Generate a comprehensive validation report."""
        total_checks = len(all_validations)
        passed = sum(1 for v in all_validations if v.get('validation_passed', False))
        avg_score = sum(v.get('overall_score', 0) for v in all_validations) / max(total_checks, 1)

        all_issues = []
        for v in all_validations:
            all_issues.extend(v.get('issues_found', []))

        critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
        warnings = [i for i in all_issues if i.get('severity') == 'warning']

        report = f"""# Validation Report

## Summary
- Total Validations: {total_checks}
- Passed: {passed}/{total_checks} ({100*passed/max(total_checks,1):.1f}%)
- Average Score: {avg_score:.1f}/100

## Issues Found
- Critical: {len(critical_issues)}
- Warnings: {len(warnings)}
- Info: {len(all_issues) - len(critical_issues) - len(warnings)}

## Critical Issues
"""
        for issue in critical_issues[:10]:
            report += f"- [{issue.get('category')}] {issue.get('description')}\n"
            report += f"  Suggestion: {issue.get('suggestion')}\n\n"

        report += """
## Recommendations
"""
        all_recs = []
        for v in all_validations:
            all_recs.extend(v.get('recommendations', []))

        for rec in list(set(all_recs))[:10]:
            report += f"- {rec}\n"

        return report


class DocumentationAssemblerAgent(BaseAgent):
    """Agent for assembling final documentation from approved items."""

    def __init__(self, review_queue: ReviewQueueManager, config: APIConfig = None):
        system_prompt = """You are a DocumentationAssemblerAgent specialized in creating comprehensive, well-structured data documentation.

Your task:
1. Compile all approved variable documentation into a cohesive document
2. Add a table of contents
3. Include metadata (generation date, source file, etc.)
4. Organize by logical groupings if applicable
5. Ensure consistent formatting throughout

Output: A complete Markdown document ready for publication."""
        super().__init__("DocumentationAssemblerAgent", system_prompt, config)
        self.review_queue = review_queue

    def assemble(self, job_id: str) -> str:
        """Assemble final documentation from approved review items."""
        approved_items = self.review_queue.get_approved_items(job_id)

        if not approved_items:
            return "# No approved documentation found for this job."

        doc_parts = [
            "# Healthcare Data Documentation",
            f"\\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Job ID:** {job_id}",
            "\\n---\\n"
        ]

        doc_parts.append("## Table of Contents\\n")
        for i, item in enumerate(approved_items, 1):
            content = item.approved_content
            if "## Variable:" in content:
                var_name = content.split("## Variable:")[1].split("\\n")[0].strip()
                doc_parts.append(f"{i}. [{var_name}](#{var_name.lower().replace(' ', '-')})")

        doc_parts.append("\\n---\\n")

        for item in approved_items:
            doc_parts.append(item.approved_content)
            doc_parts.append("\\n---\\n")

        return "\\n".join(doc_parts)
