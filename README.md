# Zhiyue AI

> AI-powered job discovery, fit analysis and application copilot.

### Live Product

[Landing Website](https://joey766.github.io/ZhiyueAI/) · [GitHub](https://github.com/Joey766/ZhiyueAI)

### Interactive Demo

Deploy the Streamlit app separately, then set `PUBLIC_APP_URL` in `website/site.js` to its real HTTPS URL before publishing. No placeholder URL is committed.

## Problem

求职者通常需要在多个招聘网站间重复筛选岗位、理解岗位要求并手动整理申请信息；固定岗位池和自动提交都无法同时保证相关性、透明度与用户控制。

## Solution

职跃 AI 将用户确认过的 Career Profile、Preferences 和自然语言 Search Intent 转换为一次动态搜索，在公开招聘来源中筛选、标准化、去重并排序。用户可按需运行 AI Job Fit / Gap Analysis，并在官方招聘页面自行申请。

## Core Features

- 简历 onboarding：PDF / DOCX 在内存中读取，AI 提取后须由用户确认；扫描 PDF 会得到 OCR 不可用提示。
- 动态岗位搜索：以 Career Profile、Preferences 和 Search Intent 构建 Primary、Close、Adjacent 查询。
- 真实公开岗位：支持公开 ATS 与国内官方招聘来源；美团使用 server-side keyword search，其他公开来源按本次意图本地过滤。
- Recommendation Score / Fit Estimate：仅用于可解释的本地排序，不代表录取概率。
- 按需岗位分析：用户主动打开后才调用 AI，展示优势、缺口、Must-have / Nice-to-have、JD Keywords、Resume Evidence 与申请前建议。
- AI Provider：默认本机 Ollama + `qwen3:1.7b`；可通过环境变量或 Streamlit secrets 配置 OpenAI-compatible hosted provider。
- Saved Jobs：仅保存当前 session，可返回分析或前往官方申请链接。
- Chrome Companion：识别当前申请表字段并提供读取、匹配、建议、复制；不会自动填写、点击 Next 或 Submit。

## Product Flow

`Resume` → `Career Profile` → `Search Intent` → `Real Jobs` → `Job Fit` → `Gap Analysis` → `User-controlled Apply`

## Product Decisions

- Fixed Job Pool → Dynamic Job Search
- AI Resume Rewrite → Skill Gap Analysis
- Automatic Application → Field Mapping + User Control

这些选择保证系统以真实岗位、用户可控和可解释的辅助为中心。

## Architecture

```text
Streamlit UI
  ├─ Onboarding / Career Profile / Preferences / Search Session
  ├─ Provider Registry → Normalize → Deduplicate → Rank
  ├─ Local Ollama (qwen3:1.7b) → structured analysis
  └─ Optional local Chrome Companion API (127.0.0.1 only)
```

## Deployment

GitHub Pages serves only `website/`. Deploy the Streamlit app to a Python-compatible host as a separate service, configure secrets there, and set the resulting HTTPS app URL in `website/site.js`. For hosted AI, set `ZHIYUE_AI_PROVIDER=remote`, `ZHIYUE_REMOTE_AI_URL`, `ZHIYUE_REMOTE_AI_MODEL`, and `ZHIYUE_REMOTE_AI_API_KEY` in the host's secret manager. Without hosted AI, the public app still searches and ranks real jobs; detailed AI analysis fails gracefully.

## Chrome Companion

Chrome Extension currently available as local Load Unpacked demo.

1. 打开 Chrome → Extensions。
2. 启用 Developer Mode。
3. 选择 Load unpacked。
4. 选择仓库中的 `browser_extension/` 目录。

默认不会启动本机 Companion。只有显式设置 `ZHIYUE_LOCAL_COMPANION=1` 时才启用 loopback API；它的资料与 token 仅保存在当前 Windows 用户的 Local App Data 中。

## Privacy & User Control

- 用户资料、Saved Jobs 仅保存在当前 Streamlit Session；不会写入仓库。
- 简历上传在内存中处理，不作为项目文件保存。
- AI 只基于用户提供的信息和岗位 JD 分析，不会补充不存在的经历。
- Chrome Companion 仅在用户点击后读取当前页面公开表单字段；不自动填写或提交申请。
- Token、Profile、`.env`、secrets、上传文件和虚拟环境均被 `.gitignore` 排除。

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

需要本机已运行 Ollama，并已安装 `qwen3:1.7b`。如改用 hosted provider，请复制 `.env.example` 的变量名到部署平台的 secret manager，绝不要提交 `.env`。

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
- 账号与跨设备 Saved Jobs（需明确的隐私与数据保留设计）

不会新增自动投递、自动点击 Next 或自动提交。
