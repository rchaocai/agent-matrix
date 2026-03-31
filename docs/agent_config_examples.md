# Agent 配置示例

## 1. 使用 AI 审核模式的质量评分

### 完整流水线配置

```yaml
agent:
  id: ai_review_agent
  name: AI审核Agent
  enabled: true
  llm_provider: deepseek
  schedule:
    cron: "0 */2 * * *"
    timezone: "Asia/Shanghai"
  skill_chain:
  - skill: generation.text
    config:
      prompt_template: '请基于以下素材生成小红书内容：\n\n素材：{content}\n\n要求：...'
      variables:
        content: "禅修是一种生活态度..."
      max_tokens: 500
      temperature: 0.8

  - skill: review.sensitive
    config:
      strictness: medium
      categories:
        - politics
        - porn
        - violence

  - skill: review.quality
    config:
      # 使用 AI 审核模式（更灵活、更智能）
      use_ai: true
      platform: xiaohongshu
      min_score: 60

  - skill: conditional.save
    config:
      condition: "overall_score >= 60 and is_safe == true"
      true_action: save_as_draft
      false_action: log_and_discard

  - skill: publishing.draft
    config:
      platform: xiaohongshu
```

### 本地规则审核模式（默认）

```yaml
- skill: review.quality
  config:
    # 使用本地规则审核（快速、无API费用）
    use_ai: false
    platform: xiaohongshu
    dimensions:
      - readability
      - completeness
      - attractiveness
    min_score: 60
```

---

## 2. 部分流水线配置示例

### 只生成内容，不审核

```yaml
agent:
  id: simple_generator
  name: 简单生成器
  skill_chain:
  - skill: generation.text
    config:
      prompt_template: '生成关于{topic}的内容'
      variables:
        topic: 禅修智慧

  - skill: publishing.draft
    config:
      platform: xiaohongshu
```

### 只生成和渲染，不发布

```yaml
agent:
  id: content_renderer
  name: 内容渲染器
  skill_chain:
  - skill: generation.text
    config:
      prompt_template: '生成关于{topic}的内容'
      variables:
        topic: 禅修智慧

  - skill: generation.render
    config:
      platform: xiaohongshu
      template: zen
      split_long: true
      output_dir: data/images
```

### 采集+生成+审核，手动发布

```yaml
agent:
  id: semi_auto_agent
  name: 半自动Agent
  skill_chain:
  - skill: collection.rss
    config:
      script: fetch_rss.py
      url: https://example.com/rss
      max_items: 5

  - skill: processing.clean
    config:
      script: clean_text.py
      min_length: 100
      remove_html: true

  - skill: generation.text
    config:
      prompt_template: '基于素材创作：{content}'
      variables: {}

  - skill: review.sensitive
    config:
      strictness: medium

  - skill: review.quality
    config:
      use_ai: true  # AI审核更灵活
      min_score: 70

  - skill: conditional.save
    config:
      condition: "overall_score >= 70 and is_safe == true"
      true_action: save_as_draft
      false_action: log_and_discard
```

---

## 3. 数据流说明

### 累积式数据流

每个 skill 会**累积**数据到数据流中，而不是覆盖：

```yaml
# 初始数据: {}

# generation.text 返回:
{parsed_title, parsed_content, tags}

# review.sensitive 返回:
{parsed_title, parsed_content, tags, is_safe, risk_level, detected_items}

# review.quality 返回:
{parsed_title, parsed_content, tags, is_safe, risk_level, detected_items,
 overall_score, is_qualified, scores, suggestions}

# conditional.save 可以访问所有字段:
condition: "overall_score >= 70 and is_safe == true"

# publishing.draft 可以使用所有字段:
title: {parsed_title}
content: {parsed_content}
tags: {tags}
```

### 字段优先级

如果多个 skill 返回相同字段名，后面的会覆盖前面的：

```python
# 合并顺序
result = {**input_data, **result}
```

示例：
- `generation.text` 返回 `{title: "AI标题"}`
- `publishing.draft` 优先使用 `config.title`，如果没有则使用 `input_data.title`

---

## 4. 审核模式对比

| 特性 | 本地规则模式 | AI审核模式 |
|------|------------|-----------|
| **配置** | `use_ai: false`（默认） | `use_ai: true` |
| **速度** | 快（< 1秒） | 慢（2-5秒，取决于LLM） |
| **成本** | 免费 | 消耗LLM tokens |
| **灵活性** | 固定规则 | 可自定义prompt |
| **准确性** | 一般 | 高（理解上下文） |
| **适用场景** | 大量内容快速筛选 | 重要内容精审 |

---

## 5. 配置建议

### 高频场景（如每2分钟执行）
```yaml
- skill: review.quality
  config:
    use_ai: false  # 使用本地规则，节省成本
```

### 重要场景（如人工精选内容）
```yaml
- skill: review.quality
  config:
    use_ai: true   # 使用AI审核，保证质量
    platform: xiaohongshu
```

### 混合审核（先规则过滤，再AI精审）
```yaml
- skill: review.quality
  config:
    use_ai: false
    min_score: 50  # 规则过滤

- skill: review.quality
  config:
    use_ai: true   # AI精审
    min_score: 70
```
