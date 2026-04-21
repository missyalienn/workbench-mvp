"""State definitions for the outer graph scope.

AgentState and AgentInputState are the top-level graph state contracts.
ClarifyWithUser and ResearchQuestion are structured LLM output schemas
internal to clarify_with_user and write_research_brief respectively —
neither surfaces in AgentState.
"""

import operator
from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from graph.schemas import DueDiligenceRequest, DueDiligenceReport


class AgentInputState(MessagesState):
    """User-facing input slice — messages only."""
    pass


class AgentState(MessagesState):
    """Main state for the full multi-agent due diligence graph."""

    # Serialized DueDiligenceRequest — written by write_research_brief,
    # read by supervisor_subgraph and final_report_generation.
    research_brief: str | None
    # Messages exchanged with the supervisor subgraph.
    supervisor_messages: Annotated[list[BaseMessage], add_messages]
    # Parsed and geocoded request — written by write_research_brief.
    request: DueDiligenceRequest | None
    # Uncompressed per-agent output accumulated across all agents.
    raw_notes: Annotated[list[str], operator.add]
    # Compressed FindingsBlock summaries — one entry per dimension agent.
    notes: Annotated[list[str], operator.add]
    # Final due diligence report — written by final_report_generation.
    report: DueDiligenceReport | None


# ===== STRUCTURED LLM OUTPUT SCHEMAS =====

class ClarifyWithUser(BaseModel):
    """Structured output for the clarify_with_user node — not stored in AgentState."""

    need_clarification: bool = Field(
        description="Whether the query lacks sufficient information to proceed"
    )
    question: str = Field(
        description="Targeted clarification question to ask the user; empty string if no clarification needed"
    )
    verification: str = Field(
        description="Acknowledgement that research will proceed; empty string if clarification is needed"
    )


class ResearchQuestion(BaseModel):
    """Structured output capturing the normalized research brief — internal to write_research_brief."""

    research_brief: str = Field(
        description="Serialized DueDiligenceRequest that will guide the supervisor and dimension agents"
    )
