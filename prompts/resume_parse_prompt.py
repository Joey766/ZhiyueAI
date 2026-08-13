import json

RESUME_PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "basic": {"type": "object", "properties": {key: {"type": "string"} for key in ["name", "english_name", "email", "phone", "location", "linkedin", "portfolio"]}, "required": ["name", "english_name", "email", "phone", "location", "linkedin", "portfolio"]},
        "education": {"type": "array", "items": {"type": "object", "properties": {key: {"type": "string"} for key in ["school", "major", "degree", "start_date", "graduation_date", "gpa"]}, "required": ["school", "major", "degree", "start_date", "graduation_date", "gpa"]}},
        "experience": {"type": "array", "items": {"type": "object", "properties": {key: {"type": "string"} for key in ["company", "role", "start_date", "end_date", "content"]}, "required": ["company", "role", "start_date", "end_date", "content"]}},
        "projects": {"type": "array", "items": {"type": "object", "properties": {key: {"type": "string"} for key in ["name", "role", "time", "description", "skills"]}, "required": ["name", "role", "time", "description", "skills"]}},
        "skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["basic", "education", "experience", "projects", "skills"],
}

SYSTEM_PROMPT = """你是职跃 AI 的本地简历信息提取器。你的唯一任务是从简历原文中提取已有事实，绝不美化、改写、推断或编造任何经历、公司、项目、技能、学历、时间、地点或成果。
简历中没有明确出现的信息必须返回空字符串；没有明确出现的经历或技能必须返回空数组。保留原文含义，工作内容和项目描述可摘录或压缩，但不得加入原文不存在的事实。只返回符合给定 JSON Schema 的合法 JSON；不要返回 Markdown、解释或思考过程。"""

def build_resume_parse_messages(resume_text):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "请提取以下简历原文中的已有信息：\n" + json.dumps({"简历原文": resume_text}, ensure_ascii=False)},
    ]
