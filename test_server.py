#!/usr/bin/env python3
"""trending-now MCP Server 测试"""
import json
import sys
import subprocess
import time

def test_server():
    """通过stdio测试MCP服务器"""
    proc = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/tmp/trending-now"
    )
    
    def send(msg):
        proc.stdin.write(json.dumps(msg) + '\n')
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line) if line else None
    
    # 1. Initialize
    print("测试1: Initialize...")
    resp = send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert resp["result"]["serverInfo"]["name"] == "trending-now"
    print(f"  ✅ 服务器: {resp['result']['serverInfo']['name']} v{resp['result']['serverInfo']['version']}")
    
    # 2. Tools list
    print("测试2: Tools list...")
    resp = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = resp["result"]["tools"]
    print(f"  ✅ 工具数: {len(tools)}")
    for t in tools:
        print(f"     - {t['name']}: {t['description'][:40]}...")
    
    # 3. Get trending (B站 only - fastest)
    print("测试3: get_trending (bilibili)...")
    resp = send({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "get_trending", "arguments": {"source": "bilibili", "limit": 5}}
    })
    text = resp["result"]["content"][0]["text"]
    print(f"  ✅ 结果预览:\n{text[:300]}")
    
    # 4. Hot score
    print("测试4: get_hot_score...")
    resp = send({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "get_hot_score", "arguments": {"keyword": "AI"}}
    })
    text = resp["result"]["content"][0]["text"]
    print(f"  ✅ 结果:\n{text[:200]}")
    
    proc.terminate()
    print("\n🎉 所有测试通过！")

if __name__ == "__main__":
    test_server()
