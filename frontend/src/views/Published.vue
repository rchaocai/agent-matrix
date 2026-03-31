<template>
  <div class="page-container zen-fade-in">
    <div class="page-header">
      <h1 class="page-title">已发布内容</h1>
      <p class="page-subtitle">落笔生花，行云流水</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar mb-lg">
      <el-select v-model="filterAgent" placeholder="全部Agent" clearable style="width: 200px">
        <el-option label="全部Agent" value="" />
      </el-select>
      <el-select v-model="filterPlatform" placeholder="全部平台" clearable style="width: 150px">
        <el-option label="全部平台" value="" />
        <el-option label="小红书" value="xiaohongshu" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 280px"
      />
      <el-button @click="loadPublished">刷新</el-button>
    </div>

    <!-- 已发布内容列表 -->
    <div v-loading="loading" class="published-list">
      <el-empty v-if="!loading && publishedList.length === 0" description="暂无已发布内容" />

      <div v-for="item in publishedList" :key="item.id" class="published-card mb-md">
        <!-- 卡片头部 -->
        <div class="published-header">
          <div class="published-meta">
            <span class="agent-tag">{{ item.agent_name || item.agent_id }}</span>
            <span class="platform-tag">{{ getPlatformLabel(item.platform) }}</span>
            <span class="time-tag">{{ formatTime(item.published_at || item.created_at) }}</span>
          </div>
          <div class="published-actions">
            <el-tag v-if="item.status === 'success'" type="success">发布成功</el-tag>
            <el-tag v-else-if="item.status === 'failed'" type="danger">发布失败</el-tag>
            <el-tag v-else type="info">未知状态</el-tag>
          </div>
        </div>

        <!-- 内容预览 -->
        <div class="published-preview">
          <h3 class="published-title">{{ item.title || '无标题' }}</h3>
          <div class="published-body">{{ truncate(item.content, 150) }}</div>

          <!-- 图片预览 -->
          <div v-if="item.image_paths" class="published-images">
            <div
              v-for="(img, idx) in parseImages(item.image_paths).slice(0, 4)"
              :key="idx"
              class="preview-image-wrapper"
            >
              <img :src="getImageUrl(img)" :alt="`图片${idx + 1}`" class="preview-image" />
            </div>
            <div v-if="parseImages(item.image_paths).length > 4" class="more-images">
              +{{ parseImages(item.image_paths).length - 4 }}
            </div>
          </div>

          <!-- 发布详情 -->
          <div v-if="item.metadata" class="published-details">
            <div class="detail-item">
              <span class="detail-label">发布账号:</span>
              <span class="detail-value">{{ item.metadata.account_name || '-' }}</span>
            </div>
            <div v-if="item.metadata.post_url" class="detail-item">
              <span class="detail-label">文章链接:</span>
              <a :href="item.metadata.post_url" target="_blank" class="detail-link">
                {{ item.metadata.post_url }}
              </a>
            </div>
            <div v-if="item.metadata.error" class="detail-item error">
              <span class="detail-label">错误信息:</span>
              <span class="detail-value">{{ item.metadata.error }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="viewDialog" title="发布详情" width="80%" top="5vh">
      <div v-if="currentItem" class="detail-content">
        <h2 class="detail-title">{{ currentItem.title || '无标题' }}</h2>
        <div class="detail-meta">
          <span>Agent: {{ currentItem.agent_name || currentItem.agent_id }}</span>
          <span>平台: {{ getPlatformLabel(currentItem.platform) }}</span>
          <span>发布时间: {{ currentItem.published_at || currentItem.created_at }}</span>
        </div>
        <div class="detail-body">{{ currentItem.content }}</div>
        <div v-if="currentItem.image_paths" class="detail-images">
          <h4>图片 ({{ parseImages(currentItem.image_paths).length }}张)</h4>
          <div class="image-grid">
            <div
              v-for="(img, idx) in parseImages(currentItem.image_paths)"
              :key="idx"
              class="image-card"
            >
              <img :src="getImageUrl(img)" :alt="`图片${idx + 1}`" class="detail-image" />
            </div>
          </div>
        </div>
        <div v-if="currentItem.metadata" class="detail-metadata">
          <h4>发布元数据</h4>
          <pre>{{ JSON.stringify(currentItem.metadata, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { drafts } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const publishedList = ref([])
const filterAgent = ref('')
const filterPlatform = ref('')
const dateRange = ref([])
const viewDialog = ref(false)
const currentItem = ref(null)

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const parseImages = (imagePaths) => {
  if (!imagePaths) return []
  return imagePaths.split(',').filter(p => p.trim())
}

const getPlatformLabel = (platform) => {
  const platformMap = {
    'xiaohongshu': '小红书',
    'default': '未知平台'
  }
  return platformMap[platform] || platform
}

const getImageUrl = (imgPath) => {
  if (!imgPath) return ''
  if (imgPath.startsWith('http')) return imgPath
  return `http://localhost:8000/static/${imgPath.replace(/^data\//, '')}`
}

const loadPublished = async () => {
  loading.value = true
  try {
    const data = await drafts.getDrafts()
    // 筛选已发布的内容
    publishedList.value = (data.items || data || [])
      .filter(item => item.status === 'published' || item.metadata?.published === true)
    console.log('Loaded published content:', publishedList.value.length)
  } catch (error) {
    console.error('Load published error:', error)
    ElMessage.error('加载已发布内容失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPublished()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.published-list {
  min-height: 400px;
}

.published-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s;
}

.published-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.published-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.published-meta {
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

.platform-tag {
  padding: 4px 12px;
  background: var(--el-color-success);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.time-tag {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.published-preview {
  margin-top: 1rem;
}

.published-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: var(--el-text-color-primary);
}

.published-body {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  white-space: pre-wrap;
}

.published-images {
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

.published-details {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--el-border-color);
}

.detail-item {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 13px;
}

.detail-label {
  color: var(--el-text-color-secondary);
  min-width: 80px;
}

.detail-value {
  color: var(--el-text-color-primary);
}

.detail-link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.detail-link:hover {
  text-decoration: underline;
}

.detail-item.error {
  color: var(--el-color-danger);
}

/* 详情对话框 */
.detail-content {
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
  flex-wrap: wrap;
}

.detail-body {
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

.detail-metadata {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.detail-metadata h4 {
  margin: 0 0 1rem 0;
}

.detail-metadata pre {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-primary);
  overflow-x: auto;
}
</style>
