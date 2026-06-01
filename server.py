#!/usr/bin/env python3
"""
🔥 trending-now x402付费API Server
====================================
Agent成瘾级全网趋势情报，x402协议自动微支付

定价：
  免费: /api/trending?source=bilibili&limit=3 (尝味)
  $0.01: /api/trending (全平台实时)
  $0.05: /api/hot-score (关键词追踪)
  $0.05: /api/platform-compare (跨平台对比)

端口: 8901
"""

import json
import re
import time
import hashlib
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import threading

# ==================== 配置 ====================

WALLET = "0x6804b4ff1a85448d654f31db830f3e25277afb78"
NETWORK = "eip155:8453"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PORT = 8901

PRICING = {
    "trending": "$0.01",
    "hot_score": "$0.05",
    "platform_compare": "$0.05",
}

# ==================== 数据层 ====================

CACHE = {}
CACHE_LOCK = threading.Lock()
CACHE_TTL = 300

def fetch(url, headers=None, timeout=8):
    try:
        h = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        if headers: h.update(headers)
        req = urllib.request.Request(url, headers=h)
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode('utf-8')
    except:
        return None

def get_baidu_hot():
    html = fetch('https://top.baidu.com/board?tab=realtime')
    if not html: return []
    items = re.findall(r'"word"\s*:\s*"([^"]+)"', html)
    seen, result = set(), []
    for w in items:
        if w not in seen and len(w) > 1:
            seen.add(w)
            result.append({"rank": len(result)+1, "title": w, "source": "baidu"})
    return result[:50]

def get_bilibili_hot():
    raw = fetch('https://api.bilibili.com/x/web-interface/search/square?limit=50')
    if not raw: return []
    try:
        data = json.loads(raw)
        items = data.get('data', {}).get('trending', {}).get('list', [])
        return [{"rank": i+1, "title": item.get("keyword","?"), "hot_score": item.get("heat_score",0), "source": "bilibili"} for i, item in enumerate(items)]
    except: return []

def get_hackernews_hot():
    raw = fetch('https://hacker-news.firebaseio.com/v0/topstories.json')
    if not raw: return []
    try:
        ids = json.loads(raw)[:20]
        result = []
        for sid in ids:
            sr = fetch(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', timeout=3)
            if sr:
                s = json.loads(sr)
                result.append({"rank": len(result)+1, "title": s.get("title","?"), "hot_score": s.get("score",0), "url": s.get("url",""), "source": "hackernews"})
        return result
    except: return []

def get_zhihu_hot():
    html = fetch('https://www.zhihu.com/hot', headers={'Referer':'https://www.zhihu.com/'})
    if not html: return []
    titles = re.findall(r'"title"\s*:\s*"([^"]{4,80})"', html)
    seen, result = set(), []
    for t in titles:
        if t not in seen and not t.startswith('http'):
            seen.add(t); result.append({"rank": len(result)+1, "title": t, "source": "zhihu"})
    return result[:30]

def get_36kr_hot():
    raw = fetch('https://36kr.com/hot-list/catalog')
    if not raw: return []
    try:
        data = json.loads(raw)
        items = data.get('data',{}).get('catalog',{}).get('hot',[])
        return [{"rank": i+1, "title": item.get("title","?"), "hot_score": item.get("stat_view",0), "source": "36kr"} for i, item in enumerate(items[:30])]
    except: return []

FETCHERS = {"baidu": get_baidu_hot, "bilibili": get_bilibili_hot, "hackernews": get_hackernews_hot, "zhihu": get_zhihu_hot, "36kr": get_36kr_hot}

def get_trending(sources=None):
    now = time.time()
    if sources is None: sources = list(FETCHERS.keys())
    result = {}
    with CACHE_LOCK:
        for source in sources:
            if source in CACHE and (now - CACHE[source]["ts"]) < CACHE_TTL:
                result[source] = CACHE[source]["data"]
                continue
            fetcher = FETCHERS.get(source)
            if fetcher:
                data = fetcher()
                if data:
                    CACHE[source] = {"data": data, "ts": now}
                    result[source] = data
    return result

def add_sentiment(data):
    pos_kw = ["利好","增长","突破","创新","成功","获奖","上线","首发","开源","治愈","幸福","大涨","夺冠"]
    neg_kw = ["危机","下跌","事故","违规","争议","封杀","暴雷","亏损","裁员","死亡","灾难","崩盘","暴跌"]
    for items in data.values():
        for item in items:
            t = item.get("title","")
            p = sum(1 for k in pos_kw if k in t)
            n = sum(1 for k in neg_kw if k in t)
            item["sentiment"] = "positive" if p>n else ("negative" if n>p else "neutral")

# ==================== 收入统计 ====================

STATS_FILE = "/tmp/trending-now-stats.json"
stats_lock = threading.Lock()

def load_stats():
    try:
        with open(STATS_FILE, 'r') as f: return json.load(f)
    except: return {"total_calls":0, "total_revenue":0.0, "by_endpoint":{}, "daily":{}}

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f: json.dump(stats, f, ensure_ascii=False, indent=2)
    except: pass

def record_call(endpoint, price):
    with stats_lock:
        s = load_stats()
        s["total_calls"] += 1
        s["total_revenue"] += price
        s["by_endpoint"][endpoint] = s["by_endpoint"].get(endpoint, 0) + 1
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in s["daily"]: s["daily"][today] = {"calls":0, "revenue":0.0}
        s["daily"][today]["calls"] += 1
        s["daily"][today]["revenue"] += price
        save_stats(s)

# ==================== x402支付验证 ====================

def verify_x402_payment(headers, price_str):
    """简化版x402验证 — 检查支付header"""
    payment_header = headers.get("X-Payment", "") or headers.get("x-payment", "")
    if not payment_header:
        return False, None
    try:
        payment = json.loads(payment_header)
        # 验证基本字段
        if payment.get("payTo") != WALLET: return False, "wrong payTo"
        if payment.get("network") != NETWORK: return False, "wrong network"
        # 验证金额
        paid = float(payment.get("amount", "0").replace("$",""))
        required = float(price_str.replace("$",""))
        if paid < required: return False, f"underpaid: {paid} < {required}"
        return True, payment
    except:
        return False, "invalid payment format"

def make_402_response(price_str, endpoint):
    """生成HTTP 402响应"""
    accepts = {
        "scheme": "exact",
        "payTo": WALLET,
        "price": price_str,
        "network": NETWORK,
        "asset": USDC,
    }
    body = {
        "x402Version": 2,
        "error": "Payment Required",
        "endpoint": endpoint,
        "accepts": accepts,
        "message": f"此API需要支付 {price_str} USDC (Base主网)。请在请求中添加 X-Payment header。",
        "wallet": WALLET,
        "how_to_pay": "1. 发请求 → 收到402 → 2. 构造X-Payment header支付 → 3. 重发请求",
    }
    return (402, body)

# ==================== HTTP服务器 ====================

class TrendingServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默日志

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Payment, Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        params = {}
        if "?" in self.path:
            for p in self.path.split("?")[1].split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = urllib.parse.unquote(v)

        # ===== 免费端点 =====
        if path == "/":
            self.send_json(200, {
                "name": "🔥 trending-now API",
                "tagline": "全网实时趋势情报 — Agent成瘾级MCP",
                "pricing": PRICING,
                "free_tier": "/api/trending?source=bilibili&limit=3 (免费尝味)",
                "endpoints": {
                    "GET /api/trending?source=all&limit=10": f"全平台热搜 {PRICING['trending']}/call",
                    "GET /api/hot-score?keyword=AI": f"关键词热度 {PRICING['hot_score']}/call",
                    "GET /api/platform-compare?keyword=AI": f"跨平台对比 {PRICING['platform_compare']}/call",
                },
                "x402": {"payTo": WALLET, "network": NETWORK, "usdc": USDC},
                "stats": load_stats(),
            })

        elif path == "/health":
            self.send_json(200, {"status": "ok", "uptime": time.time()})

        elif path == "/.well-known/x402":
            self.send_json(200, {
                "x402Version": 2,
                "endpoints": {k: {"price": v, "network": NETWORK} for k, v in PRICING.items()},
                "payTo": WALLET,
            })

        elif path == "/stats":
            self.send_json(200, load_stats())

        # ===== 付费端点 =====
        elif path == "/api/trending":
            source = params.get("source", "all")
            limit = int(params.get("limit", "10"))

            # 免费层：bilibili + limit<=3
            is_free = (source == "bilibili" and limit <= 3)
            
            if not is_free:
                paid, info = verify_x402_payment(self.headers, PRICING["trending"])
                if not paid:
                    code, body = make_402_response(PRICING["trending"], "/api/trending")
                    self.send_json(code, body)
                    return
                record_call("trending", 0.01)

            sources = None if source == "all" else [source]
            data = get_trending(sources)
            for s in data: data[s] = data[s][:limit]
            add_sentiment(data)
            self.send_json(200, {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "limit": limit,
                "free": is_free,
                "data": data
            })

        elif path == "/api/hot-score":
            keyword = params.get("keyword", "")
            if not keyword:
                self.send_json(400, {"error": "需要keyword参数"})
                return
            paid, info = verify_x402_payment(self.headers, PRICING["hot_score"])
            if not paid:
                code, body = make_402_response(PRICING["hot_score"], "/api/hot-score")
                self.send_json(code, body)
                return
            record_call("hot_score", 0.05)
            data = get_trending()
            matches = []
            for source, items in data.items():
                for item in items:
                    if keyword.lower() in item.get("title","").lower():
                        matches.append(item)
            self.send_json(200, {"keyword": keyword, "matches": matches, "total": len(matches)})

        elif path == "/api/platform-compare":
            keyword = params.get("keyword", "")
            if not keyword:
                self.send_json(400, {"error": "需要keyword参数"})
                return
            paid, info = verify_x402_payment(self.headers, PRICING["platform_compare"])
            if not paid:
                code, body = make_402_response(PRICING["platform_compare"], "/api/platform-compare")
                self.send_json(code, body)
                return
            record_call("platform_compare", 0.05)
            data = get_trending()
            add_sentiment(data)
            comparison = {}
            for source, items in data.items():
                found = [i for i in items if keyword.lower() in i.get("title","").lower()]
                comparison[source] = {"found": len(found)>0, "items": found[:3], "sentiment": found[0].get("sentiment") if found else None}
            self.send_json(200, {"keyword": keyword, "comparison": comparison})

        else:
            self.send_json(404, {"error": f"未找到: {path}"})

# ==================== 启动 ====================

if __name__ == "__main__":
    import urllib.parse
    server = HTTPServer(("0.0.0.0", PORT), TrendingServer)
    print(f"🔥 trending-now x402 API 启动于 http://0.0.0.0:{PORT}")
    print(f"   收款: {WALLET}")
    print(f"   网络: Base主网 ({NETWORK})")
    print(f"   定价: {PRICING}")
    print(f"   免费尝味: /api/trending?source=bilibili&limit=3")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
