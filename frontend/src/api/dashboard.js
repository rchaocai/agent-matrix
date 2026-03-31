/**
 * Dashboard统计API
 */

import client from './client'

/**
 * 获取仪表盘统计数据
 */
export async function getDashboardStats() {
  return await client.get('/dashboard/stats')
}

/**
 * 获取最近发文列表
 */
export async function getRecentPosts(limit = 10) {
  return await client.get('/dashboard/recent-posts', { params: { limit } })
}

/**
 * 获取发文趋势数据
 */
export async function getPostTrend(days = 7) {
  return await client.get('/dashboard/trend', { params: { days } })
}

/**
 * 获取热门Agent排行
 */
export async function getTopAgents(limit = 5) {
  return await client.get('/dashboard/top-agents', { params: { limit } })
}
