"""多 Provider 搜索编排：固定的是 Provider，结果仅来自本次用户搜索。"""
from __future__ import annotations
from time import perf_counter
import streamlit as st

from jobs.aggregator import PROVIDERS
from jobs.deduplicator import deduplicate_jobs
from jobs.role_taxonomy import normalized
from jobs.search.search_session import new_search_session

def _matches_intent(job: dict, intent: dict) -> bool:
    text = normalized(" ".join([job.get("title", ""), job.get("department", ""), job.get("description", "")]))
    queries = [normalized(query) for group in intent["queries"].values() for query in group]
    return any(query and query in text for query in queries)

def _source_dict(item: tuple[str, str, str, str, str]) -> dict:
    company, ats, identifier, industry, company_type = item
    return {"company": company, "ats": ats, "identifier": identifier, "industry": industry, "company_type": company_type}

@st.cache_data(ttl=900, max_entries=12, show_spinner=False)
def search_all_sources(sources: tuple[tuple[str, str, str, str, str], ...], intent: dict, refresh_token: int):
    jobs, stats = [], {}
    keywords = intent["queries"]["primary"] + intent["queries"]["close"] + intent["queries"]["adjacent"]
    for raw_source in sources:
        source = _source_dict(raw_source); provider = PROVIDERS[source["ats"]]; started = perf_counter()
        try:
            search_jobs = provider.get("search_jobs")
            if search_jobs:
                provider_jobs = search_jobs(source, keywords, intent.get("locations"), [intent.get("stage", "")])
                mode = "server-side query"
            else:
                provider_jobs = [job for job in provider["fetch"](source) if _matches_intent(job, intent)]
                mode = "fetch + dynamic local filter"
            jobs.extend(provider_jobs)
            stats[source["company"]] = {"status": "success", "mode": mode, "count": len(provider_jobs), "duration_seconds": round(perf_counter() - started, 2)}
        except Exception as exc:
            stats[source["company"]] = {"status": "failed", "mode": "", "count": 0, "duration_seconds": round(perf_counter() - started, 2), "failure": type(exc).__name__}
    unique = {job["id"]: job for job in jobs if job.get("id") and job.get("job_url")}
    deduplicated = deduplicate_jobs(list(unique.values()))
    return new_search_session(intent, deduplicated, stats, len(unique))
