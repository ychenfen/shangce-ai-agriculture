#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo '首次启动：创建本地Python环境并安装依赖。'
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
if .venv/bin/python -c 'import urllib.request,json; d=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/summary",timeout=1)); assert d["title"]=="墒策：可信需水预测与灌溉决策"' >/dev/null 2>&1; then
  open http://127.0.0.1:8765
  exit 0
fi
(sleep 2; open http://127.0.0.1:8765) &
exec .venv/bin/python app/server.py --port 8765
