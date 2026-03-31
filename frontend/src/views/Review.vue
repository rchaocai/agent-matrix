<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">内容审核</h1>
      <p class="page-subtitle">明察秋毫，见微知著</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar mb-lg">
      <div class="filter-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索内容..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
        />
        <el-select v-model="filterStatus" placeholder="全部状态" style="width: 120px">
          <el-option label="全部状态" value="" />
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-select v-model="filterRisk" placeholder="全部风险" style="width: 120px">
          <el-option label="全部风险" value="" />
          <el-option label="低风险" value="low" />
          <el-option label="中风险" value="medium" />
          <el-option label="高风险" value="high" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
        />
      </div>
      <div class="filter-right">
        <el-button @click="batchApprove" :disabled="selectedItems.length === 0">
          <span class="btn-icon">✓</span>
          批量通过
        </el-button>
        <el-button @click="batchReject" :disabled="selectedItems.length === 0">
          <span class="btn-icon">✗</span>
          批量拒绝
        </el-button>
      </div>
    </div>

    <!-- 审核记录列表 -->
    <div class="review-list">
      <div
        v-for="item in filteredReviews"
        :key="item.id"
        class="review-card"
        :class="{ 'selected': selectedItems.includes(item.id) }"
        @click="toggleSelect(item.id)"
      >
        <!-- 卡片头部 -->
        <div class="review-header">
          <div class="review-info">
            <div class="review-avatar">{{ item.avatar }}</div>
            <div>
              <div class="review-agent">{{ item.agentName }}</div>
              <div class="review-platform">
                <span v-if="item.platform === 'xiaohongshu'">📕 小红书</span>
                <span v-if="item.platform === 'douyin'">🎵 抖音</span>
              </div>
            </div>
          </div>
          <div class="review-status">
            <span v-if="item.status === 'pending'" class="status-tag warning">待审核</span>
            <span v-if="item.status === 'approved'" class="status-tag success">已通过</span>
            <span v-if="item.status === 'rejected'" class="status-tag danger">已拒绝</span>
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="review-content">
          <div class="review-title">{{ item.title }}</div>
          <div class="review-text">{{ item.content }}</div>
        </div>

        <!-- 卡片底部 -->
        <div class="review-footer">
          <div class="review-meta">
            <div class="meta-item">
              <span class="meta-label">敏感词:</span>
              <span class="meta-value" :class="getRiskClass(item.riskLevel)">
                {{ item.sensitiveWordCount }} 个
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">质量分:</span>
              <span class="meta-value" :class="getQualityClass(item.qualityScore)">
                {{ item.qualityScore }}
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">提交时间:</span>
              <span class="meta-value">{{ item.submitTime }}</span>
            </div>
          </div>
          <div class="review-actions">
            <el-button size="small" @click.stop="viewDetail(item)">查看详情</el-button>
            <el-button
              v-if="item.status === 'pending'"
              size="small"
              type="success"
              @click.stop="approve(item)"
            >
              通过
            </el-button>
            <el-button
              v-if="item.status === 'pending'"
              size="small"
              type="danger"
              @click.stop="reject(item)"
            >
              拒绝
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="zen-empty">
      <div class="zen-empty-icon">⏳</div>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredReviews.length === 0" class="zen-empty">
      <div class="zen-empty-icon">🛡️</div>
      <p>暂无审核记录</p>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailDrawer"
      title="审核详情"
      size="50%"
      class="review-drawer"
    >
      <div v-if="currentReview" class="detail-content">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h3 class="detail-title">基本信息</h3>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Agent名称</span>
              <span class="detail-value">{{ currentReview.agentName }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">发布平台</span>
              <span class="detail-value">{{ currentReview.platform === 'xiaohongshu' ? '小红书' : '抖音' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">提交时间</span>
              <span class="detail-value">{{ currentReview.submitTime }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">审核状态</span>
              <span class="detail-value">
                <span v-if="currentReview.status === 'pending'" class="status-tag warning">待审核</span>
                <span v-if="currentReview.status === 'approved'" class="status-tag success">已通过</span>
                <span v-if="currentReview.status === 'rejected'" class="status-tag danger">已拒绝</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 内容预览 -->
        <div class="detail-section">
          <h3 class="detail-title">内容预览</h3>
          <div class="content-preview">
            <div class="preview-field">
              <span class="field-label">标题</span>
              <div class="field-value">{{ currentReview.title }}</div>
            </div>
            <div class="preview-field">
              <span class="field-label">正文</span>
              <div class="field-value content-text">{{ currentReview.content }}</div>
            </div>
          </div>
        </div>

        <!-- 审核结果 -->
        <div class="detail-section">
          <h3 class="detail-title">审核结果</h3>
          <div class="review-results">
            <div class="result-card">
              <div class="result-header">
                <span class="result-icon">🚨</span>
                <span class="result-title">敏感词检测</span>
                <span class="result-badge" :class="getRiskClass(currentReview.riskLevel)">
                  {{ getRiskText(currentReview.riskLevel) }}
                </span>
              </div>
              <div v-if="currentReview.sensitiveWords && currentReview.sensitiveWords.length > 0" class="result-body">
                <div
                  v-for="(word, index) in currentReview.sensitiveWords"
                  :key="index"
                  class="sensitive-word-item"
                >
                  <span class="word-text">{{ typeof word === 'string' ? word : word.word }}</span>
                  <span v-if="typeof word !== 'string' && word.category" class="word-category">{{ word.category }}</span>
                </div>
              </div>
              <div v-else class="result-empty">
                <span class="empty-icon">✓</span>
                未检测到敏感词
              </div>
            </div>

            <div class="result-card">
              <div class="result-header">
                <span class="result-icon">📊</span>
                <span class="result-title">质量评分</span>
                <span class="result-badge" :class="getQualityClass(currentReview.qualityScore)">
                  {{ currentReview.qualityScore }}分
                </span>
              </div>
              <div class="result-body">
                <div class="score-item">
                  <span class="score-label">可读性</span>
                  <el-progress
                    :percentage="currentReview.scores.readability"
                    :color="getScoreColor(currentReview.scores.readability)"
                  />
                </div>
                <div class="score-item">
                  <span class="score-label">完整性</span>
                  <el-progress
                    :percentage="currentReview.scores.completeness"
                    :color="getScoreColor(currentReview.scores.completeness)"
                  />
                </div>
                <div class="score-item">
                  <span class="score-label">吸引力</span>
                  <el-progress
                    :percentage="currentReview.scores.attractiveness"
                    :color="getScoreColor(currentReview.scores.attractiveness)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="currentReview.status === 'pending'" class="detail-actions">
          <el-button @click="detailDrawer = false">取消</el-button>
          <el-button type="danger" @click="reject(currentReview)">拒绝</el-button>
          <el-button type="primary" @click="approve(currentReview)">通过</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { reviews } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// 数据加载状态
const loading = ref(false)

// 审核记录列表
const reviewsList = ref([])

// 选中的项目
const selectedItems = ref([])

// 详情抽屉
const detailDrawer = ref(false)
const currentReview = ref(null)

// 筛选条件
const searchQuery = ref('')
const filterStatus = ref('')
const filterRisk = ref('')
const dateRange = ref([])

// 加载审核记录
const loadReviews = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRisk.value) params.risk_level = filterRisk.value

    const data = await reviews.getReviews(params)
    reviewsList.value = data.map(review => ({
      ...review,
      agentName: review.agent_name || review.agent_id,
      avatar: '📝',
      title: review.title || '待审核内容',
      content: review.content || '内容预览...',
      platform: review.platform || 'xiaohongshu',
      riskLevel: review.risk_level,
      sensitiveWordCount: review.sensitive_word_count,
      sensitiveWords: review.sensitive_words || [],
      qualityScore: review.quality_score,
      scores: review.scores || { readability: 0, completeness: 0, attractiveness: 0 },
      submitTime: formatTime(review.created_at)
    }))
  } catch (error) {
    ElMessage.error('加载审核记录失败: ' + error.message)
    console.error('Load reviews error:', error)
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000 / 60) // 分钟差

  if (diff < 60) return `${diff}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  return `${Math.floor(diff / 1440)}天前`
}

// 组件挂载时加载数据
onMounted(() => {
  loadReviews()
})

// 过滤后的审核记录
const filteredReviews = computed(() => {
  return reviewsList.value.filter(item => {
    const matchSearch = !searchQuery.value ||
      item.title.includes(searchQuery.value) ||
      item.content.includes(searchQuery.value)
    const matchStatus = !filterStatus.value || item.status === filterStatus.value
    const matchRisk = !filterRisk.value || item.riskLevel === filterRisk.value

    return matchSearch && matchStatus && matchRisk
  })
})

// 切换选择
const toggleSelect = (id) => {
  const index = selectedItems.value.indexOf(id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(id)
  }
}

// 查看详情
const viewDetail = async (item) => {
  try {
    // 调用详情 API 获取完整内容
    const detail = await reviews.getReview(item.id)
    currentReview.value = {
      ...item,
      content: detail.content,
      title: detail.title
    }
    detailDrawer.value = true
  } catch (error) {
    ElMessage.error('加载详情失败: ' + error.message)
  }
}

// 通过审核
const approve = async (item) => {
  try {
    await ElMessageBox.confirm('确认通过该内容？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'success'
    })

    await reviews.approveReview(item.id)
    item.status = 'approved'
    ElMessage.success('已通过审核')
    detailDrawer.value = false
    await loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + error.message)
    }
  }
}

// 拒绝审核
const reject = async (item) => {
  try {
    await ElMessageBox.confirm('确认拒绝该内容？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await reviews.rejectReview(item.id)
    item.status = 'rejected'
    ElMessage.success('已拒绝审核')
    detailDrawer.value = false
    await loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + error.message)
    }
  }
}

// 批量通过
const batchApprove = async () => {
  try {
    await ElMessageBox.confirm(
      `确认通过选中的 ${selectedItems.value.length} 条内容？`,
      '批量通过',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success'
      }
    )

    await reviews.batchApprove(selectedItems.value)
    ElMessage.success('批量通过成功')
    selectedItems.value = []
    await loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + error.message)
    }
  }
}

// 批量拒绝
const batchReject = async () => {
  try {
    await ElMessageBox.confirm(
      `确认拒绝选中的 ${selectedItems.value.length} 条内容？`,
      '批量拒绝',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await reviews.batchReject(selectedItems.value)
    ElMessage.success('批量拒绝成功')
    selectedItems.value = []
    await loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + error.message)
    }
  }
}

// 获取风险等级样式
const getRiskClass = (level) => {
  const classes = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return classes[level] || ''
}

// 获取风险等级文本
const getRiskText = (level) => {
  const texts = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return texts[level] || ''
}

// 获取质量分样式
const getQualityClass = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-icon {
  font-size: 16px;
  margin-right: 6px;
}

/* 审核记录列表 */
.review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.review-card:hover {
  box-shadow: var(--shadow-hover);
}

.review-card.selected {
  border-color: var(--color-accent);
  background: var(--color-accent-light);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-divider);
}

.review-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.review-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.review-agent {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.review-platform {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.review-status {
  display: flex;
  align-items: center;
}

.status-tag {
  padding: 4px 12px;
  border-radius: var(--border-radius-small);
  font-size: 12px;
  font-weight: 500;
}

.status-tag.success {
  background: #f0f9ff;
  color: var(--color-success);
}

.status-tag.warning {
  background: #fef0f0;
  color: var(--color-warning);
}

.status-tag.danger {
  background: #fef0f0;
  color: var(--color-danger);
}

/* 审核内容 */
.review-content {
  margin-bottom: 16px;
}

.review-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.review-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 审核底部 */
.review-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--color-divider);
}

.review-meta {
  display: flex;
  gap: 20px;
}

.meta-item {
  font-size: 13px;
}

.meta-label {
  color: var(--color-text-secondary);
}

.meta-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

.meta-value.success {
  color: var(--color-success);
}

.meta-value.warning {
  color: var(--color-warning);
}

.meta-value.danger {
  color: var(--color-danger);
}

.review-actions {
  display: flex;
  gap: 8px;
}

/* 详情抽屉 */
.detail-content {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 32px;
}

.detail-title {
  font-family: var(--font-family-title);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-divider);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* 内容预览 */
.content-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.field-value {
  font-size: 14px;
  color: var(--color-text-primary);
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.field-value.content-text {
  white-space: pre-line;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
}

.field-value.content-text::-webkit-scrollbar {
  width: 6px;
}

.field-value.content-text::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: 3px;
}

.field-value.content-text::-webkit-scrollbar-thumb {
  background: var(--color-text-secondary);
  border-radius: 3px;
}

.field-value.content-text::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-primary);
}

/* 审核结果 */
.review-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
  padding: 16px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.result-icon {
  font-size: 20px;
}

.result-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.result-badge {
  padding: 4px 10px;
  border-radius: var(--border-radius-small);
  font-size: 12px;
  font-weight: 500;
}

.result-badge.success {
  background: #f0f9ff;
  color: var(--color-success);
}

.result-badge.warning {
  background: #fef0f0;
  color: var(--color-warning);
}

.result-badge.danger {
  background: #fef0f0;
  color: var(--color-danger);
}

.result-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sensitive-word-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: var(--border-radius-small);
}

.word-text {
  color: var(--color-danger);
  font-weight: 500;
}

.word-category {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.result-empty {
  text-align: center;
  padding: 20px;
  color: var(--color-success);
}

.empty-icon {
  font-size: 24px;
  margin-right: 8px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.score-label {
  width: 60px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--color-divider);
}

/* 响应式 */
@media (max-width: 600px) {
  .filter-bar {
    flex-direction: column;
    gap: 12px;
  }

  .filter-left {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-right {
    width: 100%;
    display: flex;
    gap: 8px;
  }

  .filter-right .el-button {
    flex: 1;
  }

  .review-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}

.mb-lg {
  margin-bottom: 32px;
}
</style>
