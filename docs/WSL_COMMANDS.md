# WSL 启动与演示命令速查

> 用途：演示当天从零启动全部服务的命令流 + 现场可用命令演示。在 **Windows PowerShell** 输入 `wsl -d Ubuntu` 进入后逐条执行。

## 一、冷启动全流程（电脑重启后，约 1 分钟）

```bash
# ===== 1. 启动数据库（Docker 容器） =====
docker start ecommerce-mysql

# 确认（应显示 ecommerce-mysql ... Up）
docker ps

# ===== 2. 启动后端与前端（systemd 常驻服务） =====
# 需要 root 权限，直接以 root 进入也行：wsl -d Ubuntu -u root
sudo systemctl start ecommerce-backend ecommerce-frontend

# 确认两个都是 active
systemctl is-active ecommerce-backend ecommerce-frontend

# ===== 3. 一键体检（全部应绿） =====
bash /home/li177/ecommerce_project/scripts/check_status.sh
# 预期输出：
#   ecommerce-mysql Up ...
#   后端服务: active
#   前端服务: active
#   后端 8000: HTTP 200
#   前端 5173: HTTP 200
```

完成后浏览器打开 **http://localhost:5173**。

> 如果刚开机第一次进 WSL 时 systemctl 报 "System has not been booted"，是 systemd 未就绪，等 10 秒重试。

## 二、日常管理命令

```bash
# 查看服务状态（三条一起看）
systemctl status ecommerce-backend --no-pager
systemctl status ecommerce-frontend --no-pager

# 重启（改了代码 / 服务异常时）
sudo systemctl restart ecommerce-backend
sudo systemctl restart ecommerce-frontend

# 看实时日志（排查问题的第一现场）
journalctl -u ecommerce-backend -f        # Ctrl+C 退出
journalctl -u ecommerce-frontend -f

# 看最近 20 行日志（不进实时模式）
journalctl -u ecommerce-backend -n 20 --no-pager
```

## 三、现场命令演示素材（可选加分项）

### 1. API 直查（展示后端与数据规模）

```bash
# 数据总览：600 万级真实数字
curl -s http://127.0.0.1:8000/api/dashboard/overview | python3 -m json.tool

# 演示用户购买行为（265 条购买）
curl -s "http://127.0.0.1:8000/api/users/564068124/events?event_type=purchase&page_size=3" | python3 -m json.tool

# 转化漏斗（Session 口径）
curl -s http://127.0.0.1:8000/api/analytics/conversion | python3 -m json.tool

# 前端代理链路（证明 5173 → 8000 → MySQL 全通）
curl -s http://127.0.0.1:5173/api/dashboard/overview
```

### 2. 数据库直查（展示 600 万数据真实在库）

```bash
# 连库看数据规模（表名+行数一次看全）
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT table_name, table_rows
FROM information_schema.tables
WHERE table_schema='ecommerce' AND table_rows > 0
ORDER BY table_rows DESC;"

# 演示用户的购买统计（SQL 层聚合）
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT event_type, COUNT(*) AS cnt, ROUND(SUM(price),2) AS amount
FROM behavior_events WHERE user_id=564068124
GROUP BY event_type;"

# 索引效果对比（性能故事：37 秒 → 3.6 秒的原因）
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
EXPLAIN SELECT session_id, MAX(event_type='purchase') FROM behavior_events
WHERE session_id IS NOT NULL GROUP BY session_id\G" | grep -E "key|rows|Extra"
```

### 3. 测试与质量门

```bash
# 后端 37 个测试（约 3 分钟，演示时间紧可跳过）
cd /home/li177/ecommerce_project && python -m pytest -q

# 前端一键检查（类型/lint/格式/单元测试，约 30 秒）
bash scripts/frontend_check.sh
```

### 4. ETL 痕迹（幂等与断点恢复的实物证据）

```bash
# ETL 控制表：60 个 batch 全 SUCCESS、1 个中断
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT status, COUNT(*) AS batches, SUM(events_loaded) AS loaded
FROM etl_batches GROUP BY status;"

# 幂等证据：600 万事件无一重复（hash 唯一约束）
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT COUNT(*) AS total, COUNT(DISTINCT source_event_hash) AS unique_hash
FROM behavior_events;"
```

## 四、应急命令（演示现场翻车时）

```bash
# 前端页面打不开
sudo systemctl restart ecommerce-frontend

# 接口 500 / 后端挂
sudo systemctl restart ecommerce-backend

# MySQL 容器没起来
docker start ecommerce-mysql && sleep 3 && docker ps

# 全部重来一遍（1 分钟）
docker start ecommerce-mysql
sudo systemctl restart ecommerce-backend ecommerce-frontend
bash /home/li177/ecommerce_project/scripts/check_status.sh

# 看后端报什么错
journalctl -u ecommerce-backend -n 30 --no-pager
```

## 五、关机前（可选）

服务是 systemd 常驻的，重启电脑会自动跟随 WSL 启动；想手动停：

```bash
sudo systemctl stop ecommerce-backend ecommerce-frontend
docker stop ecommerce-mysql
```
