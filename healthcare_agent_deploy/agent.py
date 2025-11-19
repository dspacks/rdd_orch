import os
import json
import hashlib
from datetime import datetime
import vertexai
from google.adk.agents import Agent, LlmAgent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, List, Any, Optional

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# ==================== CORE TOOLS ====================

def parse_data_dictionary(data: str) -> Dict[str, Any]:
    """Parse a raw data dictionary into structured format."""
    lines = data.strip().split("\n")
    if not lines:
        return {"status": "error", "message": "Empty data"}

    header = lines[0].split(",")
    variables = []
    for line in lines[1:]:
        if line.strip():
            values = line.split(",")
            var_dict = dict(zip(header, values))
            variables.append(var_dict)

    return {
        "status": "success",
        "variable_count": len(variables),
        "variables": variables
    }

def map_to_ontology(variable_name: str, data_type: str) -> Dict[str, Any]:
    """Map a variable to standard healthcare ontologies."""
    ontology_map = {
        "patient_id": {"omop": "person_id", "concept_id": 0},
        "age": {"omop": "year_of_birth", "concept_id": 4154793},
        "sex": {"omop": "gender_concept_id", "concept_id": 4135376},
        "bp_systolic": {"omop": "measurement", "concept_id": 3004249},
        "bp_diastolic": {"omop": "measurement", "concept_id": 3012888},
        "hba1c": {"omop": "measurement", "concept_id": 3004410, "loinc": "4548-4"},
    }

    mapping = ontology_map.get(variable_name.lower(), {"omop": "unknown", "concept_id": 0})
    return {"status": "success", "variable_name": variable_name, "mappings": mapping}

def generate_documentation(variable_info: Dict[str, Any]) -> Dict[str, str]:
    """Generate human-readable documentation for a variable."""
    name = variable_info.get("Variable Name", "Unknown")
    field_type = variable_info.get("Field Type", "text")
    label = variable_info.get("Field Label", name)
    notes = variable_info.get("Notes", "No additional notes")

    doc = f"""## Variable: {name}

**Description:** {label}

**Technical Details:**
- Data Type: {field_type}
- Cardinality: required
- Notes: {notes}
"""
    return {"status": "success", "documentation": doc}

# ==================== DESIGN IMPROVEMENT TOOLS ====================

def improve_document_design(content: str) -> Dict[str, Any]:
    """Improve the design and structure of documentation."""
    improvements = []
    improved_content = content

    # Add header hierarchy if missing
    if not content.startswith("#"):
        improved_content = "## " + improved_content
        improvements.append({
            "type": "structural",
            "description": "Added proper header hierarchy",
            "rationale": "Improves document scannability"
        })

    # Ensure consistent spacing
    if "\n\n" not in improved_content:
        improved_content = improved_content.replace("\n", "\n\n")
        improvements.append({
            "type": "formatting",
            "description": "Added consistent paragraph spacing",
            "rationale": "Improves readability"
        })

    # Add bold for key terms
    for keyword in ["Data Type:", "Cardinality:", "Notes:"]:
        if keyword in improved_content and f"**{keyword}**" not in improved_content:
            improved_content = improved_content.replace(keyword, f"**{keyword}**")

    return {
        "status": "success",
        "original_content": content,
        "improved_content": improved_content,
        "improvements_made": improvements,
        "design_score": {
            "before": 65,
            "after": 85,
            "metrics": {
                "readability": 85,
                "scannability": 90,
                "consistency": 80,
                "accessibility": 85
            }
        }
    }

def analyze_design_patterns(documents: List[str]) -> Dict[str, Any]:
    """Analyze design patterns across multiple documents."""
    patterns = {
        "header_usage": sum(1 for d in documents if d.startswith("#")),
        "bold_usage": sum(1 for d in documents if "**" in d),
        "list_usage": sum(1 for d in documents if "- " in d),
        "consistent_structure": len(set(d.split("\n")[0] for d in documents)) == 1
    }

    return {
        "status": "success",
        "total_documents": len(documents),
        "patterns": patterns,
        "recommendations": [
            "Ensure all documents start with proper headers",
            "Use consistent formatting for similar content types"
        ]
    }

# ==================== DATA CONVENTIONS TOOLS ====================

def analyze_variable_conventions(variable_name: str, data_type: str) -> Dict[str, Any]:
    """Analyze and document data conventions for a variable."""
    # Detect naming pattern
    if "_" in variable_name:
        pattern = "snake_case"
        parts = variable_name.split("_")
        prefix = parts[0] if len(parts) > 1 else None
    elif variable_name[0].isupper():
        pattern = "PascalCase"
        prefix = None
    elif any(c.isupper() for c in variable_name[1:]):
        pattern = "camelCase"
        prefix = None
    else:
        pattern = "lowercase"
        prefix = None

    return {
        "status": "success",
        "variable_name": variable_name,
        "naming_convention": {
            "pattern": pattern,
            "prefix": prefix,
            "suffix": None,
            "follows_standard": pattern in ["snake_case", "camelCase"],
            "deviation_notes": "" if pattern in ["snake_case", "camelCase"] else "Non-standard naming pattern"
        },
        "value_conventions": {
            "coding_scheme": "Standard healthcare coding",
            "valid_values": [],
            "missing_indicator": "NA",
            "format_pattern": data_type
        },
        "recommended_documentation": {
            "technical_name": variable_name,
            "display_name": variable_name.replace("_", " ").title(),
            "code_sample": f'df["{variable_name}"]',
            "validation_rules": ["Not null", f"Type: {data_type}"]
        },
        "consistency_score": 90 if pattern == "snake_case" else 70,
        "convention_warnings": []
    }

def generate_conventions_glossary(variables: List[Dict]) -> Dict[str, Any]:
    """Generate a comprehensive conventions glossary."""
    patterns = {}
    for var in variables:
        name = var.get("Variable Name", "")
        if "_" in name:
            patterns["snake_case"] = patterns.get("snake_case", 0) + 1
        elif any(c.isupper() for c in name[1:]):
            patterns["camelCase"] = patterns.get("camelCase", 0) + 1
        else:
            patterns["other"] = patterns.get("other", 0) + 1

    dominant = max(patterns.items(), key=lambda x: x[1])[0] if patterns else "unknown"

    return {
        "status": "success",
        "naming_patterns": patterns,
        "dominant_pattern": dominant,
        "total_variables": len(variables),
        "recommendations": [
            f"Primary naming convention: {dominant}",
            "Maintain consistency across all new variables"
        ]
    }

# ==================== VERSION CONTROL TOOLS ====================

def create_version(tool_context: ToolContext, element_id: str,
                   element_type: str, content: str) -> Dict[str, Any]:
    """Create a new version of a documentation element."""
    # Get current version from state
    version_key = f"version:{element_id}"
    current_version = tool_context.state.get(version_key, "0.0.0")

    # Calculate content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    # Check if content changed
    hash_key = f"hash:{element_id}"
    old_hash = tool_context.state.get(hash_key, "")

    if old_hash == content_hash:
        return {
            "status": "no_change",
            "element_id": element_id,
            "version": current_version,
            "message": "Content unchanged, no new version created"
        }

    # Increment version (simple patch increment)
    parts = list(map(int, current_version.split(".")))
    parts[2] += 1
    new_version = ".".join(map(str, parts))

    # Store new version info
    tool_context.state[version_key] = new_version
    tool_context.state[hash_key] = content_hash
    tool_context.state[f"content:{element_id}:{new_version}"] = content

    # Store version history
    history_key = f"history:{element_id}"
    history = json.loads(tool_context.state.get(history_key, "[]"))
    history.append({
        "version": new_version,
        "timestamp": datetime.now().isoformat(),
        "hash": content_hash
    })
    tool_context.state[history_key] = json.dumps(history)

    return {
        "status": "success",
        "element_id": element_id,
        "element_type": element_type,
        "new_version": new_version,
        "previous_version": current_version,
        "content_hash": content_hash,
        "timestamp": datetime.now().isoformat()
    }

def get_version_history(tool_context: ToolContext, element_id: str) -> Dict[str, Any]:
    """Get the version history for a documentation element."""
    history_key = f"history:{element_id}"
    history = json.loads(tool_context.state.get(history_key, "[]"))

    return {
        "status": "success",
        "element_id": element_id,
        "version_count": len(history),
        "history": history,
        "current_version": tool_context.state.get(f"version:{element_id}", "1.0.0")
    }

def rollback_version(tool_context: ToolContext, element_id: str,
                     target_version: str) -> Dict[str, Any]:
    """Rollback to a previous version."""
    content_key = f"content:{element_id}:{target_version}"
    content = tool_context.state.get(content_key, None)

    if not content:
        return {
            "status": "error",
            "message": f"Version {target_version} not found for {element_id}"
        }

    # Create new version with old content
    return create_version(tool_context, element_id, "rollback", content)

def compare_versions(tool_context: ToolContext, element_id: str,
                    version_a: str, version_b: str) -> Dict[str, Any]:
    """Compare two versions of an element."""
    content_a = tool_context.state.get(f"content:{element_id}:{version_a}", "")
    content_b = tool_context.state.get(f"content:{element_id}:{version_b}", "")

    if not content_a or not content_b:
        return {"status": "error", "message": "One or both versions not found"}

    # Simple line-by-line comparison
    lines_a = set(content_a.split("\n"))
    lines_b = set(content_b.split("\n"))

    return {
        "status": "success",
        "element_id": element_id,
        "version_a": version_a,
        "version_b": version_b,
        "added_lines": len(lines_b - lines_a),
        "removed_lines": len(lines_a - lines_b),
        "unchanged_lines": len(lines_a & lines_b)
    }

# ==================== HIGHER-LEVEL DOCUMENTATION TOOLS ====================

def identify_instruments(variables: List[Dict]) -> Dict[str, Any]:
    """Identify potential instruments or measurement tools in the dataset."""
    prefix_groups = {}

    for var in variables:
        name = var.get("Variable Name", "")
        if "_" in name:
            prefix = name.split("_")[0]
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(var)

    instruments = []
    for prefix, vars in prefix_groups.items():
        if len(vars) >= 3:
            instruments.append({
                "prefix": prefix,
                "suggested_name": f"{prefix.upper()} Instrument",
                "variable_count": len(vars),
                "variables": [v.get("Variable Name") for v in vars]
            })

    return {
        "status": "success",
        "instruments_found": len(instruments),
        "instruments": instruments
    }

def document_instrument(variables: List[Dict], instrument_name: str) -> Dict[str, Any]:
    """Document a complete instrument or measurement tool."""
    var_names = [v.get("Variable Name", "Unknown") for v in variables]

    doc_markdown = f"""# {instrument_name}

## Overview
This instrument consists of {len(variables)} related variables.

## Variables Included
{chr(10).join(f"- {name}" for name in var_names)}

## Clinical Context
These variables are grouped together as they represent a cohesive measurement domain.

## Usage Guidelines
- Ensure all variables are collected together for complete instrument score
- Follow standard data collection protocols
- Document any missing values
"""

    return {
        "status": "success",
        "element_type": "instrument",
        "name": instrument_name,
        "short_name": instrument_name.split()[0] if " " in instrument_name else instrument_name,
        "description": f"Instrument containing {len(variables)} related variables",
        "variables_included": [
            {
                "variable_name": v.get("Variable Name", "Unknown"),
                "role": "item",
                "position": i + 1
            }
            for i, v in enumerate(variables)
        ],
        "documentation_markdown": doc_markdown
    }

def document_segment(variables: List[Dict], segment_name: str,
                     segment_type: str = "segment") -> Dict[str, Any]:
    """Document a segment or logical grouping of variables."""
    return {
        "status": "success",
        "element_type": segment_type,
        "name": segment_name,
        "description": f"{segment_type.title()} containing {len(variables)} variables",
        "variables_included": [v.get("Variable Name", "Unknown") for v in variables],
        "relationships": [
            {
                "type": "grouping",
                "description": f"Variables grouped under {segment_name}"
            }
        ]
    }

def generate_codebook_overview(variables: List[Dict],
                               instruments: Optional[List[Dict]] = None) -> Dict[str, str]:
    """Generate a comprehensive codebook overview."""
    overview = f"""# Codebook Overview

**Total Variables:** {len(variables)}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Variable Summary

"""

    if instruments:
        overview += f"## Identified Instruments: {len(instruments)}\n\n"
        for inst in instruments:
            overview += f"- **{inst.get('suggested_name', 'Unknown')}**: {inst.get('variable_count', 0)} variables\n"

    return {
        "status": "success",
        "overview": overview,
        "total_variables": len(variables),
        "instruments_count": len(instruments) if instruments else 0
    }

# ==================== MEMORY TOOLS ====================

def save_to_memory(tool_context: ToolContext, key: str, value: str) -> Dict[str, str]:
    """Save information to session state."""
    tool_context.state[f"memory:{key}"] = value
    return {"status": "success", "message": f"Saved {key} to memory"}

def retrieve_from_memory(tool_context: ToolContext, key: str) -> Dict[str, Any]:
    """Retrieve information from session state."""
    value = tool_context.state.get(f"memory:{key}", "Not found")
    return {"status": "success", "key": key, "value": value}

# ==================== CREATE ROOT AGENT ====================

root_agent = LlmAgent(
    name="healthcare_documentation_agent",
    model="gemini-2.5-flash-lite",
    description="Advanced agent for healthcare data documentation with design improvement, conventions enforcement, version control, and higher-level documentation capabilities",
    instruction="""You are an Advanced Healthcare Data Documentation Agent with extended capabilities:

CORE CAPABILITIES:
1. Parse data dictionaries from various formats
2. Map variables to standard healthcare ontologies (OMOP, LOINC, SNOMED)
3. Generate clear, comprehensive documentation

EXTENDED CAPABILITIES:
4. **Design Improvement**: Enhance document structure, readability, and visual hierarchy
5. **Data Conventions**: Ensure variable naming standards and coding schemes are documented
6. **Version Control**: Track changes, manage versions, and support rollbacks
7. **Higher-Level Documentation**: Document instruments, segments, and codebook structures

WORKFLOW:
When processing a data dictionary:
1. Use parse_data_dictionary to extract variable information
2. Use map_to_ontology for each variable to find standard codes
3. Use analyze_variable_conventions to ensure naming standards are documented
4. Use generate_documentation to create human-readable documentation
5. Use improve_document_design to enhance the output quality
6. Use create_version to track changes and enable rollback
7. Use identify_instruments to find related variable groups
8. Use document_instrument for higher-level documentation
9. Use generate_codebook_overview for comprehensive summary

For updates and modifications:
- Always use create_version before making changes
- Use compare_versions to understand differences
- Use rollback_version if needed to revert changes

Remember to save important findings to memory for cross-session knowledge.""",
    tools=[
        # Core tools
        parse_data_dictionary,
        map_to_ontology,
        generate_documentation,
        # Design improvement tools
        improve_document_design,
        analyze_design_patterns,
        # Data conventions tools
        analyze_variable_conventions,
        generate_conventions_glossary,
        # Version control tools
        create_version,
        get_version_history,
        rollback_version,
        compare_versions,
        # Higher-level documentation tools
        identify_instruments,
        document_instrument,
        document_segment,
        generate_codebook_overview,
        # Memory tools
        save_to_memory,
        retrieve_from_memory,
    ],
)
