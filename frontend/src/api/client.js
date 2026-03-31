/**
 * API客户端基础配置
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

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

// 防止多个请求同时触发Token刷新
let isRefreshing = false
let refreshSubscribers = []

// 创建axios实例
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // 允许携带Cookie
})

// 请求拦截器
client.interceptors.request.use(
  async (config) => {
    console.log('=== 发送API请求 ===')
    console.log('URL:', config.url)
    console.log('完整URL:', config.baseURL + config.url)
    console.log('Method:', config.method)

    // 不要在认证相关请求上检查Token刷新
    const isAuthRequest = config.url.includes('/auth/')
    // 如果当前在登录/注册页面，也不检查Token刷新
    const isAuthPage = window.location.pathname === '/login' ||
                       window.location.pathname === '/register'

    console.log('是否为认证请求:', isAuthRequest)
    console.log('是否为认证页面:', isAuthPage)

    // 从localStorage获取token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 只在非认证请求且非认证页面时检查Token是否快过期
    if (!isAuthRequest && !isAuthPage) {
      const authStore = (await import('@/stores/auth')).useAuthStore()
      if (token && authStore.isTokenExpiringSoon(5)) {
        console.log('Token快过期，准备刷新...')
        console.log('Token过期时间:', new Date(parseJWT(token).exp * 1000))
        console.log('当前时间:', new Date())

        // 如果已经在刷新，等待刷新完成
        if (isRefreshing) {
          console.log('Token刷新正在进行中，等待...')
          return new Promise((resolve, reject) => {
            refreshSubscribers.push((token, error) => {
              if (error) {
                reject(error)
              } else {
                config.headers.Authorization = `Bearer ${token}`
                resolve(config)
              }
            })
          })
        }

        isRefreshing = true
        try {
          const newToken = await authStore.refreshAccessToken()
          console.log('Token刷新成功')
          config.headers.Authorization = `Bearer ${newToken}`

          // 通知所有等待的请求
          refreshSubscribers.forEach(callback => callback(newToken, null))
          refreshSubscribers = []

          // 继续处理当前请求
        } catch (error) {
          console.error('Token refresh failed:', error)
          // 刷新失败，不重试原请求，直接跳转登录
          authStore.clearAuth()
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }

          // 通知所有等待的请求失败
          refreshSubscribers.forEach(callback => callback(null, error))
          refreshSubscribers = []

          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      }
    }

    console.log('最终Headers:', config.headers)
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
client.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // Token过期，尝试刷新
    // 不要在认证页面或认证请求上尝试刷新
    const isAuthRequest = originalRequest.url?.includes('/auth/')
    const isAuthPage = window.location.pathname === '/login' ||
                       window.location.pathname === '/register'

    if (error.response?.status === 401 &&
        !originalRequest._retry &&
        !isAuthRequest &&
        !isAuthPage) {
      originalRequest._retry = true

      try {
        const authStore = (await import('@/stores/auth')).useAuthStore()
        const refreshToken = localStorage.getItem('refresh_token')

        if (refreshToken) {
          // 调用刷新Token接口
          const newToken = await authStore.refreshAccessToken()

          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return client(originalRequest)
        }
      } catch (refreshError) {
        // 刷新失败，清除认证信息并跳转到登录页
        const authStore = (await import('@/stores/auth')).useAuthStore()
        authStore.clearAuth()

        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }

        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(refreshError)
      }
    }

    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)

    // 显示错误消息（如果还没有显示）
    if (!error.config._skipErrorMessage) {
      ElMessage.error(message)
    }

    return Promise.reject(new Error(message))
  }
)

export default client
