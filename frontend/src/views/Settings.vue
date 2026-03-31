<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-subtitle">规矩方圆，行之有效</p>
    </div>

    <!-- 设置标签页 -->
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 基础设置 -->
      <el-tab-pane label="基础设置" name="basic">
        <div class="setting-section">
          <h3 class="section-title">系统信息</h3>
          <div class="info-card">
            <div class="info-item">
              <span class="info-label">系统名称</span>
              <span class="info-value">觉知矩阵</span>
            </div>
            <div class="info-item">
              <span class="info-label">系统版本</span>
              <span class="info-value">v1.0.0</span>
            </div>
            <div class="info-item">
              <span class="info-label">运行时间</span>
              <span class="info-value">{{ systemInfo.uptime }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最后更新</span>
              <span class="info-value">{{ systemInfo.lastUpdate }}</span>
            </div>
          </div>
        </div>

        <div class="setting-section">
          <h3 class="section-title">通用设置</h3>
          <div class="form-group">
            <label class="form-label">系统名称</label>
            <el-input v-model="settings.systemName" placeholder="觉知矩阵" />
          </div>

          <div class="form-group">
            <label class="form-label">默认语言</label>
            <el-select v-model="settings.language" style="width: 200px">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </div>

          <div class="form-group">
            <label class="form-label">时区设置</label>
            <el-select v-model="settings.timezone" style="width: 200px">
              <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
              <el-option label="Asia/Hong_Kong" value="Asia/Hong_Kong" />
              <el-option label="UTC" value="UTC" />
            </el-select>
          </div>

          <div class="form-group">
            <label class="form-label">主题风格</label>
            <el-radio-group v-model="settings.theme">
              <el-radio label="zen">禅意极简</el-radio>
              <el-radio label="light">明亮</el-radio>
              <el-radio label="dark">暗色</el-radio>
            </el-radio-group>
          </div>
        </div>

        <div class="setting-actions">
          <el-button @click="resetSettings">重置</el-button>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </div>

        <div class="setting-section" style="margin-top: 32px">
          <h3 class="section-title">账户信息</h3>
          <div class="account-card">
            <div class="account-info">
              <div class="account-avatar">
                {{ user?.username?.charAt(0)?.toUpperCase() || 'U' }}
              </div>
              <div class="account-details">
                <div class="account-name">{{ user?.username || '未登录' }}</div>
                <div class="account-role">{{ userRole }}</div>
              </div>
            </div>
            <el-button @click="handleLogout" type="danger" plain>退出登录</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- LLM配置 -->
      <el-tab-pane label="LLM配置" name="llm">
        <div class="setting-section">
          <h3 class="section-title">默认提供商</h3>
          <div class="form-group">
            <label class="form-label">选择默认LLM</label>
            <el-select v-model="llmSettings.defaultProvider" style="width: 200px">
              <el-option label="通义千问" value="qianwen" />
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="文心一言" value="wenxin" />
            </el-select>
          </div>
        </div>

        <div class="setting-section">
          <h3 class="section-title">API密钥配置</h3>

          <!-- 通义千问 -->
          <div class="provider-card">
            <div class="provider-header">
              <span class="provider-icon">🌙</span>
              <span class="provider-name">通义千问</span>
              <el-switch v-model="llmSettings.providers.qianwen.enabled" />
            </div>
            <div v-if="llmSettings.providers.qianwen.enabled" class="provider-body">
              <div class="form-group">
                <label class="form-label">API Key</label>
                <el-input
                  v-model="llmSettings.providers.qianwen.apiKey"
                  type="password"
                  placeholder="sk-xxxxxxxxxxxx"
                  show-password
                />
              </div>
              <div class="form-group">
                <label class="form-label">模型</label>
                <el-select v-model="llmSettings.providers.qianwen.model" style="width: 200px">
                  <el-option label="qwen-plus" value="qwen-plus" />
                  <el-option label="qwen-turbo" value="qwen-turbo" />
                  <el-option label="qwen-max" value="qwen-max" />
                </el-select>
              </div>
              <el-button size="small" @click="testConnection('qianwen')">测试连接</el-button>
            </div>
          </div>

          <!-- DeepSeek -->
          <div class="provider-card">
            <div class="provider-header">
              <span class="provider-icon">🔍</span>
              <span class="provider-name">DeepSeek</span>
              <el-switch v-model="llmSettings.providers.deepseek.enabled" />
            </div>
            <div v-if="llmSettings.providers.deepseek.enabled" class="provider-body">
              <div class="form-group">
                <label class="form-label">API Key</label>
                <el-input
                  v-model="llmSettings.providers.deepseek.apiKey"
                  type="password"
                  placeholder="sk-xxxxxxxxxxxx"
                  show-password
                />
              </div>
              <div class="form-group">
                <label class="form-label">模型</label>
                <el-select v-model="llmSettings.providers.deepseek.model" style="width: 200px">
                  <el-option label="deepseek-chat" value="deepseek-chat" />
                  <el-option label="deepseek-coder" value="deepseek-coder" />
                </el-select>
              </div>
              <el-button size="small" @click="testConnection('deepseek')">测试连接</el-button>
            </div>
          </div>

          <!-- 文心一言 -->
          <div class="provider-card">
            <div class="provider-header">
              <span class="provider-icon">🧠</span>
              <span class="provider-name">文心一言</span>
              <el-switch v-model="llmSettings.providers.wenxin.enabled" />
            </div>
            <div v-if="llmSettings.providers.wenxin.enabled" class="provider-body">
              <div class="form-group">
                <label class="form-label">API Key</label>
                <el-input
                  v-model="llmSettings.providers.wenxin.apiKey"
                  type="password"
                  placeholder="xxxxxxxxxxxx"
                  show-password
                />
              </div>
              <div class="form-group">
                <label class="form-label">Secret Key</label>
                <el-input
                  v-model="llmSettings.providers.wenxin.secretKey"
                  type="password"
                  placeholder="xxxxxxxxxxxx"
                  show-password
                />
              </div>
              <div class="form-group">
                <label class="form-label">模型</label>
                <el-select v-model="llmSettings.providers.wenxin.model" style="width: 200px">
                  <el-option label="ERNIE-4.0-8K" value="ERNIE-4.0-8K" />
                  <el-option label="ERNIE-3.5-8K" value="ERNIE-3.5-8K" />
                </el-select>
              </div>
              <el-button size="small" @click="testConnection('wenxin')">测试连接</el-button>
            </div>
          </div>
        </div>

        <div class="setting-actions">
          <el-button type="primary" @click="saveLLMSettings">保存配置</el-button>
        </div>
      </el-tab-pane>

      <!-- 审核规则 -->
      <el-tab-pane label="审核规则" name="review">
        <div class="setting-section">
          <h3 class="section-title">敏感词检测</h3>
          <div class="form-group">
            <label class="form-label">启用敏感词检测</label>
            <el-switch v-model="reviewSettings.sensitiveWordEnabled" />
          </div>

          <div class="form-group">
            <label class="form-label">检测类别</label>
            <el-checkbox-group v-model="reviewSettings.sensitiveCategories">
              <el-checkbox label="politics">政治敏感</el-checkbox>
              <el-checkbox label="porn">色情内容</el-checkbox>
              <el-checkbox label="violence">暴力恐怖</el-checkbox>
              <el-checkbox label="spam">垃圾广告</el-checkbox>
              <el-checkbox label="illegal">违法违规</el-checkbox>
            </el-checkbox-group>
          </div>

          <div class="form-group">
            <label class="form-label">自定义敏感词</label>
            <el-input
              v-model="reviewSettings.customWords"
              type="textarea"
              :rows="3"
              placeholder="每行一个词"
            />
            <div class="form-hint">每行一个敏感词，支持中英文</div>
          </div>
        </div>

        <div class="setting-section">
          <h3 class="section-title">质量评分</h3>
          <div class="form-group">
            <label class="form-label">启用质量评分</label>
            <el-switch v-model="reviewSettings.qualityScoreEnabled" />
          </div>

          <div class="form-group">
            <label class="form-label">最低质量阈值</label>
            <el-slider
              v-model="reviewSettings.minQualityScore"
              :min="0"
              :max="100"
              :step="5"
              show-input
            />
            <div class="form-hint">低于此分数的内容将被标记为低质量</div>
          </div>

          <div class="form-group">
            <label class="form-label">评分权重</label>
            <div class="score-weights">
              <div class="weight-item">
                <span class="weight-label">可读性</span>
                <el-slider
                  v-model="reviewSettings.weights.readability"
                  :min="0"
                  :max="100"
                  :step="5"
                />
              </div>
              <div class="weight-item">
                <span class="weight-label">完整性</span>
                <el-slider
                  v-model="reviewSettings.weights.completeness"
                  :min="0"
                  :max="100"
                  :step="5"
                />
              </div>
              <div class="weight-item">
                <span class="weight-label">吸引力</span>
                <el-slider
                  v-model="reviewSettings.weights.attractiveness"
                  :min="0"
                  :max="100"
                  :step="5"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="setting-actions">
          <el-button type="primary" @click="saveReviewSettings">保存规则</el-button>
        </div>
      </el-tab-pane>

      <!-- 提示词模板 -->
      <el-tab-pane label="提示词模板" name="prompt-templates">
        <div class="setting-section">
          <div class="section-header">
            <h3 class="section-title">提示词模板管理</h3>
            <el-button type="primary" @click="goToPromptTemplates">管理模板</el-button>
          </div>

          <div class="template-stats">
            <div class="stat-card">
              <div class="stat-icon">📋</div>
              <div class="stat-content">
                <div class="stat-value">{{ templateStats.total }}</div>
                <div class="stat-label">总模板数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">✅</div>
              <div class="stat-content">
                <div class="stat-value">{{ templateStats.active }}</div>
                <div class="stat-label">已启用</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📁</div>
              <div class="stat-content">
                <div class="stat-value">{{ templateStats.categories }}</div>
                <div class="stat-label">分类数</div>
              </div>
            </div>
          </div>

          <div class="quick-templates">
            <h4 class="subsection-title">快速访问</h4>
            <div class="template-list">
              <div 
                v-for="template in recentTemplates" 
                :key="template.id" 
                class="template-item"
                @click="editTemplate(template.id)"
                style="cursor: pointer;"
              >
                <div class="template-info">
                  <span class="template-name">{{ template.name }}</span>
                  <el-tag size="small" type="info">{{ template.category }}</el-tag>
                </div>
                <el-button size="small" @click.stop="editTemplate(template.id)">编辑</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知设置" name="notification">
        <div class="setting-section">
          <h3 class="section-title">通知方式</h3>
          <div class="form-group">
            <label class="form-label">启用通知</label>
            <el-switch v-model="notificationSettings.enabled" />
          </div>

          <div class="form-group">
            <label class="form-label">通知渠道</label>
            <el-checkbox-group v-model="notificationSettings.channels">
              <el-checkbox label="email">邮件通知</el-checkbox>
              <el-checkbox label="webhook">Webhook</el-checkbox>
              <el-checkbox label="telegram">Telegram</el-checkbox>
            </el-checkbox-group>
          </div>
        </div>

        <div class="setting-section">
          <h3 class="section-title">通知事件</h3>
          <div class="notification-events">
            <div class="event-item">
              <span class="event-label">Agent执行完成</span>
              <el-switch v-model="notificationSettings.events.agentCompleted" />
            </div>
            <div class="event-item">
              <span class="event-label">内容审核通过</span>
              <el-switch v-model="notificationSettings.events.contentApproved" />
            </div>
            <div class="event-item">
              <span class="event-label">内容审核失败</span>
              <el-switch v-model="notificationSettings.events.contentRejected" />
            </div>
            <div class="event-item">
              <span class="event-label">发布成功</span>
              <el-switch v-model="notificationSettings.events.publishSuccess" />
            </div>
            <div class="event-item">
              <span class="event-label">发布失败</span>
              <el-switch v-model="notificationSettings.events.publishFailed" />
            </div>
            <div class="event-item">
              <span class="event-label">系统异常</span>
              <el-switch v-model="notificationSettings.events.systemError" />
            </div>
          </div>
        </div>

        <div class="setting-actions">
          <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
        </div>
      </el-tab-pane>

      <!-- 关于 -->
      <el-tab-pane label="关于" name="about">
        <div class="about-section">
          <div class="about-logo">
            <div class="logo-icon">☸️</div>
            <div class="logo-text">觉知矩阵</div>
            <div class="logo-version">v1.0.0</div>
          </div>

          <div class="about-info">
            <h3>项目简介</h3>
            <p>
              觉知矩阵是一个AI驱动的内容矩阵管理系统，支持多个Agent自动生成内容并发布到小红书、抖音等平台。
              每个Agent有独立的人设和技能链，可以实现内容采集、处理、生成和发布的全流程自动化。
            </p>

            <h3>技术栈</h3>
            <div class="tech-stack">
              <span class="tech-tag">FastAPI</span>
              <span class="tech-tag">Vue 3</span>
              <span class="tech-tag">Element Plus</span>
              <span class="tech-tag">ECharts</span>
              <span class="tech-tag">Playwright</span>
              <span class="tech-tag">APScheduler</span>
            </div>

            <h3>开源协议</h3>
            <p>MIT License</p>

            <h3>联系方式</h3>
            <p>GitHub: agent-matrix</p>
            <p>Email: support@agent-matrix.com</p>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { settings as settingsApi, promptTemplates } from '@/api'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const authStore = useAuthStore()
const { logout } = useAuth()

const activeTab = ref('basic')
const user = computed(() => authStore.user)
const userRole = computed(() => user.value?.role || '普通用户')

// 提示词模板统计
const templateStats = ref({
  total: 0,
  active: 0,
  categories: 0
})

const recentTemplates = ref([])

// 加载模板统计
const loadTemplateStats = async () => {
  try {
    const templates = await promptTemplates.getTemplates()
    templateStats.value = {
      total: templates.length,
      active: templates.filter(t => t.is_active).length,
      categories: [...new Set(templates.map(t => t.category))].length
    }
    recentTemplates.value = templates.slice(0, 5) // 显示前5个模板
  } catch (error) {
    console.error('加载模板统计失败:', error)
  }
}

// 跳转到模板管理页面
const goToPromptTemplates = () => {
  router.push('/prompt-templates')
}

// 编辑指定模板
const editTemplate = (templateId) => {
  router.push({
    path: '/prompt-templates',
    query: { templateId }
  })
}

// 系统信息
const systemInfo = ref({
  uptime: '15天 8小时 32分钟',
  lastUpdate: '2026-02-26 10:30:00'
})

// 基础设置
const settings = ref({
  systemName: '觉知矩阵',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  theme: 'zen'
})

// 应用主题
const applyTheme = (theme) => {
  const root = document.documentElement
  root.setAttribute('data-theme', theme)

  // 保存到localStorage
  localStorage.setItem('theme', theme)
}

// 监听主题变化
watch(() => settings.value.theme, (newTheme) => {
  applyTheme(newTheme)
})

// 组件挂载时加载保存的主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme') || 'zen'
  settings.value.theme = savedTheme
  applyTheme(savedTheme)
  loadTemplateStats()
  loadReviewSettings()
})

// LLM设置
const llmSettings = ref({
  defaultProvider: 'deepseek',
  providers: {
    qianwen: {
      enabled: false,
      apiKey: '',
      model: 'qwen-plus'
    },
    deepseek: {
      enabled: true,
      apiKey: 'sk-819ee676945e41c1a74f3153b35cfcd7',
      model: 'deepseek-chat'
    },
    wenxin: {
      enabled: false,
      apiKey: '',
      secretKey: '',
      model: 'ERNIE-4.0-8K'
    }
  }
})

// 审核规则
const reviewSettings = ref({
  sensitiveWordEnabled: true,
  sensitiveCategories: ['politics', 'porn', 'violence'],
  customWords: '',
  qualityScoreEnabled: true,
  minQualityScore: 60,
  weights: {
    readability: 30,
    completeness: 40,
    attractiveness: 30
  }
})

// 加载审核设置
const loadReviewSettings = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/review-settings')
    const data = await response.json()
    reviewSettings.value = {
      sensitiveWordEnabled: data.sensitive_word_enabled ?? true,
      sensitiveCategories: data.sensitive_categories || ['politics', 'porn', 'violence'],
      customWords: data.custom_words || '',
      qualityScoreEnabled: data.quality_score_enabled ?? true,
      minQualityScore: data.min_quality_score ?? 60,
      weights: data.weights || { readability: 30, completeness: 40, attractiveness: 30 }
    }
  } catch (error) {
    console.error('加载审核设置失败:', error)
  }
}

// 保存审核设置
const saveReviewSettings = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/review-settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sensitive_word_enabled: reviewSettings.value.sensitiveWordEnabled,
        sensitive_categories: reviewSettings.value.sensitiveCategories,
        custom_words: reviewSettings.value.customWords,
        quality_score_enabled: reviewSettings.value.qualityScoreEnabled,
        min_quality_score: reviewSettings.value.minQualityScore,
        weights: reviewSettings.value.weights
      })
    })
    
    if (response.ok) {
      ElMessage.success('审核规则保存成功')
    } else {
      throw new Error('保存失败')
    }
  } catch (error) {
    ElMessage.error('保存审核设置失败: ' + error.message)
  }
}

// 通知设置
const notificationSettings = ref({
  enabled: true,
  channels: ['email'],
  events: {
    agentCompleted: true,
    contentApproved: true,
    contentRejected: true,
    publishSuccess: true,
    publishFailed: true,
    systemError: true
  }
})

const saveSettings = async () => {
  try {
    await settingsApi.updateSettings(settings.value)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

const resetSettings = () => {
  settings.value = {
    systemName: '觉知矩阵',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    theme: 'zen'
  }
  ElMessage.success('设置已重置')
}

const handleLogout = async () => {
  try {
    await logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error('退出失败: ' + error.message)
  }
}

const saveLLMSettings = () => {
  ElMessage.success('LLM配置保存成功')
}

const testConnection = async (provider) => async () => {
  ElMessage.info(`正在测试 ${provider} 连接...`)
  try {
    await settingsApi.testLLMConnection(provider)
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败: ' + error.message)
  }
}

const saveNotificationSettings = () => {
  ElMessage.success('通知设置保存成功')
}
</script>

<style scoped>
.settings-tabs {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.setting-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--color-divider);
}

.setting-section:last-child {
  border-bottom: none;
}

.section-title {
  font-family: var(--font-family-title);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-placeholder);
  margin-top: 4px;
}

/* 信息卡片 */
.info-card {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 20px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* 提供商卡片 */
.provider-card {
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  overflow: hidden;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: var(--color-bg-secondary);
}

.provider-icon {
  font-size: 24px;
}

.provider-name {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.provider-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 评分权重 */
.score-weights {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-label {
  width: 60px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 通知事件 */
.notification-events {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.event-label {
  font-size: 14px;
  color: var(--color-text-primary);
}

/* 设置操作按钮 */
.setting-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--color-divider);
}

/* 关于页面 */
.about-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.about-logo {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.logo-text {
  font-family: var(--font-family-title);
  font-size: 32px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.logo-version {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.about-info {
  max-width: 600px;
  width: 100%;
}

.about-info h3 {
  font-family: var(--font-family-title);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 24px 0 12px 0;
}

.about-info p {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-tag {
  padding: 6px 12px;
  background: var(--color-accent-light);
  border-radius: var(--border-radius-small);
  font-size: 13px;
  color: var(--color-accent);
}

/* 响应式 */
@media (max-width: 600px) {
  .info-card {
    grid-template-columns: 1fr;
  }

  .event-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .weight-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .weight-label {
    width: 100%;
  }
}

/* 提示词模板相关样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-description {
  color: var(--color-text-secondary);
  margin-bottom: 24px;
  font-size: 14px;
}

.template-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.quick-templates {
  margin-top: 24px;
}

.subsection-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  transition: all 0.3s;
}

.template-item:hover {
  border-color: var(--color-accent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.template-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 账户卡片样式 */
.account-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
}

.account-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.account-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.account-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.account-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.account-role {
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
