import requests
from jobs.normalizer import standard_job


def fetch(source, timeout=12):
    response = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{source['identifier']}/jobs?content=true", timeout=timeout)
    response.raise_for_status()
    return [standard_job(id=f"greenhouse:{source['identifier']}:{item.get('id')}", source="greenhouse", company=source["company"], title=item.get("title"), location=(item.get("location") or {}).get("name", ""), department=", ".join(part.get("name", "") for part in item.get("departments", []) if part.get("name")), description=item.get("content", ""), job_url=item.get("absolute_url"), apply_url=item.get("absolute_url"), posted_at=item.get("updated_at"), industry=source.get("industry", ""), company_type=source.get("company_type", "")) for item in response.json().get("jobs", [])]
