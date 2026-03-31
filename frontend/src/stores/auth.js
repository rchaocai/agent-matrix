/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  // 计算属性
  const isAuthenticated = computed(() => !!user.value && !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  /**
   * 设置认证信息
   */
  function setAuth(tokens, userData) {
    token.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    user.value = userData

    // 持久化到localStorage
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    }
  }

  /**
   * 清除认证信息
   */
  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  /**
   * 自动刷新Token
   */
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const client = (await import('@/api/client')).default
      const response = await client.post('/auth/refresh')

      token.value = response.access_token
      localStorage.setItem('access_token', response.access_token)

      return response.access_token
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  /**
   * 初始化（从localStorage恢复）
   */
  function init() {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Failed to parse user from localStorage', e)
        localStorage.removeItem('user')
      }
    }
  }

  /**
   * 检查Token是否即将过期
   */
  function isTokenExpiringSoon(thresholdMinutes = 5) {
    if (!token.value) return true

    try {
      const payload = parseJWT(token.value)
      if (!payload || !payload.exp) return true

      const expiresIn = payload.exp * 1000 - Date.now()
      return expiresIn < thresholdMinutes * 60 * 1000
    } catch (e) {
      return true
    }
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    isAdmin,
    setAuth,
    clearAuth,
    refreshAccessToken,
    init,
    isTokenExpiringSoon
  }
})

/**
 * 解析JWT Token
 */
function parseJWT(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = atob(base64)
    return JSON.parse(jsonPayload)
  } catch (e) {
    return null
  }
}
