"""AI provider boundary for local and hosted deployments.

The product works without AI.  This module keeps UI code independent from a
specific model runtime and never embeds credentials in source control.
"""
from __future__ import annotations

import os
from typing import Any

import requests

from ai.ollama_client import MODEL_NAME, OllamaClient


def _setting(name: str, default: str = "") -> str:
    try:
        import streamlit as st
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    return str(value or default)


class RemoteClient:
    """Small OpenAI-compatible client; configured only through secrets/env."""
    def __init__(self) -> None:
        self.url = _setting("ZHIYUE_REMOTE_AI_URL").rstrip("/")
        self.key = _setting("ZHIYUE_REMOTE_AI_API_KEY")
        self.model = _setting("ZHIYUE_REMOTE_AI_MODEL")

    def status(self) -> dict[str, Any]:
        ready = bool(self.url and self.key and self.model)
        return {"service_online": ready, "model_ready": ready, "models": [self.model] if ready else []}

    def chat_json(self, messages, schema):
        if not self.status()["model_ready"]:
            return {"ok": False, "error": "not_configured"}
        endpoint = self.url if self.url.endswith("/chat/completions") else self.url + "/chat/completions"
        try:
            response = requests.post(endpoint, headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}, json={"model": self.model, "messages": messages, "response_format": {"type": "json_object"}, "temperature": 0.2}, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return {"ok": True, "content": content}
        except requests.Timeout:
            return {"ok": False, "error": "timeout"}
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return {"ok": False, "error": "request_failed"}


def get_provider():
    """Return configured provider. Defaults to private local Ollama."""
    return RemoteClient() if _setting("ZHIYUE_AI_PROVIDER", "local").lower() == "remote" else OllamaClient()


def provider_status() -> dict[str, Any]:
    return get_provider().status()


def parse_resume(messages, schema):
    return get_provider().chat_json(messages, schema=schema)


def analyze_job_fit(messages, schema):
    return get_provider().chat_json(messages, schema=schema)


def parse_search_intent(messages, schema):
    """Reserved for an optional provider-backed intent parser."""
    return get_provider().chat_json(messages, schema=schema)
