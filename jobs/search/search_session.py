from __future__ import annotations
from datetime import datetime
from uuid import uuid4

def new_search_session(intent: dict, jobs: list[dict], providers: dict, raw_result_count: int) -> dict:
    return {"search_id": uuid4().hex, "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "queries": intent["queries"], "intent": intent, "providers": providers, "raw_result_count": raw_result_count, "deduplicated_count": len(jobs), "recommended_count": 0, "jobs": jobs}
