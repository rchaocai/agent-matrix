/**
 * 热搜数据API
 */

import client from './client'

/**
 * 获取指定日期的热搜数据
 * @param {Object} params - 查询参数
 * @param {string} params.date - 日期 YYYY-MM-DD（可选，默认今天）
 * @param {Array<string>} params.sources - 数据源列表（可选，默认全部）
 * @returns {Promise<Object>} 热搜数据
 */
export async function getHotSearchData(params) {
  return await client.get('/hot-search/data', { params })
}

/**
 * 手动触发爬取热搜数据
 * @param {Object} data - 请求参数
 * @param {Array<string>} data.sources - 要爬取的数据源列表（可选，默认全部）
 * @param {boolean} data.force - 是否强制重新爬取（可选，默认false）
 * @returns {Promise<Object>} 爬取结果
 */
export async function fetchHotSearch(data) {
  return await client.post('/hot-search/fetch', data)
}

/**
 * 获取可用日期列表
 * @returns {Promise<Object>} 日期列表
 */
export async function getAvailableDates() {
  return await client.get('/hot-search/dates')
}

/**
 * 获取缓存状态
 * @returns {Promise<Object>} 缓存状态
 */
export async function getCacheStatus() {
  return await client.get('/hot-search/status')
}
