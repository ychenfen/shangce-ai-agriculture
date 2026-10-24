@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo 首次启动：创建本地 Python 环境并安装依赖……
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
start "" http://127.0.0.1:8765
.venv\Scripts\python app\server.py --port 8765
