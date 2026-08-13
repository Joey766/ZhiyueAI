# 在已运行的 Streamlit 演示上启动 Cloudflare Quick Tunnel。
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 cloudflared。请先安装 Cloudflare Tunnel 客户端，然后重新运行本脚本。" -ForegroundColor Yellow
    Write-Host "安装说明：https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
}

if (-not (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 localhost:8501 上的 Streamlit。请先在另一 PowerShell 运行：" -ForegroundColor Yellow
    Write-Host "cd $projectRoot"
    Write-Host ".\.venv\Scripts\python.exe -m streamlit run app.py"
    exit 1
}

Write-Host "Streamlit 已在 localhost:8501 运行，正在启动 Cloudflare Quick Tunnel..." -ForegroundColor Green
cloudflared tunnel --url http://localhost:8501

