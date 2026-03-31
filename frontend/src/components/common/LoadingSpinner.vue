<template>
  <div class="loading-container">
    <div class="loading-spinner">
      <div class="spinner-circle"></div>
      <div class="spinner-circle"></div>
      <div class="spinner-circle"></div>
    </div>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-circle {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid transparent;
  animation: spin 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.spinner-circle:nth-child(1) {
  border-top-color: #667eea;
  animation-delay: 0s;
}

.spinner-circle:nth-child(2) {
  border-right-color: #764ba2;
  animation-delay: -0.5s;
}

.spinner-circle:nth-child(3) {
  border-bottom-color: #667eea;
  animation-delay: -1s;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 24px;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
