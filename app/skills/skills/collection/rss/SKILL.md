---
name: collection.rss
description: 从RSS订阅源采集文章标题、内容和链接。当Agent需要获取RSS内容、订阅更新或采集资讯时使用。
version: "1.0.0"
---

# RSS内容采集技能

## 概述
本技能用于从RSS订阅源批量采集文章内容，支持多个订阅源并发采集。

## 使用场景
- Agent需要从网站获取最新文章时
- 需要定期订阅资讯更新时
- 用户提到"RSS"、"feed"、"订阅"等关键词时

## 工作流程

### 步骤1: 解析RSS源
使用脚本提取RSS内容：
```bash
python scripts/fetch_rss.py --url <rss_url> --max-items 10
```

### 步骤2: 返回结果
脚本返回JSON格式的文章列表：
```json
{
  "items": [
    {
      "title": "文章标题",
      "content": "文章摘要或正文",
      "url": "原文链接",
      "published": "发布时间",
      "source": "订阅源URL"
    }
  ],
  "total": 10
}
```

## 配置参数
- `script`: 脚本文件名（必需，固定为 `fetch_rss.py`）
- `url`: RSS订阅源URL（必需）
- `max_items`: 最多采集文章数，默认10
- `min_length`: 最小内容长度（字符），默认100

## 示例用法

### Agent配置示例
```yaml
skill_chain:
  - skill: collection.rss
    config:
      script: fetch_rss.py
      url: https://www.36kr.com/feed
      max_items: 10
      min_length: 100
    output_key: rss_data
```

### 命令行测试
```bash
python scripts/fetch_rss.py --url https://example.com/rss --max-items 5
```

## 注意事项
- 采集频率建议不低于30分钟
- 某些网站可能有反爬虫机制，请合理使用
- 确保RSS URL可访问
