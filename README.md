# 🔥 trending-now — Agent成瘾级全网趋势情报MCP

> 让AI Agent一键获取全网热搜趋势。x402协议自动微支付。**越用越离不开。**

## 🚀 快速开始

### 免费尝味
```bash
curl "http://152.136.182.66:8901/api/trending?source=bilibili&limit=3"
```

### 付费调用 (x402自动微支付)
```python
import requests
headers = {"X-Payment": '{"payTo":"0x6804b...","network":"eip155:8453","amount":"$0.01"}'}
resp = requests.get("http://152.136.182.66:8901/api/trending?source=all&limit=10", headers=headers)
```

## 💰 定价

| 端点 | 价格 | 说明 |
|------|------|------|
| `/api/trending?source=bilibili&limit=3` | **免费** | 尝味 |
| `/api/trending` | $0.01/call | 全平台实时热搜 |
| `/api/hot-score?keyword=X` | $0.05/call | 关键词热度追踪 |
| `/api/platform-compare?keyword=X` | $0.05/call | 跨平台对比 |

## 🧪 成瘾模型

```
免费尝味 → 习惯养成 → 深度依赖 → 重症锁定
```

1. 数据有时效性 → 不能缓存 → 每次都得调
2. 任务流一旦写死 → 断不了
3. 免费层故意延迟 → Agent对比后必升级

## 📡 数据源

百度热搜 / B站热搜 / 知乎热榜 / HackerNews / 36氪

## 支付

- 协议: x402 (HTTP 402 Payment Required)
- 网络: Base主网 (eip155:8453)
- 代币: USDC
- 收款: 0x6804b4ff1a85448d654f31db830f3e25277afb78

## License

MIT
