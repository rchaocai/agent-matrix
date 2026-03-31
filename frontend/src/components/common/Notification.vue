<template>
  <teleport to="body">
    <transition name="notification">
      <div v-if="visible" class="notification" :class="`notification-${type}`">
        <div class="notification-icon">
          <component :is="iconComponent" />
        </div>
        <div class="notification-content">
          <div v-if="title" class="notification-title">{{ title }}</div>
          <div class="notification-message">{{ message }}</div>
        </div>
        <button class="notification-close" @click="close">
          <Close />
        </button>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
  InfoFilled,
  Close
} from '@element-plus/icons-vue'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'warning', 'error', 'info'].includes(value)
  },
  title: String,
  message: {
    type: String,
    required: true
  },
  duration: {
    type: Number,
    default: 3000
  }
})

const emit = defineEmits(['close'])

const visible = ref(false)

const iconComponent = computed(() => {
  const icons = {
    success: SuccessFilled,
    warning: WarningFilled,
    error: CircleCloseFilled,
    info: InfoFilled
  }
  return icons[props.type]
})

const close = () => {
  visible.value = false
  setTimeout(() => {
    emit('close')
  }, 300)
}

onMounted(() => {
  visible.value = true
  if (props.duration > 0) {
    setTimeout(close, props.duration)
  }
})
</script>

<style scoped>
.notification {
  position: fixed;
  top: 24px;
  right: 24px;
  min-width: 320px;
  max-width: 480px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  z-index: 9999;
  backdrop-filter: blur(10px);
}

.notification-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  font-size: 24px;
}

.notification-success {
  border-left: 4px solid #67c23a;
}

.notification-success .notification-icon {
  color: #67c23a;
}

.notification-warning {
  border-left: 4px solid #e6a23c;
}

.notification-warning .notification-icon {
  color: #e6a23c;
}

.notification-error {
  border-left: 4px solid #f56c6c;
}

.notification-error .notification-icon {
  color: #f56c6c;
}

.notification-info {
  border-left: 4px solid #909399;
}

.notification-info .notification-icon {
  color: #909399;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.notification-close {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.notification-close:hover {
  background: #f5f7fa;
  color: #606266;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
