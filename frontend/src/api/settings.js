/**
 * 系统设置API
 */

import client from './client'

/**
 * 获取系统设置
 */
export async function getSettings() {
  return await client.get('/settings/')
}

/**
 * 更新系统设置
 */
export async function updateSettings(data) {
  return await client.put('/settings/', data)
}

/**
 * 测试LLM连接
 */
export async function testLLMConnection(provider) {
  return await client.post('/settings/test-llm', null, { params: { provider } })
}
