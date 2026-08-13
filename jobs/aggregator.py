"""仅在用户主动刷新时调用公开 ATS，并缓存结果。"""

from datetime import datetime

import streamlit as st

from jobs.providers import ashby, baidu, greenhouse, lever, meituan
from jobs.deduplicator import deduplicate_jobs

# Registry entries retain the normal fetch callable and optionally expose a real
# server-side search callable.  Search orchestration must use this registry,
# rather than testing attributes on a bare fetch function.
PROVIDERS = {
    "greenhouse": {"fetch": greenhouse.fetch},
    "lever": {"fetch": lever.fetch},
    "ashby": {"fetch": ashby.fetch},
    "baidu": {"fetch": baidu.fetch},
    "meituan": {"fetch": meituan.fetch, "search_jobs": meituan.search_jobs},
}


@st.cache_data(ttl=900, max_entries=12, show_spinner=False)
def fetch_all_sources(sources: tuple[tuple[str, str, str, str, str], ...], refresh_token: int):
    """返回岗位、来源错误。refresh_token 仅由刷新按钮递增。"""
    jobs, errors, provider_stats = [], [], {}
    for company, ats, identifier, industry, company_type in sources:
        source = {"company": company, "ats": ats, "identifier": identifier, "industry": industry, "company_type": company_type}
        started = datetime.now()
        try:
            provider_jobs = PROVIDERS[ats]["fetch"](source)
            jobs.extend(provider_jobs)
            provider_stats[company] = {"status": "success", "http_status": 200, "raw_jobs": len(provider_jobs), "normalized_jobs": len(provider_jobs), "parse_failures": 0, "duration_seconds": round((datetime.now() - started).total_seconds(), 2)}
        except (KeyError, Exception) as exc:
            errors.append({"company": company, "ats": ats, "message": type(exc).__name__})
            response = getattr(exc, "response", None)
            provider_stats[company] = {"status": "failed", "http_status": getattr(response, "status_code", None), "raw_jobs": 0, "normalized_jobs": 0, "parse_failures": 0, "duration_seconds": round((datetime.now() - started).total_seconds(), 2), "failure": type(exc).__name__}
    unique = {item["id"]: item for item in jobs if item.get("id") and item.get("job_url")}
    raw_count = len(unique)
    return deduplicate_jobs(list(unique.values())), errors, datetime.now().strftime("%Y-%m-%d %H:%M"), raw_count, provider_stats


def source_signature(sources):
    return tuple((item["company"], item["ats"], item["identifier"], item.get("industry", ""), item.get("company_type", "")) for item in sources)
