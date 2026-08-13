import requests
from jobs.normalizer import clean_text, standard_job


def fetch(source, timeout=12):
    response = requests.get(f"https://api.lever.co/v0/postings/{source['identifier']}?mode=json", timeout=timeout)
    response.raise_for_status()
    jobs = []
    for item in response.json():
        categories = item.get("categories") or {}
        department = " / ".join(filter(None, [categories.get("team"), categories.get("department")]))
        jobs.append(standard_job(id=f"lever:{source['identifier']}:{item.get('id')}", source="lever", company=source["company"], title=item.get("text"), location=categories.get("location", ""), department=department, employment_type=categories.get("commitment", ""), description=clean_text(item.get("descriptionPlain") or item.get("description", "")), job_url=item.get("hostedUrl"), apply_url=item.get("applyUrl") or item.get("hostedUrl"), industry=source.get("industry", ""), company_type=source.get("company_type", "")))
    return jobs
