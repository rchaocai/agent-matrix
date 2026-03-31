<template>
  <div class="stat-card">
    <div class="stat-icon">{{ icon }}</div>
    <div class="stat-content">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
      <div v-if="trend !== undefined" class="stat-trend" :class="trendClass">
        {{ trendText }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  label: {
    type: String,
    required: true
  },
  trend: {
    type: Number,
    default: undefined  // 正数增长，负数下降
  }
})

const trendClass = computed(() => ({
  'trend-up': props.trend > 0,
  'trend-down': props.trend < 0
}))

const trendText = computed(() => {
  if (props.trend === undefined) return ''
  const sign = props.trend > 0 ? '↑' : '↓'
  return `${sign} ${Math.abs(props.trend)}%`
})
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 40px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #2c2c2c;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.stat-trend {
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
}

.trend-up {
  color: #67c23a;
}

.trend-down {
  color: #f56c6c;
}
</style>
