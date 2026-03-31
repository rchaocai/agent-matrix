/**
 * 认证相关逻辑
 */

import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'
import client from '@/api/client'

/**
 * 认证Composable
 */
export function useAuth() {
  const authStore = useAuthStore()

  /**
   * 登录
   */
  const login = async (credentials) => {
    console.log('=== useAuth.login 开始 ===')
    console.log('登录凭据:', credentials)

    try {
      console.log('调用 client.post("/auth/login")')
      const response = await client.post('/auth/login', credentials)
      console.log('登录响应:', response)

      authStore.setAuth(response, response.user)
      ElMessage.success('登录成功')

      // 跳转到仪表盘
      router.push('/')
      return response
    } catch (error) {
      console.error('登录错误:', error)
      ElMessage.error(error.message || '登录失败')
      throw error
    }
  }

  /**
   * 注册
   */
  const register = async (userData) => {
    try {
      const response = await client.post('/auth/register', userData)
      authStore.setAuth(response, response.user)
      ElMessage.success('注册成功')
      router.push('/')
      return response
    } catch (error) {
      ElMessage.error(error.message || '注册失败')
      throw error
    }
  }

  /**
   * 登出
   */
  const logout = async () => {
    try {
      await client.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      authStore.clearAuth()
      ElMessage.success('已登出')
      router.push('/login')
    }
  }

  /**
   * 检查并刷新Token
   */
  const checkAndRefreshToken = async () => {
    // Token快过期时（剩余5分钟）自动刷新
    if (authStore.isTokenExpiringSoon(5)) {
      try {
        await authStore.refreshAccessToken()
      } catch (error) {
        console.error('Token refresh failed:', error)
        await logout()
      }
    }
  }

  /**
   * 获取当前用户信息
   */
  const getCurrentUser = async () => {
    try {
      const response = await client.get('/auth/me')
      authStore.user = response
      return response
    } catch (error) {
      console.error('Failed to get current user:', error)
      throw error
    }
  }

  return {
    login,
    register,
    logout,
    checkAndRefreshToken,
    getCurrentUser,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
    user: authStore.user
  }
}
