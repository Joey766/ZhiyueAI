"""合并同一岗位的多地点重复记录。"""

from __future__ import annotations

import hashlib
import re


def _key(job):
    title = re.sub(r"\W+", "", str(job.get("title", "")).lower())
    description = re.sub(r"\s+", " ", str(job.get("description", "")).lower())[:1200]
    return str(job.get("company", "")).lower(), title, hashlib.sha1(description.encode("utf-8")).hexdigest()[:16]


def deduplicate_jobs(jobs):
    merged = {}
    for job in jobs:
        key = _key(job)
        if key not in merged:
            item = dict(job)
            item["locations"] = list(dict.fromkeys([value for value in job.get("locations", []) + [job.get("location", "")] if value]))
            merged[key] = item
            continue
        item = merged[key]
        item["locations"] = list(dict.fromkeys(item["locations"] + [value for value in job.get("locations", []) + [job.get("location", "")] if value]))
        item["location"] = " / ".join(item["locations"]) if len(item["locations"]) <= 3 else "多个地点"
    return list(merged.values())
