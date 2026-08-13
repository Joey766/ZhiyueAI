"""为官方申请表的开放题准备真实、简洁的草稿；绝不编造经历。"""
from __future__ import annotations
import json

from ai.ollama_client import OllamaClient, _json_objects

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}

def prepare_open_answer(question: str, job_context: str, profile: dict) -> dict:
    prompt = """你是中文求职申请助手。仅依据给定职业档案和岗位上下文，为开放题写一段简洁、真实的回答草稿。不得编造任何经历、数字、技能、身份或授权信息；证据不足时明确说明需要用户补充。只输出 JSON。"""
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps({"question": question, "job_context": job_context[:5000], "application_profile": profile}, ensure_ascii=False)}]
    result = OllamaClient().chat_json(messages, schema=SCHEMA)
    if not result.get("ok"): return result
    try: candidate = json.loads(result["content"])
    except json.JSONDecodeError: candidate = next((item for item in _json_objects(result["content"])), None)
    answer = str((candidate or {}).get("answer", "")).strip()
    return {"ok": True, "answer": answer} if answer else {"ok": False, "error": "invalid_json"}
