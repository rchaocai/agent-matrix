---
name: review.quality
description: 评估内容质量，包括可读性、完整性、吸引力等维度。当Agent需要评估生成内容质量、优化内容或筛选优质内容时使用。
version: "1.0.0"
---

# 内容质量评分技能

## 概述
本技能对内容进行多维度质量评估，包括可读性、完整性、吸引力等，帮助筛选和优化优质内容。

## 使用场景
- Agent生成内容后需要评估质量时
- 需要从多篇内容中筛选优质内容时
- 需要优化内容质量时
- 需要评估内容发布价值时

## 工作流程

### 步骤1: 分析内容
从多个维度分析内容质量：
```bash
python scripts/score_quality.py \
  --content "待评分内容" \
  --platform "xiaohongshu" \
  --dimensions "readability,completeness,attractiveness"
```

### 步骤2: 多维度评分
- 可读性评分（0-100）
- 完整性评分（0-100）
- 吸引力评分（0-100）
- 总体评分（0-100）

### 步骤3: 返回评分和建议
```json
{
  "overall_score": 85,
  "readability": {
    "score": 80,
    "issues": ["句子过长", "段落过多"]
  },
  "completeness": {
    "score": 90,
    "missing_elements": []
  },
  "attractiveness": {
    "score": 85,
    "suggestions": ["添加emoji", "优化标题"]
  },
  "is_recommended": true
}
```

## 配置参数
- `--content`: 待评分内容（必需）
- `--platform`: 目标平台（xiaohongshu/douyin/general，默认general）
- `--dimensions`: 评分维度，逗号分隔
  - `readability`: 可读性
  - `completeness`: 完整性
  - `attractiveness`: 吸引力
  - `originality`: 原创性
  - `engagement`: 互动性
- `--min_score`: 最低合格分数（默认60）

## 评分维度详解

### 1. 可读性 (Readability)
- 句子长度（建议15-25字）
- 段落结构（建议3-5段）
- 标点使用
- 错别字检测
- 语言流畅度

### 2. 完整性 (Completeness)
- 标题是否完整
- 正文是否有头有尾
- 逻辑连贯性
- 要点是否齐全
- 结尾是否恰当

### 3. 吸引力 (Attractiveness)
- 标题吸引力
- 开头吸引力
- 内容有趣性
- 情感共鸣
- 价值感

### 4. 原创性 (Originality)
- 内容独特性
- 观点新颖性
- 表达创新性
- 信息增量

### 5. 互动性 (Engagement)
- 引导互动
- 疑问设置
- 话题讨论性
- 分享价值

## 平台特色评分

### 小红书 (xiaohongshu)
- 标题：15-25字，吸引人
- 正文：1000字内，分段清晰
- Emoji：3-5个，恰当使用
- 话题：相关话题标签
- 图片：配图质量

### 抖音 (douyin)
- 标题：简洁有力
- 正文：简短精炼
- 话题：热门话题
- BGM：背景音乐匹配
- 时长：15-60秒

### 通用 (general)
- 基础质量标准
- 适用于多平台

## 评分标准

| 分数段 | 等级 | 建议 |
|--------|------|------|
| 90-100 | 优秀 | 直接发布 |
| 75-89 | 良好 | 建议发布 |
| 60-74 | 及格 | 优化后发布 |
| 0-59 | 不及格 | 需要重写 |

## 示例用法

```bash
# 基础评分
python scripts/score_quality.py \
  --content "这是待评分的内容..."

# 平台特定评分
python scripts/score_quality.py \
  --content "内容..." \
  --platform xiaohongshu \
  --dimensions readability,attractiveness

# 设置最低分数
python scripts/score_quality.py \
  --content "内容..." \
  --min_score 70
```

## 优化建议

根据评分结果自动生成优化建议：

**可读性问题**:
- 拆分长句
- 增加段落分隔
- 修正标点符号

**完整性问题**:
- 补充开头
- 完善结尾
- 增加过渡句

**吸引力问题**:
- 优化标题
- 增加emoji
- 添加提问
- 制造悬念

## 注意事项

- 评分是相对的，需结合人工判断
- 不同平台有不同标准
- 内容类型影响评分标准
- 建议结合人工审核使用
