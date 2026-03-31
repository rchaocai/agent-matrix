<template>
  <div class="gradient-card" :class="`gradient-${variant}`">
    <div class="gradient-overlay"></div>
    <div class="gradient-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
  }
})
</script>

<style scoped>
.gradient-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.gradient-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  transition: opacity 0.3s ease;
}

.gradient-card:hover .gradient-overlay {
  opacity: 0.15;
}

.gradient-content {
  position: relative;
  z-index: 1;
  padding: 24px;
}

.gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.gradient-success {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.gradient-warning {
  background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);
}

.gradient-danger {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
}

.gradient-info {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}
</style>
