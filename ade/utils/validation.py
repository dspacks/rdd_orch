from typing import Tuple, List

def validate_markdown_content(content: str) -> Tuple[bool, List[str]]:
    """
    Validate user-edited markdown content before approval.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if not content:
        return False, ["Content is empty"]

    # Check minimum length
    if len(content.strip()) < 10:
        issues.append("Content is too short (minimum 10 characters)")

    # Check for basic markdown structure
    if "## Variable:" not in content and "#" not in content:
        issues.append("Missing markdown headers (should contain '## Variable:' or other headers)")

    # Check for common corruption patterns
    if content.count("```") % 2 != 0:
        issues.append("Unmatched code blocks (odd number of ``` markers)")

    # Check for placeholder text
    placeholder_patterns = [
        "[insert",
        "TODO",
        "FIXME",
        "XXX",
        "[TBD]",
        "[placeholder]"
    ]
    for pattern in placeholder_patterns:
        if pattern.lower() in content.lower():
            issues.append(f"Contains placeholder text: '{pattern}'")

    # Check for excessive whitespace
    if content.count('\n\n\n\n') > 2:
        issues.append("Contains excessive blank lines (may indicate formatting issue)")

    # Check for basic sections
    required_keywords = ['description', 'data', 'type']
    missing_keywords = [kw for kw in required_keywords if kw.lower() not in content.lower()]
    if len(missing_keywords) > 1:
        issues.append(f"Missing common documentation sections: {', '.join(missing_keywords)}")

    return (len(issues) == 0, issues)
