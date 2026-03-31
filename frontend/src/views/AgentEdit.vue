<template>
  <div class="page-container zen-fade-in">
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? '编辑Agent' : '创建Agent' }}</h1>
      <p class="page-subtitle">
        {{ isEdit ? '配置Agent技能链和参数' : '创建新的智能助手' }}
      </p>
      <div class="header-actions">
        <el-button @click="showPreviewDialog = true" size="default">
          📋 查看配置预览
        </el-button>
      </div>
    </div>

    <div class="config-container">
      <!-- 基础信息 -->
      <div class="section-card mb-md">
        <h3 class="form-section-title">基础信息</h3>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label required">Agent ID</label>
            <el-input
              v-model="form.id"
              placeholder="如: novel_writer"
              :disabled="isEdit"
              maxlength="50"
              show-word-limit
            />
            <div class="form-hint">唯一标识符，只能包含字母、数字和下划线</div>
          </div>

          <div class="form-group">
            <label class="form-label required">Agent名称</label>
            <el-input
              v-model="form.name"
              placeholder="如：小说创作助手"
              maxlength="50"
              show-word-limit
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">描述</label>
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="简要描述Agent的功能和用途"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">LLM提供商</label>
            <el-select v-model="form.llm_provider" style="width: 100%;">
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="通义千问" value="qwen" />
              <el-option label="月之暗面" value="moonshot" />
            </el-select>
          </div>

          <div class="form-group">
            <label class="form-label">启用状态</label>
            <div class="switch-wrapper">
              <el-switch v-model="form.enabled" />
              <span class="switch-label">{{ form.enabled ? '已启用' : '已禁用' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 调度配置 -->
      <div class="section-card mb-md">
        <h3 class="form-section-title">调度配置</h3>

        <div class="form-group" v-if="form.enabled">
          <label class="form-label">Cron表达式</label>
          <el-input
            v-model="form.schedule"
            placeholder="如: 0 */2 * * * (每2小时)"
          />
          <div class="form-hint">
            <a href="https://crontab.guru/" target="_blank">Cron表达式参考</a>
            <span class="schedule-examples">
              常用:
              <el-button size="small" text @click="form.schedule = '0 */2 * * *'">每2小时</el-button>
              <el-button size="small" text @click="form.schedule = '0 9 * * *'">每天9点</el-button>
              <el-button size="small" text @click="form.schedule = '0 9,12,18 * * *'">每天3次</el-button>
            </span>
          </div>
        </div>

        <el-alert v-else type="info" :closable="false">
          Agent已禁用，不会自动执行
        </el-alert>
      </div>

      <!-- 账户绑定（只读） -->
      <div class="section-card mb-md">
        <h3 class="form-section-title">账户绑定</h3>
        <div class="form-group">
          <label class="form-label">绑定账户</label>
          <div v-if="boundAccountInfo" class="bound-account-info">
            <el-tag type="success" size="large">
              {{ boundAccountInfo.name }} ({{ boundAccountInfo.platform }})
            </el-tag>
          </div>
          <el-alert v-else type="warning" :closable="false">
            未绑定账户，请在 
            <router-link to="/accounts">账户管理</router-link> 
            页面进行绑定
          </el-alert>
        </div>
      </div>

      <!-- Skill链配置 -->
      <div class="section-card mb-md">
        <h3 class="form-section-title">Skill链配置</h3>
        <p class="form-hint mb-md">
          拖拽Skill到右侧构建执行流程，按顺序执行。点击"查看配置预览"可查看完整的YAML配置和执行流程。
        </p>

        <SkillChainBuilder 
          v-model="form.skill_chain" 
          :account_id="form.account_id"
          :agent-id="form.id"
        />
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button @click="router.back()">取消</el-button>
        <el-button type="primary" @click="saveAgent" :loading="saving">
          {{ isEdit ? '保存修改' : '创建Agent' }}
        </el-button>
      </div>
    </div>

    <!-- 配置预览弹窗 -->
    <el-dialog
      v-model="showPreviewDialog"
      title="Agent配置预览"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="activeTab">
        <!-- YAML配置 -->
        <el-tab-pane label="YAML配置" name="yaml">
          <div class="yaml-preview-dialog">
            <pre>{{ yamlConfig }}</pre>
          </div>
        </el-tab-pane>

        <!-- 执行流程 -->
        <el-tab-pane label="执行流程" name="flow">
          <div class="flow-preview-dialog">
            <div
              v-for="(skill, index) in form.skill_chain"
              :key="skill.id"
              class="flow-step"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-header">
                  <div class="step-name">{{ getSkillLabel(skill.skill) }}</div>
                  <el-tag size="small" :type="getSkillType(skill.skill)">
                    {{ getSkillCategory(skill.skill) }}
                  </el-tag>
                </div>
                <div class="step-config">{{ getConfigSummary(skill) }}</div>
              </div>
              <div class="step-arrow" v-if="index < form.skill_chain.length - 1">↓</div>
            </div>

            <el-empty
              v-if="form.skill_chain.length === 0"
              description="添加Skill后将显示执行流程"
              :image-size="80"
            />
          </div>
        </el-tab-pane>

        <!-- 数据流说明 -->
        <el-tab-pane label="数据流" name="dataflow">
          <div class="dataflow-preview-dialog">
            <el-alert
              title="数据累积模式"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            >
              <template #default>
                <p>每个 Skill 会累积数据到数据流中，后续 Skill 可以访问之前所有 Skill 的输出数据。</p>
                <pre style="margin-top: 10px; background: #f5f7fa; padding: 10px; border-radius: 4px;">result = {**input_data, **skill_result}</pre>
              </template>
            </el-alert>

            <div v-if="form.skill_chain.length > 0" class="dataflow-steps">
              <div
                v-for="(skill, index) in form.skill_chain"
                :key="skill.id"
                class="dataflow-step"
              >
                <div class="step-title">
                  <span class="step-index">{{ index + 1 }}. {{ getSkillLabel(skill.skill) }}</span>
                </div>
                <div class="step-output">
                  <strong>输出字段：</strong>
                  <el-tag
                    v-for="field in getSkillOutputFields(skill.skill)"
                    :key="field"
                    size="small"
                    style="margin: 2px"
                  >
                    {{ field }}
                  </el-tag>
                </div>
              </div>

              <div class="dataflow-accumulation">
                <h4>最终数据结构：</h4>
                <pre>{{ getDataflowStructure() }}</pre>
              </div>
            </div>

            <el-empty
              v-else
              description="添加Skill后将显示数据流"
              :image-size="80"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button type="primary" @click="showPreviewDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import SkillChainBuilder from '@/components/SkillChainBuilder.vue'
import { agents } from '@/api'
import yaml from 'js-yaml'

const router = useRouter()
const route = useRoute()

// 表单数据
const form = ref({
  id: '',
  name: '',
  description: '',
  enabled: true,
  llm_provider: 'deepseek',
  schedule: '0 */2 * * *',
  account_id: null,
  skill_chain: []
})

// 状态
const saving = ref(false)
const isEdit = computed(() => !!route.params.id)
const showPreviewDialog = ref(false)
const activeTab = ref('yaml')
const boundAccountInfo = ref(null)

// 计算YAML配置
const yamlConfig = computed(() => {
  if (form.value.skill_chain.length === 0) {
    return '# 配置您的Agent\n#\n# 1. 填写基础信息\n# 2. 添加Skill到执行链\n# 3. 配置调度时间\n# 4. 保存并运行'
  }

  const config = {
    agent: {
      id: form.value.id || form.value.name.toLowerCase().replace(/\s+/g, '_'),
      name: form.value.name,
      description: form.value.description || form.value.name,
      enabled: form.value.enabled,
      llm_provider: form.value.llm_provider,
      schedule: form.value.schedule,
      skill_chain: form.value.skill_chain.map(item => ({
        skill: item.skill,
        config: item.config || {}
      }))
    }
  }

  try {
    return yaml.dump(config, {
      allowUnicode: true,
      defaultFlowStyle: false,
      sortKeys: false
    })
  } catch (e) {
    return '# 配置生成错误\n' + e.message
  }
})

// 加载Agent数据
const loadAgent = async () => {
  if (!isEdit.value) return

  try {
    const data = await agents.getAgent(route.params.id)

    // 解析YAML配置
    let agentConfig = {}
    if (data.config) {
      try {
        agentConfig = yaml.load(data.config)
      } catch (e) {
        console.error('Failed to parse config:', e)
      }
    }

    // 填充表单
    const agent = agentConfig.agent || agentConfig
    if (agent) {
      form.value.id = agent.id || ''
      form.value.name = agent.name || ''
      form.value.description = agent.description || ''
      form.value.enabled = agent.enabled !== false
      form.value.llm_provider = agent.llm_provider || 'deepseek'
      form.value.account_id = data.account_id || null
      boundAccountInfo.value = data.bound_account || null
      
      // 处理schedule：可能是对象（{cron, timezone}）或字符串
      if (typeof agent.schedule === 'object' && agent.schedule !== null) {
        form.value.schedule = agent.schedule.cron || '0 */2 * * *'
      } else {
        form.value.schedule = agent.schedule || '0 */2 * * *'
      }

      // 转换skill_chain
      if (agent.skill_chain && Array.isArray(agent.skill_chain)) {
        form.value.skill_chain = agent.skill_chain.map(skill => ({
          id: Date.now() + Math.random(),
          skill: skill.skill,
          config: skill.config || {}
        }))
      }
    }
  } catch (error) {
    ElMessage.error('加载Agent失败: ' + error.message)
  }
}

// 保存Agent
const saveAgent = async () => {
  // 验证
  if (!form.value.id) {
    ElMessage.warning('请输入Agent ID')
    return
  }
  if (!form.value.name) {
    ElMessage.warning('请输入Agent名称')
    return
  }
  if (form.value.skill_chain.length === 0) {
    ElMessage.warning('请至少添加一个Skill')
    return
  }

  saving.value = true
  try {
    // 生成YAML配置
    const config = {
      agent: {
        id: form.value.id,
        name: form.value.name,
        description: form.value.description,
        enabled: form.value.enabled,
        llm_provider: form.value.llm_provider,
        schedule: {
          cron: form.value.schedule,
          timezone: 'Asia/Shanghai'
        },
        skill_chain: form.value.skill_chain.map(item => ({
          skill: item.skill,
          config: item.config || {}
        }))
      }
    }

    const yamlStr = yaml.dump(config, {
      allowUnicode: true,
      defaultFlowStyle: false,
      sortKeys: false
    })

    const payload = {
      id: form.value.id,
      name: form.value.name,
      enabled: form.value.enabled,
      config: yamlStr
    }

    console.log('=== 保存Agent ===')
    console.log('是否为编辑模式:', isEdit.value)
    console.log('Agent ID:', route.params.id)
    console.log('Payload:', payload)
    console.log('YAML配置:', yamlStr)

    if (isEdit.value) {
      console.log('调用 updateAgent API...')
      await agents.updateAgent(route.params.id, payload)
      ElMessage.success('更新成功')
    } else {
      console.log('调用 createAgent API...')
      await agents.createAgent(payload)
      ElMessage.success('创建成功')
    }

    router.push('/agents')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

// 刷新预览
const refreshPreview = () => {
  showPreviewDialog.value = true
}

// 辅助函数
const getSkillLabel = (skillName) => {
  return skillName.split('.').pop().replace('_', ' ')
}

const getSkillCategory = (skillName) => {
  const categoryMap = {
    'generation': '内容生成',
    'review': '内容审核',
    'render': '渲染',
    'publishing': '发布',
    'collection': '采集',
    'processing': '处理',
    'conditional': '条件'
  }
  const prefix = skillName.split('.')[0]
  return categoryMap[prefix] || '其他'
}

const getSkillType = (skillName) => {
  const typeMap = {
    'generation': 'primary',
    'review': 'warning',
    'render': 'success',
    'publishing': 'info',
    'collection': '',
    'processing': '',
    'conditional': 'danger'
  }
  const prefix = skillName.split('.')[0]
  return typeMap[prefix] || ''
}

const getConfigSummary = (skill) => {
  const config = skill.config || {}
  const parts = []

  if (config.sources && Array.isArray(config.sources)) {
    parts.push(`数据源: ${config.sources.join(', ')}`)
  }
  if (config.platform) parts.push(`平台: ${config.platform}`)
  if (config.template) parts.push(config.template)
  if (config.min_score) parts.push(`≥${config.min_score}分`)
  if (config.strictness) parts.push(config.strictness)
  if (config.prompt_template) parts.push('自定义模板')
  if (config.max_tokens) parts.push(`${config.max_tokens} tokens`)
  if (config.use_ai !== undefined) parts.push(config.use_ai ? 'AI审核' : '规则审核')
  if (config.use_llm !== undefined) parts.push(config.use_llm ? 'LLM分析' : '热度排序')
  if (config.count) parts.push(`推荐${config.count}个`)
  if (config.force_refresh) parts.push('强制刷新')

  return parts.length > 0 ? parts.join(' | ') : '默认配置'
}

// 获取Skill输出字段
const getSkillOutputFields = (skillName) => {
  const fieldMap = {
    'collection.rss': ['items', 'total', 'source'],
    'processing.analyze_topic': ['topics', 'analysis_summary', 'llm_info'],
    'processing.clean': ['text', 'cleaned_length', 'original_length'],
    'generation.text': ['parsed_title', 'parsed_content', 'parsed_tags', 'tags'],
    'generation.render': ['rendered_images', 'total_pages', 'image_paths'],
    'review.sensitive': ['is_safe', 'risk_level', 'detected_items'],
    'review.quality': ['overall_score', 'is_qualified', 'scores'],
    'conditional.save': ['should_save', 'reasons'],
    'publishing.draft': ['draft_id', 'status'],
    'publishing.publish': ['success', 'post_url']
  }
  return fieldMap[skillName] || []
}

// 获取数据流结构
const getDataflowStructure = () => {
  let fields = []
  form.value.skill_chain.forEach(skill => {
    const skillFields = getSkillOutputFields(skill.skill)
    fields = [...fields, ...skillFields]
  })

  // 去重
  fields = [...new Set(fields)]

  return {
    accumulated_data: fields.reduce((obj, field) => {
      obj[field] = '...'
      return obj
    }, {})
  }
}

// 初始化
onMounted(() => {
  loadAgent()
})
</script>

<style scoped>
/* 页面容器 */
.config-container {
  max-width: 900px;
  margin: 0 auto;
}

/* Header actions */
.header-actions {
  margin-top: 16px;
}

/* 卡片样式 */
.section-card {
  background: white;
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 12px;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.form-section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #333;
}

.bound-account-info {
  padding: 8px 0;
}

/* 间距 */
.mb-md {
  margin-bottom: 24px;
}

/* 表单样式 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-label.required::after {
  content: '*';
  color: #f56c6c;
  margin-left: 4px;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.form-hint a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.schedule-examples {
  margin-left: 8px;
}

.switch-wrapper {
  display: flex;
  align-items: center;
  height: 32px;
}

.switch-label {
  margin-left: 12px;
  font-size: 14px;
  color: #666;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 0;
}

/* Dialog预览样式 */
.yaml-preview-dialog {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.yaml-preview-dialog pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.flow-preview-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.dataflow-preview-dialog {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
}

.dataflow-steps {
  margin-top: 16px;
}

.dataflow-step {
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.step-title {
  font-weight: 500;
  margin-bottom: 8px;
}

.step-index {
  color: var(--el-color-primary);
}

.step-output {
  font-size: 13px;
  color: #666;
}

.dataflow-accumulation {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.dataflow-accumulation h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.dataflow-accumulation pre {
  margin: 0;
  font-size: 12px;
  color: #333;
  overflow-x: auto;
}

.flow-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  background: white;
  border-radius: 6px;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.step-config {
  font-size: 12px;
  color: #999;
}

.step-arrow {
  font-size: 18px;
  color: var(--el-color-primary);
  flex-shrink: 0;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .config-container {
    max-width: 100%;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
