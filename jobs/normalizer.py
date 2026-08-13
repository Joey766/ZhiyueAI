"""将公开 ATS 返回的字段标准化为应用内岗位格式。"""

from __future__ import annotations

import re
from html import unescape


def clean_text(value: object) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def standard_job(**values) -> dict:
    """生成统一 Job Schema；只保留公开 ATS 已返回的信息。"""
    return {
        "id": str(values.get("id", "")), "source": values.get("source", ""), "source_type": values.get("source_type", values.get("source", "")),
        "company": clean_text(values.get("company")), "title": clean_text(values.get("title")),
        "location": clean_text(values.get("location")) or "未注明", "locations": [clean_text(item) for item in values.get("locations", []) if clean_text(item)], "department": clean_text(values.get("department")),
        "employment_type": clean_text(values.get("employment_type")), "recruitment_type": clean_text(values.get("recruitment_type")), "description": clean_text(values.get("description")),
        "responsibilities": clean_text(values.get("responsibilities")), "requirements": clean_text(values.get("requirements")),
        "job_url": str(values.get("job_url") or ""), "apply_url": str(values.get("apply_url") or values.get("job_url") or ""),
        "compensation": clean_text(values.get("compensation")) or None, "posted_at": values.get("posted_at"),
        "industry": clean_text(values.get("industry")), "company_type": clean_text(values.get("company_type", "")),
        "is_demo": bool(values.get("is_demo", False)), "is_real_job": bool(values.get("is_real_job", not values.get("is_demo", False))),
    }
