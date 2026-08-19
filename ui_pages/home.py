import streamlit as st

from utils.session import go_to


def render():
    st.caption("职跃 AI · 你的求职发现与决策助手")
    st.markdown('<div class="hero"><span class="eyebrow">WELCOME</span><h1>找到真正适合你的<br>下一份工作。</h1><p>上传简历建立 Career Profile，再告诉我们想找的机会。职跃 AI 会搜索真实公开岗位、帮助你理解匹配与差距；是否申请始终由你决定。</p></div>', unsafe_allow_html=True)
    if st.button("上传简历 PDF / DOCX", type="primary", width="stretch"):
        go_to("我的档案")
    if st.button("先不上传，手动建立档案", width="stretch"):
        go_to("我的档案")
    st.caption("简历仅用于建立职业档案与岗位匹配。AI 提取的信息需由你确认；我们不会保存上传文件。")
    st.markdown("### 接下来会发生什么")
    cards = [("01", "建立 Career Profile", "确认简历提取信息，补充你的真实经历与求职信息。"), ("02", "描述 Search Intent", "用自然语言说出今天想找什么机会。"), ("03", "发现并理解岗位", "真实岗位、个性化排序、按需 AI 分析与官方申请入口。")]
    for col, (icon, title, desc) in zip(st.columns(3), cards):
        with col:
            st.markdown(f'<div class="feature-card"><div class="step">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
