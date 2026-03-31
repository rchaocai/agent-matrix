<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <div class="logo-icon">☸️</div>
        <div class="logo-text">
          <h2 class="logo-title">觉知矩阵</h2>
          <p class="subtitle">智能内容自动化平台</p>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>

        <el-menu-item index="/agents">
          <el-icon><Monitor /></el-icon>
          <span>Agent管理</span>
        </el-menu-item>

        <el-sub-menu index="/workspace">
          <template #title>
            <el-icon><EditPen /></el-icon>
            <span>内容工作台</span>
          </template>
          <el-menu-item index="/workspace/generate">
            <el-icon><DocumentAdd /></el-icon>
            <span>生成</span>
          </el-menu-item>
          <el-menu-item index="/workspace/review">
            <el-icon><Select /></el-icon>
            <span>审核</span>
          </el-menu-item>
          <el-menu-item index="/workspace/published">
            <el-icon><View /></el-icon>
            <span>已发布</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/render">
          <el-icon><Picture /></el-icon>
          <span>图文渲染</span>
        </el-menu-item>

        <el-menu-item index="/statistics">
          <el-icon><TrendCharts /></el-icon>
          <span>数据统计</span>
        </el-menu-item>

        <el-menu-item index="/hot-search">
          <el-icon><TrendCharts /></el-icon>
          <span>热搜数据</span>
        </el-menu-item>

        <el-menu-item index="/accounts">
          <el-icon><User /></el-icon>
          <span>账户管理</span>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis, Monitor, EditPen, DocumentAdd, Select,
  View, User, TrendCharts, Picture, Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前激活的菜单项
const activeMenu = ref(route.path)

// 监听路由变化，更新激活菜单
watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
})

const handleMenuSelect = (index) => {
  console.log('菜单选择:', index)
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #ffffff;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #e5e7eb;
}

.logo {
  padding: 28px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f0f4ff 0%, #f5f0ff 100%);
}

.logo-icon {
  font-size: 36px;
  flex-shrink: 0;
}

.logo-text {
  flex: 1;
  min-width: 0;
}

.logo-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.3;
}

.logo .subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-menu {
  border-right: none;
  background-color: transparent;
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  font-size: 16px;
  display: flex;
  flex-direction: column;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 100%;
}

:deep(.el-menu) {
  background-color: transparent !important;
  border: none !important;
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-menu-item) {
  color: #4b5563;
  height: 50px;
  line-height: 50px;
  margin: 4px 16px !important;
  border-radius: 10px;
  padding: 0 16px !important;
  box-sizing: border-box;
}

:deep(.el-menu-item:hover) {
  background-color: #f3f4f6 !important;
  color: #1f2937;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  color: #fff;
}

:deep(.el-sub-menu) {
  margin-bottom: 4px;
}

:deep(.el-sub-menu__title) {
  color: #4b5563;
  height: 50px;
  line-height: 50px;
  margin: 4px 16px !important;
  border-radius: 10px;
  padding: 0 40px 0 16px !important;
  box-sizing: border-box;
  position: relative !important;
}

:deep(.el-sub-menu__title:hover) {
  background-color: #f3f4f6 !important;
  color: #1f2937;
}

:deep(.el-sub-menu .el-menu) {
  background-color: transparent !important;
  padding-top: 4px;
}

:deep(.el-sub-menu .el-menu-item) {
  padding: 0 16px 0 54px !important;
  background-color: transparent !important;
  color: #6b7280;
  margin: 3px 16px !important;
  border-radius: 10px;
  height: 44px;
  line-height: 44px;
  box-sizing: border-box;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  background-color: #f3f4f6 !important;
  color: #1f2937;
}

:deep(.el-sub-menu .el-menu-item.is-active) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  color: #fff;
}

:deep(.el-icon) {
  margin-right: 12px;
  font-size: 22px;
}

:deep(.el-sub-menu__icon-arrow) {
  position: absolute !important;
  right: 16px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  margin: 0 !important;
  width: 14px !important;
  height: 14px !important;
  color: #9ca3af;
  font-size: 14px;
}

:deep(.el-sub-menu__icon-arrow svg) {
  width: 14px !important;
  height: 14px !important;
  display: block !important;
}

:deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  transform: translateY(-50%) rotate(180deg) !important;
}

.main-content {
  background-color: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}
</style>
