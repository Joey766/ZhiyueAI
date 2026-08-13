import streamlit as st

from ai.job_analyzer import analyze_job_match
from ai.ollama_client import MODEL_NAME, OllamaClient
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
    st.header("1. 岗位匹配")
    st.metric("整体匹配度", f"{analysis['overall_score']}%")
    st.subheader("综合评价")
    st.write(analysis["summary"])
    st.subheader("能力匹配")
    for item in analysis["dimensions"]:
        st.write(f"**{item['name']}　{item['score']}%**")
        st.progress(item["score"])
        st.caption(item["reason"])
    st.subheader("我的优势")
    if analysis["strengths"]:
        for item in analysis["strengths"]:
            st.write(f"✅ {item['name']}")
            st.caption(f"档案证据：{item['evidence']}")
    else:
        st.caption("当前档案中尚未找到可直接佐证的岗位优势；补充真实项目或经历后可再次分析。")

    st.divider()
    st.header("2. 能力差距")
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
    st.header("3. 如果想申请这个岗位，建议怎么提升？")
    for item in analysis["application_advice"]:
        st.write(f"- {item}")
    advice = analysis["apply_recommendation"]
    st.subheader("现在应该申请吗？")
    st.success(f"{advice['decision']}：{advice['reason']}")


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
        st.caption(f"📍 {job['location']}　·　{job['department'] or '未注明部门'}　·　来源：{job['source'].title()}")
        if job.get("job_url"):
            st.link_button("查看官方岗位", job["job_url"])
    st.caption("🔒 AI 仅在你点击分析后于本机调用 qwen3:1.7b；岗位列表阶段不会调用 AI。")
    status = OllamaClient().status()
    if not status["service_online"]:
        st.warning("⚠️ 本地 AI 服务未启动。请先启动 Ollama，然后重新尝试。")
        return
    if not status["model_ready"]:
        st.warning(f"⚠️ 尚未安装 {MODEL_NAME}。请先运行 ollama pull {MODEL_NAME}。")
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
