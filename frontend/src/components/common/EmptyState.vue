<template>
  <div class="zen-empty">
    <div class="zen-empty-icon">{{ icon }}</div>
    <p class="zen-empty-title">{{ title }}</p>
    <p v-if="description" class="zen-empty-description">{{ description }}</p>
    <div v-if="$slots.actions" class="zen-empty-actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    default: '📭'
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.zen-empty {
  text-align: center;
  padding: 60px 20px;
}

.zen-empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.zen-empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-primary, #2c2c2c);
  margin-bottom: 8px;
}

.zen-empty-description {
  font-size: 14px;
  color: var(--el-text-color-secondary, #666);
  margin-bottom: 24px;
}

.zen-empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
