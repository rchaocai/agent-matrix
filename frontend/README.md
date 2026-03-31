# 觉知矩阵 - 前端管理系统

AI驱动的内容矩阵管理系统的Web前端，采用禅意极简设计风格。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **UI组件库**: Element Plus
- **图表库**: ECharts
- **路由**: Vue Router
- **构建工具**: Vite
- **样式**: 禅意极简主题 CSS

## 功能页面

### 1. 仪表盘 (`/`)
- 核心指标卡片（总Agent数、今日发文、待审核、账号状态）
- 审核概览
- 最近发文列表
- 7日发文趋势图
- 热门Agent排行
- 系统状态监控

### 2. Agent管理 (`/agents`)
- Agent卡片网格展示
- 平台筛选（小红书、抖音）
- 状态筛选（开启、暂停）
- 搜索功能
- Agent启用/禁用切换
- Agent编辑、运行、数据查看
- 新建Agent入口

### 3. Agent编辑 (`/agents/new`, `/agents/:id/edit`)
- 基础信息配置
  - Agent名称
  - 平台选择（小红书、抖音）
  - 头像占位符预览
- 身份设定
  - 人设描述
  - 禁忌词配置
- 发文计划
  - 发文频率（每天、每周、自定义）
  - 发文时间配置
  - Cron表达式
- Skill配置
  - 采集Skill（本地语料、RSS、API）
  - 处理Skill（随机、顺序、权重）
  - 生成Skill（Prompt模板选择）
  - 审核Skill（严格、温和、免审）
  - 发布Skill（直接发布、存草稿）
- 实时预览
  - 内容卡片预览
  - 配图预览

### 4. 内容审核 (`/review`)
- 审核记录列表
- 多维度筛选
  - 状态（待审核、已通过、已拒绝）
  - 风险等级（低、中、高）
  - 时间范围
- 批量操作（批量通过、批量拒绝）
- 审核详情抽屉
  - 基本信息展示
  - 内容预览
  - 敏感词检测结果
  - 质量评分详情
  - 操作按钮

### 5. 账号管理 (`/accounts`)
- 账号卡片展示
- 平台图标区分
- 账号状态（在线/离线）
- 账号统计（粉丝数、发文数）
- 绑定Agent列表
- 绑定新账号
  - 平台选择
  - 登录方式（Cookie、扫码、短信）
  - Agent绑定
- 账号编辑、刷新、解绑

### 6. 数据统计 (`/statistics`)
- 时间范围选择
- 核心指标卡片
  - 总发文数及增长
  - 总粉丝数及增长
  - 总互动量及增长
  - 平均质量分及趋势
- 发文趋势图
- Agent表现对比图
- Agent详细数据表格
- 热门内容TOP 10

### 7. 系统设置 (`/settings`)
- 基础设置
  - 系统信息
  - 通用配置
  - 主题风格
- LLM配置
  - 默认提供商选择
  - API密钥配置
    - 通义千问
    - DeepSeek
    - 文心一言
  - 连接测试
- 审核规则
  - 敏感词检测配置
  - 质量评分规则
  - 自定义敏感词
- 通知设置
  - 通知渠道配置
  - 通知事件选择
- 关于
  - 项目简介
  - 技术栈展示

## 设计风格

### 禅意极简主题

**配色方案**:
- 背景色: `#faf7f2` (米白色，如宣纸)
- 强调色: `#a88f6e` (淡茶色)
- 文字色: `#2c2c2c` (深灰)
- 边框色: `#e8e0d5` (浅米灰)

**设计原则**:
- 留白充足，呼吸感强
- 圆角柔和（12px）
- 阴影轻盈
- 字体优雅（标题用楷体）
- 动画流畅自然

**字体**:
- 标题: `'STKaiti', 'KaiTi', serif` (楷体)
- 正文: `-apple-system, BlinkMacSystemFont, 'Inter', sans-serif`

## 安装与运行

### 环境要求

- Node.js >= 16.x
- npm >= 8.x 或 pnpm >= 7.x

### 安装依赖

```bash
cd frontend
npm install
# 或
pnpm install
```

### 开发模式

```bash
npm run dev
# 或
pnpm dev
```

访问: http://localhost:5173/zen-matrix-frontend

### 生产构建

```bash
npm run build
# 或
pnpm build
```

构建产物输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
# 或
pnpm preview
```

## 项目结构

```
frontend/
├── src/
│   ├── App.vue              # 主应用组件（侧边栏布局）
│   ├── main.js              # 应用入口
│   ├── router/
│   │   └── index.js         # 路由配置
│   ├── views/               # 页面组件
│   │   ├── Dashboard.vue    # 仪表盘
│   │   ├── Agents.vue       # Agent管理
│   │   ├── AgentEdit.vue    # Agent编辑
│   │   ├── Review.vue       # 内容审核
│   │   ├── Accounts.vue     # 账号管理
│   │   ├── Statistics.vue   # 数据统计
│   │   └── Settings.vue     # 系统设置
│   └── styles/              # 样式文件
│       ├── zen-theme.css    # 禅意主题变量
│       └── common.css       # 通用样式
├── index.html               # HTML模板
├── vite.config.js           # Vite配置
├── package.json             # 项目依赖
└── README.md                # 本文件
```

## 与后端API集成

当前前端使用模拟数据（mock data）。要连接实际后端API:

1. 在 `src/` 下创建 `api/` 目录
2. 创建API客户端:

```javascript
// src/api/client.js
import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000
})

export default client
```

3. 创建API服务模块:

```javascript
// src/api/agents.js
import client from './client'

export async function getAgents() {
  const response = await client.get('/agents')
  return response.data
}

export async function createAgent(data) {
  const response = await client.post('/agents', data)
  return response.data
}
```

4. 在组件中使用:

```javascript
import { getAgents } from '@/api/agents'

const agents = ref([])

onMounted(async () => {
  agents.value = await getAgents()
})
```

## 注意事项

1. **路由基础路径**: 当前配置为 `/zen-matrix-frontend`，可根据需要修改 `vite.config.js` 和 `router/index.js`

2. **Element Plus**: 按需导入已配置，如需添加更多组件:
   ```javascript
   // main.js
   import { ElButton, ElInput, ... } from 'element-plus'
   app.use(ElButton)
   app.use(ElInput)
   ```

3. **ECharts**: 图表容器需要明确的高度，否则无法渲染

4. **响应式设计**: 系统已适配移动端，在小屏幕上会自动调整布局

## 开发建议

1. 使用Vue DevTools浏览器插件进行调试
2. 遵循Vue 3 Composition API最佳实践
3. 保持组件单一职责
4. 合理使用computed、watch、watchEffect
5. 优先使用Element Plus组件而非自定义组件

## 待实现功能

- [ ] 实际API集成（替换mock数据）
- [ ] 用户认证/登录
- [ ] WebSocket实时更新
- [ ] 文件上传（图片、视频）
- [ ] 内容编辑器
- [ ] 更多图表类型
- [ ] 导出功能增强
- [ ] 国际化支持

## 许可证

MIT License
