import streamlit as st

from utils.session import go_to


def render():
    st.caption("职跃 AI · Demo　当前为个人作品演示版本，AI 由本地模型运行。")
    st.markdown('<div class="hero"><span class="eyebrow">为早期职业发展而设计</span><h1>发现值得申请的真实岗位，<br>更清楚地准备下一步。</h1><p>上传一次简历并告诉我们求职目标；职跃 AI 从国内外公开招聘源和你手动添加的候选岗位中，帮助判断匹配、差距与行动方向。</p></div>', unsafe_allow_html=True)
    if st.button("开始完善我的档案", type="primary"):
        go_to("我的档案")
    st.markdown("### 你可以这样开始")
    cards = [("🎯", "中外真实岗位推荐", "结合职业方向，从国内外公开招聘源筛选真正值得关注的机会。"), ("🧪", "AI岗位分析", "判断你和岗位的匹配程度，并解释已有优势。"), ("🚀", "能力提升建议", "帮助你识别最值得优先补强的技能与经历。")]
    for col, (icon, title, desc) in zip(st.columns(3), cards):
        with col:
            st.markdown(f'<div class="feature-card"><div class="icon">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown("### 我的求职进度")
    profile = ("已完成", "资料已保存") if st.session_state.profile_saved else ("待完善", "填写并保存个人资料")
    preferences = ("已完成", "偏好已保存") if st.session_state.preferences_saved else ("待完善", "选择目标方向")
    real = (f"{len(st.session_state.get('real_jobs', []))} 个", "当前真实岗位") if st.session_state.get("real_jobs") else ("未获取", "为我寻找岗位")
    selected = ("已选择", "可查看岗位分析") if st.session_state.selected_job else ("未选择", "从岗位推荐开始")
    for col, (label, value, sub) in zip(st.columns(4), [("个人档案", *profile), ("求职偏好", *preferences), ("真实岗位", *real), ("岗位分析", *selected)]):
        with col:
            st.markdown(f'<div class="stat-card"><span>{label}</span><strong>{value}</strong><small>{sub}</small></div>', unsafe_allow_html=True)
