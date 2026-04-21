"""State definitions for the researcher subgraph.

ResearcherState is the internal state of the researcher loop.
ResearcherOutputState is the slice returned to the supervisor after
compress_research completes.
"""

import operator
from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import TypedDict


class ResearcherState(TypedDict):
    """Internal state for a single dimension research agent."""

    # Message history for the researcher's tool-calling loop.
    researcher_messages: Annotated[list[BaseMessage], add_messages]
    # Number of LLM + tool-call iterations completed; exits at cap of 3.
    tool_call_iterations: int
    # Research topic string passed in by supervisor_tools.
    research_topic: str
    # Compressed FindingsBlock serialized as a string — written by compress_research.
    compressed_research: str
    # Raw tool-call output accumulated across iterations.
    raw_notes: Annotated[list[str], operator.add]


class ResearcherOutputState(TypedDict):
    """Output slice returned from the researcher subgraph to supervisor_tools."""

    compressed_research: str
    raw_notes: Annotated[list[str], operator.add]
