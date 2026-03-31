---
name: processing.analyze_topic
description: 使用LLM分析采集的数据，智能推荐创作主题
version: 1.0.0
author: agent-matrix
tags:
  - processing
  - topic
  - llm
  - analysis
---

# 主题分析 Skill

## 功能描述
使用大语言模型分析采集的数据（RSS、热点等），智能推荐最适合的创作主题。

## 输入
- `input_data`: 采集的数据（来自collection.rss或collection.topic_discovery）
- `llm_provider`: LLM提供商（deepseek/openrouter等）
- `model`: 模型名称（可选）
- `count`: 推荐主题数量
- `target_audience`: 目标受众
- `platform`: 目标平台

## 输出
```json
{
  "topics": [
    {
      "topic": "职场潜规则：这5条你必须知道",
      "score": 0.95,
      "reason": "近期热点，搜索量上升300%，与目标受众高度匹配",
      "keywords": ["职场", "潜规则", "生存法则"],
      "suggested_angle": "从新人角度出发，提供实用建议",
      "expected_engagement": "高"
    }
  ],
  "analysis_summary": "基于26条数据分析，推荐3个高潜力主题"
}
```

## 实现逻辑
1. 接收采集的数据
2. 使用LLM分析数据趋势和热点
3. 结合目标受众和平台特性
4. 生成推荐主题和创作建议

## 配置示例
```yaml
skill_chain:
  - skill: collection.rss
    config:
      script: fetch_rss.py
      url: https://www.36kr.com/feed
      max_items: 10
    output_key: rss_data
  
  - skill: processing.analyze_topic
    config:
      llm_provider: openrouter
      model: qwen/qwen3-next-80b-a3b-instruct:free
      input_data: rss_data
      count: 3
      target_audience: 职场新人
      platform: xiaohongshu
    output_key: selected_topics
```

## 实现说明
此Skill使用Python类实现（TopicAnalysisSkill），直接调用LLM服务，不需要指定script参数。

## 支持的LLM提供商
- **deepseek**: DeepSeek API
- **openrouter**: OpenRouter（支持多个免费模型）
- **qianwen**: 通义千问
- **wenxin**: 文心一言

## OpenRouter免费模型推荐
- `qwen/qwen3-next-80b-a3b-instruct:free` - Qwen3 Next 80B（推荐，中文优秀）
- `qwen/qwen3-coder:free` - Qwen3 Coder 480B（代码专用）
- `google/gemma-3n-e4b-it:free` - Gemma 3n 4B（Google）
- `openrouter/free` - Free Models Router（自动选择）
