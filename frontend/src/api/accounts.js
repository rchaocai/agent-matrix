/**
 * 账号管理API
 */

import client from './client'

/**
 * 获取账号列表
 */
export async function getAccounts(params = {}) {
  return await client.get('/accounts/', { params })
}

/**
 * 获取账号详情
 */
export async function getAccount(accountId) {
  return await client.get(`/accounts/${accountId}/`)
}

/**
 * 创建账号
 */
export async function createAccount(data) {
  return await client.post('/accounts/', data)
}

/**
 * 更新账号
 */
export async function updateAccount(accountId, data) {
  return await client.put(`/accounts/${accountId}/`, data)
}

/**
 * 删除账号
 */
export async function deleteAccount(accountId) {
  return await client.delete(`/accounts/${accountId}/`)
}

/**
 * 刷新账号状态
 */
export async function refreshAccount(accountId) {
  return await client.post(`/accounts/${accountId}/refresh/`)
}

/**
 * 切换账号启用状态
 */
export async function toggleAccount(accountId) {
  return await client.patch(`/accounts/${accountId}/toggle/`)
}
