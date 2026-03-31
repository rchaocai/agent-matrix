---
name: processing.clean
description: 清洗和处理文本内容，包括移除HTML标签、多余空白、特殊字符等。当Agent需要清理原始文本、格式化内容或准备文本用于进一步处理时使用。
version: "1.0.0"
---

# 文本清洗技能

## 概述
本技能用于清洗和处理文本内容，确保文本干净、格式统一，适合后续的内容生成或发布。

## 使用场景
- Agent采集到原始文本需要清理时
- 需要移除HTML标签和格式时
- 需要统一文本格式时
- 需要去重或过滤短内容时

## 工作流程

### 步骤1: 移除HTML标签
使用脚本清理HTML标签和特殊字符：
```bash
python scripts/clean_text.py --input "<raw_text>" --remove-html --min-length 100
```

### 步骤2: 格式化文本
- 移除多余空白
- 统一换行符
- 去除特殊字符

### 步骤3: 返回结果
返回清洗后的文本和统计信息：
```json
{
  "original_length": 1500,
  "cleaned_length": 800,
  "text": "清洗后的文本内容...",
  "removed_html": true,
  "removed_duplicates": false
}
```

## 配置参数
- `--input`: 输入文本（必需）
- `--remove-html`: 是否移除HTML标签（默认true）
- `--min-length`: 最小内容长度，低于此长度返回空（默认0）
- `--remove-duplicates`: 是否移除重复段落（默认false）
- `--preserve-urls`: 是否保留URL链接（默认false）

## 示例用法

```bash
# 基础清洗
python scripts/clean_text.py --input "<p>Hello World</p>" --remove-html

# 完整清洗
python scripts/clean_text.py --input "$(cat raw_content.txt)" \
  --remove-html --min-length 100 --remove-duplicates

# 保留URL
python scripts/clean_text.py --input "Visit https://example.com" --preserve-urls
```

## 清洗规则

1. **HTML标签移除**
   - 移除所有HTML标签（如 `<p>`, `<div>`, `<span>`）
   - 保留文本内容

2. **空白处理**
   - 移除多余空格
   - 统一换行符
   - 去除首尾空白

3. **特殊字符**
   - 移除控制字符
   - 统一引号和标点

4. **去重**
   - 检测重复段落
   - 只保留首次出现

## 注意事项
- 清洗会改变原始文本格式
- 建议在清洗前保存原始内容
- 某些特殊格式可能需要额外处理
