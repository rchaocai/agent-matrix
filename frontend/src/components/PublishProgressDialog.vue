<template>
  <el-dialog
    v-model="visible"
    title="发布中"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="showClose"
  >
    <div class="publish-progress">
      <el-progress :percentage="progress" :status="status" />

      <div class="progress-steps">
        <div
          v-for="step in steps"
          :key="step.key"
          class="step-item"
          :class="{
            'active': step.key === currentStep,
            'completed': step.completed,
            'pending': !step.completed && step.key !== currentStep
          }"
        >
          <el-icon v-if="step.completed" class="step-icon"><SuccessFilled /></el-icon>
          <el-icon v-else-if="step.key === currentStep" class="step-icon is-loading"><Loading /></el-icon>
          <span v-else class="step-icon">{{ step.index + 1 }}</span>

          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>

      <div v-if="error" class="progress-error">
        <el-icon><WarningFilled /></el-icon>
        {{ error }}
      </div>
    </div>

    <template #footer v-if="showClose">
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { SuccessFilled, Loading, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  steps: {
    type: Array,
    default: () => []
  },
  currentStep: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const progress = computed(() => {
  if (!props.steps || props.steps.length === 0) return 0
  const completed = props.steps.filter(s => s.completed).length
  return Math.round((completed / props.steps.length) * 100)
})

const status = computed(() => {
  if (props.error) return 'exception'
  if (progress.value === 100) return 'success'
  return undefined
})

const showClose = computed(() => {
  return props.error || progress.value === 100
})

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.publish-progress {
  padding: 20px 0;
}

.progress-steps {
  margin-top: 30px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  font-size: 14px;
}

.step-item.active {
  color: #667eea;
  font-weight: 500;
}

.step-item.completed {
  color: #67c23a;
}

.step-item.pending {
  color: #999;
}

.step-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0f0f0;
  font-size: 12px;
}

.step-item.active .step-icon {
  background: #667eea;
  color: white;
}

.step-item.completed .step-icon {
  background: #67c23a;
  color: white;
}

.progress-error {
  margin-top: 20px;
  padding: 12px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
</style>
