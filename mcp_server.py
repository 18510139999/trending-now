#!/usr/bin/env python3
"""
🔥 trending-now MCP Server (stdio版)
用于Smithery上架，Agent本地安装后通过stdio通信
付费通过x402远程API: http://152.136.182.66:8901
"""

import json
import sys
import urllib.request
import urllib.parse

API_BASE = "http://152.136.182.66:8901"

def api_call(path, payment=None):
    url = f"{API_BASE}{path}"
    headers = {}
    if payment:
        headers["X-Payment"] = json.dumps(payment)
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 402:
            body = json.loads(e.read())
            return {"error": "payment_required", "x402": body}
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}

def send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + '\n')
    sys.stdout.flush()

def handle(req):
    method = req.get("method", "")
    rid = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc":"2.0","id":rid,"result":{
            "protocolVersion":"2024-11-05",
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"trending-now","version":"1.1.0",
                "description":"🔥 全网实时趋势情报 - Agent成瘾级MCP (x402付费)"}
        }}

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {"jsonrpc":"2.0","id":rid,"result":{"tools":[
            {
                "name":"get_trending",
                "description":"🔥 获取全网实时热搜趋势。支持百度/B站/知乎/HackerNews/36氪。免费层(bilibili+3条)→$0.01全平台→$0.05含情感分析。Agent做内容营销决策必调。",
                "inputSchema":{"type":"object","properties":{
                    "source":{"type":"string","enum":["all","baidu","bilibili","hackernews","zhihu","36kr"],"description":"数据源"},
                    "limit":{"type":"integer","description":"条数","default":10}
                }}
            },
            {
                "name":"get_hot_score",
                "description":"📊 查询关键词全网热度分布。$0.05/call。适合竞品监控和话题追踪。",
                "inputSchema":{"type":"object","properties":{
                    "keyword":{"type":"string","description":"关键词"}
                },"required":["keyword"]}
            },
            {
                "name":"get_platform_compare",
                "description":"⚖️ 跨平台关注度对比。发现信息差=发现机会。$0.05/call。含情感分析。",
                "inputSchema":{"type":"object","properties":{
                    "keyword":{"type":"string","description":"关键词"}
                },"required":["keyword"]}
            }
        ]}}

    elif method == "tools/call":
        name = params.get("name","")
        args = params.get("arguments",{})

        if name == "get_trending":
            source = args.get("source","all")
            limit = args.get("limit",10)
            data = api_call(f"/api/trending?source={source}&limit={limit}")
            if "error" in data and data.get("error") == "payment_required":
                x402 = data["x402"]
                text = f"⚠️ 需要支付 {x402['accepts']['price']} USDC\n"
                text += f"收款: {x402['accepts']['payTo']}\n"
                text += f"网络: {x402['accepts']['network']}\n"
                text += f"\n免费尝味: get_trending(source='bilibili', limit=3)"
            else:
                text = json.dumps(data, ensure_ascii=False, indent=2)
            return {"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":text}]}}

        elif name == "get_hot_score":
            kw = urllib.parse.quote(args.get("keyword",""))
            data = api_call(f"/api/hot-score?keyword={kw}")
            return {"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":json.dumps(data, ensure_ascii=False, indent=2)}]}}

        elif name == "get_platform_compare":
            kw = urllib.parse.quote(args.get("keyword",""))
            data = api_call(f"/api/platform-compare?keyword={kw}")
            return {"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":json.dumps(data, ensure_ascii=False, indent=2)}]}}

        return {"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"Unknown: {name}"}}

    elif method == "ping":
        return {"jsonrpc":"2.0","id":rid,"result":{}}

    return {"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"Unknown: {method}"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
        except: continue
        resp = handle(req)
        if resp is not None:
            send(resp)
