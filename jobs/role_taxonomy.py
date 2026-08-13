"""岗位方向分层、基础排除和地点偏好的纯本地规则。"""

from __future__ import annotations

import re


ROLE_TAXONOMY = {
    "AI产品经理": {
        "exact": ["ai product", "product manager, ai", "product manager - ai", "genai product", "generative ai product", "llm product", "ai pm", "ai产品", "大模型产品", "智能产品"],
        "close": ["product manager", "product intern", "product management", "technical product", "associate product", "产品经理", "产品实习", "产品策划", "产品策略"],
        "adjacent": ["product analyst", "product analytics", "product operations", "business analyst", "business analytics", "strategy analyst", "data analyst", "产品分析", "产品运营", "商业分析", "业务分析", "战略分析", "数据分析"],
    },
    "产品经理": {
        "exact": ["product manager", "product intern", "product management", "technical product", "associate product", "产品经理", "产品实习", "产品策划", "产品策略"],
        "close": ["product analyst", "product analytics", "product operations", "产品分析", "产品运营"],
        "adjacent": ["business analyst", "business analytics", "strategy analyst", "data analyst", "商业分析", "业务分析", "战略分析", "数据分析"],
    },
    "产品分析师": {
        "exact": ["product analyst", "product analytics", "product data analyst", "产品分析", "产品数据分析"],
        "close": ["data analyst", "business analyst", "business analytics", "analytics", "数据分析", "商业分析", "业务分析"],
        "adjacent": ["product manager", "product intern", "产品经理", "产品实习", "strategy analyst", "战略分析"],
    },
    "商业分析师": {
        "exact": ["business analyst", "business analytics", "strategy analyst", "商业分析", "业务分析", "经营分析", "战略分析"],
        "close": ["data analyst", "analytics", "product analyst", "product analytics", "数据分析", "产品分析"],
        "adjacent": ["product manager", "product intern", "产品经理", "产品实习"],
    },
    "数据分析师": {
        "exact": ["data analyst", "business intelligence", "bi analyst", "数据分析"],
        "close": ["analytics", "product analytics", "business analytics", "product analyst", "商业分析", "产品分析"],
        "adjacent": ["business analyst", "strategy analyst", "data scientist", "商业分析", "战略分析", "数据科学家"],
    },
    "数据科学家": {
        "exact": ["data scientist", "applied scientist", "数据科学家"],
        "close": ["machine learning", "ml engineer", "data analyst", "机器学习", "数据分析"],
        "adjacent": ["business analytics", "product analytics", "business analyst", "商业分析", "产品分析"],
    },
    "量化分析": {
        "exact": ["quantitative analyst", "quant research", "quantitative researcher", "quantitative developer", "量化分析", "量化研究"],
        "close": ["risk analyst", "data analyst", "data scientist", "数据分析", "数据科学家"],
        "adjacent": ["business analyst", "business analytics", "商业分析"],
    },
    "机器学习工程师": {
        "exact": ["machine learning", "ml engineer", "机器学习工程师"],
        "close": ["applied scientist", "data scientist", "数据科学家"],
        "adjacent": ["data analyst", "analytics", "数据分析"],
    },
}

SENIOR_TERMS = ["senior", "sr.", "director", "head", "vice president", "vp", "principal", "staff", "executive", "lead", "高级", "总监", "负责人", "专家", "资深"]
IRRELEVANT_TERMS = ["accountant", "tax", "legal", "lawyer", "human resources", "recruiter", "mechanical engineer", "civil engineer", "sales representative", "credit risk", "nurse", "doctor", "hardware design", "会计", "税务", "法务", "律师", "人力资源", "招聘", "销售", "信贷风险", "护士", "医生", "机械", "土木", "硬件设计"]
AI_TERMS = ["ai", "llm", "genai", "generative ai", "agent", "machine learning", "人工智能", "大模型", "生成式ai", "智能"]
CHINA_MARKERS = ["china", "beijing", "shanghai", "shenzhen", "guangzhou", "hangzhou", "chengdu", "wuhan", "nanjing", "xi'an", "xian", "suzhou", "中国", "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "西安", "苏州"]


def normalized(value):
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def text_for(job):
    return normalized(" ".join([job.get("title", ""), job.get("department", ""), job.get("description", "")]))


def title_for(job):
    return normalized(job.get("title", ""))


def has_seniority(job):
    return any(term in title_for(job) for term in SENIOR_TERMS)


def clearly_irrelevant(job):
    return any(term in title_for(job) for term in IRRELEVANT_TERMS)


def role_match_level(job, targets):
    """按当前目标动态得到 exact / close / adjacent / unrelated。"""
    title = title_for(job)
    content = text_for(job)
    best = "unrelated"
    rank = {"unrelated": 0, "adjacent": 1, "close": 2, "exact": 3}
    for target in targets or []:
        groups = ROLE_TAXONOMY.get(target, {})
        for level in ("exact", "close", "adjacent"):
            if any(term in title for term in groups.get(level, [])) and rank[level] > rank[best]:
                best = level
        # 产品岗位标题未写 AI、但 JD 明确强调 AI 时仍属于 Close；排序时会由
        # 技能、行业等分数提高，不把普通产品岗误写成 Exact。
    return best


def matched_roles(job):
    """保留供筛选控件展示的目标方向标签。"""
    return {target for target in ROLE_TAXONOMY if role_match_level(job, [target]) != "unrelated"}


def recruitment_type(job):
    text = text_for(job)
    if any(term in text for term in ["summer intern", "暑期实习"]): return "暑期实习"
    if any(term in text for term in ["intern", "internship", "实习"]): return "日常实习"
    if any(term in text for term in ["campus", "graduate", "new grad", "校招", "应届"]): return "校招"
    if any(term in text for term in ["social recruitment", "社会招聘", "社招"]): return "社招"
    if any(term in text for term in ["full-time", "full time", "permanent", "全职"]): return "全职"
    return "未知"


def region(job):
    location = normalized(" ".join(job.get("locations") or [job.get("location", "")]))
    return "国内" if any(marker in location for marker in CHINA_MARKERS) else "海外"


def location_matches(job, preferences):
    wanted = preferences.get("工作地点", [])
    if not wanted: return True
    location = normalized(" ".join(job.get("locations") or [job.get("location", "")]))
    mapping = {"中国大陆": CHINA_MARKERS, "加拿大": ["canada", "toronto", "vancouver", "montreal"], "美国": ["united states", " usa", "us-", "new york", "san francisco", "seattle", "chicago"], "香港": ["hong kong"], "新加坡": ["singapore"], "英国": ["united kingdom", "london", "dublin"], "远程": ["remote", "anywhere"]}
    return any(any(token in location for token in mapping.get(item, [normalized(item)])) for item in wanted)


def is_location_expansion(job, preferences):
    if "中国大陆" not in preferences.get("工作地点", []): return False
    location = normalized(" ".join(job.get("locations") or [job.get("location", "")]))
    return any(term in location for term in ["hong kong", "singapore", "remote", "anywhere"])


def stage_matches(job, stage):
    if stage in {"", "都可以", None}: return True
    actual = recruitment_type(job)
    return actual in {"日常实习", "暑期实习"} if stage == "日常实习" else actual == stage


def hard_filter(jobs, preferences):
    """只排除高级和明显无关职位；角色、地点和阶段用于排序而不是默认清空结果。"""
    filtered = []
    for job in jobs:
        if has_seniority(job) or clearly_irrelevant(job):
            continue
        copy = dict(job)
        copy["role_tags"] = sorted(matched_roles(copy))
        copy["recruitment_type"] = copy.get("recruitment_type") or recruitment_type(copy)
        copy["region"] = region(copy)
        filtered.append(copy)
    return filtered
