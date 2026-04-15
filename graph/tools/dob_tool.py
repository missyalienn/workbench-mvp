"""DOB permit lookup tool for research agents.

Exposes search_permits as a plain function — passed to agents as an
OpenAI tool definition, not wrapped in any LangChain abstraction.
"""

from __future__ import annotations

from graph.tools.permit_client import NYCDOBClient, PermitRecord


def search_permits(location: str, project_type: str) -> str:
    """Look up recent NYC DOB permits for a renovation project type and location.

    Returns a formatted summary of matching permit records, suitable for
    passing directly into an agent's message context.

    Args:
        location: City and state, e.g. 'Brooklyn, NY'.
        project_type: Type of renovation, e.g. 'deck addition'.
    """
    client = NYCDOBClient()
    records = client.search_permits(location=location, project_type=project_type)

    if not records:
        return f"No DOB permit records found for {project_type!r} in {location!r}."

    lines: list[str] = [f"NYC DOB permits for '{project_type}' in {location} ({len(records)} results):\n"]
    for i, r in enumerate(records, start=1):
        lines.append(f"[{i}] Job type: {r.job_type} | Work type: {r.work_type or 'N/A'}")
        if r.address and r.borough:
            lines.append(f"    Address: {r.address}, {r.borough}")
        if r.description:
            lines.append(f"    Description: {r.description[:200]}")
        lines.append(f"    Status: {r.filing_status or 'N/A'} | Issued: {r.issuance_date or 'N/A'} | Expires: {r.expiration_date or 'N/A'}")
        lines.append("")

    return "\n".join(lines)
