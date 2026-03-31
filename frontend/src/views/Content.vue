<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">内容管理</h1>
      <p class="page-subtitle">妙笔生花，文不加点</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar mb-lg">
      <el-select v-model="filterAgent" placeholder="全部Agent" clearable style="width: 200px">
        <el-option label="全部Agent" value="" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 150px">
        <el-option label="全部状态" value="" />
        <el-option label="待审核" value="pending_review" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已发布" value="published" />
      </el-select>
      <el-button @click="loadContent">刷新</el-button>
    </div>

    <!-- 内容列表 -->
    <div v-loading="loading" class="content-list">
      <el-empty v-if="!loading && contentList.length === 0" description="暂无内容" />

      <div v-for="item in contentList" :key="item.id" class="content-card mb-md">
        <!-- 卡片头部 -->
        <div class="content-header">
          <div class="content-meta">
            <span class="agent-tag">{{ item.agent_name || item.agent_id }}</span>
            <span class="status-tag" :class="getStatusClass(item.status)">{{ getStatusText(item.status) }}</span>
            <span v-if="item.review_status" class="review-tag" :class="item.review_status">
              审核: {{ getReviewStatusText(item.review_status) }}
            </span>
            <span class="time-tag">{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="content-actions">
            <el-button size="small" @click="viewContent(item)">查看</el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="publishContent(item)"
              :disabled="!canPublish(item)"
            >
              发布
            </el-button>
            <el-button size="small" type="danger" @click="deleteContent(item)">删除</el-button>
          </div>
        </div>

        <!-- 内容预览 -->
        <div class="content-preview">
          <h3 class="content-title">{{ item.title || '无标题' }}</h3>
          <div class="content-body">{{ truncate(item.content, 200) }}</div>
          <div v-if="item.image_paths" class="content-images">
            <div
              v-for="(img, idx) in parseImages(item.image_paths).slice(0, 3)"
              :key="idx"
              class="preview-image-wrapper"
            >
              <img :src="getImageUrl(img)" :alt="`图片${idx + 1}`" class="preview-image" />
            </div>
            <div v-if="parseImages(item.image_paths).length > 3" class="more-images">
              +{{ parseImages(item.image_paths).length - 3 }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看内容对话框 -->
    <el-dialog v-model="viewDialog" title="内容详情" width="80%" top="5vh">
      <div v-if="currentContent" class="content-detail">
        <h2 class="detail-title">{{ currentContent.title || '无标题' }}</h2>
        <div class="detail-meta">
          <span>Agent: {{ currentContent.agent_name || currentContent.agent_id }}</span>
          <span>创建时间: {{ currentContent.created_at }}</span>
          <span v-if="currentContent.platform">平台: {{ currentContent.platform }}</span>
        </div>
        <div v-if="currentContent.tags && currentContent.tags.length > 0" class="detail-tags">
          <el-tag v-for="tag in currentContent.tags" :key="tag" type="info" class="tag-item">#{{ tag }}</el-tag>
        </div>
        <div class="detail-content">{{ currentContent.content }}</div>
        <div v-if="currentContent.image_paths" class="detail-images">
          <h4>图片 ({{ parseImages(currentContent.image_paths).length }}张)</h4>
          <div class="image-grid">
            <div
              v-for="(img, idx) in parseImages(currentContent.image_paths)"
              :key="idx"
              class="image-card"
            >
              <img :src="getImageUrl(img)" :alt="`图片${idx + 1}`" class="detail-image" />
              <div class="image-path">{{ img.split('/').pop() }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 发布对话框 -->
    <el-dialog v-model="publishDialog" title="发布到平台" width="500px">
      <div v-if="publishItem" class="publish-form">
        <el-form label-width="100px">
          <el-form-item label="内容标题">
            <div class="publish-title">{{ publishItem.title || '无标题' }}</div>
          </el-form-item>

          <el-form-item label="发布平台">
            <el-tag>{{ publishItem.platform || 'xiaohongshu' }}</el-tag>
          </el-form-item>

          <el-form-item label="发布账号">
            <div v-if="publishAccount" class="account-info">
              <span class="account-name">{{ publishAccount.name }}</span>
              <span v-if="publishAccount.status === 'online'" class="account-status online">✓ 在线</span>
              <span v-else class="account-status offline">✗ 离线</span>
              <span v-if="!publishAccount.hasCookie" class="account-status warning">(未登录)</span>
            </div>
            <div v-else class="account-info error">
              未配置账号，请在 Agent 配置中绑定账号
            </div>
          </el-form-item>

          <el-form-item label="调试模式">
            <el-switch v-model="headlessMode" active-text="显示浏览器" inactive-text="隐藏浏览器" />
            <div class="form-hint">首次发布建议显示浏览器，观察发布过程</div>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="publishDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmPublish" :loading="publishing" :disabled="!publishAccount || !publishAccount.hasCookie">
            {{ publishing ? '发布中...' : '确认发布' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { drafts, accounts } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const contentList = ref([])
const filterAgent = ref('')
const filterStatus = ref('')
const viewDialog = ref(false)
const currentContent = ref(null)

// 发布相关
const publishDialog = ref(false)
const publishItem = ref(null)
const publishAccount = ref(null)
const publishing = ref(false)
const headlessMode = ref(false)

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = (now - date) / 1000

  if (diff < 60) return `${Math.floor(diff)}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const parseImages = (imagePaths) => {
  if (!imagePaths) return []
  return imagePaths.split(',').filter(p => p.trim())
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '待发布',
    'pending_review': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'published': '已发布',
    'failed': '发布失败',
    'draft': '草稿'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const classMap = {
    'pending': 'warning',
    'pending_review': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'published': 'success',
    'failed': 'danger',
    'draft': 'info'
  }
  return classMap[status] || ''
}

const getReviewStatusText = (status) => {
  const statusMap = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝'
  }
  return statusMap[status] || status
}

const canPublish = (item) => {
  return item.review_status === 'approved'
}

// 获取图片URL
const getImageUrl = (imgPath) => {
  if (!imgPath) return ''
  if (imgPath.startsWith('http')) return imgPath
  // 如果是相对路径，添加后端地址
  return `http://localhost:8000/static/${imgPath.replace(/^data\//, '')}`
}

const loadContent = async () => {
  loading.value = true
  try {
    const data = await drafts.getDrafts()
    contentList.value = data.items || data || []
    console.log('Loaded content:', contentList.value)
  } catch (error) {
    console.error('Load content error:', error)
    ElMessage.error('加载内容失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const viewContent = (item) => {
  currentContent.value = item
  viewDialog.value = true
}

const publishContent = async (item) => {
  // 检查审核状态
  if (!item.review_status) {
    ElMessage.warning('该内容尚未审核，请先在审核页面进行审核')
    return
  }
  if (item.review_status === 'pending') {
    ElMessage.warning('该内容待审核中，请等待审核通过后再发布')
    return
  }
  if (item.review_status === 'rejected') {
    ElMessage.warning('该内容已被拒绝，无法发布')
    return
  }

  try {
    // 从 Agent 配置获取账号
    const agentResponse = await fetch(`http://localhost:8000/api/agents/${item.agent_id}`)
    const agentData = await agentResponse.json()
    
    if (!agentData.account_id) {
      ElMessage.warning('该 Agent 未配置账号，请在 Agent 配置中绑定账号')
      return
    }

    // 获取账号信息
    const accountResponse = await fetch(`http://localhost:8000/api/accounts/${agentData.account_id}`)
    if (!accountResponse.ok) {
      ElMessage.warning('账号不存在，请检查 Agent 配置')
      return
    }
    
    publishAccount.value = await accountResponse.json()

    // 设置发布项
    publishItem.value = item
    headlessMode.value = false
    publishDialog.value = true

  } catch (error) {
    console.error('Load account error:', error)
    ElMessage.error('加载账号失败: ' + error.message)
  }
}

const confirmPublish = async () => {
  if (!publishAccount.value || !publishAccount.value.hasCookie) {
    ElMessage.error('账号未登录，请先在账户管理页面扫码登录')
    return
  }

  publishing.value = true

  try {
    // 调用后端发布API
    const response = await fetch('http://localhost:8000/api/publish/xiaohongshu', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: publishItem.value.title || '无标题',
        content: publishItem.value.content,
        images: parseImages(publishItem.value.image_paths || ''),
        account_id: publishAccount.value.id,
        platform: publishItem.value.platform,
        draft_id: publishItem.value.id,
        topics: publishItem.value.tags || [],
        headless: !headlessMode.value
      })
    })

    const result = await response.json()

    if (result.success || result.message) {
      ElMessage.success(result.message || '发布成功')
      publishDialog.value = false
      await loadContent()
    } else {
      const errorMsg = result.error || '发布失败'
      ElMessage.error(`${publishAccount.value.name}: ${errorMsg}`)
    }

  } catch (error) {
    console.error('Publish error:', error)
    ElMessage.error('发布失败: ' + error.message)
  } finally {
    publishing.value = false
  }
}

const deleteContent = async (item) => {
  try {
    await ElMessageBox.confirm('确认删除此内容？', '提示', {
      type: 'warning'
    })

    await drafts.deleteDraft(item.id)
    ElMessage.success('删除成功')
    await loadContent()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

onMounted(() => {
  loadContent()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.content-list {
  min-height: 400px;
}

.content-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s;
}

.content-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.content-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.agent-tag {
  padding: 4px 12px;
  background: var(--el-color-primary);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.warning {
  background: var(--el-color-warning);
  color: white;
}

.status-tag.success {
  background: var(--el-color-success);
  color: white;
}

.status-tag.danger {
  background: var(--el-color-danger);
  color: white;
}

.status-tag.info {
  background: var(--el-color-info);
  color: white;
}

.status-tag.pending {
  background: var(--el-color-warning);
  color: white;
}

.status-tag.pending_review {
  background: var(--el-color-warning);
  color: white;
}

.status-tag.approved {
  background: var(--el-color-success);
  color: white;
}

.status-tag.rejected {
  background: var(--el-color-danger);
  color: white;
}

.status-tag.published {
  background: var(--el-color-success);
  color: white;
}

.status-tag.failed {
  background: var(--el-color-danger);
  color: white;
}

.review-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.review-tag.pending {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #e6a23c;
}

.review-tag.approved {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #67c23a;
}

.review-tag.rejected {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #f56c6c;
}

.content-actions .el-button.is-disabled {
  background-color: #c0c4cc !important;
  border-color: #c0c4cc !important;
  color: #ffffff !important;
  cursor: not-allowed;
}

.time-tag {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.content-preview {
  margin-top: 1rem;
}

.content-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: var(--el-text-color-primary);
}

.content-body {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  white-space: pre-wrap;
}

.content-images {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.preview-image-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-images {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 4px;
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color);
  font-size: 12px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.content-detail {
  padding: 1rem;
}

.detail-title {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
}

.detail-meta {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.detail-tags {
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  font-size: 13px;
}

.detail-content {
  line-height: 1.8;
  white-space: pre-wrap;
  margin-bottom: 2rem;
}

.detail-images h4 {
  margin: 0 0 1rem 0;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.image-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.detail-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.image-path {
  padding: 0.5rem;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 发布表单样式 */
.publish-form {
  padding: 1rem 0;
}

.publish-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.account-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-name {
  font-size: 14px;
  font-weight: 500;
}

.account-status {
  font-size: 12px;
}

.account-status.online {
  color: #67c23a;
}

.account-status.offline {
  color: #f56c6c;
}

.account-status.warning {
  color: #e6a23c;
}

.account-info.error {
  color: #f56c6c;
}

.form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
