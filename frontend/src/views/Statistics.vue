<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">数据统计</h1>
      <p class="page-subtitle">知彼知己，百战不殆</p>
    </div>

    <!-- 时间范围选择 -->
    <div class="time-selector mb-lg">
      <el-radio-group v-model="timeRange">
        <el-radio-button label="today">今日</el-radio-button>
        <el-radio-button label="week">本周</el-radio-button>
        <el-radio-button label="month">本月</el-radio-button>
        <el-radio-button label="custom">自定义</el-radio-button>
      </el-radio-group>
      <el-date-picker
        v-if="timeRange === 'custom'"
        v-model="customDateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="margin-left: 12px"
      />
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid grid-4 mb-lg">
      <div class="metric-card">
        <div class="metric-icon">📝</div>
        <div class="metric-content">
          <div class="metric-value">{{ metrics.totalPosts }}</div>
          <div class="metric-label">总发文数</div>
          <div class="metric-trend success">
            <span class="trend-icon">↑</span>
            <span>{{ metrics.postsGrowth }}%</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">👥</div>
        <div class="metric-content">
          <div class="metric-value">{{ formatNumber(metrics.totalFollowers) }}</div>
          <div class="metric-label">总粉丝数</div>
          <div class="metric-trend success">
            <span class="trend-icon">↑</span>
            <span>{{ metrics.followersGrowth }}%</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">❤️</div>
        <div class="metric-content">
          <div class="metric-value">{{ formatNumber(metrics.totalLikes) }}</div>
          <div class="metric-label">总互动量</div>
          <div class="metric-trend success">
            <span class="trend-icon">↑</span>
            <span>{{ metrics.likesGrowth }}%</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-content">
          <div class="metric-value">{{ metrics.avgQualityScore }}</div>
          <div class="metric-label">平均质量分</div>
          <div class="metric-trend" :class="metrics.qualityTrend > 0 ? 'success' : 'danger'">
            <span class="trend-icon">{{ metrics.qualityTrend > 0 ? '↑' : '↓' }}</span>
            <span>{{ Math.abs(metrics.qualityTrend) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid-2" style="gap: 24px; margin-bottom: 24px;">
      <!-- 发文趋势图 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">发文趋势</h3>
          <el-select v-model="postsChartType" size="small" style="width: 100px">
            <el-option label="数量" value="count" />
            <el-option label="互动" value="interaction" />
          </el-select>
        </div>
        <div ref="postsChartRef" class="chart-container" style="height: 300px;"></div>
      </div>

      <!-- Agent表现对比 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Agent表现对比</h3>
        </div>
        <div ref="agentChartRef" class="chart-container" style="height: 300px;"></div>
      </div>
    </div>

    <!-- 详细数据表格 -->
    <div class="data-card mb-lg">
      <div class="card-header">
        <h3 class="card-title">Agent详细数据</h3>
        <el-button size="small" @click="exportData">📥 导出数据</el-button>
      </div>

      <el-table :data="agentStats" stripe style="width: 100%">
        <el-table-column prop="name" label="Agent名称" width="180">
          <template #default="{ row }">
            <div class="agent-cell">
              <span class="agent-avatar">{{ row.avatar }}</span>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <span v-if="row.platform === 'xiaohongshu'">📕 小红书</span>
            <span v-if="row.platform === 'douyin'">🎵 抖音</span>
          </template>
        </el-table-column>
        <el-table-column prop="posts" label="发文数" sortable />
        <el-table-column prop="followers" label="粉丝数" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.followers) }}
          </template>
        </el-table-column>
        <el-table-column prop="likes" label="互动量" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.likes) }}
          </template>
        </el-table-column>
        <el-table-column prop="qualityScore" label="质量分" sortable>
          <template #default="{ row }">
            <span :class="getQualityClass(row.qualityScore)">
              {{ row.qualityScore }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="approvalRate" label="通过率" sortable>
          <template #default="{ row }">
            {{ row.approvalRate }}%
          </template>
        </el-table-column>
        <el-table-column prop="engagementRate" label="互动率" sortable>
          <template #default="{ row }">
            {{ row.engagementRate }}%
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 热门内容排行 -->
    <div class="data-card">
      <div class="card-header">
        <h3 class="card-title">热门内容 TOP 10</h3>
      </div>

      <div class="top-content-list">
        <div
          v-for="(item, index) in topContent"
          :key="item.id"
          class="content-item"
        >
          <div class="content-rank" :class="`rank-${index + 1}`">
            {{ index + 1 }}
          </div>
          <div class="content-avatar">{{ item.avatar }}</div>
          <div class="content-info">
            <div class="content-title">{{ item.title }}</div>
            <div class="content-agent">{{ item.agentName }}</div>
          </div>
          <div class="content-stats">
            <div class="stat-item">
              <span class="stat-icon">❤️</span>
              {{ formatNumber(item.likes) }}
            </div>
            <div class="stat-item">
              <span class="stat-icon">💬</span>
              {{ formatNumber(item.comments) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statistics } from '@/api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const timeRange = ref('today')
const customDateRange = ref([])
const postsChartRef = ref(null)
const agentChartRef = ref(null)

// 核心指标数据
const metrics = ref({
  totalPosts: 0,
  todayPublished: 0,
  totalFollowers: 0,
  totalLikes: 0,
  avgQualityScore: 0,
  postsGrowth: 0,
  followersGrowth: 0,
  likesGrowth: 0,
  qualityTrend: 0
})

// Agent统计数据
const agentStats = ref([])

// 热门内容
const topContent = ref([])

// 加载统计数据
const loadMetrics = async () => {
  try {
    const data = await statistics.getStatsOverview()
    metrics.value = data
  } catch (error) {
    ElMessage.error('加载统计数据失败: ' + error.message)
    console.error('Load metrics error:', error)
  }
}

// 加载Agent统计
const loadAgentStats = async () => {
  try {
    const data = await statistics.getAgentStats(10)
    agentStats.value = data
  } catch (error) {
    ElMessage.error('加载Agent统计失败: ' + error.message)
    console.error('Load agent stats error:', error)
  }
}

// 加载热门内容
const loadTopContent = async () => {
  try {
    const data = await statistics.getTopContent(10)
    topContent.value = data
  } catch (error) {
    ElMessage.error('加载热门内容失败: ' + error.message)
    console.error('Load top content error:', error)
  }
}

// 格式化数字
const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

// 获取质量分样式
const getQualityClass = (score) => {
  if (score >= 90) return 'quality-excellent'
  if (score >= 80) return 'quality-good'
  return 'quality-normal'
}

// 导出数据
const exportData = () => {
  ElMessage.success('数据导出成功')
}

// 初始化发文趋势图
const initPostsChart = async () => {
  if (!postsChartRef.value) return

  try {
    const data = await statistics.getPostTrend(7)

    const chart = echarts.init(postsChartRef.value)

    const option = {
      grid: {
        left: '3%',
        right: '5%',
        bottom: '10%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.labels.slice(-7),  // 最近7天
        axisLine: {
          lineStyle: { color: '#e8e0d5' }
        },
        axisLabel: {
          color: '#999'
        }
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: { color: '#e8e0d5', type: 'dashed' }
        },
        axisLabel: {
          color: '#999'
        }
      },
      series: [{
        data: data.data.slice(-7),  // 最近7天
        type: 'bar',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#a88f6e' },
            { offset: 1, color: '#c9b896' }
          ])
        },
        borderRadius: [6, 6, 0, 0]
      }]
    }

    chart.setOption(option)
    window.addEventListener('resize', () => chart.resize())
  } catch (error) {
    console.error('Init posts chart error:', error)
  }
}

// 初始化Agent表现对比图
const initAgentChart = async () => {
  if (!agentChartRef.value) return

  try {
    const data = await statistics.getAgentStats(6)

    const chart = echarts.init(agentChartRef.value)

    const option = {
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        splitLine: {
          lineStyle: { color: '#e8e0d5', type: 'dashed' }
        },
        axisLabel: {
          color: '#999'
        }
      },
      yAxis: {
        type: 'category',
        data: data.map(a => a.name),
        axisLine: {
          lineStyle: { color: '#e8e0d5' }
        },
        axisLabel: {
          color: '#666'
        }
      },
      series: [{
        type: 'bar',
        data: data.map(a => ({
          value: a.posts,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#a88f6e' },
              { offset: 1, color: '#c9b896' }
            ])
          }
        })),
        barWidth: '60%',
        itemStyle: {
          borderRadius: [0, 6, 6, 0]
        }
      }]
    }

    chart.setOption(option)
    window.addEventListener('resize', () => chart.resize())
  } catch (error) {
    console.error('Init agent chart error:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    loadMetrics(),
    loadAgentStats(),
    loadTopContent()
  ])
  await initPostsChart()
  await initAgentChart()
})
</script>

<style scoped>
.time-selector {
  display: flex;
  align-items: center;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

/* 指标卡片 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.metric-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-hover);
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-family: var(--font-family-title);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-accent);
  line-height: 1;
  margin-bottom: 6px;
}

.metric-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.metric-trend {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.metric-trend.success {
  color: var(--color-success);
}

.metric-trend.danger {
  color: var(--color-danger);
}

.trend-icon {
  font-weight: 600;
}

/* 图表卡片 */
.chart-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-family: var(--font-family-title);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.chart-container {
  position: relative;
}

/* 数据卡片 */
.data-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-divider);
}

.card-title {
  font-family: var(--font-family-title);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.agent-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-avatar {
  font-size: 18px;
}

.quality-excellent {
  color: var(--color-success);
  font-weight: 600;
}

.quality-good {
  color: var(--color-accent);
  font-weight: 600;
}

.quality-normal {
  color: var(--color-warning);
  font-weight: 600;
}

/* 热门内容 */
.top-content-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.content-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  transition: all 0.2s ease;
}

.content-item:hover {
  background: var(--color-accent-light);
}

.content-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.content-rank.rank-1 {
  background: #ffd700;
  color: white;
}

.content-rank.rank-2 {
  background: #c0c0c0;
  color: white;
}

.content-rank.rank-3 {
  background: #cd7f32;
  color: white;
}

.content-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.content-info {
  flex: 1;
  min-width: 0;
}

.content-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.content-agent {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.content-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.stat-icon {
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .grid-2 {
    grid-template-columns: 1fr;
  }
}

.mb-lg {
  margin-bottom: 32px;
}
</style>
