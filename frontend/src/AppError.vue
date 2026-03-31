<template>
  <div v-if="error" class="error-boundary">
    <div class="error-content">
      <div class="error-icon">⚠️</div>
      <h2>出错了</h2>
      <p>{{ error.message }}</p>
      <div class="error-actions">
        <el-button @click="reload">刷新页面</el-button>
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const error = ref(null)
const router = useRouter()

onErrorCaptured((err) => {
  error.value = err
  console.error('Global error caught:', err)
  return false  // 阻止错误继续传播
})

const reload = () => {
  window.location.reload()
}

const goHome = () => {
  error.value = null
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #faf7f2;
}

.error-content {
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-content h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: #2c2c2c;
}

.error-content p {
  color: #666;
  margin-bottom: 24px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
