#!/bin/bash

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

echo "=============================="
echo "  家計簿アプリ 起動中..."
echo "=============================="

# 既存プロセスを停止
pkill -f "uvicorn api:app" 2>/dev/null
pkill -f "streamlit run app.py" 2>/dev/null
sleep 1

# FastAPI サーバー起動（バックグラウンド）
echo "📡 APIサーバー起動中 (port 8000)..."
uvicorn api:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &

# Streamlit 起動
echo "📊 Streamlit起動中 (port 8501)..."
echo ""
echo "ブラウザが自動で開きます。"
echo "スマホからは http://$(ipconfig getifaddr en0):8000 にアクセスしてください。"
echo ""
echo "終了するにはこのウィンドウを閉じてください。"
echo "=============================="

# Streamlit をバックグラウンドで起動
streamlit run app.py --server.headless true &

# 起動を待ってからブラウザを開く
sleep 3
open http://localhost:8501

# プロセスを維持
wait
