# Skill配置说明

## Skill类型

### 1. 脚本类Skill
需要指定`script`参数，通过命令行调用Python脚本。

**示例：collection.rss**
```yaml
skill_chain:
  - skill: collection.rss
    config:
      script: fetch_rss.py  # 必需：指定脚本文件名
      url: https://www.36kr.com/feed
      max_items: 10
    output_key: rss_data
```

**其他脚本类Skill：**
- `processing.clean` - 文本清洗
- `review.quality` - 质量评分
- `review.sensitive` - 敏感词检测
- `publishing.draft` - 保存草稿
- `publishing.publish` - 发布内容
- `conditional.save` - 条件保存

### 2. LLM类Skill
直接调用LLM服务，不需要指定script参数。

**示例：generation.text**
```yaml
skill_chain:
  - skill: generation.text
    config:
      prompt_template: |
        你是一位{role}，请创作内容：{content}
      variables:
        role: "科技博主"
        content: "AI发展趋势"
      max_tokens: 500
    output_key: generated_content
```

**其他LLM类Skill：**
- `generation.render` - 图文渲染
- `generation.template_generator` - 模板生成

### 3. Python类Skill
使用Python类实现，直接调用，不需要指定script参数。

**示例：processing.analyze_topic**
```yaml
skill_chain:
  - skill: processing.analyze_topic
    config:
      llm_provider: openrouter
      model: qwen/qwen3-next-80b-a3b-instruct:free
      input_data: rss_data
      count: 3
      target_audience: 职场新人
      platform: xiaohongshu
    output_key: selected_topics
```

**其他Python类Skill：**
- `collection.topic_discovery` - 主题发现

## 配置参数规则

### 必需参数
- **脚本类Skill**: 必须指定 `script` 参数
- **LLM类Skill**: 必须指定 `prompt_template` 参数
- **Python类Skill**: 根据具体Skill要求配置参数

### 通用参数
- `output_key`: 输出数据的键名（可选）

### 内部参数（不要在配置中使用）
以下参数会被系统自动处理，不要在config中指定：
- `script` - 仅脚本类Skill使用
- `variables` - LLM模板变量
- `agent_id` - Agent ID
- `condition` - 条件判断
- `true_action` / `false_action` - 条件分支
- `skip_on_failure` - 失败跳过
- `metadata` - 元数据
- `platform` - 平台信息
- `input` - 输入数据

## 常见错误

### 错误1: Skill xxx 缺少脚本配置
**原因**: 脚本类Skill没有指定 `script` 参数

**解决**: 在config中添加 `script` 参数
```yaml
config:
  script: fetch_rss.py  # 添加这一行
  url: https://example.com/feed
```

### 错误2: Skill xxx 脚本执行失败
**原因**: 脚本参数不正确或脚本本身有错误

**解决**: 
1. 检查脚本参数是否正确
2. 手动运行脚本测试：`python scripts/fetch_rss.py --url xxx`

### 错误3: 未采集到任何数据
**原因**: 采集类Skill没有获取到数据

**解决**:
1. 检查数据源URL是否可访问
2. 检查网络连接
3. 调整 `min_length` 参数

## 完整示例

### 流量提升Agent
```yaml
agent:
  id: traffic_boost_agent
  name: 流量提升Agent
  llm_provider: openrouter
  
  skill_chain:
    # 第一步：采集RSS数据（脚本类）
    - skill: collection.rss
      config:
        script: fetch_rss.py
        url: https://www.36kr.com/feed
        max_items: 10
        min_length: 100
      output_key: rss_data
    
    # 第二步：分析主题（Python类）
    - skill: processing.analyze_topic
      config:
        llm_provider: openrouter
        model: qwen/qwen3-next-80b-a3b-instruct:free
        input_data: rss_data
        count: 3
        target_audience: 职场新人
        platform: xiaohongshu
      output_key: selected_topics
    
    # 第三步：生成内容（LLM类）
    - skill: generation.text
      config:
        prompt_template: |
          请基于以下主题创作小红书内容：{topic}
          风格：实用干货
          受众：职场新人
        variables:
          topic: "{selected_topics.topics[0].topic}"
        max_tokens: 1000
      output_key: article_content
    
    # 第四步：质量审核（脚本类）
    - skill: review.quality
      config:
        script: score_quality.py
        min_score: 0.7
      output_key: quality_check
    
    # 第五步：条件保存（条件类）
    - skill: conditional.save
      config:
        condition: "quality_check.score >= 0.7"
        on_success:
          skill: publishing.draft
          config:
            script: save_draft.py
            platform: xiaohongshu
      output_key: save_result
```

## 参考文档
- [Agent Skills标准](../AGENT_SKILLS_STANDARD.md)
- [OpenRouter免费模型](./openrouter_free_models.md)
- [OpenRouter配置指南](./openrouter_guide.md)
