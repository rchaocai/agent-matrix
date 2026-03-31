<template>
  <div class="hot-search">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">热搜数据</h1>
      <p class="page-subtitle">实时追踪全网热点</p>
    </div>

    <!-- 日期标签栏 -->
    <el-card class="date-bar-card" shadow="never">
      <div class="date-bar">
        <el-scrollbar>
          <div class="date-labels">
            <el-radio-group
              v-model="selectedDate"
              @change="handleDateChange"
              class="date-radio-group"
            >
              <el-radio-button
                v-for="date in availableDates"
                :key="date"
                :label="date"
                class="date-radio-button"
              >
                {{ formatDate(date) }}
              </el-radio-button>
            </el-radio-group>
          </div>
        </el-scrollbar>
        <el-button
          :icon="Refresh"
          @click="handleRefresh"
          :loading="isRefreshing"
          class="refresh-btn"
          type="primary"
          :title="'点击刷新缓存，按住Shift键强制重新爬取'"
        >
          刷新
        </el-button>
      </div>
      <el-alert
        v-if="cacheStatus"
        :type="cacheStatus.has_cache ? 'success' : 'warning'"
        :closable="false"
        class="cache-alert"
      >
        <template #title>
          <span v-if="cacheStatus.has_cache">
            数据缓存时间: {{ cacheStatus.timestamp }}
          </span>
          <span v-else>
            当前日期暂无缓存数据，请点击"刷新"按钮
          </span>
        </template>
      </el-alert>
    </el-card>

    <!-- 平台Tab -->
    <el-card class="tabs-card" shadow="never">
      <el-tabs v-model="activePlatform" type="border-card" @tab-change="handleTabChange">
        <!-- 微博热搜 -->
        <el-tab-pane label="微博" name="weibo">
          <div class="tab-header">
            <div class="tab-info">
              <span class="tab-title">微博热搜</span>
              <el-tag v-if="hotData.weibo" size="small" type="info">
                共 {{ hotData.weibo.total || 0 }} 条
              </el-tag>
            </div>
            <div v-if="hotData.weibo && hotData.weibo.timestamp" class="tab-time">
              更新时间: {{ formatTime(hotData.weibo.timestamp) }}
            </div>
          </div>
          <HotSearchList
            :data="hotData.weibo?.items || []"
            :loading="loading.weibo"
            @use-topic="handleUseTopic"
          />
        </el-tab-pane>

        <!-- 百度热搜 -->
        <el-tab-pane label="百度" name="baidu">
          <div class="tab-header">
            <div class="tab-info">
              <span class="tab-title">百度热搜</span>
              <el-tag v-if="hotData.baidu" size="small" type="info">
                共 {{ hotData.baidu.total || 0 }} 条
              </el-tag>
            </div>
            <div v-if="hotData.baidu && hotData.baidu.timestamp" class="tab-time">
              更新时间: {{ formatTime(hotData.baidu.timestamp) }}
            </div>
          </div>
          <HotSearchList
            :data="hotData.baidu?.items || []"
            :loading="loading.baidu"
            @use-topic="handleUseTopic"
          />
        </el-tab-pane>

        <!-- 头条热搜 -->
        <el-tab-pane label="头条" name="toutiao">
          <div class="tab-header">
            <div class="tab-info">
              <span class="tab-title">头条热搜</span>
              <el-tag v-if="hotData.toutiao" size="small" type="info">
                共 {{ hotData.toutiao.total || 0 }} 条
              </el-tag>
            </div>
            <div v-if="hotData.toutiao && hotData.toutiao.timestamp" class="tab-time">
              更新时间: {{ formatTime(hotData.toutiao.timestamp) }}
            </div>
          </div>
          <HotSearchList
            :data="hotData.toutiao?.items || []"
            :loading="loading.toutiao"
            @use-topic="handleUseTopic"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { hotSearch } from '@/api'
import HotSearchList from '@/components/HotSearchList.vue'

// 数据状态
const selectedDate = ref('')
const availableDates = ref([])
const activePlatform = ref('weibo')
const isRefreshing = ref(false)

const hotData = reactive({
  weibo: null,
  baidu: null,
  toutiao: null
})

const loading = reactive({
  weibo: false,
  baidu: false,
  toutiao: false
})

// 缓存状态
const cacheStatus = computed(() => {
  const platformData = hotData[activePlatform.value]
  if (!platformData) return null

  return {
    has_cache: platformData.cached && platformData.items && platformData.items.length > 0,
    timestamp: platformData.timestamp ? formatTime(platformData.timestamp) : null
  }
})

// 格式化日期显示
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  // 重置时间为0点以便比较
  date.setHours(0, 0, 0, 0)
  today.setHours(0, 0, 0, 0)
  yesterday.setHours(0, 0, 0, 0)

  if (date.getTime() === today.getTime()) {
    return '今天'
  } else if (date.getTime() === yesterday.getTime()) {
    return '昨天'
  } else {
    // 返回 MM-DD 格式
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}-${day}`
  }
}

// 格式化时间显示
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

// 加载可用日期列表
const loadAvailableDates = async () => {
  try {
    const response = await hotSearch.getAvailableDates()
    availableDates.value = response.dates || []

    // 如果有可用日期，默认选择最新的
    if (availableDates.value.length > 0 && !selectedDate.value) {
      selectedDate.value = availableDates.value[0]
      await loadDateData(selectedDate.value)
    }
  } catch (error) {
    console.error('获取可用日期失败:', error)
    ElMessage.error('获取可用日期失败')
  }
}

// 加载指定日期的数据
const loadDateData = async (date) => {
  // 重置所有平台的加载状态
  loading.weibo = true
  loading.baidu = true
  loading.toutiao = true

  try {
    // 并发请求所有平台的数据
    const [weiboResult, baiduResult, toutiaoResult] = await Promise.allSettled([
      hotSearch.getHotSearchData({ date, sources: ['weibo'] }),
      hotSearch.getHotSearchData({ date, sources: ['baidu'] }),
      hotSearch.getHotSearchData({ date, sources: ['toutiao'] })
    ])

    // 更新微博数据
    if (weiboResult.status === 'fulfilled' && weiboResult.value) {
      hotData.weibo = weiboResult.value.sources?.weibo || null
    } else {
      hotData.weibo = null
    }

    // 更新百度数据
    if (baiduResult.status === 'fulfilled' && baiduResult.value) {
      hotData.baidu = baiduResult.value.sources?.baidu || null
    } else {
      hotData.baidu = null
    }

    // 更新头条数据
    if (toutiaoResult.status === 'fulfilled' && toutiaoResult.value) {
      hotData.toutiao = toutiaoResult.value.sources?.toutiao || null
    } else {
      hotData.toutiao = null
    }
  } catch (error) {
    console.error('加载热搜数据失败:', error)
    ElMessage.error('加载热搜数据失败')
  } finally {
    loading.weibo = false
    loading.baidu = false
    loading.toutiao = false
  }
}

// 日期切换处理
const handleDateChange = (newDate) => {
  if (newDate) {
    loadDateData(newDate)
  }
}

// Tab切换处理
const handleTabChange = (tabName) => {
  console.log('切换到平台:', tabName)
}

// 刷新当前日期的数据
const handleRefresh = async (event) => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期')
    return
  }

  // 检测是否按住Shift键（强制刷新）
  const isForceRefresh = event && event.shiftKey

  isRefreshing.value = true

  try {
    const today = new Date().toISOString().split('T')[0]
    const isToday = selectedDate.value === today

    // 强制刷新模式
    if (isForceRefresh) {
      if (!isToday) {
        ElMessage.warning('只能强制刷新今天的数据')
        return
      }

      ElMessage.info('正在强制重新爬取...')
      const response = await hotSearch.fetchHotSearch({
        sources: ['weibo', 'baidu', 'toutiao'],
        force: true
      })

      if (response.success) {
        ElMessage.success('强制刷新成功')
        await loadDateData(selectedDate.value)
        await loadAvailableDates()
      } else {
        ElMessage.error(response.message || '刷新失败')
      }
      return
    }

    // 普通刷新模式
    let shouldFetch = false

    if (isToday) {
      // 检查当前平台是否有缓存数据
      const currentData = hotData[activePlatform.value]
      if (!currentData || !currentData.cached || currentData.total === 0) {
        // 今天没有缓存数据，需要爬取
        shouldFetch = true
      } else {
        // 今天已有缓存，提示用户
        ElMessage.info('今天已爬取过，使用缓存数据')
      }
    } else {
      // 历史日期，不需要爬取
      ElMessage.info('历史数据无需重新爬取')
    }

    // 如果需要爬取
    if (shouldFetch) {
      ElMessage.info('正在获取最新热搜数据...')
      const response = await hotSearch.fetchHotSearch({
        sources: ['weibo', 'baidu', 'toutiao'],
        force: true
      })

      if (response.success) {
        ElMessage.success('刷新成功')
        await loadDateData(selectedDate.value)
        await loadAvailableDates()
      } else {
        ElMessage.error(response.message || '刷新失败')
      }
    } else {
      // 不需要爬取，直接重新加载缓存数据
      await loadDateData(selectedDate.value)
      ElMessage.success('已更新显示')
    }
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新失败')
  } finally {
    isRefreshing.value = false
  }
}

// 使用话题
const handleUseTopic = (item) => {
  console.log('使用话题:', item)
  ElMessage.success(`已选择话题: ${item.title}`)
  // TODO: 集成到内容生成功能
}

// 组件挂载时初始化
onMounted(async () => {
  await loadAvailableDates()
})
</script>

<style scoped>
.hot-search {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.date-bar-card {
  margin-bottom: 20px;
}

.date-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.date-labels {
  flex: 1;
}

.date-radio-group {
  display: flex;
  flex-wrap: nowrap;
}

.date-radio-button {
  flex-shrink: 0;
}

.refresh-btn {
  flex-shrink: 0;
}

.cache-alert {
  margin-top: 16px;
}

.tabs-card {
  margin-bottom: 20px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tab-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tab-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tab-time {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .hot-search {
    padding: 12px;
  }

  .date-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .refresh-btn {
    width: 100%;
  }

  .tab-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
