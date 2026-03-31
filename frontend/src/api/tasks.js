/**
 * Tasks API - Agent执行历史
 */

import client from './client'

/**
 * 获取Task执行历史列表
 */
export async function getTasks(params = {}) {
  return await client.get('/tasks', { params })
}

/**
 * 获取指定Task详情
 */
export async function getTask(taskId) {
  return await client.get(`/tasks/${taskId}`)
}

/**
 * 获取指定Agent的执行历史
 */
export async function getAgentTasks(agentId, params = {}) {
  return await client.get('/tasks', { params: { ...params, agent_id: agentId } })
}

/**
 * 删除指定Task
 */
export async function deleteTask(taskId) {
  return await client.delete(`/tasks/${taskId}`)
}

/**
 * 批量删除指定Agent的Task
 */
export async function deleteAgentTasks(agentId, status) {
  return await client.delete('/tasks', {
    params: { agent_id: agentId, status }
  })
}
