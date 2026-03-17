"""
Agent Extensions - Add inject_toons() method to agents

This module extends the BaseAgent class to add the inject_toons() method
that is referenced throughout the documentation.

Import this after defining your agents to enable the documented API.
"""

from typing import List
from toon_manager import Toon


def inject_toons(self, toons: List[Toon]) -> str:
    """
    Inject Toons into agent context.

    This method adds Toon content to the agent's system prompt or context,
    allowing agents to use learned mappings, instructions, and other
    context from the Toon system.

    Args:
        toons: List of Toon objects to inject

    Returns:
        str: The formatted toon context that was added

    Example:
        >>> from toon_manager import ToonManager, ToonType
        >>> toon_manager = ToonManager(db)
        >>> toons = toon_manager.list_toons(ToonType.MAPPING)
        >>> agent.inject_toons(toons)
    """
    if not toons:
        return ""

    # Format toons for injection
    toon_context = "\n\n=== CONTEXT FROM TOON LIBRARY ===\n\n"

    for toon in toons:
        toon_context += f"## {toon.name} ({toon.toon_type.value if hasattr(toon.toon_type, 'value') else toon.toon_type})\n"
        toon_context += f"{toon.content}\n\n"

    toon_context += "=== END TOON CONTEXT ===\n"

    # Add to agent's additional context (if attribute exists)
    if hasattr(self, 'additional_context'):
        if self.additional_context:
            self.additional_context += "\n" + toon_context
        else:
            self.additional_context = toon_context
    else:
        # Create the attribute if it doesn't exist
        self.additional_context = toon_context

    return toon_context


def add_toon_support_to_agent_class(agent_class):
    """
    Add inject_toons method to an agent class.

    Args:
        agent_class: The agent class to extend

    Example:
        >>> from agent_extensions import add_toon_support_to_agent_class
        >>> add_toon_support_to_agent_class(BaseAgent)
        >>> add_toon_support_to_agent_class(DataParserAgent)
    """
    agent_class.inject_toons = inject_toons


# Convenience function to patch multiple agent classes at once
def enable_toon_injection(*agent_classes):
    """
    Enable inject_toons() method on multiple agent classes.

    Args:
        *agent_classes: Agent classes to patch

    Example:
        >>> from agent_extensions import enable_toon_injection
        >>> enable_toon_injection(
        ...     BaseAgent,
        ...     DataParserAgent,
        ...     TechnicalAnalyzerAgent,
        ...     DomainOntologyAgent
        ... )
    """
    for agent_class in agent_classes:
        add_toon_support_to_agent_class(agent_class)


# Auto-patch BaseAgent if available
try:
    # Try to import and patch BaseAgent automatically
    # This won't work if BaseAgent isn't defined yet, but that's okay
    import sys
    if 'BaseAgent' in dir():
        add_toon_support_to_agent_class(BaseAgent)
except:
    pass  # BaseAgent not available yet, will need manual patching

