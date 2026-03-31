<template>
  <div class="render-page">
    <!-- 操作模式切换 -->
    <div class="mode-tabs">
      <button
        :class="['tab-btn', { active: mode === 'single' }]"
        @click="mode = 'single'"
      >
        渲染
      </button>
      <button
        :class="['tab-btn', { active: mode === 'preview' }]"
        @click="mode = 'preview'"
      >
        模板管理
      </button>
    </div>

    <!-- 渲染模式 -->
    <div v-if="mode === 'single'" class="render-layout">
      <!-- 左侧：内容输入 + 实时预览 -->
      <div class="left-panel">
        <!-- 内容输入区 -->
        <div class="input-section">
          <!-- 内容来源选择 -->
          <div class="form-group">
            <label class="form-label">内容来源</label>
            <div class="source-selector">
              <button
                :class="['source-btn', { active: contentSource === 'new' }]"
                @click="switchSource('new')"
              >
                新建内容
              </button>
              <button
                :class="['source-btn', { active: contentSource === 'draft' }]"
                @click="switchSource('draft')"
              >
                从草稿选择
              </button>
            </div>
          </div>

          <!-- 草稿选择器 -->
          <div v-if="contentSource === 'draft'" class="form-group">
            <label class="form-label">选择草稿</label>
            <select v-model="selectedDraftId" class="form-select" @change="loadDraftContent">
              <option value="">请选择草稿...</option>
              <option v-for="draft in draftsList" :key="draft.id" :value="draft.id">
                {{ draft.title || '无标题' }} - {{ draft.agent_name || draft.agent_id }} ({{ formatStatus(draft.status) }})
              </option>
            </select>
            <div v-if="selectedDraftId" class="draft-info">
              <span class="draft-id">草稿ID: {{ selectedDraftId }}</span>
              <span class="draft-status" :class="`status-${selectedDraft?.status}`">
                {{ formatStatus(selectedDraft?.status) }}
              </span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">标题</label>
            <input
              v-model="formData.title"
              type="text"
              class="form-input"
              placeholder="请输入标题"
            />
          </div>

          <div class="form-group">
            <label class="form-label">正文内容</label>
            <textarea
              v-model="formData.content"
              class="form-textarea"
              rows="12"
              placeholder="请输入正文内容..."
            ></textarea>
            <div class="char-count">{{ formData.content.length }} 字</div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">作者（可选）</label>
              <input
                v-model="formData.author"
                type="text"
                class="form-input"
                placeholder="@作者名"
              />
            </div>
            <div class="form-group">
              <label class="form-label">目标平台</label>
              <select v-model="formData.platform" class="form-select">
                <option value="xiaohongshu">小红书</option>
                <option value="douyin">抖音</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">
              <input
                v-model="formData.split_long"
                type="checkbox"
              />
              自动分割长文
            </label>
            <div v-if="formData.split_long" class="split-config">
              <label class="sub-label">单张最大字数</label>
              <input
                v-model.number="formData.max_length"
                type="number"
                class="form-input"
                placeholder="默认500字"
                min="100"
                max="2000"
              />
              <span class="hint">当前内容将分为 {{ Math.ceil(formData.content.length / (formData.max_length || 500)) }} 页</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons-row">
            <button
              @click="handleRender"
              :disabled="isRendering || !formData.content"
              class="btn-primary"
            >
              {{ isRendering ? '渲染中...' : '开始渲染' }}
            </button>
            <button
              v-if="renderResult && renderResult.images"
              @click="handleSaveDraft"
              :disabled="isSaving"
              class="btn-secondary"
            >
              {{ isSaving ? '保存中...' : (selectedDraftId ? '更新草稿' : '保存为新草稿') }}
            </button>
          </div>
        </div>

        <!-- 渲染结果 -->
        <div class="result-section">
          <h3 class="result-title">
            <span>
              渲染结果
              <span v-if="renderResult && renderResult.total_pages" class="result-info">
                (共 {{ renderResult.total_pages }} 页)
              </span>
            </span>
            <div v-if="renderResult && renderResult.images && renderResult.images.length > 1" class="slide-nav">
              <button class="nav-btn" @click="slideImages('left')" :disabled="!canSlideLeft">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 18l-6-6 6-6"/>
                </svg>
              </button>
              <button class="nav-btn" @click="slideImages('right')" :disabled="!canSlideRight">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            </div>
          </h3>

          <div 
            v-if="renderResult && renderResult.images && renderResult.images.length > 0" 
            ref="resultImagesContainer"
            class="result-images"
            @scroll="updateSlideButtons"
          >
            <div
              v-for="(img, index) in renderResult.images"
              :key="index"
              class="image-item"
            >
              <div class="image-wrapper">
                <img :src="getImageUrl(img.url)" :alt="`Page ${index + 1}`" @error="handleImageError" />
                <div class="image-overlay">
                  <span>第 {{ img.index }} 页</span>
                </div>
              </div>
              <div class="image-actions">
                <button @click="downloadImage(img.url)" class="btn-download">
                  下载
                </button>
                <button @click="copyImageUrl(img.url)" class="btn-copy">
                  复制链接
                </button>
              </div>
            </div>
          </div>
          <div v-else class="placeholder-state">
            点击"开始渲染"生成图片
          </div>
        </div>
      </div>

      <!-- 右侧：模板选择器 -->
      <div class="right-panel">
        <div class="template-selector">
          <h3>模板样式</h3>

          <div class="template-grid">
            <div
              v-for="tpl in currentTemplates"
              :key="tpl"
              :class="['cover-item-container', { active: selectedTemplate === tpl }]"
              @click="selectTemplate(tpl)"
            >
              <div class="cover-item">
                <img
                  v-if="templatePreviewUrls[tpl]"
                  :src="templatePreviewUrls[tpl]"
                  :alt="getTemplateName(tpl)"
                />
                <div v-else class="preview-loading">加载中...</div>

                <!-- 换配色按钮 - 只在选中项显示 -->
                <div
                  v-if="selectedTemplate === tpl && hasColorSchemes(tpl)"
                  class="change-btn"
                  @click.stop="toggleColorScheme(tpl)"
                  title="换配色"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M4.24362 4.95735C5.12749 3.89183 6.46547 3.21348 7.96217 3.21348C10.6223 3.21348 12.7788 5.35648 12.7788 8C12.7788 10.6435 10.6223 12.7865 7.96217 12.7865C6.58464 12.7865 5.34299 12.2126 4.46432 11.2907C4.23246 11.0474 3.84601 11.0369 3.60118 11.2673C3.35635 11.4977 3.34584 11.8818 3.57771 12.1251C4.67738 13.279 6.23554 14 7.96217 14C11.2967 14 13.9999 11.3137 13.9999 8C13.9999 4.68629 11.2967 2 7.96217 2C6.01163 2 4.27791 2.91919 3.17453 4.34397L2.35211 3.87212C1.8287 3.57181 1.2012 4.05029 1.35763 4.63044L1.9997 7.01173C2.09668 7.37137 2.46867 7.58479 2.83057 7.48843L5.22685 6.85037C5.81064 6.69492 5.91388 5.91565 5.39046 5.61534L4.24362 4.95735Z" fill="currentColor"></path>
                  </svg>
                </div>

                <!-- 换字体按钮 - 只在选中项显示 -->
                <div
                  v-if="selectedTemplate === tpl && hasFontSchemes(tpl)"
                  class="change-btn change-font-btn"
                  @click.stop="toggleFontScheme(tpl)"
                  title="换字体"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3.5 2C3.5 1.72386 3.72386 1.5 4 1.5H12C12.2761 1.5 12.5 1.72386 12.5 2C12.5 2.27614 12.2761 2.5 12 2.5H8.5V13.5C8.5 13.7761 8.27614 14 8 14C7.72386 14 7.5 13.7761 7.5 13.5V2.5H4C3.72386 2.5 3.5 2.27614 3.5 2Z" fill="currentColor"></path>
                  </svg>
                </div>
              </div>
              <div class="cover-name">{{ getTemplateName(tpl) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模板管理模式 -->
    <div v-if="mode === 'preview'" class="mode-content">
      <div class="template-manager">
        <div class="manager-header">
          <h3>模板管理</h3>
          <div class="manager-stats">
            <span class="stat-item">
              <strong>{{ getAllTemplatesCount() }}</strong> 个模板
            </span>
            <span class="stat-item">
              <strong>{{ getCustomTemplatesCount() }}</strong> 个自定义
            </span>
          </div>
        </div>

        <!-- 配置信息栏 -->
        <div class="config-info-bar">
          <div class="font-info">
            <span class="info-label">当前字体大小：</span>
            <span class="info-value">标题 {{ currentFontSize.title }}px / 正文 {{ currentFontSize.body }}px</span>
          </div>
          <div class="cache-actions">
            <button
              @click="handleClearCache"
              class="btn-clear-cache"
              :disabled="isClearingCache"
            >
              {{ isClearingCache ? '清除中...' : '清除预览缓存' }}
            </button>
            <button
              @click="showAIGenerateDialog = true"
              class="btn-ai-generate-inline"
            >
              <span class="icon">✨</span>
              AI生成模板
            </button>
          </div>
        </div>

        <!-- 平台选择 -->
        <div class="platform-tabs">
          <button
            :class="['platform-tab', { active: managerConfig.platform === 'xiaohongshu' }]"
            @click="managerConfig.platform = 'xiaohongshu'"
          >
            小红书
          </button>
          <button
            :class="['platform-tab', { active: managerConfig.platform === 'douyin' }]"
            @click="managerConfig.platform = 'douyin'"
          >
            抖音
          </button>
        </div>

        <!-- 模板网格 - 使用真实预览图 -->
        <div class="template-preview-grid">
          <div
            v-for="tpl in currentManagerTemplates"
            :key="tpl.name"
            :class="['template-preview-card', { custom: tpl.is_custom }]"
          >
            <div class="template-preview-image" @click="handleManagerPreview(tpl)">
              <img
                v-if="managerTemplatePreviewUrls[tpl.name]"
                :src="managerTemplatePreviewUrls[tpl.name]"
                :alt="getTemplateName(tpl.name)"
              />
              <div v-else class="preview-loading-state">
                <span>加载中...</span>
              </div>
              <div class="template-overlay">
                <span class="template-name">{{ getTemplateName(tpl.name) }}</span>
                <span v-if="tpl.is_custom" class="badge-custom">自定义</span>
              </div>
            </div>

            <div class="template-preview-actions">
              <button
                @click="handleManagerPreview(tpl)"
                class="btn-preview-action"
                title="查看预览"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M1 8C1 8 4 4 8 4C12 4 15 8 15 8C15 8 12 12 8 12C4 12 1 8 1 8Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="8" cy="8" r="2" fill="currentColor"/>
                </svg>
                预览
              </button>
              <button
                v-if="tpl.is_custom"
                @click="handleDeleteTemplate(tpl)"
                class="btn-delete-action"
                title="删除模板"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 5H13M5 5V4C5 3.44772 5.44772 3 6 3H10C10.5523 3 11 3.44772 11 4V5M12 5L11.683 11.6747C11.6346 12.6178 10.8486 13.35 9.90428 13.35H6.09572C5.15136 13.35 4.36541 12.6178 4.31704 11.6747L4 5M12 5H4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                删除
              </button>
              <span v-else class="badge-preset">预设</span>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="currentManagerTemplates.length === 0" class="empty-state">
            <p>暂无模板</p>
          </div>
        </div>

        <!-- 预览区域 - 全屏弹窗 -->
        <div v-if="managerPreviewResult" class="preview-modal-overlay" @click.self="managerPreviewResult = null">
          <div class="preview-modal">
            <div class="preview-modal-header">
              <h4>模板预览 - {{ getTemplateName(managerPreviewResult.template) }}</h4>
              <button @click="managerPreviewResult = null" class="btn-close">✕</button>
            </div>
            <div class="preview-modal-content">
              <img
                :src="getImageUrl(managerPreviewResult.image_url)"
                alt="模板预览"
                @error="handleImageError"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div v-if="message.text" :class="['message-toast', message.type]">
      {{ message.text }}
    </div>

    <!-- AI生成模板对话框 -->
    <div v-if="showAIGenerateDialog" class="ai-dialog-overlay" @click.self="showAIGenerateDialog = false">
      <div class="ai-dialog">
        <div class="ai-dialog-header">
          <h3>✨ AI生成模板</h3>
          <button @click="showAIGenerateDialog = false" class="btn-close">&times;</button>
        </div>

        <div class="ai-dialog-body">
          <div v-if="!aiGenerateResult" class="ai-form">
            <div class="form-group">
              <label class="form-label">风格描述</label>
              <textarea
                v-model="aiGenerateForm.description"
                class="form-textarea"
                rows="3"
                placeholder="例如：粉色渐变背景、大字体标题、优雅杂志风格..."
              ></textarea>
              <div class="example-hints">
                <span
                  v-for="hint in exampleHints"
                  :key="hint"
                  @click="aiGenerateForm.description = hint"
                  class="hint-tag"
                >
                  {{ hint }}
                </span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">目标平台</label>
                <select v-model="aiGenerateForm.platform" class="form-select">
                  <option value="xiaohongshu">小红书</option>
                  <option value="douyin">抖音</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">参考风格</label>
                <select v-model="aiGenerateForm.style" class="form-select">
                  <option value="modern">现代简约</option>
                  <option value="elegant">优雅杂志</option>
                  <option value="vibrant">鲜艳活力</option>
                </select>
              </div>
            </div>
          </div>

          <!-- 预览结果区域 -->
          <div v-if="aiGenerateResult" class="ai-preview-section">
            <h4>✨ 生成结果</h4>

            <div class="ai-result-content">
              <!-- 左侧：预览图片 -->
              <div class="preview-image-section">
                <div v-if="!previewImageUrl" class="preview-placeholder">
                  <div class="placeholder-icon">🎨</div>
                  <p>点击"生成预览图"查看效果</p>
                  <button @click="handlePreviewGeneratedTemplate" class="btn-preview-large" :disabled="isPreviewing">
                    {{ isPreviewing ? '生成中...' : '生成预览图' }}
                  </button>
                </div>
                <div v-else class="preview-image-container">
                  <img :src="previewImageUrl" alt="模板预览" />
                  <button @click="handlePreviewGeneratedTemplate" class="btn-refresh-preview" :disabled="isPreviewing">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 8C13.5 11.0376 11.0376 13.5 8 13.5C4.96243 13.5 2.5 11.0376 2.5 8C2.5 4.96243 4.96243 2.5 8 2.5C11.0376 2.5 13.5 4.96243 13.5 8Z" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M11 8L9 6M11 8L9 10M11 8H5M5 8L7 6M5 8L7 10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                    重新生成
                  </button>
                </div>
              </div>

              <!-- 右侧：信息表单 -->
              <div class="info-form-section">
                <div class="template-info-form">
                  <div class="form-group">
                    <label class="form-label">模板名称（可修改）</label>
                    <input
                      v-model="customTemplateName"
                      type="text"
                      class="form-input"
                      placeholder="输入模板名称"
                    />
                  </div>

                  <div class="form-group">
                    <label class="form-label">质量评分</label>
                    <div class="quality-display">
                      <span :class="['quality-badge', getQualityClass(aiGenerateResult.code_quality)]">
                        {{ aiGenerateResult.code_quality }}/100
                      </span>
                      <span class="quality-hint">
                        {{ getQualityHint(aiGenerateResult.code_quality) }}
                      </span>
                    </div>
                  </div>

                  <!-- 错误列表 -->
                  <div v-if="aiGenerateResult.errors && aiGenerateResult.errors.length > 0" class="error-list">
                    <p class="error-title">⚠️ 生成警告:</p>
                    <ul>
                      <li v-for="(error, index) in aiGenerateResult.errors" :key="index">{{ error }}</li>
                    </ul>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="result-actions">
                  <button @click="handleSaveTemplate" class="btn-primary btn-save" :disabled="!customTemplateName.trim()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M8 3.5C8 3.22386 8.22386 3 8.5 3H11.5C11.7761 3 12 3.22386 12 3.5V6.5C12 6.77614 11.7761 7 11.5 7C11.2239 7 11 6.77614 11 6.5V4H9V6.5C9 6.77614 8.77614 7 8.5 7C8.22386 7 8 6.77614 8 6.5V3.5Z" fill="currentColor"/>
                      <path d="M3 3.5C3 3.22386 3.22386 3 3.5 3H5.5C5.77614 3 6 3.22386 6 3.5C6 3.77614 5.77614 4 5.5 4H4V11C4 11.2761 4.22386 11.5 4.5 11.5H11.5C11.7761 11.5 12 11.2761 12 11V9.5C12 9.22386 12.2239 9 12.5 9C12.7761 9 13 9.22386 13 9.5V11C13 11.8284 12.3284 12.5 11.5 12.5H4.5C3.67157 12.5 3 11.8284 3 11V3.5Z" fill="currentColor"/>
                      <path d="M8.5 5.5C8.22386 5.5 8 5.72386 8 6V10C8 10.2761 8.22386 10.5 8.5 10.5C8.77614 10.5 9 10.2761 9 10V6C9 5.72386 8.77614 5.5 8.5 5.5Z" fill="currentColor"/>
                    </svg>
                    保存模板
                  </button>
                  <button @click="handleRegenerate" class="btn-secondary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M4.5 8C4.5 6.067 6.067 4.5 8 4.5C9.933 4.5 11.5 6.067 11.5 8C11.5 9.933 9.933 11.5 8 11.5C6.067 11.5 4.5 9.933 4.5 8ZM3.5 8C3.5 10.4853 5.51472 12.5 8 12.5C10.4853 12.5 12.5 10.4853 12.5 8C12.5 5.51472 10.4853 3.5 8 3.5C5.51472 3.5 3.5 5.51472 3.5 8Z" fill="currentColor"/>
                      <path d="M8 5V8L10 10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                    重新生成
                  </button>
                  <button @click="handleDiscard" class="btn-danger">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M3 5H13M5 5V4C5 3.44772 5.44772 3 6 3H10C10.5523 3 11 3.44772 11 4V5M12 5L11.683 11.6747C11.6346 12.6178 10.8486 13.35 9.90428 13.35H6.09572C5.15136 13.35 4.36541 12.6178 4.31704 11.6747L4 5M12 5H4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    丢弃
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 对话框底部操作按钮 -->
        <div v-if="!aiGenerateResult" class="ai-dialog-footer">
          <button @click="showAIGenerateDialog = false" class="btn-secondary">
            取消
          </button>
          <button
            @click="handleAIGenerate"
            :disabled="isGenerating || !aiGenerateForm.description"
            class="btn-primary"
          >
            {{ isGenerating ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as renderApi from '../api/render'

// 模式
const mode = ref('single')

// 内容来源
const contentSource = ref('new')
const selectedDraftId = ref('')
const draftsList = ref([])
const selectedDraft = ref(null)
const isSaving = ref(false)

// 表单数据
const formData = ref({
  title: '',
  content: '',
  platform: 'xiaohongshu',
  author: '',
  split_long: true,
  max_length: 500
})

// 选中的模板
const selectedTemplate = ref('minimal')

// 配色方案
const colorSchemes = ref({})
const templateColorIndices = ref({})

// 字体方案
const fontSchemes = ref({})
const templateFontIndices = ref({})

// 模板预览图URL缓存
const templatePreviewUrls = ref({})

// 模板管理页的模板预览图URL缓存
const managerTemplatePreviewUrls = ref({})

// 模板管理配置
const managerConfig = ref({
  platform: 'xiaohongshu'
})

// 模板管理数据
const managerTemplates = ref({})
const managerPreviewResult = ref(null)

// 当前字体大小配置
const currentFontSize = ref({
  title: 100,
  body: 60
})

// 清除缓存状态
const isClearingCache = ref(false)

// 渲染状态
const isRendering = ref(false)
const renderResult = ref(null)

// 图片滑动控制
const resultImagesContainer = ref(null)
const canSlideLeft = ref(false)
const canSlideRight = ref(false)

// 模板数据
const allTemplates = ref({
  xiaohongshu: ['minimal', 'zen', 'gradient', 'modern', 'elegant', 'vibrant'],
  douyin: ['dark', 'neon']
})

// 消息提示
const message = ref({ text: '', type: '' })

// AI生成相关
const showAIGenerateDialog = ref(false)
const isGenerating = ref(false)
const aiGenerateForm = ref({
  description: '',
  platform: 'xiaohongshu',
  style: 'modern'
})
const aiGenerateResult = ref(null)
const customTemplateName = ref('')
const previewImageUrl = ref('')
const isPreviewing = ref(false)

const exampleHints = [
  '粉色渐变背景、大字体标题、优雅杂志风格',
  '深色背景、霓虹灯效果、赛博朋克风格',
  '简约白底、黑色大标题、极简主义',
  '温暖橙色调、圆润字体、活力四射',
  '高级灰底、金色装饰、奢华感'
]

// 当前平台的模板
const currentTemplates = computed(() => {
  return allTemplates.value[formData.value.platform] || []
})

// 模板管理的当前平台模板
const currentManagerTemplates = computed(() => {
  return managerTemplates.value[managerConfig.value.platform] || []
})

// 获取模板名称
const getTemplateName = (tpl) => {
  const names = {
    minimal: '极简',
    zen: '禅意',
    gradient: '渐变',
    modern: '现代',
    elegant: '优雅',
    vibrant: '活力',
    dark: '暗色',
    neon: '霓虹'
  }
  return names[tpl] || tpl
}

// 获取图片URL
const getImageUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${window.location.protocol}//${window.location.hostname}:8000${url}`
}

// 加载配色方案
const loadColorSchemes = async () => {
  try {
    const response = await renderApi.getColorSchemes()
    if (response.status === 'success') {
      colorSchemes.value = response.platforms

      // 初始化每个模板的配色索引
      for (const platform in response.platforms) {
        for (const template in response.platforms[platform]) {
          const key = `${platform}-${template}`
          if (templateColorIndices.value[key] === undefined) {
            templateColorIndices.value[key] = 0
          }
        }
      }
    }
  } catch (error) {
    console.error('加载配色方案失败:', error)
  }
}

// 加载字体方案
const loadFontSchemes = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/render/templates/font-schemes')
    const data = await response.json()
    if (data.status === 'success') {
      fontSchemes.value = data.platforms

      // 初始化每个模板的字体索引
      for (const platform in data.platforms) {
        for (const template in data.platforms[platform]) {
          const key = `${platform}-${template}`
          if (templateFontIndices.value[key] === undefined) {
            templateFontIndices.value[key] = 0
          }
        }
      }
    }
  } catch (error) {
    console.error('加载字体方案失败:', error)
  }
}

// 检查模板是否有配色方案
const hasColorSchemes = (templateName) => {
  const schemes = colorSchemes.value[formData.value.platform]?.[templateName]
  return schemes && schemes.length > 1
}

// 获取当前配色方案名称
const getCurrentColorSchemeName = (templateName) => {
  const key = `${formData.value.platform}-${templateName}`
  const schemes = colorSchemes.value[formData.value.platform]?.[templateName]
  const index = templateColorIndices.value[key] ?? 0
  return schemes?.[index]?.name || null
}

// 加载模板预览图
const loadTemplatePreview = async (templateName) => {
  // 检查缓存
  if (templatePreviewUrls.value[templateName]) {
    return templatePreviewUrls.value[templateName]
  }

  try {
    const response = await renderApi.previewTemplate({
      template: templateName,
      platform: formData.value.platform,
      color_scheme: getCurrentColorSchemeName(templateName) || undefined,
      font_scheme: getCurrentFontSchemeName(templateName) || undefined,
      sample: true,
    })

    if (response && response.image_url) {
      // 直接使用返回的URL，不需要下载blob
      const imageUrl = getImageUrl(response.image_url)
      templatePreviewUrls.value[templateName] = imageUrl
      return imageUrl
    }
    throw new Error('响应中没有 image_url')
  } catch (error) {
    console.error(`[loadTemplatePreview] ${templateName} 失败:`, error.message)
    return null
  }
}

// 切换配色方案
const toggleColorScheme = async (templateName) => {
  const key = `${formData.value.platform}-${templateName}`
  const schemes = colorSchemes.value[formData.value.platform]?.[templateName]

  if (!schemes || schemes.length === 0) return

  // 循环切换
  const currentIndex = templateColorIndices.value[key] || 0
  const nextIndex = (currentIndex + 1) % schemes.length
  templateColorIndices.value[key] = nextIndex

  // 清除缓存，重新加载模板预览图
  delete templatePreviewUrls.value[templateName]
  await loadTemplatePreview(templateName)
  
  // 如果有渲染结果，自动重新渲染
  if (renderResult.value && formData.value.content) {
    await handleRender()
  }
}

// 检查模板是否有字体方案
const hasFontSchemes = (templateName) => {
  const schemes = fontSchemes.value[formData.value.platform]?.[templateName]
  return schemes && schemes.length > 1
}

// 获取当前字体方案名称
const getCurrentFontSchemeName = (templateName) => {
  const key = `${formData.value.platform}-${templateName}`
  const schemes = fontSchemes.value[formData.value.platform]?.[templateName]
  const index = templateFontIndices.value[key] ?? 0
  return schemes?.[index]?.name || null
}

// 切换字体方案
const toggleFontScheme = async (templateName) => {
  const key = `${formData.value.platform}-${templateName}`
  const schemes = fontSchemes.value[formData.value.platform]?.[templateName]

  if (!schemes || schemes.length === 0) return

  // 循环切换
  const currentIndex = templateFontIndices.value[key] || 0
  const nextIndex = (currentIndex + 1) % schemes.length
  templateFontIndices.value[key] = nextIndex
  
  console.log(`切换字体方案: ${key}, 当前索引: ${nextIndex}, 方案:`, schemes[nextIndex])

  // 清除缓存，重新加载模板预览图
  delete templatePreviewUrls.value[templateName]
  await loadTemplatePreview(templateName)
  
  // 如果有渲染结果，自动重新渲染
  if (renderResult.value && formData.value.content) {
    await handleRender()
  }
}

// 选择模板
const selectTemplate = (templateName) => {
  selectedTemplate.value = templateName
}

// 监听平台变化，重新加载模板预览图
watch(() => formData.value.platform, async () => {
  // 清空预览URL缓存
  templatePreviewUrls.value = {}

  // 重置选中的模板为第一个可用模板
  const newTemplates = allTemplates.value[formData.value.platform] || []
  if (newTemplates.length > 0) {
    selectedTemplate.value = newTemplates[0]
  }

  // 预加载新平台的模板预览图
  const previewPromises = currentTemplates.value.map(tpl => loadTemplatePreview(tpl))
  await Promise.allSettled(previewPromises)
})

// 监听模板管理页平台变化，加载模板预览
watch(() => managerConfig.value.platform, async () => {
  // 清空管理页的预览URL缓存
  managerTemplatePreviewUrls.value = {}

  // 预加载当前平台的模板预览图
  const templates = currentManagerTemplates.value
  if (templates && templates.length > 0) {
    const previewPromises = templates.map(tpl => loadManagerTemplatePreview(tpl))
    await Promise.allSettled(previewPromises)
  }
})

// 单篇渲染
const handleRender = async () => {
  isRendering.value = true
  renderResult.value = null

  const colorSchemeName = getCurrentColorSchemeName(selectedTemplate.value)
  const fontSchemeName = getCurrentFontSchemeName(selectedTemplate.value)
  
  console.log('渲染参数:', {
    title: formData.value.title,
    content_length: formData.value.content.length,
    platform: formData.value.platform,
    template: selectedTemplate.value,
    color_scheme: colorSchemeName,
    font_scheme: fontSchemeName,
    split_long: formData.value.split_long,
    max_length: formData.value.max_length
  })

  try {
    const response = await renderApi.renderFromText({
      title: formData.value.title,
      content: formData.value.content,
      platform: formData.value.platform,
      template: selectedTemplate.value,
      color_scheme: colorSchemeName,
      font_scheme: fontSchemeName,
      author: formData.value.author || undefined,
      split_long: formData.value.split_long,
      max_length: formData.value.max_length || undefined
    })

    renderResult.value = response
    showMessage('渲染成功', 'success')
    console.log('渲染结果:', response)
    
    // 重置滑动按钮状态
    nextTick(() => {
      updateSlideButtons()
    })
  } catch (error) {
    console.error('渲染失败:', error)
    showMessage('渲染失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isRendering.value = false
  }
}

// 更新滑动按钮状态
const updateSlideButtons = () => {
  if (!resultImagesContainer.value) {
    canSlideLeft.value = false
    canSlideRight.value = false
    return
  }
  
  const el = resultImagesContainer.value
  canSlideLeft.value = el.scrollLeft > 0
  canSlideRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 1
}

// 滑动图片
const slideImages = (direction) => {
  if (!resultImagesContainer.value) return
  
  const el = resultImagesContainer.value
  const scrollAmount = 240 // 一个图片宽度 + 间距
  
  if (direction === 'left') {
    el.scrollBy({ left: -scrollAmount, behavior: 'smooth' })
  } else {
    el.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }
}

// 下载图片
const downloadImage = (url) => {
  const link = document.createElement('a')
  link.href = getImageUrl(url)
  link.download = url.split('/').pop()
  link.click()
  showMessage('开始下载', 'success')
}

// 复制链接
const copyImageUrl = (url) => {
  const fullUrl = getImageUrl(url)
  navigator.clipboard.writeText(fullUrl).then(() => {
    showMessage('链接已复制', 'success')
  })
}

// 处理图片加载错误
const handleImageError = (event) => {
  console.error('图片加载失败:', event.target.src)
  showMessage('图片加载失败，请检查URL', 'error')
}

// 显示消息
const showMessage = (text, type = 'info') => {
  message.value = { text, type }
  setTimeout(() => {
    message.value = { text: '', type: '' }
  }, 3000)
}

// 加载模板列表
const loadTemplates = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/render/templates/detail')
    const data = await response.json()

    if (data.status === 'success') {
      managerTemplates.value = data.templates

      const templates = {}
      for (const platform in data.templates) {
        templates[platform] = data.templates[platform].map(t => t.name)
      }
      allTemplates.value = templates
    }
  } catch (error) {
    console.error('加载模板列表失败:', error)
  }
}

// 加载草稿列表
const loadDraftsList = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/drafts/?limit=100')
    const data = await response.json()
    draftsList.value = data || []
  } catch (error) {
    console.error('加载草稿列表失败:', error)
  }
}

// 切换内容来源
const switchSource = (source) => {
  contentSource.value = source
  if (source === 'new') {
    selectedDraftId.value = ''
    selectedDraft.value = null
    formData.value = {
      title: '',
      content: '',
      platform: 'xiaohongshu',
      author: '',
      split_long: true,
      max_length: 500
    }
    renderResult.value = null
  } else {
    loadDraftsList()
  }
}

// 加载草稿内容
const loadDraftContent = async () => {
  if (!selectedDraftId.value) {
    selectedDraft.value = null
    return
  }
  
  const draft = draftsList.value.find(d => d.id === selectedDraftId.value)
  if (draft) {
    selectedDraft.value = draft
    formData.value.title = draft.title || ''
    formData.value.content = draft.content || ''
    formData.value.platform = draft.platform || 'xiaohongshu'
    
    // 如果有已渲染的图片，显示结果
    if (draft.image_paths) {
      const images = draft.image_paths.split(',').filter(p => p.trim())
      if (images.length > 0) {
        renderResult.value = {
          images: images.map(path => {
            // 处理不同格式的路径
            let url = path
            if (path.startsWith('data/images')) {
              url = `http://localhost:8000/static/${path.replace('data/', '')}`
            } else if (path.startsWith('/static')) {
              url = `http://localhost:8000${path}`
            } else if (!path.startsWith('http')) {
              url = `http://localhost:8000/static/images/${path}`
            }
            return { url, path }
          }),
          total_pages: images.length
        }
      }
    } else {
      renderResult.value = null
    }
  }
}

// 格式化状态
const formatStatus = (status) => {
  const statusMap = {
    'pending': '待发布',
    'pending_review': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'published': '已发布',
    'failed': '发布失败',
    'draft': '草稿'
  }
  return statusMap[status] || status
}

// 保存草稿
const handleSaveDraft = async () => {
  if (!renderResult.value || !renderResult.value.images) {
    showMessage('请先渲染内容', 'error')
    return
  }
  
  isSaving.value = true
  try {
    // 使用相对路径保存
    const imagePaths = renderResult.value.images.map(img => img.path).join(',')
    
    const payload = {
      agent_id: 'manual_render',
      platform: formData.value.platform,
      title: formData.value.title || '无标题',
      content: formData.value.content,
      image_paths: imagePaths,
      status: 'pending'
    }
    
    let response
    if (selectedDraftId.value) {
      // 更新现有草稿
      response = await fetch(`http://localhost:8000/api/drafts/${selectedDraftId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } else {
      // 创建新草稿
      response = await fetch('http://localhost:8000/api/drafts/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    }
    
    const data = await response.json()
    if (data.id) {
      showMessage(selectedDraftId.value ? '草稿更新成功' : '草稿保存成功', 'success')
      // 刷新草稿列表
      await loadDraftsList()
      // 如果是新建，更新选中的草稿ID
      if (!selectedDraftId.value) {
        selectedDraftId.value = data.id
        selectedDraft.value = data
      }
    } else {
      showMessage('保存失败: ' + (data.detail || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('保存草稿失败:', error)
    showMessage('保存失败: ' + error.message, 'error')
  } finally {
    isSaving.value = false
  }
}

// 获取所有模板数量
const getAllTemplatesCount = () => {
  let count = 0
  for (const platform in managerTemplates.value) {
    count += managerTemplates.value[platform].length
  }
  return count
}

// 获取自定义模板数量
const getCustomTemplatesCount = () => {
  let count = 0
  for (const platform in managerTemplates.value) {
    count += managerTemplates.value[platform].filter(t => t.is_custom).length
  }
  return count
}

// 加载字体配置
const loadFontConfig = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/render/platforms')
    const data = await response.json()

    if (data.status === 'success') {
      // 这里暂时使用默认值，实际应该从后端API获取
      currentFontSize.value = {
        title: 100,
        body: 60
      }
    }
  } catch (error) {
    console.error('加载字体配置失败:', error)
  }
}

// 清除预览缓存
const handleClearCache = async () => {
  if (!confirm('确定要清除所有预览缓存吗？清除后需要重新生成预览图。')) {
    return
  }

  isClearingCache.value = true

  try {
    const response = await fetch('http://localhost:8000/api/render/clear-cache', {
      method: 'POST'
    })

    const data = await response.json()

    if (data.status === 'success') {
      showMessage(`缓存已清除，共删除 ${data.deleted_count} 个文件`, 'success')
      // 清空前端预览URL缓存
      templatePreviewUrls.value = {}
      // 重新加载模板预览
      if (currentTemplates.value.length > 0) {
        const previewPromises = currentTemplates.value.map(tpl => loadTemplatePreview(tpl))
        await Promise.allSettled(previewPromises)
      }
    } else {
      showMessage('清除缓存失败: ' + (data.error || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('清除缓存失败:', error)
    showMessage('清除缓存失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isClearingCache.value = false
  }
}

// 模板管理预览
const handleManagerPreview = async (tpl) => {
  isRendering.value = true
  managerPreviewResult.value = null

  try {
    const response = await renderApi.previewTemplate({
      template: tpl.name,
      platform: managerConfig.value.platform,
      sample: true
    })

    managerPreviewResult.value = {
      ...response,
      template: tpl.name
    }
  } catch (error) {
    console.error('预览生成失败:', error)
    showMessage('预览生成失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isRendering.value = false
  }
}

// 加载管理页模板预览图
const loadManagerTemplatePreview = async (tpl) => {
  // 检查缓存
  if (managerTemplatePreviewUrls.value[tpl.name]) {
    return managerTemplatePreviewUrls.value[tpl.name]
  }

  try {
    const response = await renderApi.previewTemplate({
      template: tpl.name,
      platform: managerConfig.value.platform,
      sample: true,
    })

    if (response && response.image_url) {
      const imageUrl = getImageUrl(response.image_url)
      managerTemplatePreviewUrls.value[tpl.name] = imageUrl
      return imageUrl
    }
    throw new Error('响应中没有 image_url')
  } catch (error) {
    console.error(`[loadManagerTemplatePreview] ${tpl.name} 失败:`, error.message)
    return null
  }
}

// 删除模板
const handleDeleteTemplate = async (tpl) => {
  if (!confirm(`确定要删除模板"${getTemplateName(tpl.name)}"吗？此操作不可恢复。`)) {
    return
  }

  try {
    const response = await fetch(`http://localhost:8000/api/render/templates/${tpl.platform}/${tpl.name}`, {
      method: 'DELETE'
    })

    const data = await response.json()

    if (data.status === 'success' || data.success) {
      showMessage('模板删除成功', 'success')
      await loadTemplates()
    } else {
      showMessage('删除失败: ' + (data.error || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('删除模板失败:', error)
    showMessage('删除模板失败: ' + (error.message || '未知错误'), 'error')
  }
}

// AI生成模板
const handleAIGenerate = async () => {
  if (!aiGenerateForm.value.description) {
    showMessage('请输入风格描述', 'error')
    return
  }

  isGenerating.value = true
  aiGenerateResult.value = null

  try {
    const response = await fetch('http://localhost:8000/api/render/generate-template', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        description: aiGenerateForm.value.description,
        platform: aiGenerateForm.value.platform,
        style: aiGenerateForm.value.style
      })
    })

    const data = await response.json()

    if (data.status === 'success') {
      aiGenerateResult.value = data
      customTemplateName.value = data.template_name
      previewImageUrl.value = ''
      showMessage('模板生成成功', 'success')
    } else {
      showMessage('生成失败: ' + (data.detail || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('AI生成失败:', error)
    showMessage('AI生成失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isGenerating.value = false
  }
}

// 保存生成的模板
const handleSaveTemplate = async () => {
  if (!aiGenerateResult.value) return

  if (!customTemplateName.value.trim()) {
    showMessage('请输入模板名称', 'error')
    return
  }

  try {
    const response = await fetch('http://localhost:8000/api/render/save-template', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        template_html: aiGenerateResult.value.template_html,
        template_name: customTemplateName.value.trim(),
        platform: aiGenerateForm.value.platform
      })
    })

    const data = await response.json()

    if (data.status === 'success' || data.success) {
      showMessage('模板保存成功', 'success')
      await loadTemplates()

      // 重新加载当前平台的预览图
      managerTemplatePreviewUrls.value = {}
      const templates = currentManagerTemplates.value
      if (templates && templates.length > 0) {
        const previewPromises = templates.map(tpl => loadManagerTemplatePreview(tpl))
        await Promise.allSettled(previewPromises)
      }

      selectedTemplate.value = customTemplateName.value.trim()
      showAIGenerateDialog.value = false
      aiGenerateResult.value = null
      customTemplateName.value = ''
      previewImageUrl.value = ''
      aiGenerateForm.value.description = ''
    } else {
      showMessage('保存失败: ' + (data.error || data.detail || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('保存模板失败:', error)
    showMessage('保存模板失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 重新生成
const handleRegenerate = () => {
  aiGenerateResult.value = null
  customTemplateName.value = ''
  previewImageUrl.value = ''
  handleAIGenerate()
}

// 丢弃生成结果
const handleDiscard = () => {
  aiGenerateResult.value = null
  customTemplateName.value = ''
  previewImageUrl.value = ''
  aiGenerateForm.value.description = ''
  showAIGenerateDialog.value = false
}

// 预览生成的模板
const handlePreviewGeneratedTemplate = async () => {
  if (!aiGenerateResult.value) return

  isPreviewing.value = true
  previewImageUrl.value = ''

  try {
    const tempName = `temp_preview_${Date.now()}`

    const saveResponse = await fetch('http://localhost:8000/api/render/save-template', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        template_html: aiGenerateResult.value.template_html,
        template_name: tempName,
        platform: aiGenerateForm.value.platform
      })
    })

    const saveData = await saveResponse.json()
    if (!(saveData.status === 'success' || saveData.success)) {
      showMessage('无法预览：' + (saveData.error || '未知错误'), 'error')
      return
    }

    const previewResponse = await fetch('http://localhost:8000/api/render/preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        template: tempName,
        platform: aiGenerateForm.value.platform,
        sample: true
      })
    })

    const previewData = await previewResponse.json()
    if (previewData.status === 'success' && previewData.image_url) {
      previewImageUrl.value = getImageUrl(previewData.image_url)
      showMessage('预览生成成功', 'success')
    } else {
      showMessage('预览生成失败', 'error')
    }

  } catch (error) {
    console.error('预览生成失败:', error)
    showMessage('预览生成失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    isPreviewing.value = false
  }
}

// 获取质量评分样式
const getQualityClass = (score) => {
  if (score >= 90) return 'quality-excellent'
  if (score >= 70) return 'quality-good'
  return 'quality-fair'
}

// 获取质量评分提示
const getQualityHint = (score) => {
  if (score >= 90) return '优秀的代码质量'
  if (score >= 70) return '良好的代码质量'
  return '需要改进'
}

onMounted(async () => {
  // 先加载模板列表
  await loadTemplates()
  // 再加载配色方案
  await loadColorSchemes()
  // 加载字体方案
  await loadFontSchemes()
  // 加载字体配置
  await loadFontConfig()

  // 等待 Vue 更新 DOM
  await nextTick()

  // 再等待一小段时间，确保所有响应式数据已更新
  await new Promise(resolve => setTimeout(resolve, 200))

  // 预加载所有模板预览图（渲染页）
  if (currentTemplates.value.length > 0) {
    const previewPromises = currentTemplates.value.map(tpl => loadTemplatePreview(tpl))
    await Promise.allSettled(previewPromises)
    console.log('✓ 模板预览加载完成，缓存数量:', Object.keys(templatePreviewUrls.value).length)
  } else {
    console.warn('⚠️ 当前模板列表为空，无法预加载')
  }

  // 预加载管理页的模板预览图
  const managerTemplates = currentManagerTemplates.value
  if (managerTemplates && managerTemplates.length > 0) {
    const previewPromises = managerTemplates.map(tpl => loadManagerTemplatePreview(tpl))
    await Promise.allSettled(previewPromises)
    console.log('✓ 管理页模板预览加载完成')
  }
})
</script>

<style scoped>
.render-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 模式切换标签 */
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 4px;
  background: #f5f2ed;
  border-radius: 12px;
  width: fit-content;
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  color: #2c2c2c;
}

.tab-btn.active {
  background: white;
  color: #a88f6e;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 主布局 */
.render-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  align-items: start;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.right-panel {
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
}

/* 内容输入区 */
.input-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.split-config {
  margin-top: 8px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
}

.split-config .sub-label {
  display: block;
  font-size: 12px;
  color: #888;
  margin-bottom: 6px;
}

.split-config .hint {
  display: block;
  font-size: 11px;
  color: #999;
  margin-top: 6px;
}

.form-input,
.form-select,
.form-textarea {
  padding: 12px 16px;
  border: 1px solid #e8e0d5;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.3s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #a88f6e;
  box-shadow: 0 0 0 3px rgba(168, 143, 110, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
}

/* 实时预览区 */
.live-preview-section {
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.live-preview-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #2c2c2c;
  margin-bottom: 12px;
}

.preview-container {
  aspect-ratio: 9 / 16;
  max-height: 350px;
  background: #f5f2ed;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading-state,
.placeholder-state {
  color: #999;
  font-size: 14px;
}

/* 模板选择器 */
.template-selector {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.template-selector h3 {
  font-size: 16px;
  font-weight: 600;
  color: #2c2c2c;
  margin-bottom: 16px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.cover-item-container {
  cursor: pointer;
  transition: all 0.2s ease;
}

.cover-item {
  position: relative;
  aspect-ratio: 9 / 16;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f2ed;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.cover-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-item-container.active .cover-item {
  border-color: #FF2442;
}

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 12px;
}

/* 换配色按钮 */
.change-btn {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
  user-select: none;
  z-index: 10;
}

.change-btn:hover {
  background: white;
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.change-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* 换字体按钮 */
.change-font-btn {
  right: auto;
  left: 8px;
}

.change-font-btn:hover {
  transform: scale(1.05);
}

.cover-name {
  margin-top: 8px;
  text-align: center;
  font-size: 13px;
  color: #666;
}

/* 按钮 */
.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #a88f6e;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #96805e;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f2ed;
  color: #666;
}

.btn-secondary:hover {
  background: #e8e0d5;
}

/* 内容来源选择器 */
.source-selector {
  display: flex;
  gap: 8px;
}

.source-btn {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e8e0d5;
  background: white;
  color: #666;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.source-btn:hover {
  border-color: #a88f6e;
  color: #a88f6e;
}

.source-btn.active {
  background: #a88f6e;
  border-color: #a88f6e;
  color: white;
}

/* 草稿信息 */
.draft-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f9f7f4;
  border-radius: 6px;
  font-size: 12px;
}

.draft-id {
  color: #888;
}

.draft-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-pending_review {
  background: #e2e3e5;
  color: #383d41;
}

.status-published {
  background: #d4edda;
  color: #155724;
}

/* 操作按钮行 */
.action-buttons-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.action-buttons-row .btn-primary,
.action-buttons-row .btn-secondary {
  flex: 1;
}

/* AI生成按钮 */
.btn-ai-generate {
  width: 100%;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn-ai-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-ai-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ai-generate .icon {
  font-size: 16px;
}

.ai-hint {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin-top: 4px;
  margin-bottom: 16px;
}

/* 渲染结果 */
.result-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.result-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c2c2c;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.result-info {
  font-size: 14px;
  font-weight: normal;
  color: #999;
  margin-left: 8px;
}

.slide-nav {
  display: flex;
  gap: 8px;
}

.nav-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e8e0d5;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s ease;
}

.nav-btn:hover:not(:disabled) {
  border-color: #a88f6e;
  color: #a88f6e;
  background: #faf8f5;
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.result-images {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 12px;
  scroll-behavior: smooth;
}

.result-images::-webkit-scrollbar {
  height: 6px;
}

.result-images::-webkit-scrollbar-track {
  background: #f5f2ed;
  border-radius: 3px;
}

.result-images::-webkit-scrollbar-thumb {
  background: #d4c4b0;
  border-radius: 3px;
}

.result-images::-webkit-scrollbar-thumb:hover {
  background: #a88f6e;
}

.image-item {
  flex-shrink: 0;
  width: 220px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0ebe4;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.image-wrapper {
  position: relative;
  aspect-ratio: 9 / 16;
  overflow: hidden;
}

.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 12px;
  text-align: center;
}

.image-actions {
  display: flex;
  padding: 12px;
  gap: 8px;
}

.btn-download,
.btn-copy {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-download {
  background: #a88f6e;
  color: white;
}

.btn-copy {
  background: #f5f2ed;
  color: #666;
}

.btn-download:hover {
  background: #96805e;
}

.btn-copy:hover {
  background: #e8e0d5;
}

/* 模板管理 */
.template-manager {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.manager-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2c2c2c;
  margin: 0;
}

.manager-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 14px;
  color: #666;
}

.stat-item strong {
  color: #a88f6e;
  font-size: 18px;
}

/* 配置信息栏 */
.config-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f5f2ed 0%, #ebe7e0 100%);
  border-radius: 12px;
  margin-bottom: 24px;
}

.font-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #2c2c2c;
  font-weight: 600;
  padding: 6px 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.cache-actions {
  display: flex;
  gap: 12px;
}

.btn-clear-cache {
  padding: 8px 16px;
  border: none;
  background: #a88f6e;
  color: white;
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-clear-cache:hover:not(:disabled) {
  background: #96805e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(168, 143, 110, 0.3);
}

.btn-clear-cache:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ai-generate-inline {
  padding: 8px 16px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-ai-generate-inline:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-ai-generate-inline .icon {
  font-size: 14px;
}

.platform-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 4px;
  background: #f5f2ed;
  border-radius: 12px;
  width: fit-content;
}

.platform-tab {
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.platform-tab:hover {
  color: #2c2c2c;
}

.platform-tab.active {
  background: white;
  color: #a88f6e;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 模板预览网格 - 使用真实预览图 */
.template-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.template-preview-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.template-preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.template-preview-image {
  position: relative;
  aspect-ratio: 9 / 16;
  overflow: hidden;
  cursor: pointer;
  background: #f5f2ed;
}

.template-preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.template-preview-card:hover .template-preview-image img {
  transform: scale(1.05);
}

.preview-loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 13px;
}

.template-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
  display: flex;
  flex-direction: column;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.template-preview-image:hover .template-overlay {
  opacity: 1;
}

.template-overlay .template-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.template-preview-actions {
  display: flex;
  padding: 12px;
  gap: 8px;
  background: white;
  border-top: 1px solid #f0f0f0;
}

.btn-preview-action,
.btn-delete-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-preview-action {
  background: #a88f6e;
  color: white;
}

.btn-preview-action:hover {
  background: #96805e;
}

.btn-delete-action {
  background: #ffebee;
  color: #f44336;
}

.btn-delete-action:hover {
  background: #f44336;
  color: white;
}

.badge-preset {
  flex: 1;
  padding: 8px 12px;
  text-align: center;
  background: #f5f2ed;
  color: #999;
  font-size: 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 预览模态框 */
.preview-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
  animation: fadeIn 0.2s ease;
  padding: 40px;
}

.preview-modal {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

.preview-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.preview-modal-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: #2c2c2c;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #f5f2ed;
  color: #666;
}

.preview-modal-content {
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f2ed;
}

.preview-modal-content img {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.manager-preview-section {
  margin-top: 32px;
  padding: 24px;
  background: #f5f2ed;
  border-radius: 12px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #2c2c2c;
  margin: 0;
}

.btn-close-small {
  padding: 4px 12px;
  border: none;
  background: #e8e0d5;
  color: #666;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
}

.btn-close-small:hover {
  background: #d0c8c0;
}

.preview-content {
  text-align: center;
}

.preview-content img {
  max-width: 300px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
}

.preview-template-name {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}

/* 消息提示 */
.message-toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  padding: 16px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
  z-index: 1000;
}

.message-toast.success {
  background: #4caf50;
  color: white;
}

.message-toast.error {
  background: #f44336;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* 调试信息 */
.debug-info {
  margin-top: 16px;
  padding: 12px;
  background: #f5f2ed;
  border-radius: 8px;
  font-size: 12px;
}

.debug-info summary {
  cursor: pointer;
  color: #666;
  margin-bottom: 8px;
}

.debug-info pre {
  margin: 0;
  padding: 8px;
  background: white;
  border-radius: 4px;
  overflow-x: auto;
  color: #333;
}

.warning-message {
  padding: 12px 16px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  color: #856404;
  margin-bottom: 16px;
}

/* 复选框样式 */
input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

/* AI生成对话框 */
.ai-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.ai-dialog {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
  display: flex;
  flex-direction: column;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.ai-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e8e0d5;
}

.ai-dialog-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c2c2c;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #f5f2ed;
  color: #666;
}

.ai-dialog-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.ai-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e0d5;
}

.ai-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.example-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.hint-tag {
  padding: 6px 12px;
  background: #f5f2ed;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hint-tag:hover {
  background: #a88f6e;
  color: white;
}

.ai-preview-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ai-preview-section h4 {
  font-size: 18px;
  font-weight: 600;
  color: #2c2c2c;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-result-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  background: #f9f9f9;
  padding: 20px;
  border-radius: 12px;
}

/* 预览图片区域 */
.preview-image-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  aspect-ratio: 9 / 16;
  width: 100%;
  background: linear-gradient(135deg, #f5f2ed 0%, #ebe7e0 100%);
  border-radius: 12px;
  border: 2px dashed #d0c8c0;
}

.placeholder-icon {
  font-size: 48px;
  opacity: 0.5;
}

.preview-placeholder p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.btn-preview-large {
  padding: 10px 20px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-preview-large:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.preview-image-container {
  position: relative;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  background: white;
}

.preview-image-container img {
  width: 100%;
  height: auto;
  display: block;
}

.btn-refresh-preview {
  position: absolute;
  bottom: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.btn-refresh-preview:hover:not(:disabled) {
  background: white;
  transform: scale(1.05);
}

/* 信息表单区域 */
.info-form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-info-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quality-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quality-badge {
  padding: 6px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.quality-hint {
  font-size: 13px;
  color: #666;
}

.quality-excellent {
  background: #e8f5e9;
  color: #4caf50;
}

.quality-good {
  background: #fff3e0;
  color: #ff9800;
}

.quality-fair {
  background: #ffebee;
  color: #f44336;
}

.error-list {
  margin-top: 12px;
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
}

.error-title {
  font-size: 13px;
  font-weight: 600;
  color: #856404;
  margin: 0 0 8px 0;
}

.error-list ul {
  margin: 0;
  padding-left: 20px;
}

.error-list li {
  font-size: 12px;
  color: #856404;
  margin-bottom: 4px;
}

.result-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.result-actions button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-save {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-actions .btn-secondary {
  background: #f5f2ed;
  color: #666;
}

.result-actions .btn-secondary:hover {
  background: #e8e0d5;
}

.result-actions .btn-danger {
  border: 1px solid #f44336;
  background: white;
  color: #f44336;
}

.result-actions .btn-danger:hover {
  background: #f44336;
  color: white;
}

/* 响应式布局 */
@media (max-width: 1024px) {
  .render-layout {
    grid-template-columns: 1fr;
  }

  .right-panel {
    position: static;
  }

  .template-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .ai-result-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .template-grid {
    grid-template-columns: 1fr;
  }

  .result-actions {
    flex-direction: column;
  }
}

/* 不同模板的预览样式 */
.tpl-xiaohongshu-minimal { background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%) !important; color: #666 !important; }
.tpl-xiaohongshu-zen { background: #f5f5f0 !important; color: #666 !important; }
.tpl-xiaohongshu-gradient { background: linear-gradient(135deg, #ffe5e5 0%, #ffd0d0 100%) !important; color: #666 !important; }
.tpl-xiaohongshu-modern { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: #fff !important; }
.tpl-xiaohongshu-elegant { background: linear-gradient(to bottom, #F5F5F0 0%, #E8E8E0 100%) !important; color: #666 !important; }
.tpl-xiaohongshu-vibrant { background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #FFB347 100%) !important; color: #fff !important; }
.tpl-douyin-dark { background: #1a1a1a !important; color: #fff !important; }
.tpl-douyin-neon { background: linear-gradient(180deg, #0a0a0a 0%, #2a2a2a 100%) !important; color: #fff !important; }
</style>
