#!/bin/bash
docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null | grep mysql || echo 'MySQL: 未运行'
echo "后端服务: $(systemctl is-active ecommerce-backend 2>/dev/null)"
echo "前端服务: $(systemctl is-active ecommerce-frontend 2>/dev/null)"
curl -s -o /dev/null -w '后端 8000: HTTP %{http_code}\n' --max-time 3 http://127.0.0.1:8000/ 2>/dev/null
curl -s -o /dev/null -w '前端 5173: HTTP %{http_code}\n' --max-time 3 http://127.0.0.1:5173/ 2>/dev/null
