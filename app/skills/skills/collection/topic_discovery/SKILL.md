---
name: collection.topic_discovery
description: 自动发现热门主题，基于多源数据智能推荐选题
version: 1.1.0
author: agent-matrix
tags:
  - collection
  - topic
  - trending
---

# 主题发现 Skill

## 功能描述
自动发现热门主题，基于多源数据（微博热搜、百度热搜、头条热搜）智能推荐选题。
支持LLM分析，针对特定平台用户特征选择最合适的主题，并提供详细的内容创作建议。

## 输入参数

### 必需参数
- `sources`: 数据源列表
  - `weibo`: 微博热搜
  - `baidu`: 百度热搜
  - `toutiao`: 头条热搜
  - 示例: `['weibo', 'baidu', 'toutiao']`

### 可选参数
- `platform`: 目标平台（默认: xiaohongshu）
  - `xiaohongshu`: 小红书 - 年轻女性，关注美妆、穿搭、生活方式
  - `weixin`: 微信公众号 - 年龄层较广，关注深度内容、职场技能
  - `douyin`: 抖音 - 喜欢娱乐、搞笑、生活技巧、情感故事
  
- `count`: 推荐主题数量（默认: 5，范围: 1-10）

- `use_llm`: 是否使用LLM分析（默认: true）
  - `true`: 使用LLM智能分析，根据平台用户特征选择主题
  - `false`: 仅按热度排序

- `force_refresh`: 是否强制刷新缓存（默认: false）
  - `true`: 强制重新爬取数据
  - `false`: 使用本地缓存（每天只爬一次）

## 输出格式
```json
{
  "topics": [
    {
      "topic": "5款网红护肝片含量检测全虚标",
      "source": "weibo",
      "source_name": "微博热搜",
      "rank": "30",
      "heat": "120425",
      "score": 0.85,
      "reason": "小红书用户高度关注健康养生、美颜护肤和产品测评...",
      "content_direction": "以'测评避雷'或'成分党深扒'为标题风格...",
      "keywords": ["护肝片测评", "保健品避雷", "成分党"],
      "target_audience": "20-35岁职场女性、熬夜学生党...",
      "predicted_heat": "高",
      "engagement_potential": "高互动潜力，容易引发讨论和分享"
    }
  ],
  "total_found": 133
}
```

## 实现逻辑
1. 从本地缓存获取热点数据（每天只爬一次）
2. 整合微博、百度、头条三大平台数据
3. 使用LLM分析，根据平台用户特征选择最合适的主题
4. 提供详细的内容创作建议（标题风格、内容结构、呈现方式）
5. 生成目标受众画像和互动潜力预测

## 配置示例

### 示例1：小红书平台推荐
```yaml
- skill: collection.topic_discovery
  config:
    sources: ['weibo', 'baidu', 'toutiao']
    platform: xiaohongshu
    count: 3
    use_llm: true
```

### 示例2：微信公众号推荐
```yaml
- skill: collection.topic_discovery
  config:
    sources: ['weibo', 'baidu']
    platform: weixin
    count: 5
    use_llm: true
```

### 示例3：抖音平台推荐（不使用LLM）
```yaml
- skill: collection.topic_discovery
  config:
    sources: ['weibo', 'toutiao']
    platform: douyin
    count: 5
    use_llm: false
```

## 数据源说明

### 微博热搜
- 数据量：约50条
- 更新频率：每天一次
- 特点：实时热点、娱乐八卦、社会事件

### 百度热搜
- 数据量：约50条
- 更新频率：每天一次
- 特点：搜索趋势、新闻资讯、科技热点

### 头条热搜
- 数据量：约30条
- 更新频率：每天一次
- 特点：新闻资讯、社会热点、民生话题

## 注意事项
1. 数据每天只爬取一次，缓存在本地 `data/hot_cache/` 目录
2. LLM分析需要配置 `DEEPSEEK_API_KEY` 环境变量
3. 建议使用LLM分析以获得更精准的推荐
4. 不同平台的用户特征不同，推荐结果会有差异
