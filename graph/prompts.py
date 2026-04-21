"""All prompt strings for the V2 due diligence graph.

Import constants from here — never define prompt strings inline in node files.
"""

# clarify_with_user node
# Evaluates whether the user's query has sufficient information to proceed.
# If not, generates a targeted clarification question.
CLARIFY_WITH_USER_PROMPT: str = ""

# write_research_brief node
# Classifies query type, infers active_dimensions, invokes geocoding,
# and produces a fully populated DueDiligenceRequest.
WRITE_RESEARCH_BRIEF_PROMPT: str = ""

# llm_call node (researcher subgraph)
# Instructs a dimension-specific research agent to call its bound tools
# and gather findings for one due diligence dimension.
RESEARCHER_AGENT_PROMPT: str = ""

# compress_research node
# Serializes raw tool-call output into a structured FindingsBlock summary
# to be returned to the supervisor as ToolMessage content.
COMPRESS_RESEARCH_PROMPT: str = ""

# supervisor node
# Lead researcher prompt — delegates via ConductResearch per active dimension,
# then calls ResearchComplete when satisfied.
LEAD_RESEARCHER_PROMPT: str = ""

# final_report_generation node
# Synthesizes compressed findings into a fixed DueDiligenceReport schema
# with risk flags, risk score, and narrative recommendation.
FINAL_REPORT_GENERATION_PROMPT: str = ""
