import json
import re

import requests

from ai.inference_lock import AI_REQUEST_LOCK

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen3:1.7b"
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "dimensions": {
            "type": "array", "minItems": 3, "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "score": {"type": "integer", "minimum": 0, "maximum": 100}, "reason": {"type": "string"}},
                "required": ["name", "score", "reason"],
            },
        },
        "strengths": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "resume_tips": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall_score", "summary", "dimensions", "strengths", "gaps", "resume_tips"],
}


class OllamaClient:
    def __init__(self, base_url=OLLAMA_URL, model=MODEL_NAME, timeout=300):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def status(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=1)
            response.raise_for_status()
            models = [item.get("name", "") for item in response.json().get("models", [])]
            return {"service_online": True, "model_ready": any(item == self.model or item.startswith(self.model + ":") for item in models), "models": models}
        except requests.RequestException:
            return {"service_online": False, "model_ready": False, "models": []}

    def chat_json(self, messages, schema=ANALYSIS_SCHEMA):
        # Quick Tunnel 演示共享同一台本机模型；不等待，忙时立即让用户稍后重试。
        if not AI_REQUEST_LOCK.acquire(blocking=False):
            return {"ok": False, "error": "busy"}
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": "10m",
            "format": schema,
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            if response.status_code == 404:
                return {"ok": False, "error": "model_missing"}
            response.raise_for_status()
            final_response = response.json()
            # 仅使用最终回答；绝不读取、拼接或展示 message.thinking。
            content = final_response["message"]["content"]
            return {"ok": True, "content": content}
        except requests.Timeout:
            return {"ok": False, "error": "timeout"}
        except requests.ConnectionError:
            return {"ok": False, "error": "service_offline"}
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return {"ok": False, "error": "request_failed"}
        finally:
            AI_REQUEST_LOCK.release()


def _json_objects(text):
    """从额外文字中依次提取合法 JSON 对象。"""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
            if isinstance(value, dict):
                yield value
        except json.JSONDecodeError:
            continue


def _score(value):
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not match:
        raise ValueError("未找到数值评分")
    return max(0, min(100, int(float(match.group(0)))))


def _validate_analysis(data):
    required = {"overall_score", "summary", "dimensions", "strengths", "gaps", "resume_tips"}
    if not isinstance(data, dict) or not required.issubset(data):
        return None
    try:
        data["overall_score"] = _score(data["overall_score"])
        data["dimensions"] = [
            {"name": str(item["name"]), "score": _score(item["score"]), "reason": str(item["reason"])}
            for item in data["dimensions"][:5]
        ]
    except (KeyError, TypeError, ValueError):
        return None
    return data if 3 <= len(data["dimensions"]) <= 5 else None


def parse_json_response(content):
    if not isinstance(content, str):
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    try:
        parsed = _validate_analysis(json.loads(text))
        if parsed is not None:
            return parsed
    except json.JSONDecodeError:
        pass
    for data in _json_objects(text):
        parsed = _validate_analysis(data)
        if parsed is not None:
            return parsed
    return None
