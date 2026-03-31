# Agent Matrix

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/rchaocai/agent-matrix?style=social)](https://github.com/rchaocai/agent-matrix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/rchaocai/agent-matrix?style=social)](https://github.com/rchaocai/agent-matrix/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/rchaocai/agent-matrix)](https://github.com/rchaocai/agent-matrix/issues)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI Built](https://img.shields.io/badge/AI%20Built-95%25-brightgreen.svg)](https://github.com/rchaocai/agent-matrix)

> AI驱动的内容矩阵管理系统，支持Agent自动生成内容并发布到小红书平台。

**🤖 本项目 95% 的代码由 AI 辅助完成，使用智谱 GLM-4.7 作为核心开发助手。**

## 🌟 已实现特性

### 核心功能
- **🤖 多Agent管理**: 支持创建和管理多个独立的Agent
- **📋 Agent Skills标准**: 遵循Anthropic Agent Skills开放标准
- **⚡ 渐进式披露**: 优化的三级Skill加载系统
- **⏰ 定时调度**: 基于APScheduler的定时任务调度
- **🧠 LLM集成**: 支持通义千问、DeepSeek、文心一言、OpenRouter

### 内容发布
- **📕 小红书自动发布**: 已实现基于Playwright的自动化发布
- **📝 草稿系统**: 支持保存草稿供手动发布
- **🎨 AI智能审核**: 基于AI的内容审核系统

### 热点数据采集
- **🔥 多平台热点数据**: 支持微博、百度、知乎三个平台的热点数据自动采集
- **📊 数据统计**: 完整的内容和数据统计功能

### 系统功能
- **👥 多账号管理**: 支持多个平台账号绑定
- **🌐 Web界面**: 现代化的前端管理界面
- **📖 API文档**: 完整的RESTful API文档

## 🚧 待扩展功能

- **📱 抖音自动发布**: 计划支持
- **🎬 视频号自动发布**: 计划支持
- **📲 更多平台**: 持续扩展中

## 快速开始

<details>
<summary>📦 安装依赖</summary>

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```
</details>

<details>
<summary>🔑 配置环境变量</summary>

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
# QIANWEN_API_KEY=your_qianwen_api_key_here
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
```
</details>

<details>
<summary>🗄️ 初始化数据库</summary>

```bash
python scripts/init_db.py
```
</details>

<details>
<summary>🚀 启动应用</summary>

```bash
# 启动后端
uvicorn app.main:app --reload --port 8000

# 启动前端（新开终端）
cd frontend
npm install
npm run dev
```
</details>

<details>
<summary>🌐 访问应用</summary>

- **API文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:5173
- **健康检查**: http://localhost:8000/health
</details>

## 项目结构

```
agent-matrix/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── core/                # 核心模块
│   │   ├── scheduler.py     # 任务调度
│   │   └── agent_manager.py # Agent管理
│   ├── models/              # 数据库模型
│   ├── agents/              # Agent实现
│   ├── skills/              # Skill插件系统
│   │   └── skills/          # Skill插件（Agent Skills标准）
│   └── api/routes/          # API路由
├── config/
│   ├── settings.yaml        # 全局配置
│   └── agents/              # Agent配置文件
└── data/                    # 数据目录
```

## Agent Skills标准

本项目完全遵循Anthropic Agent Skills开放标准：

```
skill-name/
├── SKILL.md      # 必需 - Skill元数据和指令
├── scripts/      # 可选 - 可执行脚本
├── references/   # 可选 - 参考文档
└── assets/       # 可选 - 静态资源
```

### 渐进式披露架构

- **Level 1**: 元数据 (~100 tokens) - 始终加载
- **Level 2**: 指令 (< 5000 tokens) - 触发时加载
- **Level 3**: 资源 - 按需动态加载

## 配置示例

### Agent配置

创建一个Agent配置文件 `config/agents/my_agent.yaml`:

```yaml
agent:
  id: "my_agent"
  name: "我的Agent"
  enabled: true

  schedule:
    cron: "0 9,12,18 * * *"

  persona:
    name: "AI助手"
    tone: "友好、专业"

  skill_chain:
    - skill: "collection.rss"
      config:
        url: "https://example.com/rss"
        max_items: 5

    - skill: "publishing.draft"
      config:
        platform: "xiaohongshu"
```

### LLM配置

在 `config/settings.yaml` 中配置LLM提供商:

```yaml
llm:
  default_provider: "qianwen"
  providers:
    qianwen:
      api_key: "${QIANWEN_API_KEY}"
      model: "qwen-plus"
```

## API端点

- `GET /` - API信息
- `GET /health` - 健康检查
- `GET /api/agents` - 列出所有Agent
- `GET /api/agents/{id}` - 获取Agent详情
- `POST /api/agents/{id}/run` - 手动触发Agent
- `GET /api/content` - 列出所有内容
- `GET /api/tasks` - 列出所有任务

## 开发指南

### 创建新的Skill

1. 在 `app/skills/skills/` 创建目录
2. 创建 `SKILL.md` 文件
3. 添加 `scripts/` 目录和可执行脚本

示例:
```bash
mkdir -p app/skills/skills/myskill/scripts
# 编辑 SKILL.md
# 添加 scripts/script.py
```

### 调试

```bash
# 启动开发服务器
uvicorn app.main:app --reload --log-level debug

# 查看日志
tail -f data/logs/app.log
```

## License

[MIT](LICENSE)

## 🤝 贡献

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

## 📮 联系方式

- **Issues**: [GitHub Issues](https://github.com/rchaocai/agent-matrix/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rchaocai/agent-matrix/discussions)

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star！

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Agent Skills 标准 & Claude AI
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Playwright](https://playwright.dev/) - 浏览器自动化工具

---

## 🤖 AI 辅助开发说明

本项目是一个**AI原生项目**，约 **95% 的代码由 AI 辅助完成**：

### 开发方式
- **核心AI助手**: 智谱 GLM-4.7 (智谱AI)
- **开发模式**: 人机协作，人类提供需求和方向，AI 负责实现
- **主要工作流**:
  1. 需求分析与设计（人工）
  2. 代码实现（AI 辅助）
  3. 代码审查与优化（人工 + AI）
  4. 测试与调试（AI 辅助）
  5. 文档编写（AI 辅助）

### AI 完成的主要工作
- ✅ 前后端完整代码实现
- ✅ Agent Skills 标准实现
- ✅ 数据库模型设计
- ✅ API 接口开发
- ✅ 自动化测试脚本
- ✅ 文档和 README
- ✅ 配置文件和示例

### 人类完成的主要工作
- 🎯 产品需求定义
- 🎯 架构设计决策
- 🎯 代码审查与质量把控
- 🎯 问题定位与方向调整
- 🎯 最终测试与部署

**这种AI辅助的开发模式大大提高了开发效率，让一个人也能快速完成复杂的全栈项目。**

---

**注意**: 本项目仅供学习和研究使用，请遵守相关平台的服务条款。
