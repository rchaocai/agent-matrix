<template>
  <div class="dashboard">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-subtitle">运筹帷幄，决胜千里</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="navigateTo('/agents')">
          <div class="stat-icon" style="background: #409eff;">
            <el-icon :size="32"><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalAgents }}</div>
            <div class="stat-label">Agent总数</div>
            <el-tag v-if="stats.activeAgents > 0" size="small" type="success">
              {{ stats.activeAgents }} 个活跃中
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="navigateTo('/workspace/review')">
          <div class="stat-icon" style="background: #e6a23c;">
            <el-icon :size="32"><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pendingReview }}</div>
            <div class="stat-label">待审核内容</div>
            <el-tag v-if="stats.pendingReview > 0" size="small" type="danger">
              需要处理
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="navigateTo('/workspace/published')">
          <div class="stat-icon" style="background: #67c23a;">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.publishedToday }}</div>
            <div class="stat-label">今日已发布</div>
            <el-tag size="small" type="success">
              +{{ stats.publishedGrowth }}%
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="navigateTo('/workspace/generate')">
          <div class="stat-icon" style="background: #f56c6c;">
            <el-icon :size="32"><Edit /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalDrafts }}</div>
            <div class="stat-label">草稿箱</div>
            <el-tag v-if="stats.totalDrafts > 0" size="small" type="warning">
              待发布
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="actions-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">⚡ 快捷操作</span>
            </div>
          </template>

          <div class="quick-actions">
            <el-button type="primary" size="large" @click="navigateTo('/agents/new')">
              <el-icon><Plus /></el-icon>
              创建新Agent
            </el-button>

            <el-button type="success" size="large" @click="quickGenerate">
              <el-icon><Tools /></el-icon>
              快速发布内容
            </el-button>

            <el-button type="warning" size="large" @click="navigateTo('/accounts')">
              <el-icon><User /></el-icon>
              管理发布账号
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20" class="activity-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">🕐 最近活动</span>
              <span class="view-all-btn" @click="navigateTo('/statistics')">
                查看全部
                <el-icon><ArrowRight /></el-icon>
              </span>
            </div>
          </template>

          <el-table :data="stats.recentActivities" style="width: 100%">
            <el-table-column prop="time" label="时间" width="180">
              <template #default="scope">
                <span class="time-text">{{ scope.row.time }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="agent" label="Agent" width="150" />
            <el-table-column prop="action" label="操作" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <span
                  v-if="scope.row.link"
                  class="view-btn"
                  @click="navigateTo(scope.row.link)"
                >
                  查看
                </span>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="stats.recentActivities.length === 0" description="暂无活动记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Monitor, Clock, CircleCheck, Edit, Plus, Tools, User, Document, ArrowRight
} from '@element-plus/icons-vue'
import { dashboard } from '@/api'

const router = useRouter()

// 统计数据
const stats = ref({
  totalAgents: 0,
  activeAgents: 0,
  pendingReview: 0,
  publishedToday: 0,
  publishedGrowth: 0,
  totalDrafts: 0,
  recentActivities: []
})

// 加载统计数据
const loadStats = async () => {
  try {
    // 从后端 API 获取统计数据
    const data = await dashboard.getDashboardStats()
    
    stats.value.totalAgents = data.totalAgents || 0
    stats.value.activeAgents = data.activeAgents || 0
    stats.value.pendingReview = data.pendingReview || 0
    stats.value.publishedToday = data.todayPublished || 0
    stats.value.publishedGrowth = 0
    stats.value.totalDrafts = data.totalDrafts || 0

    // 获取最近活动
    const recentPosts = await dashboard.getRecentPosts(5)
    stats.value.recentActivities = recentPosts.map(post => ({
      time: post.time,
      agent: post.agentName,
      action: '发布内容',
      status: post.statusText,
      link: `/workspace/review?id=${post.id}`
    }))

  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 导航到指定页面
const navigateTo = (path) => {
  router.push(path)
}

// 快速生成内容
const quickGenerate = () => {
  router.push('/workspace/generate')
}

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    '已发布': 'success',
    '草稿': 'warning',
    '待审核': 'danger',
    '生成中': 'info'
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 96px;
  box-sizing: border-box;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-height: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.actions-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.quick-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.activity-row {
  margin-bottom: 20px;
}

.time-text {
  color: #909399;
  font-size: 13px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 500;
}

.view-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px 8px;
  border-radius: 4px;
}

.view-all-btn:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.view-all-btn .el-icon {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.view-all-btn:hover .el-icon {
  transform: translateX(2px);
}

.view-btn {
  display: inline-block;
  color: #409eff;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.view-btn:hover {
  background-color: #ecf5ff;
  color: #66b1ff;
}
</style>
