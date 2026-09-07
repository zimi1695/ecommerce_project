#!/bin/bash
set -e
# 后端
source ~/miniconda3/etc/profile.d/conda.sh
conda activate bigdata
cd ~/ecommerce_project
nohup uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &
# 前端
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use v22.23.2 > /dev/null
cd ~/ecommerce_project/frontend
nohup npm run dev:api > /tmp/vite.log 2>&1 &
sleep 10
echo "后端: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8000/)"
echo "前端: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:5173/)"
echo "代理链路: $(curl -s --max-time 15 http://127.0.0.1:5173/api/dashboard/overview | head -c 80)"
