import streamlit as st

ROLES = ["AI产品经理", "产品经理", "产品分析师", "商业分析师", "数据分析师", "数据科学家", "量化分析", "机器学习工程师"]
INDUSTRIES = ["人工智能", "科技互联网", "金融科技", "金融", "咨询", "游戏", "电子商务", "医疗科技", "SaaS"]
COMPANIES = ["大型科技公司", "大型成熟企业", "AI创业公司", "金融科技创业公司", "金融机构", "咨询公司", "中小型科技公司", "没有明显偏好"]
LOCATIONS = ["中国大陆", "香港", "加拿大", "美国", "新加坡", "英国", "远程"]


def _setdefault(key, value):
    st.session_state.setdefault(key, value)


def render():
    current = st.session_state.preferences
    st.title("求职偏好")
    st.caption("这些偏好会先用于本地强筛选，再用于推荐排序；不会在岗位列表阶段调用 AI。")
    _setdefault("pref_roles", current.get("目标岗位", []))
    st.multiselect("目标岗位", ROLES, key="pref_roles")
    _setdefault("pref_industries", current.get("目标行业", []))
    st.multiselect("目标行业", INDUSTRIES, key="pref_industries")
    _setdefault("pref_company_types", current.get("企业类型", []))
    st.multiselect("企业类型", COMPANIES, key="pref_company_types")
    _setdefault("pref_target_companies", current.get("目标公司", ""))
    st.text_input("目标公司（可选）", key="pref_target_companies", placeholder="例如：字节跳动、腾讯、OpenAI")
    left, right = st.columns(2)
    _setdefault("pref_locations", current.get("工作地点", []))
    left.multiselect("工作地点", LOCATIONS, key="pref_locations")
    _setdefault("pref_stage", current.get("求职阶段", current.get("工作类型", "都可以")))
    right.selectbox("当前求职阶段", ["日常实习", "暑期实习", "校招", "全职", "都可以"], key="pref_stage")
    left, right = st.columns(2)
    _setdefault("pref_grad_year", current.get("毕业年份", "其他"))
    left.selectbox("毕业年份", ["2026", "2027", "2028", "2029", "其他"], key="pref_grad_year")
    _setdefault("pref_sponsorship", current.get("签证支持偏好", "没有明显偏好"))
    right.selectbox("Sponsorship 偏好", ["没有明显偏好", "优先考虑提供签证支持", "不需要签证支持"], key="pref_sponsorship")
    _setdefault("pref_startup", current.get("接受Startup", True))
    st.checkbox("接受 Startup / 创业公司", key="pref_startup")
    save, continue_ = st.columns(2)
    if save.button("保存求职偏好", type="secondary", width="stretch"):
        st.session_state.preferences = {
            "目标岗位": st.session_state.pref_roles, "目标行业": st.session_state.pref_industries,
            "企业类型": st.session_state.pref_company_types, "目标公司": st.session_state.pref_target_companies,
            "工作地点": st.session_state.pref_locations, "工作类型": st.session_state.pref_stage,
            "求职阶段": st.session_state.pref_stage, "毕业年份": st.session_state.pref_grad_year,
            "签证支持偏好": st.session_state.pref_sponsorship, "接受Startup": st.session_state.pref_startup,
        }
        st.session_state.preferences_saved = True
        st.success("求职偏好已保存。")
    if continue_.button("前往 AI Search Intent →", type="primary", width="stretch"):
        st.session_state.preferences = {
            "目标岗位": st.session_state.pref_roles, "目标行业": st.session_state.pref_industries,
            "企业类型": st.session_state.pref_company_types, "目标公司": st.session_state.pref_target_companies,
            "工作地点": st.session_state.pref_locations, "工作类型": st.session_state.pref_stage,
            "求职阶段": st.session_state.pref_stage, "毕业年份": st.session_state.pref_grad_year,
            "签证支持偏好": st.session_state.pref_sponsorship, "接受Startup": st.session_state.pref_startup,
        }
        st.session_state.preferences_saved = True
        from utils.session import go_to
        go_to("岗位推荐")
