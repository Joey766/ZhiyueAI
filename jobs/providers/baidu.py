"""百度校园招聘公开页面适配器。

只读取官网服务端渲染页面中已经公开展示的首屏岗位；不使用未公开接口、
不登录，也不会尝试绕过访问限制。
"""

from __future__ import annotations

import json

import requests

from jobs.normalizer import standard_job
from jobs.role_taxonomy import recruitment_type as infer_recruitment_type


LIST_URL = "https://talent.baidu.com/jobs/list?recruitType=INTERN"


def _initial_data(html: str) -> dict:
    marker = "window.__INITIAL_DATA__ ="
    start = html.index(marker) + len(marker)
    end = html.index("; window.prefix", start)
    return json.loads(html[start:end])


def fetch(source: dict, timeout: int = 15) -> list[dict]:
    """读取百度官网公开的日常实习岗位首屏（当前每页 10 条）。"""
    response = requests.get(
        source.get("url") or LIST_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ZhiyueAI/0.6)"},
        timeout=timeout,
    )
    response.raise_for_status()
    details = _initial_data(response.text).get("listData", {}).get("listDetailData", [])
    jobs = []
    for item in details:
        job_id = item.get("jobId") or item.get("postId")
        if not job_id or not item.get("name"):
            continue
        place = item.get("workPlace", "")
        locations = [part.strip() for part in place.replace("，", ",").split(",") if part.strip()]
        jobs.append(
            standard_job(
                id=f"baidu:{job_id}", source="百度官方招聘", source_type="official_domestic",
                company=source["company"], title=item.get("name"),
                location=locations[0] if locations else place, locations=locations,
                department=item.get("bgShortName", ""), employment_type=item.get("projectType", "实习"),
                recruitment_type=infer_recruitment_type({"title": item.get("name", ""), "description": item.get("projectType", "")}),
                responsibilities=item.get("workContent", ""), requirements=item.get("serviceCondition", ""),
                description="\n".join(filter(None, [item.get("workContent", ""), item.get("serviceCondition", "")])),
                # 官网当前岗位详情在前端交互中打开；公开列表仍是可用的官方申请入口。
                job_url=source.get("url") or LIST_URL, apply_url=source.get("url") or LIST_URL,
                posted_at=item.get("publishDate") or item.get("updateDate"),
                industry=source.get("industry", "科技互联网"), company_type=source.get("company_type", "大型科技公司"),
                is_real_job=True,
            )
        )
    return jobs
