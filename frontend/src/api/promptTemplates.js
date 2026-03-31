/**
 * 提示词模板API
 */

import client from './client'

/**
 * 获取所有提示词模板
 */
export async function getTemplates(params = {}) {
  return await client.get('/prompt-templates/', { params })
}

/**
 * 获取指定提示词模板
 */
export async function getTemplate(templateId) {
  return await client.get(`/prompt-templates/${templateId}`)
}

/**
 * 创建提示词模板
 */
export async function createTemplate(data) {
  return await client.post('/prompt-templates/', data)
}

/**
 * 更新提示词模板
 */
export async function updateTemplate(templateId, data) {
  return await client.put(`/prompt-templates/${templateId}`, data)
}

/**
 * 删除提示词模板
 */
export async function deleteTemplate(templateId) {
  return await client.delete(`/prompt-templates/${templateId}`)
}

/**
 * 复制提示词模板
 */
export async function duplicateTemplate(templateId) {
  return await client.post(`/prompt-templates/${templateId}/duplicate`)
}

/**
 * 获取所有模板分类
 */
export async function getCategories() {
  return await client.get('/prompt-templates/categories/list')
}

export default {
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  duplicateTemplate,
  getCategories
}
