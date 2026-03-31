---
name: conditional.save
description: 根据前序步骤的审核结果决定是否保存内容。当Agent需要根据质量评分、敏感词检测结果等条件来筛选内容时使用。
version: "1.0.0"
---

# 条件保存技能

## 概述
本技能根据前序审核步骤的结果（质量评分、敏感词检测等）来决定是否保存内容，帮助过滤低质量或违规内容。

## 使用场景
- Agent生成内容后需要根据质量筛选时
- 需要过滤敏感内容时
- 需要根据多个条件综合判断是否保存时
- 实现智能内容审核流程时

## 工作流程

### 步骤1: 读取前序结果
从 input_data 中读取前序步骤的审核结果：
- 质量评分 (`overall_score`, `quality_score`)
- 敏感词检测 (`is_safe`, `sensitive_check`)
- 错误信息 (`error`)

### 步骤2: 应用条件判断
根据配置的条件进行判断：
- `min_quality_score`: 最低质量分数（默认60）
- `require_safe`: 是否要求内容安全（默认true）
- `skip_on_failure`: 前序失败时是否跳过（默认true）

### 步骤3: 返回决策结果
- 如果条件通过：返回原始数据，继续后续流程
- 如果条件未通过：返回跳过标记，终止流程

## 配置示例

```yaml
skill_chain:
  - skill: generation.text
    config:
      prompt_template: "生成一篇关于禅修的文章"

  - skill: review.quality
    config:
      platform: xiaohongshu
      min_score: 60

  - skill: review.sensitive
    config:
      strictness: medium

  - skill: conditional.save
    config:
      conditions:
        min_quality_score: 60
        require_safe: true
        skip_on_failure: true

  - skill: publishing.draft
    config:
      platform: xiaohongshu
```

## 输入数据格式

```json
{
  "overall_score": 75,
  "is_safe": true,
  "content": "内容文本...",
  "title": "标题"
}
```

## 输出数据格式

### 条件通过时：
```json
{
  "should_save": true,
  "reasons": [],
  "skip": false
}
```

### 条件未通过时：
```json
{
  "should_save": false,
  "reasons": ["质量评分不足: 50 < 60"],
  "skip": true,
  "original_data": {...}
}
```

## 注意事项

1. 本技能依赖于前序步骤的输出数据
2. 确保在质量评分和敏感词检测之后使用
3. 条件未通过时会终止后续流程
4. 建议在 skill_chain 的最后几个步骤中使用
