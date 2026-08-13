import os
from urllib.parse import urlparse

import streamlit as st

from data.company_sources import COMPANY_SOURCES
from data.domestic_company_sources import DOMESTIC_COMPANIES
from jobs.aggregator import source_signature
from jobs.search.query_builder import build_search_intent
from jobs.search.orchestrator import search_all_sources
from jobs.external_job import create_external_job
from jobs.recommender import LEVEL_LABELS, TARGET_RECOMMENDATIONS, curated_jobs, rank_jobs
from jobs.role_taxonomy import hard_filter, recruitment_type, region, role_match_level
from application_fields.field_taxonomy import application_profile
from application_fields.local_api import save_application_profile
from utils.session import go_to

PAGE_SIZE = 25


def _render_dev_diagnostics():
    """仅供开发时核对漏斗；必须显式设置环境变量才会显示。"""
    if os.getenv("ZHIYUE_DEV_DIAGNOSTICS") != "1":
        return
    jobs = (st.session_state.get("current_job_search") or {}).get("jobs", [])
    prefs = st.session_state.preferences
    targets = prefs.get("目标岗位", [])
    base = hard_filter(jobs, prefs)
    with st.expander("开发诊断：推荐漏斗", expanded=False):
        st.caption("仅开发模式显示；统计基于当前浏览器会话已刷新、去重后的真实岗位。")
        cn = [job for job in jobs if region(job) == "国内"]
        interns = [job for job in jobs if recruitment_type(job) in {"日常实习", "暑期实习"}]
        st.write({"原始唯一岗位": st.session_state.get("jobs_raw_count", len(jobs)), "去重后岗位": len(jobs), "中国大陆岗位": len(cn), "实习岗位": len(interns), "中国大陆 + 实习": sum(job in interns for job in cn), "exact": sum(role_match_level(job, targets) == "exact" for job in base), "close": sum(role_match_level(job, targets) == "close" for job in base), "adjacent": sum(role_match_level(job, targets) == "adjacent" for job in base), "unrelated": sum(role_match_level(job, targets) == "unrelated" for job in base), "最终精选": len(curated_jobs(rank_jobs(jobs, st.session_state.profile, prefs)))})
        st.markdown("**Provider 同步明细**")
        for company, stats in st.session_state.get("provider_stats", {}).items():
            company_jobs = [job for job in jobs if job.get("company") == company]
            china_jobs = [job for job in company_jobs if region(job) == "国内"]
            intern_jobs = [job for job in company_jobs if recruitment_type(job) in {"日常实习", "暑期实习"}]
            product_jobs = [job for job in company_jobs if any(token in (job.get("title", "") + " " + job.get("department", "")).lower() for token in ["product", "产品"])]
            ai_product_jobs = [job for job in product_jobs if any(token in (job.get("title", "") + " " + job.get("description", "")).lower() for token in ["ai", "llm", "大模型", "人工智能"])]
            st.write({"Provider": company, "状态": stats.get("status"), "HTTP": stats.get("http_status"), "原始返回": stats.get("raw_jobs"), "标准化后": stats.get("normalized_jobs"), "中国大陆": len(china_jobs), "实习": len(intern_jobs), "Product": len(product_jobs), "AI Product": len(ai_product_jobs), "解析失败": stats.get("parse_failures"), "耗时(秒)": stats.get("duration_seconds"), "失败原因": stats.get("failure", "")})
        for item in DOMESTIC_COMPANIES:
            company_jobs = [job for job in jobs if job.get("company") == item["company"]]
            if not item.get("auto_sync"):
                st.write({"Provider": item["company"], "状态": item["status"], "HTTP": "未请求（未接入 Provider）", "原始返回": 0, "标准化后": 0, "中国大陆": 0, "实习": 0, "Product": 0, "AI Product": 0, "解析失败": 0, "耗时(秒)": 0})


def _sources():
    domestic = [item for item in DOMESTIC_COMPANIES if item.get("auto_sync")]
    return COMPANY_SOURCES + domestic + st.session_state.get("custom_job_sources", [])


def _refresh(intent=None):
    intent = intent or build_search_intent(st.session_state.profile, st.session_state.preferences)
    session = search_all_sources(source_signature(_sources()), intent, st.session_state.job_refresh_token)
    st.session_state.current_job_search = session
    # 临时兼容旧会话键；推荐页面主流程仅使用 current_job_search。
    st.session_state.real_jobs = session["jobs"]
    st.session_state.job_source_errors = [name for name, data in session["providers"].items() if data["status"] == "failed"]
    st.session_state.jobs_updated_at = session["searched_at"]
    st.session_state.jobs_raw_count = session["raw_result_count"]
    st.session_state.provider_stats = session["providers"]


def _add_external_form():
    st.subheader("没找到你想看的岗位？")
    with st.expander("➕ 添加外部岗位", expanded=False):
        st.caption("可粘贴 BOSS、LinkedIn、Indeed、公司官网等公开链接，也可直接粘贴 JD。系统不会登录、绕过验证码或自动抓取受限网站。")
        with st.form("external_job_form", border=False):
            link = st.text_input("粘贴岗位链接（可选）", placeholder="https://...")
            company, title = st.columns(2)
            company_value = company.text_input("公司名称")
            title_value = title.text_input("岗位名称")
            location = st.text_input("地点（可选）")
            description = st.text_area("直接粘贴岗位描述", placeholder="职责、要求、地点等；若链接无法自动读取，请将 JD 粘贴到这里。", height=180)
            submitted = st.form_submit_button("加入我的候选岗位", type="primary")
        if submitted:
            if not company_value.strip() or not title_value.strip() or not description.strip():
                st.error("请至少填写公司名称、岗位名称和岗位描述。")
            else:
                st.session_state.saved_jobs.append(create_external_job(company_value.strip(), title_value.strip(), location.strip(), link.strip(), description.strip()))
                st.success("已加入我的候选岗位，可在“我的候选岗位”中进入 AI 分析。")
        st.caption("对于暂时无法自动读取的外部链接，请复制岗位 JD 到上方；不会尝试登录或绕过网站限制。")


def _show_details(job):
    st.markdown("**岗位描述**")
    st.write(job.get("description") or "未提供岗位描述。")
    details = [
        ("地点", " / ".join(job.get("locations") or [job.get("location", "")])) ,
        ("部门", job.get("department")), ("招聘类型", job.get("recruitment_type")),
        ("发布时间", job.get("posted_at")), ("薪资", job.get("compensation")), ("来源", job.get("source")),
    ]
    for label, value in details:
        if value:
            st.write(f"**{label}：** {value}")


def _render_card(job):
    with st.container(border=True):
        head, score = st.columns([7, 2], vertical_alignment="center")
        head.markdown(f"#### {job['company']} · {job['title']}")
        parts = [f"📍 {job.get('location', '未注明')}"]
        if job.get("recruitment_type"):
            parts.append(f"💼 {job['recruitment_type']}")
        if job.get("industry"):
            parts.append(f"🏢 {job['industry']}")
        head.caption("　·　".join(parts))
        score.markdown(f'<div class="match"><small>推荐度</small>{job["recommendation_score"]}%</div>', unsafe_allow_html=True)
        tag = "我的候选岗位" if job.get("source_type") == "external" else "真实岗位"
        st.caption(f"{tag} · 来源：{job['source']}")
        reasons = job.get("recommendation_reasons", [])
        if reasons:
            st.write("**为什么推荐给你？** " + "；".join(reasons[:4]))
        buttons = st.container(horizontal=True)
        with buttons:
            if st.button("查看详情", key=f"detail_{job['id']}"):
                st.session_state.expanded_job_id = None if st.session_state.expanded_job_id == job["id"] else job["id"]
            if st.button("AI 分析", key=f"analyse_{job['id']}", type="primary"):
                st.session_state.selected_job = job
                st.session_state.ai_job_analysis = None
                go_to("岗位分析")
            apply_url = job.get("apply_url") or job.get("job_url")
            if apply_url:
                if st.button("去申请（记录岗位）", key=f"prepare_{job['id']}"):
                    application_job = {key: job.get(key, "") for key in ("company", "title", "description", "requirements", "job_url", "apply_url")}
                    st.session_state.application_job = application_job
                    if os.getenv("ZHIYUE_LOCAL_COMPANION") == "1":
                        save_application_profile(application_profile(st.session_state.profile), application_job)
                        st.success("已将该岗位资料同步到本机 Chrome Companion。")
                    else:
                        st.caption("已记住该岗位；启用本机 Companion 后可让扩展使用完整 JD。")
                st.link_button("打开官方申请页", apply_url)
        if st.session_state.expanded_job_id == job["id"]:
            _show_details(job)


def _render_domestic_status():
    with st.expander("国内公司官方招聘入口与同步状态"):
        st.caption("仅对已验证可低频读取的公开官网页面启用同步；其他公司保留官方入口，不猜测接口、不登录也不绕过限制。")
        for item in DOMESTIC_COMPANIES:
            row = st.container(horizontal=True, horizontal_alignment="distribute")
            with row:
                st.write(f"{item['company']}：{item['status']}")
                if item["url"]:
                    st.link_button("打开官方招聘网站", item["url"], key=f"official_{item['company']}")


def _filtered_jobs(tab):
    jobs = (st.session_state.get("current_job_search") or {}).get("jobs", [])
    if tab == "国内":
        jobs = [job for job in jobs if region(job) == "国内"]
    elif tab == "海外":
        jobs = [job for job in jobs if region(job) == "海外"]
    elif tab == "我的候选岗位":
        jobs = st.session_state.saved_jobs
        return rank_jobs(jobs, st.session_state.profile, st.session_state.preferences, force_include=True)
    return rank_jobs(jobs, st.session_state.profile, st.session_state.preferences)


def _render_grouped_jobs(jobs):
    for level, icon in [("exact", "🎯"), ("close", "🤝"), ("adjacent", "🧭")]:
        group = [job for job in jobs if job.get("role_match_level") == level]
        if not group:
            continue
        st.subheader(f"{icon} {LEVEL_LABELS[level]}")
        for job in group:
            _render_card(job)


def render():
    jobs_ready = bool((st.session_state.get("current_job_search") or {}).get("jobs"))
    selected = _filtered_jobs("全部") if jobs_ready else []
    curated = curated_jobs(selected)
    total = len((st.session_state.get("current_job_search") or {}).get("jobs", []))
    st.title(f"为你精选 {len(curated)} 个岗位" if jobs_ready else "为你精选岗位")
    if jobs_ready:
        search = st.session_state.current_job_search
        search["recommended_count"] = len(curated)
        st.caption(f"本次发现 {search['raw_result_count']} 个潜在岗位，去重后 {search['deduplicated_count']} 个，为你精选 {len(curated)} 个机会。")
    else:
        st.caption("根据你的职业档案和求职偏好，从多个真实招聘来源寻找当前机会。")
    st.info("结果按最匹配、相近机会和拓展机会分层。推荐度仅用于本地排序，不代表录取概率；岗位列表不会调用本地 AI。")
    toolbar = st.container(horizontal=True, horizontal_alignment="distribute")
    with toolbar:
        if st.button("✨ 为我寻找岗位", type="primary"):
            st.session_state.job_refresh_token += 1
            intent = build_search_intent(st.session_state.profile, st.session_state.preferences)
            with st.status("正在为你寻找岗位…", expanded=True) as status:
                st.write("正在分析你的求职方向…")
                st.write("正在生成搜索条件…")
                st.write("正在搜索百度招聘、美团招聘、Greenhouse、Lever 与 Ashby…")
                _refresh(intent)
                st.write("正在去除重复岗位并计算推荐度…")
                status.update(label="岗位搜索完成", state="complete", expanded=False)
            st.rerun()
        if st.session_state.get("jobs_updated_at"):
            st.caption(f"岗位数据更新于：{st.session_state.jobs_updated_at}")
        st.session_state.setdefault("show_all_matching_jobs", False)
        if st.button("查看全部匹配岗位" if not st.session_state.show_all_matching_jobs else "返回精选岗位"):
            st.session_state.show_all_matching_jobs = not st.session_state.show_all_matching_jobs
            st.rerun()
    if st.session_state.get("job_source_errors"):
        st.warning("部分招聘源暂时无法同步，其他岗位仍可正常浏览。")
    _add_external_form()
    _render_domestic_status()
    if jobs_ready:
        with st.expander("本次搜索来源", expanded=False):
            for name, info in st.session_state.current_job_search.get("providers", {}).items():
                if info.get("status") == "success":
                    st.write(f"{name}：{info.get('count', 0)} 个（{info.get('mode', '')}）")
                else:
                    st.write(f"{name}：暂时无法同步（{info.get('failure', '未知原因')}）")
    _render_dev_diagnostics()
    if not jobs_ready:
        st.info("点击“✨ 为我寻找岗位”，根据当前档案与偏好创建一次新的岗位搜索。")
        return
    # “中国大陆”是排序偏好而非默认把结果锁死在国内 Tab；相关岗位不足时应能补充相近机会。
    default_tab = 0
    tab = st.segmented_control("岗位范围", ["全部", "国内", "海外", "我的候选岗位"], default=["全部", "国内", "海外", "我的候选岗位"][default_tab], label_visibility="collapsed")
    if not tab:
        tab = ["全部", "国内", "海外", "我的候选岗位"][default_tab]
    ranked = _filtered_jobs(tab)
    roles = ["全部"] + sorted({tag for job in ranked for tag in job.get("role_tags", [])})
    companies = ["全部"] + sorted({job["company"] for job in ranked})
    industries = ["全部"] + sorted({job["industry"] for job in ranked if job.get("industry")})
    recruitment = ["全部"] + sorted({job["recruitment_type"] for job in ranked if job.get("recruitment_type")})
    with st.form("job_filters", border=False):
        role, company, industry = st.columns(3)
        role_value = role.selectbox("岗位方向", roles)
        company_value = company.selectbox("公司", companies)
        industry_value = industry.selectbox("行业", industries)
        recruitment_col, minimum_col = st.columns(2)
        recruitment_value = recruitment_col.selectbox("招聘类型", recruitment)
        minimum_value = minimum_col.slider("最低推荐度", 0, 100, 0)
        st.form_submit_button("应用筛选")
    filtered = [job for job in ranked if (role_value == "全部" or role_value in job.get("role_tags", [])) and (company_value == "全部" or company_value == job["company"]) and (industry_value == "全部" or industry_value == job.get("industry")) and (recruitment_value == "全部" or recruitment_value == job.get("recruitment_type")) and job["recommendation_score"] >= minimum_value]
    shown = filtered if st.session_state.show_all_matching_jobs or tab == "我的候选岗位" else curated_jobs(filtered)
    if not st.session_state.show_all_matching_jobs and tab != "我的候选岗位":
        st.caption(f"精选五层目标为约 {TARGET_RECOMMENDATIONS} 个；岗位不足时将如实显示实际数量。")
        china_preferred = "中国大陆" in st.session_state.preferences.get("工作地点", [])
        domestic_shown = [job for job in shown if region(job) == "国内"]
        overseas_shown = [job for job in shown if region(job) != "国内"]
        if china_preferred:
            st.subheader("🇨🇳 中国大陆机会")
            _render_grouped_jobs(domestic_shown)
            if overseas_shown:
                st.subheader("🌎 国内匹配机会较少，为你补充的海外相近机会")
                _render_grouped_jobs(overseas_shown)
        else:
            _render_grouped_jobs(shown)
        if not shown:
            st.info("没有符合当前条件的岗位。可调整偏好、降低最低推荐度，或查看我的候选岗位。")
        return
    page_key = f"jobs_page_{tab}"
    st.session_state.setdefault(page_key, 1)
    total_pages = max(1, (len(shown) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 1
    if len(shown) > PAGE_SIZE:
        page = st.number_input("页码", min_value=1, max_value=total_pages, step=1, key=page_key)
    start = (page - 1) * PAGE_SIZE
    st.subheader(f"{len(shown)} 个匹配岗位")
    for job in shown[start:start + PAGE_SIZE]:
        _render_card(job)
    if not shown:
        st.info("没有符合当前条件的精选岗位。可调整偏好、降低最低推荐度，或查看我的候选岗位。")
