---
name: publishing.draft
description: 将生成的内容保存为草稿到数据库，支持标题、正文、图片、平台等字段。当Agent完成内容生成需要保存、或需要手动审核后再发布时使用。
version: "1.0.0"
---

# 草稿保存技能

## 概述
本技能将Agent生成的内容保存到数据库草稿表中，供后续查看、编辑或手动发布。

## 使用场景
- Agent完成内容生成需要保存时
- 内容需要人工审核后再发布时
- 需要批量管理待发布内容时
- 需要保留内容历史记录时

## 工作流程

### 步骤1: 准备内容数据
确保内容包含必要的字段：
```bash
python scripts/save_draft.py \
  --agent-id "buddhism_agent" \
  --platform "xiaohongshu" \
  --title "文章标题" \
  --content "文章正文内容..."
```

### 步骤2: 保存到数据库
- 自动创建草稿记录
- 分配草稿ID
- 记录创建时间

### 步骤3: 返回草稿信息
```json
{
  "draft_id": 1,
  "status": "saved",
  "created_at": "2026-02-26T10:30:00",
  "platform": "xiaohongshu",
  "message": "草稿保存成功"
}
```

## 配置参数
- `--agent-id`: Agent ID（必需）
- `--platform`: 目标平台（xiaohongshu/douyin，必需）
- `--title`: 内容标题（可选）
- `--content`: 正文内容（必需）
- `--images`: 图片路径，多个用逗号分隔（可选）
- `--metadata`: 额外元数据，JSON格式（可选）

## 示例用法

```bash
# 基础保存
python scripts/save_draft.py \
  --agent-id "buddhism_agent" \
  --platform "xiaohongshu" \
  --content "这是文章正文内容"

# 完整保存
python scripts/save_draft.py \
  --agent-id "buddhism_agent" \
  --platform "xiaohongshu" \
  --title "佛法智慧：如何在忙碌中找到内心的宁静" \
  --content "完整文章内容..." \
  --images "/path/to/image1.png,/path/to/image2.png"

# 带元数据
python scripts/save_draft.py \
  --agent-id "buddhism_agent" \
  --platform "xiaohongshu" \
  --content "内容..." \
  --metadata '{"tags": ["佛学", "智慧"], "category": "修行"}'
```

## 支持的平台

### 小红书 (xiaohongshu)
- 标题：必需，建议20字以内
- 正文：必需，建议1000字以内
- 图片：可选，建议1-9张

### 抖音 (douyin)
- 标题：必需
- 正文：必需，建议简短
- 图片/视频：可选

### 通用 (general)
- 适用于其他平台或测试

## 草稿状态

草稿有以下状态：
- `pending`: 待发布（默认）
- `published`: 已发布
- `failed`: 发布失败

## 元数据字段

可以在metadata中存储额外信息：
```json
{
  "tags": ["标签1", "标签2"],
  "category": "分类",
  "source_url": "原始链接",
  "author": "作者",
  "schedule_time": "计划发布时间"
}
```

## 数据库表结构

```sql
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50),
    platform VARCHAR(50),
    title VARCHAR(200),
    content TEXT,
    image_paths TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    metadata JSON,
    created_at TIMESTAMP,
    published_at TIMESTAMP
);
```

## 注意事项

- 草稿会持久化保存到数据库
- 建议定期清理已发布的旧草稿
- 图片路径应该是相对路径或绝对路径
- metadata字段必须使用有效的JSON格式
