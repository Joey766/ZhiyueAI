# 一键启动本项目 Streamlit，并在端口就绪后启动 Cloudflare Quick Tunnel。
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "未找到项目虚拟环境：$python" -ForegroundColor Yellow
    exit 1
}
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 cloudflared。请先安装 Cloudflare Tunnel 客户端，然后重新运行本脚本。" -ForegroundColor Yellow
    Write-Host "安装说明：https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
}

if (-not (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $python -ArgumentList "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true" -WorkingDirectory $projectRoot -WindowStyle Hidden
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) { $ready = $true; break }
    }
    if (-not $ready) {
        Write-Host "Streamlit 未能在 30 秒内启动，请检查 app.py 后重试。" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Streamlit 已就绪，正在启动 Cloudflare Quick Tunnel..." -ForegroundColor Green
cloudflared tunnel --url http://localhost:8501

