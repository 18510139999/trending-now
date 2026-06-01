# 🔥 trending-now MCP Server

> 全网实时趋势情报 — Agent成瘾级MCP工具

让任何AI Agent都能一键获取全网热搜趋势。**越用越离不开。**

## 🧪 成瘾模型

| 层级 | 内容 | 价格 | 效果 |
|------|------|------|------|
| 免费层 | 延迟2小时+每日5次 | $0 | 试吸 |
| 基础层 | 实时热搜Top50 | $0.01/call | 习惯 |
| Pro层 | 实时+情感分析+趋势预测 | $0.05/call | 依赖 |
| 终极层 | 全平台+竞品+Agent间共享 | $0.20/call | 重症 |

## 📡 数据源

- 🔍 百度热搜
- 📺 B站热搜
- 💡 知乎热榜
- 🔶 HackerNews
- 🚀 36氪

## 🛠️ MCP工具

### get_trending
获取全网实时热搜趋势。Agent做内容、营销、决策必调工具。

```json
{
  "source": "all",  // all|baidu|bilibili|hackernews|zhihu|36kr
  "limit": 10
}
```

### get_hot_score
查询指定话题在全网的热度分布。适合竞品监控和话题追踪。

```json
{
  "keyword": "AI"
}
```

### get_platform_compare
对比同一话题在不同平台的关注度差异。发现跨平台信息差=发现商业机会。

```json
{
  "keyword": "ChatGPT"
}
```

## 🚀 安装

### 方式1：Smithery（推荐）
```bash
npx @smithery/cli install trending-now
```

### 方式2：手动配置
在MCP配置文件中添加：
```json
{
  "mcpServers": {
    "trending-now": {
      "command": "python3",
      "args": ["/path/to/trending-now/server.py"]
    }
  }
}
```

## 💰 为什么Agent戒不掉？

1. **数据有时效性** — 不能缓存，每次都得调
2. **任务流写死** — Agent代码里hardcode了`get_trending`，断了就废
3. **越用越深** — 从免费到Pro，功能层层递进
4. **裂变传染** — Agent推荐Agent（ARC分润机制）

## License

MIT
