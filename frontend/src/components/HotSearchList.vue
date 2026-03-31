<template>
  <div class="hot-search-list">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else-if="!data || data.length === 0"
      description="暂无数据"
    />

    <!-- 热搜列表 -->
    <el-table
      v-else
      :data="displayData"
      stripe
      style="width: 100%"
      class="hot-table"
    >
      <!-- 排名 -->
      <el-table-column label="排名" width="80" align="center">
        <template #default="scope">
          <div
            class="rank-badge"
            :class="`rank-${scope.row.rank}`"
          >
            {{ scope.row.rank }}
          </div>
        </template>
      </el-table-column>

      <!-- 标题 -->
      <el-table-column label="标题" min-width="300">
        <template #default="scope">
          <div
            class="title-cell"
            :class="{ 'is-top': scope.row.is_top }"
            @click="openUrl(scope.row.url)"
          >
            <el-tag v-if="scope.row.is_top" size="small" type="danger" class="top-tag">
              置顶
            </el-tag>
            <span class="title-text">{{ scope.row.title }}</span>
          </div>
        </template>
      </el-table-column>

      <!-- 热度 -->
      <el-table-column label="热度" width="120" align="right">
        <template #default="scope">
          <div v-if="scope.row.heat" class="heat-value">
            <el-icon><View /></el-icon>
            {{ formatHeat(scope.row.heat) }}
          </div>
          <span v-else class="no-heat">-</span>
        </template>
      </el-table-column>

      <!-- 标签 -->
      <el-table-column label="标签" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.tag" :type="getTagType(scope.row.tag)" size="small">
            {{ scope.row.tag }}
          </el-tag>
          <span v-else class="no-tag">-</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="120" align="center">
        <template #default="scope">
          <el-button
            size="small"
            type="primary"
            text
            @click="handleUseTopic(scope.row)"
          >
            使用话题
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['use-topic'])

// 显示的数据（默认全部显示，可以添加分页）
const displayData = computed(() => {
  return props.data || []
})

// 格式化热度值
const formatHeat = (value) => {
  if (!value) return ''

  const num = parseInt(value)
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'W'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return value.toString()
}

// 获取标签类型
const getTagType = (tag) => {
  const tagMap = {
    '热': 'danger',
    '新': 'success',
    '爆': 'danger',
    '沸': 'warning'
  }
  return tagMap[tag] || 'info'
}

// 打开链接
const openUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 使用话题
const handleUseTopic = (item) => {
  emit('use-topic', item)
}
</script>

<style scoped>
.hot-search-list {
  min-height: 300px;
}

.loading-container {
  padding: 20px;
}

.hot-table {
  font-size: 14px;
}

/* 排名徽章 */
.rank-badge {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #8b4513;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #666;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #daa06d 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.3);
}

/* 标题单元格 */
.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: color 0.2s;
}

.title-cell:hover {
  color: var(--el-color-primary);
}

.title-cell.is-top {
  font-weight: 600;
}

.top-tag {
  flex-shrink: 0;
}

.title-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 热度值 */
.heat-value {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  color: var(--el-color-warning);
  font-weight: 600;
}

.no-heat {
  color: var(--el-text-color-placeholder);
}

/* 标签 */
.no-tag {
  color: var(--el-text-color-placeholder);
}

/* 响应式 */
@media (max-width: 768px) {
  .hot-table {
    font-size: 12px;
  }

  .rank-badge {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
}
</style>
