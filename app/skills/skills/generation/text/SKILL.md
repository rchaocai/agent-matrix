---
name: generation.text
description: 使用大语言模型生成高质量内容。当Agent需要基于素材创作文章、生成文案、改写文本时使用。
version: "2.0.0"
---

# 文本生成技能

## 概述
本技能使用大语言模型（LLM）生成高质量内容，支持多种生成场景和自定义Prompt模板。

**架构说明**: 此技能通过 LLM 服务统一接口调用大语言模型，不关心具体使用哪个提供商。LLM 提供商配置在 Agent 级别。

## 使用场景
- Agent需要基于素材创作内容时
- 需要生成文章、文案、评论时
- 需要改写或扩写文本时
- 需要根据人设生成特定风格内容时

## 工作流程

### 步骤1: 准备Prompt模板
使用配置的Prompt模板和输入内容：
```yaml
skill: "generation.text"
config:
  prompt_template: |
    你是一位{role}，请基于以下素材创作小红书内容：{content}
    要求：
    1. 语气{tone}
    2. 字数{length}字
  variables:
    role: "佛学传播者"
    tone: "平和、智慧"
    length: "200-300"
  max_tokens: 500
```

### 步骤2: 调用LLM生成
- 自动使用Agent配置的LLM提供商
- 处理API调用和错误重试
- 返回生成结果和token使用情况

### 步骤3: 返回生成结果
```json
{
  "generated_text": "生成的完整内容...",
  "tokens_used": 450,
  "model": "deepseek-chat",
  "provider": "deepseek"
}
```

## 配置参数

Skill 配置（在 Agent 的 skill_chain 中）:
- `prompt_template`: Prompt 模板，支持 `{variable}` 占位符（必需）
- `variables`: 模板变量字典（可选）
- `max_tokens`: 最大生成 token 数（默认500）
- `temperature`: 温度参数，0-2，越高越随机（默认1.0）
- `system_message`: 系统消息，设定AI行为（可选）

**注意**: `llm_provider` 应该在 **Agent 级别**配置，而不是 Skill 级别。

## 示例用法

### Agent 配置示例
```yaml
agent:
  id: "buddhism_agent"
  llm_provider: "deepseek"  # Agent 级别配置

  skill_chain:
    - skill: "generation.text"
      config:
        prompt_template: |
          你是一位佛学传播者，请基于以下素材创作适合小红书的内容：{content}
          要求：
          1. 语气平和、富有智慧
          2. 引用相关佛经典故
          3. 结合现代生活
          4. 字数200-300字
        max_tokens: 500
        temperature: 0.8
```

### 使用变量模板
```yaml
- skill: "generation.text"
  config:
    prompt_template: |
      角色：{role}
      语气：{tone}
      请基于素材创作：{content}
    variables:
      role: "科技博主"
      tone: "专业、幽默"
    max_tokens: 800
```

## Prompt模板最佳实践

### 1. 明确角色定位
```yaml
prompt_template: |
  你是一位{role}，请{task}...
variables:
  role: "佛学传播者"
  task: "基于素材创作小红书内容"
```

### 2. 提供示例
```yaml
prompt_template: |
  请按照以下示例创作内容：

  示例输入：{example_input}
  示例输出：{example_output}

  现在请处理：{content}
```

### 3. 指定格式
```yaml
prompt_template: |
  请按以下格式输出：
  ## 标题
  ## 正文
  ## 标签

  内容：{content}
```

### 4. 控制长度和风格
```yaml
prompt_template: |
  请基于素材创作内容：
  {content}

  要求：
  - 字数：{length}字
  - 语气：{tone}
  - 风格：{style}
variables:
  length: "200-300"
  tone: "平和、智慧"
  style: "引用经典、结合现代"
```

## 错误处理

- API调用失败会自动重试（最多3次）
- 超时时间：30秒
- 错误会记录到日志并返回错误信息
- Skill 执行失败不会中断整个 Agent 执行链

## 与 LLM 解耦

**重要设计原则**: 此技能不关心具体使用哪个 LLM 提供商。

- ✅ **Skill 定义**: WHAT - 需要生成文本，使用什么 prompt
- ✅ **Agent 配置**: WHICH - 使用哪个 LLM 提供商
- ✅ **LLM Service**: HOW - 如何调用具体提供商的 API

这样设计的好处：
1. **可移植性**: Skill 可以在不同项目间复用
2. **灵活性**: 切换 LLM 提供商只需修改 Agent 配置
3. **可测试性**: 可以注入 Mock LLM 服务进行测试
4. **可维护性**: LLM API 变更只需修改 LLM Service

## 注意事项

- 确保 Agent 配置了 `llm_provider`
- 确保 `.env` 中配置了对应提供商的 API 密钥
- 生成内容会受 token 限制影响
- 较高的 temperature 会产生更创意的内容
- 建议在生产环境使用 API 密钥配额限制
