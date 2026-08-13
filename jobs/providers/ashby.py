import requests
from jobs.normalizer import standard_job


def fetch(source, timeout=12):
    response = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{source['identifier']}?includeCompensation=true", timeout=timeout)
    response.raise_for_status()
    jobs = []
    for item in response.json().get("jobs", []):
        if item.get("isListed") is False:
            continue
        compensation = ((item.get("compensation") or {}).get("scrapeableCompensationSalarySummary") or (item.get("compensation") or {}).get("compensationTierSummary"))
        locations = [item.get("location", "")] + [part.get("location", "") for part in item.get("secondaryLocations", []) if isinstance(part, dict)]
        jobs.append(standard_job(id=f"ashby:{source['identifier']}:{item.get('id')}", source="ashby", company=source["company"], title=item.get("title"), location=item.get("location", ""), locations=locations, department=item.get("department", ""), employment_type=item.get("employmentType", ""), description=item.get("descriptionPlain") or item.get("descriptionHtml", ""), job_url=item.get("jobUrl"), apply_url=item.get("applyUrl") or item.get("jobUrl"), compensation=compensation, posted_at=item.get("publishedAt"), industry=source.get("industry", ""), company_type=source.get("company_type", "")))
    return jobs
