"""基于表单语义的申请字段分类；不包含任何网站专属 CSS 选择器。"""
from __future__ import annotations
import json
import re
from pathlib import Path

_ALIASES = json.loads(Path(__file__).with_name("field_aliases.json").read_text(encoding="utf-8"))
FIELD_TAXONOMY = _ALIASES["fields"]
OPEN_ENDED_TERMS = _ALIASES["open_ended_terms"]
"""FIELD_TAXONOMY is deliberately loaded from field_aliases.json.

The Chrome extension loads that same file, so canonical keys and matching order stay aligned.
"""
'''{
    "first_name": ["first name", "given name", "名字"], "last_name": ["last name", "family name", "surname", "姓氏"],
    "full_name": ["full name", "name", "姓名"], "preferred_name": ["preferred name", "chosen name", "常用名"],
    "email": ["email address", "email", "邮箱", "电子邮件"], "phone": ["phone number", "phone", "mobile", "手机", "联系电话"],
    "location": ["current location", "location", "address", "所在地", "现居地"], "linkedin": ["linkedin"], "github": ["github"],
    "portfolio": ["portfolio", "personal website", "website", "作品集", "个人网站"], "school": ["university", "institution", "school", "学校", "院校"],
    "degree": ["degree", "学历", "学位"], "major": ["field of study", "major", "专业"], "gpa": ["gpa"],
    "graduation_date": ["expected graduation", "graduation date", "graduation", "毕业时间", "预计毕业"],
    "work_authorization": ["legally authorized to work", "work authorization", "工作许可", "工作授权"],
    "requires_sponsorship": ["require sponsorship", "visa sponsorship", "签证支持", "需要签证"],
    "willing_to_relocate": ["willing to relocate", "relocation", "愿意搬迁", "是否愿意搬迁"],
    "company": ["employer", "company", "公司"], "job_title": ["job title", "position", "职位"], "start_date": ["start date", "开始时间"], "end_date": ["end date", "结束时间"], "responsibilities": ["responsibilities", "工作内容", "岗位职责"],
}'''

def normalize_label(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()

def classify_field(label: object, field_type: str = "") -> str:
    text = normalize_label(label)
    if any(term in text for term in OPEN_ENDED_TERMS): return "open_ended"
    for field, terms in FIELD_TAXONOMY.items():
        if any(term in text for term in terms):
            if field == "full_name" and any(term in text for term in ["first", "given", "last", "family", "surname"]): continue
            return field
    return "unknown"

def _first(records: list[dict], *keys: str) -> str:
    for record in records or []:
        for key in keys:
            value = str(record.get(key, "") or "").strip()
            if value: return value
    return ""

def application_profile(profile: dict) -> dict:
    """从已保存档案生成最小化 Application Profile，缺失值绝不推断。"""
    basic, app = profile.get("basic", {}), profile.get("application", {})
    education = [{"school": item.get("学校", ""), "degree": item.get("学位", ""), "major": item.get("专业", ""), "graduation_date": item.get("预计毕业时间", ""), "gpa": item.get("GPA", "")} for item in profile.get("education", [])]
    experience = [{"company": item.get("公司名称", ""), "job_title": item.get("职位", ""), "start_date": item.get("开始时间", ""), "end_date": item.get("结束时间", ""), "responsibilities": item.get("工作内容", "")} for item in profile.get("experience", [])]
    projects = [{"name": item.get("项目名称", ""), "role": item.get("项目角色", ""), "time": item.get("项目时间", ""), "description": item.get("项目描述", ""), "skills": item.get("使用技能", "")} for item in profile.get("projects", [])]
    sponsorship, relocation = str(app.get("visa_support", "") or "").strip(), str(app.get("relocation", "") or "").strip()
    authorization = str(app.get("work_authorization", "") or "").strip()
    if authorization == "未填写": authorization = ""
    return {"personal": {"first_name": str(basic.get("first_name", "") or "").strip(), "last_name": str(basic.get("last_name", "") or "").strip(), "full_name": str(basic.get("name", "") or "").strip(), "preferred_name": str(basic.get("preferred_name", "") or "").strip(), "email": str(basic.get("email", "") or "").strip(), "phone": str(basic.get("phone", "") or "").strip(), "location": str(basic.get("location", "") or "").strip(), "linkedin": str(basic.get("linkedin", "") or "").strip(), "github": str(basic.get("github", "") or "").strip(), "portfolio": str(basic.get("portfolio", "") or "").strip()}, "education": education, "experience": experience, "projects": projects, "skills": list(profile.get("skills", [])), "application_info": {"graduation_date": _first(education, "graduation_date"), "work_authorization": authorization, "requires_sponsorship": {"是": True, "否": False}.get(sponsorship), "willing_to_relocate": {"是": True, "否": False}.get(relocation)}}

def value_for_field(application: dict, field: str) -> object:
    personal = application.get("personal", {})
    if field in personal: return personal[field]
    if field in {"school", "degree", "major", "gpa"}: return _first(application.get("education", []), field)
    if field == "graduation_date": return application.get("application_info", {}).get("graduation_date", "")
    if field in {"work_authorization", "requires_sponsorship", "willing_to_relocate"}: return application.get("application_info", {}).get(field, "")
    if field in {"company", "job_title", "start_date", "end_date", "responsibilities"}: return _first(application.get("experience", []), field)
    return ""

def completeness(application: dict) -> list[tuple[str, bool]]:
    personal, info = application.get("personal", {}), application.get("application_info", {})
    return [("基本信息", bool(personal.get("full_name"))), ("教育经历", bool(_first(application.get("education", []), "school"))), ("联系方式", bool(personal.get("email") and personal.get("phone"))), ("LinkedIn", bool(personal.get("linkedin"))), ("GitHub", bool(personal.get("github"))), ("工作授权", bool(info.get("work_authorization"))), ("Sponsorship", info.get("requires_sponsorship") is not None), ("搬迁意愿", info.get("willing_to_relocate") is not None)]
