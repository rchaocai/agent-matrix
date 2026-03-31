---
name: generation.template_generator
description: 使用AI生成自定义HTML模板。当用户需要描述风格并自动生成渲染模板时使用。
version: "1.0.0"
category: generation
---

# AI模板生成器技能

## 概述
本技能使用大语言模型（LLM）根据用户的描述自动生成HTML/CSS模板，支持自定义风格和平台适配。

**架构说明**: 此技能通过 LLM 服务统一接口调用大语言模型，生成符合Jinja2语法的模板代码。

## 使用场景
- 用户需要特定风格的模板但现有模板不满足需求
- 需要快速生成多种风格变体进行选择
- 需要基于描述创建自定义模板
- 需要A/B测试不同模板风格

## 工作流程

### 步骤1: 接收用户描述
接收用户的风格描述和配置参数：
```yaml
skill: "generation.template_generator"
config:
  description: "粉色渐变背景、大字体标题、优雅杂志风格"
  platform: "xiaohongshu"
  style: "elegant"
```

### 步骤2: 调用LLM生成模板
- 使用预定义的提示词模板
- 调用LLM生成HTML+CSS代码
- 验证生成的代码语法

### 步骤3: 返回生成结果
```json
{
  "template_html": "{% extends 'base/layout.html' %}...",
  "template_name": "custom_a1b2c3d4",
  "preview_url": "/static/previews/custom_a1b2c3d4.png",
  "code_quality": 95
}
```

## 配置参数

Skill 配置（在 Agent 的 skill_chain 中）:
- `description`: 风格描述文本（必需）
- `platform`: 目标平台，xiaohongshu 或 douyin（默认xiaohongshu）
- `style`: 参考风格，modern/elegant/vibrant（默认modern）
- `max_tokens`: 最大生成 token 数（默认2000）
- `temperature`: 温度参数（默认0.8）

## 输出格式

生成的模板必须符合以下规范：
1. 继承 `base/layout.html`
2. 使用 `{% block extra_css %}` 定义自定义样式
3. 使用 `{{ config.* }}` 变量确保可配置性
4. 字体大小：标题64-72px，正文40-48px
5. 响应式设计，确保不同长度内容都美观

## 示例用法

### Agent 配置示例
```yaml
agent:
  id: "template_generator_agent"
  llm_provider: "deepseek"

  skill_chain:
    - skill: "generation.template_generator"
      config:
        description: "粉色渐变背景、大字体标题、优雅杂志风格"
        platform: "xiaohongshu"
        style: "elegant"
        max_tokens: 2000
        temperature: 0.8
```

### 风格描述示例
- "粉色渐变背景、大字体标题、优雅杂志风格"
- "深色背景、霓虹灯效果、赛博朋克风格"
- "简约白底、黑色大标题、极简主义"
- "温暖橙色调、圆润字体、活力四射"
- "高级灰底、金色装饰、奢华感"

## 模板验证规则

生成的模板必须满足：
1. ✅ 继承 `base/layout.html`
2. ✅ 包含 `{% block extra_css %}`
3. ✅ 使用 `{{ config.* }}` 变量
4. ✅ HTML结构完整闭合
5. ✅ CSS选择器不冲突
6. ✅ 字体大小符合规范

## 错误处理

- LLM生成失败会自动重试（最多3次）
- 生成的代码会进行语法验证
- 验证失败会返回错误信息和建议
- 支持重新生成直到满意

## 注意事项

- 生成模板需要30-60秒
- 预览图生成依赖后端渲染服务
- 保存的模板会自动添加到模板列表
- 自定义模板命名格式：custom_xxxxxxxx

## 后端API集成

此技能通过以下API端点调用：
- `POST /api/render/generate-template` - 生成模板
- `POST /api/render/save-template` - 保存模板
- `GET /api/render/templates` - 列出所有模板
