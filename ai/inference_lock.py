"""串行化本机 Ollama 推理，避免公开演示同时占满 CPU。"""

from threading import Lock


# 这是唯一的跨会话状态：不保存简历、偏好或分析结果，只表示模型是否忙碌。
AI_REQUEST_LOCK = Lock()
