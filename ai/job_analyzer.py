import json

from ai.ollama_client import _json_objects
from ai.provider import analyze_job_fit
from prompts.job_match_prompt import build_job_match_messages

ANALYSIS_SCHEMA = {
    "type": "object", "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100}, "summary": {"type": "string"},
        "dimensions": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "object", "properties": {"name": {"type": "string"}, "score": {"type": "integer"}, "reason": {"type": "string"}}, "required": ["name", "score", "reason"]}},
        "strengths": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["name", "evidence"]}},
        "gaps": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "object", "properties": {"name": {"type": "string"}, "priority": {"type": "string"}, "reason": {"type": "string"}, "current_evidence": {"type": "string"}, "actions": {"type": "array", "items": {"type": "string"}}, "estimated_effort": {"type": "string"}}, "required": ["name", "priority", "reason", "current_evidence", "actions", "estimated_effort"]}},
        "skill_gap": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "category": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["name", "category", "evidence"]}},
        "jd_keywords": {"type": "array", "items": {"type": "string"}}, "resume_evidence": {"type": "array", "items": {"type": "string"}},
        "application_advice": {"type": "array", "items": {"type": "string"}},
        "apply_recommendation": {"type": "object", "properties": {"decision": {"type": "string"}, "reason": {"type": "string"}}, "required": ["decision", "reason"]},
    }, "required": ["overall_score", "summary", "dimensions", "strengths", "gaps", "application_advice", "apply_recommendation"],
}


def _profile_text(profile):
    def walk(item):
        if isinstance(item, dict):
            for part in item.values():
                yield from walk(part)
        elif isinstance(item, list):
            for part in item:
                yield from walk(part)
        elif isinstance(item, str):
            yield item.strip().lower()
    return " ".join(part for part in walk(profile) if part)


def _valid(value, profile):
    required = set(ANALYSIS_SCHEMA["required"])
    if not isinstance(value, dict) or not required.issubset(value):
        return None
    try:
        value["overall_score"] = max(0, min(100, int(value["overall_score"])))
        value["dimensions"] = [{"name": str(item["name"]), "score": max(0, min(100, int(item["score"]))), "reason": str(item["reason"])} for item in value["dimensions"][:5]]
        profile_text = _profile_text(profile)
        value["strengths"] = [{"name": str(item["name"]), "evidence": str(item["evidence"])} for item in value["strengths"] if isinstance(item, dict) and str(item.get("evidence", "")).strip().lower() in profile_text]
        value["gaps"] = [{"name": str(item["name"]), "priority": str(item["priority"] if item["priority"] in ["高", "中", "低"] else "中"), "reason": str(item["reason"]), "current_evidence": str(item["current_evidence"]).strip() or "当前档案没有直接体现这项经验。", "actions": [str(action) for action in item["actions"][:4] if str(action).strip()], "estimated_effort": str(item["estimated_effort"])} for item in value["gaps"][:5]]
        value["skill_gap"] = [{"name": str(item.get("name", "")), "category": str(item.get("category", "Missing / unclear")), "evidence": str(item.get("evidence", "当前档案中尚未看到明确证据。"))} for item in value.get("skill_gap", [])[:8] if isinstance(item, dict)]
        value["jd_keywords"] = [str(item) for item in value.get("jd_keywords", [])[:12] if str(item).strip()]
        value["resume_evidence"] = [str(item) for item in value.get("resume_evidence", [])[:8] if str(item).strip()]
    except (KeyError, TypeError, ValueError):
        return None
    return value if 3 <= len(value["dimensions"]) <= 5 and 3 <= len(value["gaps"]) <= 5 else None


def analyze_job_match(profile, preferences, job):
    result = analyze_job_fit(build_job_match_messages(profile, preferences, job), schema=ANALYSIS_SCHEMA)
    if not result["ok"]:
        return result
    try:
        candidate = _valid(json.loads(result["content"]), profile)
    except json.JSONDecodeError:
        candidate = None
    if candidate is None:
        candidate = next((parsed for parsed in (_valid(item, profile) for item in _json_objects(result["content"])) if parsed), None)
    return {"ok": True, "analysis": candidate} if candidate else {"ok": False, "error": "invalid_json"}
