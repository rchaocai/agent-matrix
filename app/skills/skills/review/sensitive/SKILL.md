---
name: review.sensitive
description: 检测文本中的敏感词、违规内容和不当言论。当Agent需要审核内容合规性、检查敏感词或评估内容风险时使用。
version: "1.0.0"
---

# 敏感词检测技能

## 概述
本技能用于检测文本中的敏感词、违规内容和不当言论，确保内容符合平台规范和法律法规。

## 使用场景
- Agent生成内容后需要审核时
- 发布前需要检查合规性时
- 需要过滤敏感词汇时
- 需要评估内容风险时

## 工作流程

### 步骤1: 加载敏感词库
从配置的词库中加载敏感词：
```bash
python scripts/check_sensitive.py \
  --content "待检测内容" \
  --categories "politics,porn,violence"
```

### 步骤2: 执行检测
- 关键词匹配
- 正则表达式检测
- 语义分析（可选）

### 步骤3: 返回检测结果
```json
{
  "is_safe": true,
  "risk_level": "low",
  "detected_items": [],
  "sensitive_words": [],
  "categories_checked": ["politics", "porn", "violence"],
  "confidence": 0.95
}
```

## 配置参数
- `--content`: 待检测内容（必需）
- `--categories`: 检测类别，逗号分隔（默认all）
  - `politics`: 政治敏感
  - `porn`: 色情低俗
  - `violence`: 暴力恐怖
  - `spam`: 垃圾广告
  - `illegal`: 违法信息
- `--strictness`: 严格程度（low/medium/high，默认medium）
- `--custom-words`: 自定义敏感词，逗号分隔（可选）

## 检测类别详解

### 1. 政治敏感 (politics)
- 政治人物相关
- 政治事件
- 政治组织

### 2. 色情低俗 (porn)
- 色情词汇
- 低俗表达
- 不当暗示

### 3. 暴力恐怖 (violence)
- 暴力行为
- 恐怖主义
- 极端思想

### 4. 垃圾广告 (spam)
- 广告关键词
- 联系方式
- 营销用语

### 5. 违法信息 (illegal)
- 违法物品
- 违法行为
- 欺诈信息

## 风险等级

- **low**: 无敏感词，安全
- **medium**: 发现少量敏感词，需关注
- **high**: 发现大量敏感词或严重违规，建议拒绝

## 示例用法

```bash
# 基础检测
python scripts/check_sensitive.py \
  --content "这是一篇正常的文章内容"

# 检测特定类别
python scripts/check_sensitive.py \
  --content "待检测内容" \
  --categories "politics,violence"

# 严格模式
python scripts/check_sensitive.py \
  --content "待检测内容" \
  --strictness high

# 自定义敏感词
python scripts/check_sensitive.py \
  --content "待检测内容" \
  --custom-words "词1,词2,词3"
```

## 敏感词库

敏感词库位置：`assets/sensitive_words/`

- `politics.txt` - 政治敏感词
- `porn.txt` - 色情低俗词
- `violence.txt` - 暴力恐怖词
- `spam.txt` - 垃圾广告词
- `illegal.txt` - 违法信息词

## 检测方法

1. **关键词匹配**
   - 精确匹配
   - 模糊匹配
   - 变体检测

2. **正则表达式**
   - 电话号码
   - 邮箱地址
   - URL链接
   - 微信号/QQ号

3. **上下文分析**
   - 语义理解
   - 上下文相关性
   - 误报过滤

## 注意事项

- 敏感词库需要定期更新
- 可能存在误报，建议人工复核
- 不同平台有不同的审核标准
- 建议结合其他审核方法使用
