---
name: publishing.publish
description: 将内容发布到小红书平台
version: "1.0.0"
author: "Agent Matrix"
category: "publishing"

# Skill 配置参数
inputs:
  title:
    type: string
    required: true
    description: "笔记标题"

  content:
    type: string
    required: true
    description: "笔记正文"

  images:
    type: array
    required: true
    description: "图片路径列表"

  platform:
    type: string
    required: true
    default: "xiaohongshu"
    description: "目标平台"

  account_id:
    type: string
    required: true
    description: "发布账号ID"

  topics:
    type: array
    required: false
    description: "话题标签列表"

  location:
    type: string
    required: false
    description: "地理位置"

  headless:
    type: boolean
    required: false
    default: true
    description: "是否使用无头模式"

# 输出参数
outputs:
  success:
    type: boolean
    description: "是否发布成功"

  post_url:
    type: string
    description: "发布后的笔记URL"

  error:
    type: string
    description: "错误信息（如果失败）"

# 使用示例
examples:
  - name: "发布笔记"
    input:
      title: "禅修的智慧"
      content: "禅修的核心智慧在于觉知当下..."
      images: ["data/images/20260226/test.png"]
      platform: "xiaohongshu"
      account_id: "xhs_account_1"
    output:
      success: true
      post_url: "https://www.xiaohongshu.com/explore/..."


# 依赖
dependencies:
  - playwright>=1.41.0
---
