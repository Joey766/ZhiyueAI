import os
import streamlit as st

from ai.resume_parser import parse_resume
from utils.session import new_record
from application_fields.field_taxonomy import application_profile, completeness
from application_fields.local_api import save_application_profile

SKILLS = ["Python", "SQL", "R", "Excel", "Tableau", "Power BI", "Figma", "数据分析", "产品设计", "机器学习", "大语言模型", "RAG", "提示词工程"]
EMPTY_PDF_MESSAGE = "没有读取到足够文字，这份简历可能是扫描件或图片型 PDF。当前版本暂不支持 OCR，请上传可复制文字的 PDF 或 DOCX。"
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024


def ensure_widget(key, value=""):
    if key not in st.session_state:
        st.session_state[key] = value


def profile_to_widgets(profile):
    basic = profile["basic"]
    for field in ["name", "english_name", "first_name", "last_name", "preferred_name", "email", "phone", "location", "linkedin", "github", "portfolio"]:
        st.session_state[f"basic_{field}"] = basic.get(field, "")
    for record in profile["education"]:
        rid = record["id"]
        mapping = {"school": "学校", "major": "专业", "degree": "学位", "start": "开始时间", "grad": "预计毕业时间", "gpa": "GPA"}
        for widget, source in mapping.items(): st.session_state[f"edu_{rid}_{widget}"] = record.get(source, "")
    for record in profile["experience"]:
        rid = record["id"]
        mapping = {"company": "公司名称", "role": "职位", "start": "开始时间", "end": "结束时间", "content": "工作内容"}
        for widget, source in mapping.items(): st.session_state[f"exp_{rid}_{widget}"] = record.get(source, "")
    for record in profile["projects"]:
        rid = record["id"]
        mapping = {"name": "项目名称", "role": "项目角色", "time": "项目时间", "desc": "项目描述", "skills": "使用技能"}
        for widget, source in mapping.items(): st.session_state[f"proj_{rid}_{widget}"] = record.get(source, "")
    st.session_state["profile_skills"] = profile.get("skills", [])
    for field in ["work_authorization", "visa_support", "relocation", "start_date"]:
        st.session_state[f"app_{field}"] = profile["application"].get(field, "")


def sync():
    profile = st.session_state.profile
    profile["basic"] = {key: st.session_state.get(f"basic_{key}", "") for key in ["name", "english_name", "first_name", "last_name", "preferred_name", "email", "phone", "location", "linkedin", "github", "portfolio"]}
    profile["education"] = [{"id": item["id"], "学校": st.session_state.get(f"edu_{item['id']}_school", ""), "专业": st.session_state.get(f"edu_{item['id']}_major", ""), "学位": st.session_state.get(f"edu_{item['id']}_degree", ""), "开始时间": st.session_state.get(f"edu_{item['id']}_start", ""), "预计毕业时间": st.session_state.get(f"edu_{item['id']}_grad", ""), "GPA": st.session_state.get(f"edu_{item['id']}_gpa", "")} for item in profile["education"]]
    profile["experience"] = [{"id": item["id"], "公司名称": st.session_state.get(f"exp_{item['id']}_company", ""), "职位": st.session_state.get(f"exp_{item['id']}_role", ""), "开始时间": st.session_state.get(f"exp_{item['id']}_start", ""), "结束时间": st.session_state.get(f"exp_{item['id']}_end", ""), "工作内容": st.session_state.get(f"exp_{item['id']}_content", "")} for item in profile["experience"]]
    profile["projects"] = [{"id": item["id"], "项目名称": st.session_state.get(f"proj_{item['id']}_name", ""), "项目角色": st.session_state.get(f"proj_{item['id']}_role", ""), "项目时间": st.session_state.get(f"proj_{item['id']}_time", ""), "项目描述": st.session_state.get(f"proj_{item['id']}_desc", ""), "使用技能": st.session_state.get(f"proj_{item['id']}_skills", "")} for item in profile["projects"]]
    profile["skills"] = st.session_state.get("profile_skills", [])
    profile["application"] = {key: st.session_state.get(f"app_{key}", "") for key in ["work_authorization", "visa_support", "relocation", "start_date"]}


def change(section, record_id=None):
    sync()
    if record_id:
        st.session_state.profile[section] = [item for item in st.session_state.profile[section] if item["id"] != record_id]
    else:
        st.session_state.profile[section].append(new_record())
    st.rerun()


def _empty(value):
    return not str(value or "").strip()


def _merge_record(existing, incoming, overwrite):
    output = dict(existing)
    for key, value in incoming.items():
        if overwrite or _empty(output.get(key)):
            output[key] = value
    return output


def _merge_list(existing, incoming, mapper, overwrite):
    if overwrite:
        return [{"id": new_record()["id"], **mapper(item)} for item in incoming] or [new_record()]
    result = list(existing)
    for index, item in enumerate(incoming):
        mapped = mapper(item)
        if index < len(result): result[index] = _merge_record(result[index], mapped, False)
        else: result.append({"id": new_record()["id"], **mapped})
    return result or [new_record()]


def import_resume_result(parsed, overwrite):
    sync()
    profile = st.session_state.profile
    profile["basic"] = _merge_record(profile["basic"], parsed["basic"], overwrite)
    profile["education"] = _merge_list(profile["education"], parsed["education"], lambda item: {"学校": item["school"], "专业": item["major"], "学位": item["degree"], "开始时间": item["start_date"], "预计毕业时间": item["graduation_date"], "GPA": item["gpa"]}, overwrite)
    profile["experience"] = _merge_list(profile["experience"], parsed["experience"], lambda item: {"公司名称": item["company"], "职位": item["role"], "开始时间": item["start_date"], "结束时间": item["end_date"], "工作内容": item["content"]}, overwrite)
    profile["projects"] = _merge_list(profile["projects"], parsed["projects"], lambda item: {"项目名称": item["name"], "项目角色": item["role"], "项目时间": item["time"], "项目描述": item["description"], "使用技能": item["skills"]}, overwrite)
    profile["skills"] = parsed["skills"] if overwrite else list(dict.fromkeys(profile.get("skills", []) + parsed["skills"]))
    for key in list(st.session_state.keys()):
        if key.startswith(("basic_", "edu_", "exp_", "proj_", "app_")) or key == "profile_skills": del st.session_state[key]
    profile_to_widgets(profile)
    st.session_state.profile_saved = True
    st.session_state.resume_parse_result = None
    st.rerun()


def resume_preview():
    data = st.session_state.resume_parse_result
    if not data: return
    parsed = data["result"]
    st.divider(); st.subheader("简历解析结果")
    st.caption("以下是从简历中提取的原有信息。导入前可先核对；不会自动覆盖你的档案。")
    with st.expander("基本信息", expanded=True):
        visible = [(label, parsed["basic"].get(key, "")) for key, label in [("name", "姓名"), ("english_name", "英文姓名"), ("email", "Email"), ("phone", "电话"), ("location", "所在地"), ("linkedin", "LinkedIn"), ("portfolio", "GitHub / Portfolio")]]
        st.write("　·　".join(f"{label}：{value or '未提取'}" for label, value in visible))
    for title, records, fields in [("教育经历", parsed["education"], ["school", "major", "degree", "start_date", "graduation_date", "gpa"]), ("工作 / 实习经历", parsed["experience"], ["company", "role", "start_date", "end_date", "content"]), ("项目经历", parsed["projects"], ["name", "role", "time", "description", "skills"])]:
        with st.expander(title, expanded=bool(records)):
            if not records: st.caption("未提取到明确记录")
            for record in records: st.write("　·　".join(record.get(field, "") for field in fields if record.get(field)))
    with st.expander("技能", expanded=True): st.write("、".join(parsed["skills"]) or "未提取到明确技能")
    mode = st.radio("导入方式", ["只填补当前为空的信息", "使用简历解析结果覆盖当前档案"], horizontal=True, key="resume_import_mode")
    if st.button("导入到我的档案", type="primary"):
        import_resume_result(parsed, mode == "使用简历解析结果覆盖当前档案")


def resume_upload_area():
    st.subheader("上传现有简历")
    upload_key = f"resume_upload_{st.session_state.resume_upload_nonce}"
    file = st.file_uploader("选择简历文件", type=["pdf", "docx"], key=upload_key, label_visibility="collapsed")
    st.caption("仅支持 PDF、DOCX，文件不超过 10 MB。上传后请手动点击解析，不会自动调用 AI。")
    if file:
        suffix = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
        if suffix not in {"pdf", "docx"}:
            st.warning("仅支持 PDF 或 DOCX 格式的简历文件。")
            return
        if file.size > MAX_RESUME_SIZE_BYTES:
            st.warning("简历文件超过 10 MB，请压缩后重新上传。")
            return
        st.session_state.uploaded_resume_name = file.name
        st.success(f"已选择简历：{file.name}")
        if st.button("✨ 解析我的简历", type="primary"):
            with st.spinner("正在读取并分析你的简历……"):
                result = parse_resume(file.getvalue(), file.name)
            if result["ok"]:
                st.session_state.resume_parse_result = {"filename": file.name, "result": result["result"], "text_length": result["text_length"]}
                st.rerun()
            elif result["error"] == "insufficient_text":
                st.warning(EMPTY_PDF_MESSAGE if file.name.lower().endswith(".pdf") else "没有读取到足够文字，请上传包含可复制文字的 PDF 或 DOCX。")
            elif result["error"] == "service_offline": st.warning("⚠️ 本地 AI 服务未启动，请先启动 Ollama 后重新尝试。")
            elif result["error"] == "model_missing": st.warning("⚠️ 尚未安装 qwen3:1.7b，请先运行 ollama pull qwen3:1.7b。")
            elif result["error"] == "busy": st.warning("AI 当前正在处理其他请求，请稍后再试。")
            elif result["error"] == "timeout": st.warning("简历分析时间较长或服务未响应，请稍后重新尝试。")
            elif result["error"] == "invalid_json": st.warning("本次简历解析结果格式异常，请重新解析。")
            else: st.warning("简历读取或解析失败，请确认文件格式后重新尝试。")
    if st.session_state.resume_parse_result and st.button("重新解析"):
        st.session_state.resume_parse_result = None; st.rerun()
    if (file or st.session_state.resume_parse_result) and st.button("清除当前简历"):
        st.session_state.resume_parse_result = None; st.session_state.uploaded_resume_name = None; st.session_state.resume_upload_nonce += 1; st.rerun()
    resume_preview()


def render():
    profile = st.session_state.profile
    st.title("我的档案"); st.caption("完善你的职业信息。系统将基于这些真实信息进行岗位搜索、匹配分析与申请辅助。")
    saved_application = application_profile(profile)
    with st.expander("申请资料完整度", expanded=True):
        st.caption("这些信息可由浏览器 Companion 识别后逐项复制到官方申请表；空白项不会被猜测。")
        for label, ready in completeness(saved_application):
            st.write(f"{'✅' if ready else '⚠️'} {label}{'' if ready else '：未填写'}")
    with st.container(border=True): resume_upload_area()
    st.subheader("基本信息"); basic = profile["basic"]; left, right = st.columns(2)
    for column, label, key, placeholder in [(left, "姓名", "name", "请输入姓名"), (right, "英文姓名", "english_name", "例如：Zhang San"), (left, "电子邮箱", "email", "name@example.com"), (right, "手机号码", "phone", "请输入手机号码"), (left, "当前所在地", "location", "例如：上海"), (right, "LinkedIn", "linkedin", "个人主页链接（可选）")]:
        with column: ensure_widget("basic_" + key, basic.get(key, "")); st.text_input(label, key="basic_" + key, placeholder=placeholder)
    a, b, c = st.columns(3)
    for column, label, key in [(a, "First Name（可选）", "first_name"), (b, "Last Name（可选）", "last_name"), (c, "Preferred Name（可选）", "preferred_name")]:
        with column: ensure_widget("basic_" + key, basic.get(key, "")); st.text_input(label, key="basic_" + key)
    a, b = st.columns(2)
    with a: ensure_widget("basic_github", basic.get("github", "")); st.text_input("GitHub（可选）", key="basic_github", placeholder="链接")
    with b: ensure_widget("basic_portfolio", basic.get("portfolio", "")); st.text_input("Portfolio / 个人网站（可选）", key="basic_portfolio", placeholder="链接")
    st.divider(); st.subheader("教育经历")
    for index, record in enumerate(profile["education"], 1):
        rid = record["id"]
        with st.container(border=True):
            a,b=st.columns([5,1]); a.markdown(f"**教育经历 {index}**")
            if b.button("删除", key="de"+rid) and len(profile["education"]) > 1: change("education", rid)
            a,b,c=st.columns(3)
            for col,label,key in [(a,"学校","school"),(b,"专业","major")]:
                with col: ensure_widget(f"edu_{rid}_{key}",record.get({"school":"学校","major":"专业"}[key],"")); st.text_input(label,key=f"edu_{rid}_{key}")
            ensure_widget(f"edu_{rid}_degree",record.get("学位","本科")); c.selectbox("学位",["本科","硕士","博士","其他"],key=f"edu_{rid}_degree")
            a,b,c=st.columns(3)
            for col,label,key in [(a,"开始时间","start"),(b,"预计毕业时间","grad"),(c,"GPA（可选）","gpa")]:
                with col: ensure_widget(f"edu_{rid}_{key}",record.get({"start":"开始时间","grad":"预计毕业时间","gpa":"GPA"}[key],"")); st.text_input(label,key=f"edu_{rid}_{key}")
    if st.button("+ 添加教育经历"): change("education")
    st.divider(); st.subheader("工作 / 实习经历")
    for index, record in enumerate(profile["experience"], 1):
        rid=record["id"]
        with st.container(border=True):
            a,b=st.columns([5,1]); a.markdown(f"**工作 / 实习经历 {index}**")
            if b.button("删除",key="dx"+rid) and len(profile["experience"]) > 1: change("experience",rid)
            a,b=st.columns(2)
            for col,label,key in [(a,"公司名称","company"),(b,"职位","role"),(a,"开始时间","start"),(b,"结束时间","end")]:
                with col: ensure_widget(f"exp_{rid}_{key}",record.get({"company":"公司名称","role":"职位","start":"开始时间","end":"结束时间"}[key],"")); st.text_input(label,key=f"exp_{rid}_{key}")
            ensure_widget(f"exp_{rid}_content",record.get("工作内容","")); st.text_area("工作内容",key=f"exp_{rid}_content",height=110,placeholder="描述你的职责、成果和影响…")
    if st.button("+ 添加工作 / 实习经历"): change("experience")
    st.divider(); st.subheader("项目经历")
    for index, record in enumerate(profile["projects"],1):
        rid=record["id"]
        with st.container(border=True):
            a,b=st.columns([5,1]); a.markdown(f"**项目经历 {index}**")
            if b.button("删除",key="dp"+rid) and len(profile["projects"]) > 1: change("projects",rid)
            a,b,c=st.columns(3)
            for col,label,key in [(a,"项目名称","name"),(b,"项目角色","role"),(c,"项目时间","time")]:
                with col: ensure_widget(f"proj_{rid}_{key}",record.get({"name":"项目名称","role":"项目角色","time":"项目时间"}[key],"")); st.text_input(label,key=f"proj_{rid}_{key}")
            ensure_widget(f"proj_{rid}_desc",record.get("项目描述","")); st.text_area("项目描述",key=f"proj_{rid}_desc",height=100,placeholder="说明项目目标、你的贡献与结果…")
            ensure_widget(f"proj_{rid}_skills",record.get("使用技能","")); st.text_input("使用技能",key=f"proj_{rid}_skills",placeholder="例如：Python、SQL、Figma")
    if st.button("+ 添加项目经历"): change("projects")
    st.divider(); st.subheader("技能"); ensure_widget("profile_skills",profile.get("skills",[])); st.multiselect("选择已掌握的技能",SKILLS,key="profile_skills",placeholder="选择或搜索技能")
    st.divider(); st.subheader("常用申请信息"); app=profile["application"]; a,b=st.columns(2)
    for column,label,key,options in [(a,"当前是否拥有合法工作资格？","work_authorization",["未填写","是","否","视国家 / 地区而定"]),(b,"未来是否需要公司提供工作签证支持？","visa_support",["未填写","是","否","不确定"]),(a,"是否愿意搬迁？","relocation",["未填写","是","否","视岗位而定"])]:
        with column: ensure_widget("app_"+key,app.get(key) or options[0]); st.radio(label,options,key="app_"+key,horizontal=True)
    ensure_widget("app_start_date",app.get("start_date","")); b.text_input("最早可入职时间",key="app_start_date",placeholder="例如：2026-06")
    if st.button("保存我的档案",type="primary",width="stretch"):
        sync(); st.session_state.profile_saved=True
        st.success("个人档案已保存")
    if os.getenv("ZHIYUE_LOCAL_COMPANION") == "1":
        st.divider()
        if st.button("同步到本机 Chrome Companion", width="stretch"):
            sync()
            token = save_application_profile(application_profile(st.session_state.profile))
            st.success("已同步到本机 Chrome Companion。")
            with st.expander("本机 Chrome Companion 连接信息", expanded=True):
                st.caption("仅供本机浏览器扩展使用。请勿通过公网 Demo 共享此访问密钥。")
                st.code(token, language=None)
