# OpenRouter API 配置指南

## 什么是OpenRouter？

OpenRouter是一个统一的LLM API平台，提供多个免费和付费的AI模型。

## 获取API密钥

### 步骤1：注册账号
访问：https://openrouter.ai/

### 步骤2：创建API密钥
1. 登录后，进入 Settings → Keys
2. 点击 "Create Key"
3. 复制生成的API密钥

### 步骤3：设置环境变量

```bash
# macOS/Linux
export OPENROUTER_API_KEY='sk-or-v1-xxxxxxxxxxxxx'

# 或添加到 ~/.zshrc 或 ~/.bashrc
echo 'export OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

## 免费模型列表

OpenRouter提供多个免费模型：

### 推荐模型

1. **Qwen3 Next 80B** (强烈推荐)
   ```
   qwen/qwen3-next-80b-a3b-instruct:free
   ```
   - 阿里巴巴通义实验室
   - 80B参数，性能强大
   - 中文支持优秀
   - 上下文长度：262K tokens
   - ✅ 已验证可用

2. **Qwen3 Coder 480B**
   ```
   qwen/qwen3-coder:free
   ```
   - 代码专用模型
   - 480B参数
   - 适合编程任务

3. **Gemma 3n 4B**
   ```
   google/gemma-3n-e4b-it:free
   ```
   - Google出品
   - 轻量级，响应快
   - 适合简单任务

4. **Free Models Router**
   ```
   openrouter/free
   ```
   - 自动选择最佳免费模型
   - 智能路由

## 测试功能

### 测试主题分析Skill

```bash
python test_topic_analysis.py
```

### 预期输出

```
🎯 主题分析结果
============================================================

1. 职场新人必知的5个潜规则
   评分: 0.95
   理由: 近期热点，与目标受众高度匹配
   关键词: 职场, 新人, 规则
   建议角度: 从新人角度出发，提供实用建议
   预期互动: 高

2. AI时代的学习方法
   评分: 0.90
   理由: AI是热门话题，学习类内容受欢迎
   关键词: AI, 学习, 效率
   建议角度: 结合实际案例，提供可操作的方法
   预期互动: 高

3. 如何提升个人影响力
   评分: 0.85
   理由: 职场发展类内容，受众关注度高
   关键词: 个人品牌, 影响力, 职场
   建议角度: 分享具体技巧和案例
   预期互动: 中高
```

## 在Agent中使用

### 配置示例

```yaml
skill_chain:
  # 第一步：采集数据
  - skill: collection.rss
    config:
      url: https://www.36kr.com/feed
      max_items: 10
    output_key: rss_data
  
  # 第二步：分析数据
  - skill: analysis.topic
    config:
      llm_provider: openrouter
      model: meta-llama/llama-3-8b-instruct:free
      input_data: rss_data
      count: 3
      target_audience: 职场新人
      platform: xiaohongshu
    output_key: selected_topics
  
  # 第三步：生成内容
  - skill: generation.text
    config:
      prompt_template: hot_topic_article
      variables:
        topic: "{selected_topics[0].topic}"
      max_tokens: 1000
    output_key: article_content
```

## 常见问题

### Q: 免费模型有限制吗？
A: 免费模型有速率限制（每分钟请求数），但对于主题分析场景完全够用。

### Q: 如何选择模型？
A: 推荐使用 `meta-llama/llama-3-8b-instruct:free`，性能和速度平衡最好。

### Q: API调用失败怎么办？
A: 检查：
1. API密钥是否正确
2. 网络连接是否正常
3. 模型名称是否正确

### Q: 可以使用付费模型吗？
A: 可以！OpenRouter支持付费模型，如GPT-4、Claude等。只需在配置中指定模型名称即可。

## 成本对比

| 提供商 | 模型 | 成本 | 推荐 |
|--------|------|------|------|
| OpenRouter | Llama 3 8B | 免费 | ⭐⭐⭐⭐⭐ |
| OpenRouter | GPT-4 | 付费 | ⭐⭐⭐⭐ |
| DeepSeek | DeepSeek Chat | 付费（便宜） | ⭐⭐⭐⭐ |
| OpenAI | GPT-4 | 付费（贵） | ⭐⭐⭐ |

## 技术支持

- OpenRouter文档：https://openrouter.ai/docs
- 问题反馈：在GitHub Issues中提交
