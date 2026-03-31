<template>
  <div class="skeleton-wrapper">
    <div v-for="i in rows" :key="i" class="skeleton-row" :style="{ width: getWidth(i) }"></div>
  </div>
</template>

<script setup>
const props = defineProps({
  rows: {
    type: Number,
    default: 3
  }
})

const getWidth = (index) => {
  // 最后一行短一些
  if (index === props.rows) return '60%'
  return '100%'
}
</script>

<style scoped>
.skeleton-wrapper {
  padding: 20px;
}

.skeleton-row {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s ease-in-out infinite;
  margin-bottom: 12px;
  border-radius: 4px;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
