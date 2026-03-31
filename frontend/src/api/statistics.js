/**
 * 数据统计API
 */

import client from './client'

/**
 * 获取统计数据概览
 */
export async function getStatsOverview() {
  return await client.get('/statistics/overview')
}

/**
 * 获取Agent详细统计
 */
export async function getAgentStats(limit = 10) {
  return await client.get('/statistics/agents', { params: { limit } })
}

/**
 * 获取发文趋势
 */
export async function getPostTrend(days = 30) {
  return await client.get('/statistics/trend', { params: { days } })
}

/**
 * 获取热门内容
 */
export async function getTopContent(limit = 10) {
  return await client.get('/statistics/top-content', { params: { limit } })
}

/**
 * 导出统计数据
 */
export async function exportStatistics(format = 'csv') {
  return await client.get('/statistics/export', { params: { format } })
}
