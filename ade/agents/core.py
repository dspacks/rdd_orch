from typing import List, Dict, Optional
import json
import time
from .base import BaseAgent
from ..config import APIConfig
from ..utils.formatters import ToonNotation

class DataParserAgent(BaseAgent):
    """Agent for parsing raw data into standardized JSON format."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a DataParserAgent specialized in converting raw data specifications into standardized JSON format.

Your task:
1. Parse the input data (CSV, JSON, or XML)
2. Preserve all original field names and values
3. Output a JSON array where each element represents one variable/field
4. Include: original_name, original_type, original_description, and any metadata

Output format:
```json
[
  {
    "original_name": "field_name",
    "original_type": "type",
    "original_description": "description",
    "metadata": {}
  }
]
```

Only output valid JSON. No additional commentary."""
        super().__init__("DataParserAgent", system_prompt, config)

    def parse_csv(self, csv_data: str) -> List[Dict]:
        """Parse CSV data dictionary."""
        result = self.generate(csv_data)
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        return json.loads(result)


class TechnicalAnalyzerAgent(BaseAgent):
    """Agent for analyzing technical properties and mapping to internal standards."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a TechnicalAnalyzerAgent specialized in analyzing data fields.

Your task:
1. Analyze each field from the parsed data
2. Infer technical properties (data_type, constraints, cardinality)
3. Map to standardized field names following healthcare data conventions
4. Flag unclear mappings for clarification

Output format (JSON array for ALL variables):
```json
[
  {
    "original_name": "field_name",
    "variable_name": "standardized_name",
    "data_type": "categorical|continuous|date|text|boolean",
    "description": "description",
    "constraints": {},
    "cardinality": "required|optional|repeated",
    "confidence": "high|medium|low",
    "needs_clarification": false
  }
]
```

Only output valid JSON."""
        super().__init__("TechnicalAnalyzerAgent", system_prompt, config)

    def analyze_batch(self, parsed_data: List[Dict], clarifications: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Analyze multiple variables in a single batch request."""
        additional_context = ""
        if clarifications:
            additional_context = "\\n=== USER CLARIFICATIONS ===\\n"
            for field, clarification in clarifications.items():
                additional_context += f"{field}: {clarification}\\n"
        
        # We need to manually construct batch prompt here as format_batch_prompt was part of BaseAgent in notebook but I didn't include it in BaseAgent.py yet.
        # I should have included helper methods in BaseAgent. 
        # I will implement simple batch formatting here or update BaseAgent. 
        # For now, I'll implement inline to keep it self-contained.
        
        toon_encoded = ToonNotation.encode({"variables": parsed_data})

        format_context = "\\nAnalyze ALL variables in a single JSON array. Output JSON only.\\n"
        full_prompt = f"{toon_encoded}\n{format_context}\n{additional_context}"
        
        result = self.generate(full_prompt)

        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        return json.loads(result)

    def analyze(self, parsed_data: List[Dict], clarifications: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Backward compatible single-call analyze method."""
        return self.analyze_batch(parsed_data, clarifications)


class DomainOntologyAgent(BaseAgent):
    """Agent for mapping to standard healthcare ontologies."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a DomainOntologyAgent specialized in mapping healthcare data fields to standard ontologies.

Your task:
1. For each variable, identify appropriate standard ontology codes
2. Primary ontologies: OMOP CDM, LOINC, SNOMED CT, RxNorm
3. Provide code and standard term
4. Include confidence score for each mapping

Output format:
```json
{
  "variable_name": "standardized_name",
  "ontology_mappings": [
    {
      "system": "OMOP",
      "code": "123456",
      "display": "Standard Concept Name",
      "confidence": "high"
    }
  ]
}
```

Only output valid JSON. No additional commentary."""
        super().__init__("DomainOntologyAgent", system_prompt, config)

    def map_ontologies(self, variable_data: Dict) -> Dict:
        """Map a variable to standard ontologies."""
        toon_encoded = ToonNotation.encode(variable_data)
        result = self.generate(f"{toon_encoded}\nInput is in Toon notation. Output JSON.")

        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        return json.loads(result)


class PlainLanguageAgent(BaseAgent):
    """Agent for generating human-readable documentation."""

    def __init__(self, config: APIConfig = None):
        system_prompt = """You are a PlainLanguageAgent specialized in creating clear, comprehensive documentation for healthcare data variables.

Your task:
1. Convert technical variable specifications into plain language
2. Explain clinical/research context
3. Describe data type, constraints, and valid values
4. Include ontology mappings and significance
5. Write for interdisciplinary audience (clinicians, researchers, data scientists)

Output format (Markdown for EACH variable):
```markdown
## Variable: [Variable Name]

**Description:** [Clear, concise description]

**Technical Details:**
- Data Type: [type]
- Cardinality: [required/optional]
- Valid Values: [constraints or ranges]

**Standard Ontology Mappings:**
- OMOP: [code] - [term]
- LOINC: [code] - [term]

**Clinical Context:** [Explanation of why this variable matters]
```

Process all variables and output markdown for each, separated by ---"""
        super().__init__("PlainLanguageAgent", system_prompt, config)

    def batch_items(self, items: List[Dict], batch_size: int = None) -> List[List[Dict]]:
        """Split items into batches."""
        if batch_size is None:
            batch_size = self.config.batch_size
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    def format_batch_prompt(self, items: List[Dict], item_type: str = "variable") -> str:
        """Format multiple items into a single prompt."""
        # This was in BaseAgent in notebook, duplicating here since I missed it in BaseAgent.py
        # Or I can skip using it if I construct ToonNotation directly.
        pass # Not strictly needed if we use ToonNotation wrapper in document_variables_batched

    def document_variables_batched(self, variables: List[Dict]) -> List[str]:
        """Generate documentation for multiple variables in batches."""
        batches = self.batch_items(variables)
        all_docs = []

        for batch_num, batch in enumerate(batches, 1):
            print(f"Documenting batch {batch_num}/{len(batches)} ({len(batch)} variables)")

            toon_encoded = ToonNotation.encode({"variables": batch})
            prompt = f"{toon_encoded}\nProcess these {len(batch)} variables using the Toon notation above."

            # Single API call for entire batch
            result = self.generate(prompt)

            # Parse results for each variable
            docs = self._parse_batch_documentation(result, batch)
            all_docs.extend(docs)

            if batch_num < len(batches):
                wait_time = 15.0
                # print(f"Wait {wait_time}s...")
                time.sleep(wait_time)

        return all_docs

    def _parse_batch_documentation(self, result: str, batch: List[Dict]) -> List[str]:
        """Extract individual variable documentation from batch response."""
        docs = []

        # Split by variable headers
        parts = result.split("## Variable:")

        for i, part in enumerate(parts[1:], 1):  # Skip first empty split
            doc = "## Variable:" + part
            # Clean up extra content
            if i < len(parts):
                doc = doc.split("---")[0].strip()
            docs.append(doc)

        return docs[:len(batch)]  # Only return docs for variables in batch

    def document_variable(self, enriched_data: Dict) -> str:
        """Generate plain language documentation for a single variable."""
        toon_encoded = ToonNotation.encode(enriched_data)
        result = self.generate(f"{toon_encoded}\nInput is in Toon notation. Generate markdown.")

        if "```markdown" in result:
            result = result.split("```markdown")[1].split("```")[0].strip()
        elif result.startswith("```") and result.endswith("```"):
            result = result.split("```")[1].split("```")[0].strip()
        return result
