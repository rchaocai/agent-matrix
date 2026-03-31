/**
 * 草稿管理API
 */

import client from './client'

/**
 * 获取草稿列表
 */
export async function getDrafts(params = {}) {
  return await client.get('/drafts', { params })
}

/**
 * 获取草稿详情
 */
export async function getDraft(draftId) {
  return await client.get(`/drafts/${draftId}`)
}

/**
 * 创建草稿
 */
export async function createDraft(data) {
  return await client.post('/drafts', data)
}

/**
 * 更新草稿
 */
export async function updateDraft(draftId, data) {
  return await client.put(`/drafts/${draftId}`, data)
}

/**
 * 删除草稿
 */
export async function deleteDraft(draftId) {
  return await client.delete(`/drafts/${draftId}`)
}

/**
 * 发布草稿
 */
export async function publishDraft(draftId) {
  return await client.post(`/drafts/${draftId}/publish`)
}
