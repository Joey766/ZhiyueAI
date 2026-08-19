import streamlit as st

from ai.job_analyzer import analyze_job_match
from ai.provider import provider_status
from utils.session import go_to


def _profile_has_substance(profile):
    """避免在空档案上让模型臆测用户经历。"""
    def values(item):
        if isinstance(item, dict):
            for value in item.values():
                yield from values(value)
        elif isinstance(item, list):
            for value in item:
                yield from values(value)
        elif isinstance(item, str):
            yield item.strip()
    return any(value for value in values(profile))


def _show_analysis(analysis):
    st.header("Overall Fit")
    level = "Strong" if analysis["overall_score"] >= 75 else ("Moderate" if analysis["overall_score"] >= 45 else "Stretch")
    st.subheader(level)
    st.caption("该结论用于理解岗位与档案的关系，不代表录取概率。")
    st.subheader("Why this role fits you")
    st.write(analysis["summary"])
    st.subheader("匹配维度")
    for item in analysis["dimensions"]:
        st.write(f"**{item['name']}　{item['score']}%**")
        st.progress(item["score"])
        st.caption(item["reason"])
    st.subheader("Your Strengths")
    if analysis["strengths"]:
        for item in analysis["strengths"]:
            st.write(f"✅ {item['name']}")
            st.caption(f"档案证据：{item['evidence']}")
    else:
        st.caption("当前档案中尚未找到可直接佐证的岗位优势；补充真实项目或经历后可再次分析。")

    st.divider()
    st.header("Your Gaps")
    st.caption("岗位要求通常不是必须全部满足。以下建议用于帮助你判断优先补强方向，并不代表缺少其中某一项就不应该申请。")
    for gap in analysis["gaps"]:
        with st.container(border=True):
            st.markdown(f"#### {gap['name']} · 优先级：{gap['priority']}")
            st.write(f"**为什么重要：** {gap['reason']}")
            st.write(f"**当前证据：** {gap['current_evidence']}")
            st.write("**具体行动：**")
            for action in gap["actions"]:
                st.write(f"- {action}")
            st.caption(f"预计投入：{gap['estimated_effort']}")

    st.divider()
    st.header("Skill Gap Analysis")
    if analysis.get("skill_gap"):
        for item in analysis["skill_gap"]:
            st.write(f"**{item['category']} · {item['name']}**")
            st.caption(item["evidence"])
    else:
        st.caption("模型未返回结构化技能分类；上方差距项仍基于当前 JD 与档案。")
    st.header("Before You Apply")
    for item in analysis["application_advice"]:
        st.write(f"- {item}")
    advice = analysis["apply_recommendation"]
    st.subheader("现在应该申请吗？")
    st.success(f"{advice['decision']}：{advice['reason']}")
    st.subheader("JD Keywords")
    st.write(" · ".join(analysis.get("jd_keywords", [])) or "当前 JD 未提供足够关键词。")
    st.subheader("Resume Evidence")
    if analysis.get("resume_evidence"):
        for item in analysis["resume_evidence"]: st.write(f"- {item}")
    else:
        st.caption("当前档案中未提取到可直接对应的证据。")


def render():
    st.title("岗位分析")
    job = st.session_state.selected_job
    if not job:
        st.info("请先从“岗位推荐”中选择一个岗位。")
        if st.button("前往岗位推荐", type="primary"):
            go_to("岗位推荐")
        return
    if "company" not in job:
        st.warning("当前岗位来自旧演示数据，请重新从岗位推荐中选择岗位后进行分析。")
        return
    if not st.session_state.profile_saved or not _profile_has_substance(st.session_state.profile):
        st.warning("请先在“我的档案”中填写并保存真实经历，再进行 AI 岗位分析。这样可以避免模型在信息不足时作出推测。")
        if st.button("前往我的档案", type="primary"):
            go_to("我的档案")
        return
    with st.container(border=True):
        st.markdown(f"### {job['company']} · {job['title']}")
        st.caption(f"地点：{job['location']}　·　Official Source：{job['source']}")
        if job.get("apply_url") or job.get("job_url"):
            st.link_button("Apply on Company Website ↗", job.get("apply_url") or job["job_url"])
    st.caption("AI 仅在你点击分析后调用，并且只基于你提供的信息和岗位 JD。")
    status = provider_status()
    if not status["service_online"]:
        st.warning("AI 深度分析当前未配置或暂不可用；你仍可浏览真实岗位与基础 Fit Estimate。")
        return
    if not status["model_ready"]:
        st.warning("AI 深度分析当前不可用；你仍可浏览真实岗位与基础 Fit Estimate。")
        return
    saved = st.session_state.get("ai_job_analysis")
    current = saved and saved.get("job_id") == job["id"]
    action = "重新分析" if current else "✨ 开始 AI 分析"
    if st.button(action, type="primary", width="stretch"):
        with st.spinner("正在分析你的背景与岗位要求……"):
            result = analyze_job_match(st.session_state.profile, st.session_state.preferences, job)
        if result["ok"]:
            st.session_state.ai_job_analysis = {"job_id": job["id"], "result": result["analysis"]}
            st.rerun()
        elif result.get("error") == "busy":
            st.warning("AI 当前正在处理其他请求，请稍后再试。")
        elif result.get("error") == "timeout":
            st.error("本地 AI 分析时间较长或暂未响应，请稍后重试。")
        elif result.get("error") == "invalid_json":
            st.error("本次分析结果格式异常，请重新尝试。")
        else:
            st.error("本次岗位分析未完成，请确认 Ollama 正常运行后重试。")
    if current:
        _show_analysis(saved["result"])
