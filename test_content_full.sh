#!/bin/bash
pkill -9 -f "uvicorn" 2>/dev/null
/usr/local/anaconda3/envs/agent-matrix/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/agent_test.log 2>&1 &
BACKEND_PID=$!
sleep 5

echo "=== 触发Agent执行 ==="
curl -X POST http://localhost:8000/api/agents/test_agent/run

echo ""
echo "等待执行完成（12秒）..."
sleep 12

echo ""
echo "=== 检查最新草稿 ==="
sqlite3 data/database.db "SELECT id, agent_id, length(content) as len FROM drafts ORDER BY created_at DESC LIMIT 1;"

echo ""
echo "=== 完整内容 ==="
sqlite3 data/database.db "SELECT content FROM drafts ORDER BY created_at DESC LIMIT 1;"

echo ""
echo "=== Agent执行日志（最后30行）==="
tail -30 /tmp/agent_test.log | grep -E "(执行|生成|保存|完成|error)"

kill $BACKEND_PID 2>/dev/null
