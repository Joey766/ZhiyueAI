import os
import streamlit as st
from utils.session import init_state
from application_fields.local_api import ensure_local_api
from ui_pages import home, profile, preferences, jobs, assistant

st.set_page_config(page_title="职跃 AI", page_icon="职", layout="wide", initial_sidebar_state="collapsed")
init_state()
if os.getenv("ZHIYUE_LOCAL_COMPANION") == "1":
    ensure_local_api()
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;} header[data-testid="stHeader"]{display:none}.stApp{background:#f7f8fc;color:#172033}.block-container{padding:2.4rem 3.2rem;max-width:1180px}.hero{padding:2rem 0 3rem;max-width:760px}.hero h1{font-size:3rem;line-height:1.25;margin:.5rem 0 1rem}.hero p,.feature-card p{color:#667085;line-height:1.8}.eyebrow{color:#4756d8;font-weight:700;font-size:.9rem}.feature-card,.stat-card{background:#fff;border:1px solid #e8eaf1;border-radius:16px;padding:1.45rem;min-height:170px;box-shadow:0 4px 14px rgba(16,24,40,.03)}.feature-card h3{margin:.55rem 0}.stat-card{min-height:115px;display:flex;flex-direction:column;gap:.3rem}.stat-card span,.stat-card small{color:#667085}.stat-card strong{font-size:1.65rem}.match{font-weight:700;font-size:1.65rem;line-height:1.2;text-align:right;color:#4756d8;white-space:nowrap}.match small{display:block;font-weight:400;font-size:.75rem;color:#667085}.step{font-size:.82rem;color:#667085}.stButton>button{border-radius:10px;font-weight:600}.stForm{background:#fff;border:1px solid #e8eaf1;border-radius:16px;padding:1.5rem}
</style>''',unsafe_allow_html=True)
if st.session_state.page != "欢迎":
    with st.sidebar:
        st.markdown("## 职跃 AI")
        st.caption("发现、理解、决定，再申请")
        st.divider()
        nav={"Discover · Find Jobs":"岗位推荐","Career · My Profile":"我的档案","Career · Preferences":"求职偏好","Applications · Saved Jobs":"已保存岗位","Tools · Chrome Companion":"Chrome Companion"}
        for label,page in nav.items():
            if st.button(label,key=page,width="stretch",type="primary" if st.session_state.page==page else "secondary"):
                st.session_state.page=page; st.rerun()
        st.divider(); st.caption("AI 只基于你的档案与岗位 JD 分析。")

pages={"欢迎":home,"首页":home,"我的档案":profile,"求职偏好":preferences,"岗位推荐":jobs,"岗位分析":assistant,"已保存岗位":jobs,"Chrome Companion":profile}
try:
    pages[st.session_state.page].render()
except Exception:
    # 公网 Demo 不向访问者展示 Windows 路径或 Python traceback。
    st.error("页面暂时无法加载，请刷新页面后重试。")
