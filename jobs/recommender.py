"""纯本地、可解释的分层推荐排序；列表阶段绝不调用 AI。"""

from __future__ import annotations

import re

from jobs.role_taxonomy import hard_filter, is_location_expansion, location_matches, recruitment_type, role_match_level, stage_matches

TARGET_RECOMMENDATIONS = 25
LEVEL_POINTS = {"exact": 40, "close": 30, "adjacent": 18, "unrelated": 0}
LEVEL_LABELS = {"exact": "最匹配", "close": "相近机会", "adjacent": "拓展机会"}


def _tokens(value):
    return {item for item in re.split(r"[^a-z0-9+#.]+", str(value or "").lower()) if len(item) > 1}


def _skill_score(job, skills):
    if not skills: return 0, []
    words = _tokens(job.get("title", "") + " " + job.get("description", ""))
    matched = [skill for skill in skills if _tokens(skill) & words]
    return min(10, round(10 * len(matched) / max(1, min(3, len(skills))))), matched


def _location_reason(job):
    return f"{job.get('location') or '该地点'}符合你的地点偏好"


def recommendation(job, profile, preferences):
    targets = preferences.get("目标岗位", [])
    level = role_match_level(job, targets)
    points = LEVEL_POINTS[level]
    reasons = []
    title = job.get("title", "")
    target = " / ".join(targets)
    if level == "exact": reasons.append(f"“{title}”与目标“{target}”高度匹配")
    elif level == "close": reasons.append(f"“{title}”与目标“{target}”属于相近职业方向")
    elif level == "adjacent": reasons.append(f"“{title}”是通往目标“{target}”的可拓展方向")
    location_points = 15 if location_matches(job, preferences) else (4 if is_location_expansion(job, preferences) else 0)
    if location_points == 15: reasons.append(_location_reason(job))
    elif location_points: reasons.append("位于香港、新加坡或远程，作为地点拓展机会保留")
    stage = preferences.get("求职阶段", preferences.get("工作类型", "都可以"))
    actual_stage = job.get("recruitment_type") or recruitment_type(job)
    stage_points = 15 if stage_matches(job, stage) and stage not in {"", "都可以", None} else (8 if stage in {"", "都可以", None} else 0)
    if stage_points and stage not in {"", "都可以", None}: reasons.append(f"{actual_stage}符合当前“{stage}”求职阶段")
    context = (job.get("industry", "") + " " + job.get("company_type", "") + " " + job.get("description", "")).lower()
    industry_points = 0
    industries = preferences.get("目标行业", [])
    company_types = preferences.get("企业类型", [])
    matching_industries = [value for value in industries if value.lower() in context]
    matching_types = [value for value in company_types if value.lower() in context]
    if matching_industries: industry_points += 5; reasons.append(f"岗位内容与“{matching_industries[0]}”行业偏好相关")
    if matching_types: industry_points += 5; reasons.append(f"公司属于你偏好的“{matching_types[0]}”")
    skill_points, matched_skills = _skill_score(job, profile.get("skills", []) if isinstance(profile, dict) else [])
    if matched_skills: reasons.append(f"JD 中的“{'、'.join(matched_skills[:2])}”与你的档案技能匹配")
    target_company = str(preferences.get("目标公司", "")).strip().lower()
    company_points = 5 if target_company and target_company in job.get("company", "").lower() else 0
    if company_points: reasons.append("属于你的目标公司")
    graduation = preferences.get("毕业年份", "")
    eligibility_points = 5 if graduation and actual_stage in {"日常实习", "暑期实习", "校招"} else 0
    job["role_match_level"] = level
    return min(100, points + location_points + stage_points + industry_points + skill_points + company_points + eligibility_points), reasons[:4]


def rank_jobs(jobs, profile, preferences, force_include=False):
    ranked = []
    for job in hard_filter(jobs, preferences):
        copy = dict(job)
        copy["recommendation_score"], copy["recommendation_reasons"] = recommendation(copy, profile, preferences)
        if force_include or copy["role_match_level"] != "unrelated": ranked.append(copy)
    return sorted(ranked, key=lambda item: (LEVEL_POINTS[item["role_match_level"]], item["recommendation_score"]), reverse=True)


def curated_jobs(ranked, limit=TARGET_RECOMMENDATIONS):
    """按 Exact → Close → Adjacent 动态补齐，真实数量不足时如实返回。"""
    selected = []
    for level in ("exact", "close", "adjacent"):
        selected.extend(job for job in ranked if job.get("role_match_level") == level)
        if len(selected) >= limit: break
    return selected[:limit]
