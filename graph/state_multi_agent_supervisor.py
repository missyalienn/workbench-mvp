"""State definitions and tool schemas for the supervisor subgraph.

SupervisorState is internal to the supervisor subgraph — it never surfaces
in AgentState. ConductResearch and ResearchComplete are the two tools
bound to the supervisor LLM.
"""

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class SupervisorState(TypedDict):
    """Internal state for the supervisor subgraph."""

    # Messages exchanged within the supervisor reasoning loop.
    supervisor_messages: Annotated[list[BaseMessage], add_messages]
    # Serialized DueDiligenceRequest — read-only within the supervisor subgraph.
    research_brief: str
    # Compressed FindingsBlock summaries returned by dimension agents.
    notes: Annotated[list[str], operator.add]
    # Number of supervisor → supervisor_tools iterations completed.
    research_iterations: int
    # Raw uncompressed output from dimension agents.
    raw_notes: Annotated[list[str], operator.add]


# ===== SUPERVISOR TOOLS =====

@tool
class ConductResearch(BaseModel):
    """Delegate a due diligence research task to a specialized dimension agent."""

    research_topic: str = Field(
        description=(
            "The due diligence dimension and property context to research. "
            "Must be self-contained — the sub-agent cannot see other agents' work. "
            "Include the dimension name, parcel_id, address, and any relevant context "
            "from the research brief."
        )
    )


@tool
class ResearchComplete(BaseModel):
    """Signal that all required dimensions have been researched and findings are ready for report generation."""
    pass
