"""无需 AI 的搜索意图与查询构建。"""
from __future__ import annotations

from jobs.role_taxonomy import ROLE_TAXONOMY

ROLE_QUERIES = {
    "AI产品经理": {"primary": ["AI Product Intern", "AI Product Manager Intern", "AI产品经理 实习", "大模型产品经理 实习", "智能产品经理 实习"], "close": ["Product Manager Intern", "Product Intern", "产品经理 实习", "产品实习生", "Technical Product Intern"], "adjacent": ["Product Analyst", "Product Strategy Intern", "Product Analytics"]},
    "产品经理": {"primary": ["Product Manager Intern", "Product Intern", "产品经理 实习", "产品实习生"], "close": ["Technical Product Intern", "Associate Product Manager"], "adjacent": ["Product Analyst", "Product Strategy Intern"]},
}

def build_search_intent(profile: dict, preferences: dict) -> dict:
    targets = preferences.get("目标岗位", [])
    groups = {"primary": [], "close": [], "adjacent": []}
    for target in targets:
        configured = ROLE_QUERIES.get(target)
        if configured:
            for group, queries in configured.items(): groups[group].extend(queries)
            continue
        taxonomy = ROLE_TAXONOMY.get(target, {})
        for group in groups:
            groups[group].extend(taxonomy.get(group, [])[:3])
    if not groups["primary"]:
        groups["primary"] = ["Product Intern", "产品实习生"]
    stage = preferences.get("求职阶段") or preferences.get("工作类型") or ""
    if stage in {"日常实习", "暑期实习"}:
        groups["primary"] = list(dict.fromkeys(groups["primary"] + ["Intern", "实习"]))
    return {"targets": targets, "locations": preferences.get("工作地点", []), "stage": stage, "industries": preferences.get("目标行业", []), "queries": {key: list(dict.fromkeys(value)) for key, value in groups.items()}}
