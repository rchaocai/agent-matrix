/**
 * Agent管理API
 */

import client from './client'

/**
 * 获取Agent列表
 */
export async function getAgents() {
  return await client.get('/agents/')
}

/**
 * 获取Agent详情
 */
export async function getAgent(agentId) {
  return await client.get(`/agents/${agentId}/`)
}

/**
 * 创建Agent
 */
export async function createAgent(data) {
  return await client.post('/agents/', data)
}

/**
 * 更新Agent
 */
export async function updateAgent(agentId, data) {
  return await client.put(`/agents/${agentId}/`, data)
}

/**
 * 删除Agent
 */
export async function deleteAgent(agentId) {
  return await client.delete(`/agents/${agentId}/`)
}

/**
 * 切换Agent启用状态
 */
export async function toggleAgent(agentId) {
  return await client.patch(`/agents/${agentId}/toggle/`)
}

/**
 * 手动触发Agent执行
 */
export async function runAgent(agentId) {
  return await client.post(`/agents/${agentId}/run/`)
}

/**
 * 获取所有可用Skill列表
 */
export async function getSkillsList() {
  return await client.get('/agents/skills/list')
}
