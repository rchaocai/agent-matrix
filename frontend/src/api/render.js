/**
 * 图文渲染API
 */

import client from './client'

/**
 * 渲染文本为图片
 */
export async function renderFromText(data) {
  return await client.post('/render/from-text', data, {
    timeout: 120000 // 渲染多页图片需要更长时间
  })
}

/**
 * 获取支持的平台列表
 */
export async function getPlatforms() {
  return await client.get('/render/platforms')
}

/**
 * 获取支持的模板列表
 */
export async function getTemplates(platform = null) {
  const params = platform ? { platform } : {}
  return await client.get('/render/templates', { params })
}

/**
 * 批量渲染
 */
export async function renderBatch(items, platform = null, template = null) {
  const params = {}
  if (platform) params.platform = platform
  if (template) params.template = template
  return await client.post('/render/batch', items, { params })
}

/**
 * 获取模板配色方案
 */
export async function getColorSchemes(platform = null) {
  const params = platform ? { platform } : {}
  return await client.get('/render/templates/color-schemes', { params })
}

/**
 * 获取模板HTML预览（快速预览）
 */
export async function getTemplateHtml(params) {
  return await client.get('/render/templates/html', { params })
}

/**
 * 生成模板预览（渲染为图片，用于导出）
 */
export async function previewTemplate(data, options = {}) {
  return await client.post('/render/preview', data, options)
}

/**
 * 导出所有渲染API函数
 */
export default {
  renderFromText,
  getPlatforms,
  getTemplates,
  renderBatch,
  getColorSchemes,
  getTemplateHtml,
  previewTemplate
}
