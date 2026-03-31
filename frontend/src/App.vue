<template>
  <AppError>
    <router-view />
  </AppError>
</template>

<script setup>
import AppError from './AppError.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
  color: #2c2c2c;
  background: #f0f2f5;
}

#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>