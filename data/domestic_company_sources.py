"""国内官方招聘状态：仅展示已确认入口，不猜测或调用未公开 API。"""

DOMESTIC_COMPANIES = [
    {"company": "字节跳动", "auto_sync": False, "url": "https://jobs.bytedance.com/", "status": "暂不支持自动同步：尚未验证无需认证的稳定公开职位接口"},
    {"company": "腾讯", "auto_sync": False, "url": "https://join.qq.com/", "status": "暂不支持自动同步：未验证无需认证的稳定公开职位接口"},
    {"company": "阿里巴巴", "auto_sync": False, "url": "https://www.alibabagroup.com/zh-HK/careers", "status": "暂不支持自动同步"},
    {"company": "百度", "auto_sync": True, "ats": "baidu", "identifier": "intern-public-page", "url": "https://talent.baidu.com/jobs/list?recruitType=INTERN", "industry": "人工智能 / 科技互联网", "company_type": "大型科技公司", "status": "已自动同步：官网公开日常实习岗位"},
    {"company": "小米", "auto_sync": False, "url": "https://hr.xiaomi.com/", "status": "暂不支持自动同步"},
    {"company": "华为", "auto_sync": False, "url": "https://career.huawei.com/cn", "status": "暂不支持自动同步：未验证无需认证的稳定公开职位接口"},
    {"company": "美团", "auto_sync": True, "ats": "meituan", "identifier": "official-public-jobs", "url": "https://zhaopin.meituan.com/web/position/list", "industry": "生活服务 / 科技互联网", "company_type": "大型科技公司", "status": "已自动同步：官网公开职位列表"},
    {"company": "京东", "auto_sync": False, "url": "", "status": "暂不支持自动同步"},
]
