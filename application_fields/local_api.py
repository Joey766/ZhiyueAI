"""仅供本机 Chrome Companion 使用的 loopback API。"""
from __future__ import annotations
import json, os, secrets, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from ai.application_answer import prepare_open_answer

LOCAL_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local") / "ZhiyueAI"
DATA_FILE = LOCAL_ROOT / "application_profile.json"; TOKEN_FILE = LOCAL_ROOT / "companion_access_token"; HOST, PORT = "127.0.0.1", 8765
def access_token() -> str:
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists(): return TOKEN_FILE.read_text(encoding="utf-8").strip()
    token = secrets.token_urlsafe(24); TOKEN_FILE.write_text(token, encoding="utf-8"); return token
def save_application_profile(profile: dict, application_job: dict | None = None) -> str:
    """Persist Companion-only data outside the repository.

    This function is called only after an explicit local Companion action.
    """
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {"profile": profile, "application_job": application_job or {}}
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return access_token()


def _stored_data() -> dict:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    # Compatibility with an early local-only profile file.
    return data if "profile" in data else {"profile": data, "application_job": {}}
class _Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8"); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Zhiyue-Token"); self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self._send(204, {})
    def do_GET(self):
        if self.path != "/application-profile" or self.headers.get("X-Zhiyue-Token") != access_token(): self._send(403, {"ok": False, "error": "forbidden"}); return
        if not DATA_FILE.exists(): self._send(404, {"ok": False, "error": "profile_not_ready"}); return
        data = _stored_data()
        self._send(200, {"ok": True, "profile": data.get("profile", {}), "application_job": data.get("application_job", {})})
    def do_POST(self):
        if self.path != "/open-answer" or self.headers.get("X-Zhiyue-Token") != access_token(): self._send(403, {"ok": False, "error": "forbidden"}); return
        if not DATA_FILE.exists(): self._send(404, {"ok": False, "error": "profile_not_ready"}); return
        try:
            length = int(self.headers.get("Content-Length", "0")); payload = json.loads(self.rfile.read(min(length, 7000)).decode("utf-8"))
            data = _stored_data()
            saved_job = data.get("application_job", {})
            saved_context = "\n".join(str(saved_job.get(key, "") or "") for key in ("company", "title", "description", "requirements", "job_url", "apply_url"))
            current_context = str(payload.get("job_context", ""))
            # The selected Zhiyue job is normally more complete than the application form page.
            context = saved_context if saved_context.strip() else current_context
            result = prepare_open_answer(str(payload.get("question", "")), context, data.get("profile", {}))
            self._send(200 if result.get("ok") else 422, result)
        except (ValueError, json.JSONDecodeError): self._send(400, {"ok": False, "error": "invalid_request"})
    def log_message(self, format, *args): return
def ensure_local_api() -> ThreadingHTTPServer | None:
    try: server = ThreadingHTTPServer((HOST, PORT), _Handler)
    except OSError: return None
    threading.Thread(target=server.serve_forever, daemon=True, name="zhiyue-companion-api").start(); return server
