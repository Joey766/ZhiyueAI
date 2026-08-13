# 职跃 AI · Zhiyue AI

> An AI-powered job discovery, fit analysis and application copilot.

职跃 AI 是一款 AI 求职助手：通过简历理解和求职偏好动态发现相关岗位、分析岗位匹配与能力差距，并通过 Chrome Companion 减少跨招聘网站的重复申请信息填写。

## Problem

求职者通常需要在多个招聘网站间重复筛选岗位、理解岗位要求并手动整理申请信息；固定岗位池和自动提交都无法同时保证相关性、透明度与用户控制。

## Solution

职跃 AI 将用户主动维护的职业档案和求职偏好转换为一次独立的动态搜索意图，在公开招聘来源中筛选、去重并排序岗位。用户可对选中的岗位运行本地 AI 匹配分析，并在 Chrome Companion 中获得可复制的字段建议。

## Core Features

- 动态岗位搜索：以当前 Profile 与 Preferences 构建 Primary、Close、Adjacent 查询。
- 真实公开岗位：支持公开 ATS 与国内官方招聘来源；美团使用 server-side keyword search，其他公开来源按本次意图本地过滤。
- 岗位匹配分析：使用本机 Ollama + `qwen3:1.7b` 输出结构化匹配度、优势、差距与简历优化建议。
- 简历解析：本地读取 PDF / DOCX，再由本地模型提取已有信息；不美化、不编造。
- Chrome Companion：识别当前申请表字段并提供读取、匹配、建议、复制；不会自动填写、点击 Next 或 Submit。

## Product Flow

`简历 / 我的档案` → `求职偏好` → `动态岗位搜索` → `岗位匹配与 Gap Analysis` → `用户自主申请` → `Chrome Companion 辅助填写`

## Product Decisions

- Fixed Job Pool → Dynamic Job Search
- AI Resume Rewrite → Skill Gap Analysis
- Automatic Application → Field Mapping + User Control

这些选择保证系统以真实岗位、用户可控和可解释的辅助为中心。

## Architecture

```text
Streamlit UI
  ├─ Profile / Preferences / Search Session
  ├─ Provider Registry → Normalize → Deduplicate → Rank
  ├─ Local Ollama (qwen3:1.7b) → structured analysis
  └─ Optional local Chrome Companion API (127.0.0.1 only)
```

## Screenshots / Demo

产品官网展示当前流程和产品决策。稳定的交互式 Streamlit Demo 暂不公开托管：其 AI 后端依赖本机 Ollama，因此不会在官网使用失效的临时 Tunnel 链接。

如需补充 README 截图，建议后续提供四张真实截图：Homepage、Dynamic Job Search、AI Job Analysis、Chrome Companion。

## Chrome Companion

Chrome Extension currently available as local Load Unpacked demo.

1. 打开 Chrome → Extensions。
2. 启用 Developer Mode。
3. 选择 Load unpacked。
4. 选择仓库中的 `browser_extension/` 目录。

默认不会启动本机 Companion。只有显式设置 `ZHIYUE_LOCAL_COMPANION=1` 时才启用 loopback API；它的资料与 token 仅保存在当前 Windows 用户的 Local App Data 中。

## Privacy & User Control

- 用户资料仅保存在当前 Streamlit Session；不会写入仓库。
- 简历上传在内存中处理，不作为项目文件保存。
- 本地 AI 使用 Ollama，不调用付费云端 AI API。
- Chrome Companion 仅在用户点击后读取当前页面公开表单字段；不自动填写或提交申请。
- Token、Profile、`.env`、secrets、上传文件和虚拟环境均被 `.gitignore` 排除。

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

需要本机已运行 Ollama，并已安装 `qwen3:1.7b`。

## Tech Stack

- Python, Streamlit, Requests
- Ollama, qwen3:1.7b
- pypdf, python-docx
- Public ATS / official careers providers
- Chrome Extension Manifest V3
- GitHub Actions + GitHub Pages（静态产品官网）

## Future Work

- 更多稳定的公开官方招聘 Provider
- 更多真实产品截图与演示材料
- 可选的、明确授权的远程交互式 Demo 架构

不会新增自动投递、自动填写、自动提交或付费 AI API。
