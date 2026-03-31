# OpenRouter 免费模型列表

> 最后更新：2026-03-03

## 推荐模型 ⭐

### 1. Qwen3 Next 80B（强烈推荐）
```
qwen/qwen3-next-80b-a3b-instruct:free
```
- **提供商**: 阿里巴巴通义实验室
- **参数**: 80B
- **上下文长度**: 262K tokens
- **特点**:
  - 完全免费
  - 中文支持优秀
  - 性能强大
  - 适合主题分析、内容生成
- **测试状态**: ✅ 已验证可用

### 2. Qwen3 Coder 480B
```
qwen/qwen3-coder:free
```
- **提供商**: 阿里巴巴通义实验室
- **参数**: 480B (A35B)
- **上下文长度**: 262K tokens
- **特点**:
  - 代码专用模型
  - 编程能力强
  - 适合代码生成、技术文档

### 3. Gemma 3n 4B
```
google/gemma-3n-e4b-it:free
```
- **提供商**: Google
- **参数**: 4B
- **上下文长度**: 8K tokens
- **特点**:
  - 轻量级模型
  - 响应速度快
  - 适合简单任务

### 4. Free Models Router
```
openrouter/free
```
- **提供商**: OpenRouter
- **上下文长度**: 200K tokens
- **特点**:
  - 自动选择最佳免费模型
  - 智能路由

## 其他免费模型

### StepFun系列
```
stepfun/step-3.5-flash:free
```
- **上下文长度**: 256K tokens
- **特点**: 快速响应

### NVIDIA系列
```
nvidia/nemotron-3-nano-30b-a3b:free
nvidia/nemotron-nano-12b-v2-vl:free
nvidia/nemotron-nano-9b-v2:free
```
- **特点**: NVIDIA优化模型

### Arcee AI系列
```
arcee-ai/trinity-large-preview:free
arcee-ai/trinity-mini:free
```
- **上下文长度**: 131K tokens

### LiquidAI系列
```
liquid/lfm-2.5-1.2b-thinking:free
liquid/lfm-2.5-1.2b-instruct:free
```
- **参数**: 1.2B
- **特点**: 轻量级

### Z.ai系列
```
z-ai/glm-4.5-air:free
```
- **上下文长度**: 131K tokens

### OpenAI系列
```
openai/gpt-oss-120b:free
openai/gpt-oss-20b:free
```
- **特点**: OpenAI开源模型

### Venice系列
```
cognitivecomputations/dolphin-mistral-24b-venice-edition:free
```
- **特点**: 无审查版本

## 使用方法

### 1. 设置环境变量
```bash
export OPENROUTER_API_KEY='your-api-key'
```

### 2. 在Agent配置中使用
```yaml
skill_chain:
  - skill: processing.analyze_topic
    config:
      llm_provider: openrouter
      model: qwen/qwen3-next-80b-a3b-instruct:free  # 推荐模型
      input_data: rss_data
      count: 3
      target_audience: 职场新人
      platform: xiaohongshu
    output_key: selected_topics
```

### 3. 在代码中使用
```python
from app.core.llm_service import OpenRouterProvider

provider = OpenRouterProvider(
    api_key='your-api-key',
    model='qwen/qwen3-next-80b-a3b-instruct:free'
)

result = await provider.generate(
    prompt="你的提示词",
    max_tokens=1000,
    temperature=0.7
)
```

## 选择建议

### 按用途选择

| 用途 | 推荐模型 | 原因 |
|------|---------|------|
| 主题分析 | qwen/qwen3-next-80b-a3b-instruct:free | 中文优秀，性能强大 |
| 内容生成 | qwen/qwen3-next-80b-a3b-instruct:free | 质量高，创意性好 |
| 代码生成 | qwen/qwen3-coder:free | 代码专用，能力强 |
| 快速响应 | google/gemma-3n-e4b-it:free | 轻量级，速度快 |
| 自动选择 | openrouter/free | 智能路由，省心 |

### 按语言选择

| 语言 | 推荐模型 | 原因 |
|------|---------|------|
| 中文 | qwen/qwen3-next-80b-a3b-instruct:free | 阿里巴巴，中文优化 |
| 英文 | google/gemma-3n-e4b-it:free | Google，英文优秀 |
| 多语言 | openrouter/free | 自动适配 |

## 注意事项

1. **速率限制**: 免费模型有速率限制，但足够日常使用
2. **上下文长度**: 不同模型上下文长度不同，注意选择
3. **模型可用性**: 模型可能随时变化，建议定期检查
4. **API密钥**: 妥善保管API密钥，不要泄露

## 获取最新模型列表

运行以下命令获取最新的免费模型列表：

```python
import asyncio
import httpx

async def get_free_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        models = response.json()['data']
        free_models = [
            m['id'] for m in models 
            if float(m['pricing']['prompt']) == 0 
            and float(m['pricing']['completion']) == 0
        ]
        print(f"免费模型: {free_models}")

asyncio.run(get_free_models())
```

## 相关文档

- [OpenRouter官网](https://openrouter.ai/)
- [OpenRouter文档](https://openrouter.ai/docs)
- [模型列表](https://openrouter.ai/models)
