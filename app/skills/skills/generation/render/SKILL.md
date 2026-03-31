---
name: generation.render
description: 将文本内容渲染为平台图文卡片
version: "1.0.0"
author: "Agent Matrix"
category: "generation"

# Skill 配置参数
inputs:
  title:
    type: string
    required: true
    description: "标题文本"

  content:
    type: string
    required: true
    description: "正文内容"

  platform:
    type: string
    required: false
    default: "xiaohongshu"
    description: "目标平台 (xiaohongshu, douyin)"

  template:
    type: string
    required: false
    default: "minimal"
    description: "模板名称"

  max_length:
    type: integer
    required: false
    default: 500
    description: "单张最大字数（超过自动分页）"

  split_long:
    type: boolean
    required: false
    default: true
    description: "是否自动分割长文"

  output_dir:
    type: string
    required: false
    default: "data/images"
    description: "输出目录"

# 输出参数
outputs:
  rendered_images:
    type: array
    description: "生成的图片路径列表"

  total_pages:
    type: integer
    description: "总页数"

# 使用示例
examples:
  - name: "渲染小红书图文"
    input:
      title: "禅修的智慧"
      content: "禅修的核心智慧在于..."
      platform: "xiaohongshu"
      template: "zen"
    output:
      rendered_images: ["data/images/20250226/zen_1.png"]
      total_pages: 1

# 依赖
dependencies:
  - Pillow>=10.2.0
  - Jinja2>=3.1.3
  - playwright>=1.41.0
---
