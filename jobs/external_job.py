"""用户主动导入的外部岗位；绝不尝试绕过第三方招聘网站限制。"""

from urllib.parse import urlparse
from uuid import uuid4

from jobs.normalizer import standard_job


def source_label(url):
    host = urlparse(url).netloc.lower()
    if "zhipin" in host:
        return "用户添加 · BOSS直聘"
    if "linkedin" in host:
        return "用户添加 · LinkedIn"
    if "indeed" in host:
        return "用户添加 · Indeed"
    return "用户手动粘贴"


def create_external_job(company, title, location, url, description):
    return standard_job(id=f"external:{uuid4().hex}", source=source_label(url), source_type="external", company=company, title=title, location=location, description=description, job_url=url, apply_url=url, is_real_job=True, is_demo=False)
