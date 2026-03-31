/**
 * 审核管理API
 */

import client from './client'

/**
 * 获取审核记录列表
 */
export async function getReviews(params = {}) {
  return await client.get('/reviews', { params })
}

/**
 * 获取审核详情
 */
export async function getReview(reviewId) {
  return await client.get(`/reviews/${reviewId}`)
}

/**
 * 通过审核
 */
export async function approveReview(reviewId) {
  return await client.post(`/reviews/${reviewId}/approve`)
}

/**
 * 拒绝审核
 */
export async function rejectReview(reviewId, notes) {
  return await client.post(`/reviews/${reviewId}/reject`, null, {
    params: { notes }
  })
}

/**
 * 批量通过审核
 */
export async function batchApprove(reviewIds) {
  return await client.post('/reviews/batch-approve', reviewIds)
}

/**
 * 批量拒绝审核
 */
export async function batchReject(reviewIds, notes) {
  return await client.post('/reviews/batch-reject', reviewIds, {
    params: { notes }
  })
}
