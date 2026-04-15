"""Permit data client abstraction and NYC DOB implementation.

Provides:
  - PermitRecord: structured permit data returned by any client implementation
  - PermitDataClient: Protocol defining the search interface
  - NYCDOBClient: implementation backed by the NYC DOB Permit Issuance dataset
    via the Socrata SODA API (data.cityofnewyork.us)
"""

from __future__ import annotations

from typing import Protocol

import httpx
from pydantic import BaseModel

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

_DOB_ENDPOINT = "https://data.cityofnewyork.us/resource/ipu4-2q9a.json"
_DEFAULT_LIMIT = 15

# Renovation permit job types: A1 = major alteration, A2 = minor alteration
_RENOVATION_JOB_TYPES = ("A1", "A2")

_BOROUGH_MAP: dict[str, str] = {
    "brooklyn": "BROOKLYN",
    "manhattan": "MANHATTAN",
    "queens": "QUEENS",
    "bronx": "BRONX",
    "staten island": "STATEN ISLAND",
}


class PermitRecord(BaseModel):
    """Structured permit record returned by any PermitDataClient implementation."""

    job_type: str
    work_type: str | None = None
    filing_status: str | None = None
    permit_status: str | None = None
    issuance_date: str | None = None
    expiration_date: str | None = None
    address: str | None = None
    borough: str | None = None
    description: str | None = None


class PermitDataClient(Protocol):
    """Interface for permit data sources. Swap implementations per jurisdiction."""

    def search_permits(self, location: str, project_type: str) -> list[PermitRecord]:
        ...


class NYCDOBClient:
    """Queries the NYC DOB Permit Issuance dataset via the Socrata SODA API."""

    def __init__(self) -> None:
        headers = {"Accept": "application/json"}
        if settings.SOCRATA_APP_TOKEN:
            headers["X-App-Token"] = settings.SOCRATA_APP_TOKEN
        self._headers = headers

    def _extract_borough(self, location: str) -> str | None:
        lower = location.lower()
        for key, value in _BOROUGH_MAP.items():
            if key in lower:
                return value
        return None

    def search_permits(self, location: str, project_type: str) -> list[PermitRecord]:
        borough = self._extract_borough(location)

        job_types_clause = ", ".join(f"'{jt}'" for jt in _RENOVATION_JOB_TYPES)
        where = f"job_type IN ({job_types_clause})"
        if borough:
            where += f" AND borough = '{borough}'"

        params: dict[str, str | int] = {
            "$where": where,
            "$order": "issuance_date DESC",
            "$limit": _DEFAULT_LIMIT,
        }

        logger.info("dob.search", location=location, borough=borough, project_type=project_type)

        try:
            response = httpx.get(_DOB_ENDPOINT, params=params, headers=self._headers, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("dob.request_failed", error=str(exc))
            return []

        records = []
        for row in response.json():
            records.append(PermitRecord(
                job_type=row.get("job_type", ""),
                work_type=row.get("work_type"),
                filing_status=row.get("filing_status"),
                permit_status=row.get("permit_status"),
                issuance_date=row.get("issuance_date"),
                expiration_date=row.get("expiration_date"),
                address=f"{row.get('house__', '')} {row.get('street_name', '')}".strip() or None,
                borough=row.get("borough"),
                description=row.get("job_doc___"),
            ))

        logger.info("dob.results", n_records=len(records))
        return records
