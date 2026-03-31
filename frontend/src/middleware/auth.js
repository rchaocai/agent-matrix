/**
 * 认证路由守卫
 */

import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

export function setupAuthGuard(router) {
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // 公开路由（不需要认证）
    const publicRoutes = ['/login', '/register']
    if (publicRoutes.includes(to.path)) {
      // 如果已登录，访问登录页时跳转到首页
      if (authStore.isAuthenticated && to.path === '/login') {
        next('/')
        return
      }
      next()
      return
    }

    // 需要认证的路由
    if (!authStore.isAuthenticated) {
      ElMessage.warning('请先登录')
      next('/login')
      return
    }

    // 检查Token是否快过期，自动刷新
    if (authStore.token && authStore.isTokenExpiringSoon(5)) {
      try {
        await authStore.refreshAccessToken()
      } catch (error) {
        console.error('Token refresh failed:', error)
        ElMessage.error('登录已过期，请重新登录')
        authStore.clearAuth()
        next('/login')
        return
      }
    }

    next()
  })
}
