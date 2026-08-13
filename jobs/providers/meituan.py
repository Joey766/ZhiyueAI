"""美团官方招聘公开职位列表适配器。"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from jobs.normalizer import standard_job
from jobs.role_taxonomy import recruitment_type as infer_recruitment_type

LIST_URL = "https://zhaopin.meituan.com/api/official/job/getJobList"
DETAIL_URL = "https://zhaopin.meituan.com/web/position/detail?jobUnionId={job_id}&jobShareType=1"
PAGE_SIZE = 1000


def _request_page(page_no: int, timeout: int) -> tuple[list[dict], dict]:
    payload = {"page": {"pageNo": page_no, "pageSize": PAGE_SIZE}, "jobShareType": "1", "keywords": "", "cityList": [], "department": [], "jfJgList": [], "jobType": [], "typeCode": [], "specialCode": []}
    response = requests.post(LIST_URL, json=payload, headers={"User-Agent": "Mozilla/5.0 (compatible; ZhiyueAI/0.6)", "Content-Type": "application/json"}, timeout=timeout)
    response.raise_for_status()
    data = response.json().get("data", {})
    return data.get("list", []), data.get("page", {})


def _published_at(value: object) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def fetch(source: dict, timeout: int = 20, raw_items: list[dict] | None = None) -> list[dict]:
    """同步官网全部当前公开职位；不按用户目标职位或招聘类型裁剪。"""
    if raw_items is None:
        raw, page = _request_page(1, timeout)
        for page_no in range(2, max(1, int(page.get("totalPage") or 1)) + 1):
            items, _ = _request_page(page_no, timeout)
            raw.extend(items)
    else:
        raw = raw_items
    jobs = []
    for item in raw:
        job_id, title = item.get("jobUnionId"), item.get("name")
        if not job_id or not title:
            continue
        locations = [city.get("name", "") for city in item.get("cityList") or [] if city.get("name")]
        departments = [dept.get("name", "") for dept in item.get("department") or [] if dept.get("name")]
        recruitment_hint = {"1": "校园招聘", "2": "校园招聘", "3": "社会招聘"}.get(str(item.get("jobType") or ""), "")
        responsibilities, requirements = item.get("jobDuty", ""), item.get("jobRequirement", "")
        description = "\n".join(filter(None, [item.get("desc", ""), responsibilities, requirements, item.get("highLight", "")]))
        detail_url = DETAIL_URL.format(job_id=job_id)
        jobs.append(standard_job(
            id=f"meituan:{job_id}", source="美团官方招聘", source_type="official_domestic", company=source["company"], title=title,
            location=locations[0] if locations else "", locations=locations, department=" / ".join(departments) or item.get("jobFamily", ""),
            employment_type=recruitment_hint, recruitment_type=infer_recruitment_type({"title": title, "description": f"{recruitment_hint}\n{description}"}),
            description=description, responsibilities=responsibilities, requirements=requirements, job_url=detail_url, apply_url=detail_url,
            posted_at=_published_at(item.get("refreshTime") or item.get("firstPostTime")), industry=source.get("industry", "生活服务 / 科技互联网"),
            company_type=source.get("company_type", "大型科技公司"), is_real_job=True,
        ))
    return jobs


def search_jobs(source: dict, queries: list[str], locations=None, recruitment_types=None, timeout: int = 20) -> list[dict]:
    """使用官网公开接口的 keywords 参数查询；不下载全站岗位池。"""
    # 复用标准化逻辑，单次只取官网关键词返回的候选；多关键词结果由 orchestrator 去重。
    collected = []
    for query in list(dict.fromkeys(query for query in queries if query))[:10]:
        payload = {"page": {"pageNo": 1, "pageSize": 100}, "jobShareType": "1", "keywords": query, "cityList": [], "department": [], "jfJgList": [], "jobType": [], "typeCode": [], "specialCode": []}
        response = requests.post(LIST_URL, json=payload, headers={"User-Agent": "Mozilla/5.0 (compatible; ZhiyueAI/0.7.1)", "Content-Type": "application/json"}, timeout=timeout)
        response.raise_for_status()
        collected.extend(response.json().get("data", {}).get("list", []))
    return fetch(source, timeout, raw_items=collected)
