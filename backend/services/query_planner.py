"""Deterministic query planner for routing marine questions to ORCA capabilities.

This is intentionally transparent keyword routing, not an LLM agent. It produces a
reviewable plan and can later be replaced by a model without changing the API contract.
"""
from dataclasses import asdict, dataclass
import re
from typing import List


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    selected_agents: List[str]
    required_data_sources: List[str]
    needs_location: bool
    needs_time_context: bool
    limitations: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


AGENT_KEYWORDS = {
    "Ocean Monitoring Agent": ("ocean", "temperature", "salinity", "oxygen", "ph", "water quality", "sea surface"),
    "Fisheries Agent": ("fish", "fishing", "fisheries", "catch", "habitat", "fishing zone", "pfz", "potential fishing"),
    "Biodiversity Agent": ("biodiversity", "species", "coral", "reef", "ecosystem", "marine life"),
    "Climate & Oceanographic Agent": ("climate", "warming", "heatwave", "acidification", "current", "climate change"),
    "Pollution Detection Agent": ("pollution", "oil spill", "plastic", "turbidity", "contamination", "waste"),
}

SAFETY_TERMS = ("safe to sail", "sea safety", "wave", "waves", "swell", "rough sea", "boat safety", "marine weather", "sea condition", "wind at sea")
PFZ_TERMS = ("pfz", "potential fishing zone", "best place to fish", "fishing zone")


def plan_query(query: str) -> QueryPlan:
    normalized = re.sub(r"\s+", " ", query.casefold()).strip()
    if not normalized:
        raise ValueError("query must not be empty")

    selected = [
        agent for agent, terms in AGENT_KEYWORDS.items()
        if any(term in normalized for term in terms)
    ]
    safety = any(term in normalized for term in SAFETY_TERMS)
    pfz = any(term in normalized for term in PFZ_TERMS)

    if safety:
        intent = "marine_conditions"
        selected = []  # Wave-forecast requests use the live provider, not ecosystem agents.
        sources = ["Open-Meteo Marine API (wave forecast; when coordinates are provided)"]
        limitations = ["Wave forecasts are not official maritime warnings or a vessel-specific safety clearance."]
    elif pfz:
        intent = "potential_fishing_zone"
        sources = ["Fisheries and ocean observations (not yet integrated for live PFZ retrieval)"]
        limitations = ["Live PFZ retrieval and ranking are not implemented yet; current ecosystem scenarios cannot identify a real fishing zone."]
        if "Fisheries Agent" not in selected:
            selected.append("Fisheries Agent")
        if "Ocean Monitoring Agent" not in selected:
            selected.append("Ocean Monitoring Agent")
    else:
        intent = "ecosystem_assessment"
        sources = ["ORCA scenario data (demo mode) or configured PostgreSQL observations"]
        limitations = ["Domain agents currently use prototype heuristics, not scientifically validated predictive models."]

    if not selected and not safety:
        selected = list(AGENT_KEYWORDS.keys())

    return QueryPlan(
        intent=intent,
        selected_agents=selected,
        required_data_sources=sources,
        needs_location=safety or pfz,
        needs_time_context=safety or pfz or any(t in normalized for t in ("today", "tomorrow", "now", "latest", "forecast")),
        limitations=limitations,
    )
