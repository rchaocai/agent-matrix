<template>
  <div class="skill-chain-builder">
    <!-- 已选择的Skill链 -->
    <div class="chain-section">
      <div class="section-header">
        <h3>Skill链配置</h3>
        <el-button size="small" @click="clearChain" v-if="skillChain.length > 0">清空</el-button>
      </div>

      <div class="chain-list">
        <draggable
          v-model="skillChain"
          item-key="id"
          handle=".drag-handle"
          @change="onChainChange"
          class="draggable-list"
        >
          <template #item="{ element: item, index }">
            <div class="chain-item" :class="{ 'error': item.error }">
              <div class="drag-handle">⋮⋮</div>
              <div class="item-content">
                <div class="item-header">
                  <span class="skill-name">{{ getSkillLabel(item.skill) }}</span>
                  <el-tag size="small" :type="getSkillType(item.skill)">
                    {{ getSkillCategory(item.skill) }}
                  </el-tag>
                </div>
                <div class="item-description">
                  {{ getSkillDescription(item.skill) }}
                </div>
                <!-- 配置参数 -->
                <div class="item-config" v-if="item.config">
                  <el-button
                    size="small"
                    text
                    @click="editConfig(item)"
                  >
                    ⚙️ 配置参数
                  </el-button>
                  <span class="config-summary">
                    {{ getConfigSummary(item) }}
                  </span>
                </div>
              </div>
              <el-button
                size="small"
                type="danger"
                text
                @click="removeSkill(index)"
                class="remove-btn"
              >
                ✕
              </el-button>
            </div>
          </template>
        </draggable>

        <el-empty
          v-if="skillChain.length === 0"
          description="拖拽Skill到此处构建流程"
          :image-size="80"
        />
      </div>
    </div>

    <!-- Skill选择器 -->
    <div class="skills-section">
      <div class="section-header">
        <h3>可用Skill</h3>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索Skill..."
          size="small"
          style="width: 200px"
          clearable
        />
      </div>

      <div class="skills-list">
        <div
          v-for="category in filteredCategories"
          :key="category.category"
          class="skill-category"
        >
          <div class="category-header">
            <span class="category-label">{{ category.label }}</span>
            <span class="category-count">({{ category.skills.length }})</span>
          </div>
          <div class="category-skills">
            <div
              v-for="skill in category.skills"
              :key="skill.name"
              class="skill-card"
              :class="{ disabled: isSkillAdded(skill.name) }"
              draggable="true"
              @dragstart="onDragStart($event, skill)"
              @click="addSkill(skill)"
            >
              <div class="skill-icon">{{ getSkillIcon(skill.name) }}</div>
              <div class="skill-info">
                <div class="skill-name-small">{{ skill.name }}</div>
                <div class="skill-desc">{{ skill.description.substring(0, 30) }}...</div>
              </div>
              <el-icon v-if="isSkillAdded(skill.name)" class="check-indicator" color="#67c23a">
                <Check />
              </el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="`配置 ${currentSkill?.skill || ''}`"
      width="600px"
    >
      <el-form :model="currentConfig" label-width="120px">
        <!-- 根据不同Skill显示不同配置项 -->
        <div v-if="currentSkill?.skill === 'generation.text'">
          <el-form-item label="提示词模板">
            <el-select
              v-model="currentConfig.prompt_template_id"
              placeholder="选择提示词模板"
              style="width: 100%"
              @change="onPromptTemplateSelect"
            >
              <el-option-group
                v-for="category in groupedTemplates"
                :key="category.name"
                :label="category.name"
              >
                <el-option
                  v-for="template in category.templates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                >
                  <div class="template-option">
                    <span class="template-name">{{ template.name }}</span>
                    <span class="template-desc">{{ template.description }}</span>
                  </div>
                </el-option>
              </el-option-group>
            </el-select>

            <div class="template-hint" v-if="currentConfig.prompt_template_id">
              <span>💡 </span>
              <span>从提示词模板库中选择模板，系统会自动解析模板中的变量</span>
            </div>

            <div v-if="currentConfig.prompt_template" class="template-preview-box">
              <div class="preview-header">模板内容预览</div>
              <div class="preview-text">{{ promptTemplateContent }}</div>
            </div>
          </el-form-item>

          <el-form-item label="变量配置">
            <div class="variables-config">
              <!-- 无变量时的提示 -->
              <div v-if="variablesList.length === 0" class="no-variables">
                <el-empty description="暂无变量" :image-size="60">
                  <p class="hint-text">在上方提示词中使用 {变量名} 添加变量，或点击下方按钮手动添加</p>
                </el-empty>
              </div>

              <!-- 变量列表 -->
              <div v-else class="variables-list">
                <div
                  v-for="(variable, index) in variablesList"
                  :key="index"
                  class="variable-card"
                >
                  <!-- 变量名输入 -->
                  <div class="var-name-row">
                    <span class="var-prefix">{</span>
                    <el-input
                      v-model="variable.name"
                      placeholder="变量名"
                      size="small"
                      style="flex: 1"
                    />
                    <span class="var-suffix">}</span>
                    <el-button
                      size="small"
                      type="danger"
                      text
                      @click="removeVariable(index)"
                      class="remove-btn"
                    >
                      删除
                    </el-button>
                  </div>

                  <!-- 值配置 -->
                  <div class="var-value-row">
                    <!-- 手动输入 -->
                    <el-input
                      v-model="variable.manual_value"
                      type="textarea"
                      :rows="3"
                      placeholder="输入变量的值"
                      class="value-input"
                    />
                  </div>
                </div>
              </div>

              <!-- 添加变量按钮 -->
              <el-button
                type="primary"
                plain
                @click="addVariable"
                style="width: 100%; margin-top: 12px"
              >
                + 添加变量
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="最大Token数">
            <el-input-number
              v-model="currentConfig.max_tokens"
              :min="100"
              :max="4000"
              :step="100"
            />
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'generation.render'">
          <el-form-item label="平台">
            <el-select v-model="currentConfig.platform">
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="抖音" value="douyin" />
            </el-select>
          </el-form-item>
          <el-form-item label="作者">
            <el-input
              v-model="currentConfig.author"
              placeholder="显示在图片上的作者名"
            />
          </el-form-item>
          <el-form-item label="模板">
            <el-select v-model="currentConfig.template" placeholder="选择渲染样式">
              <el-option v-for="tpl in renderTemplates" :key="tpl.name" :label="tpl.label" :value="tpl.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="分段">
            <el-switch v-model="currentConfig.split_long" />
          </el-form-item>
          <el-form-item label="最大长度">
            <el-input-number v-model="currentConfig.max_length" :min="100" :max="1000" />
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'collection.rss'">
          <el-form-item label="RSS源地址">
            <el-input
              v-model="currentConfig.url"
              placeholder="请输入RSS订阅地址"
            />
            <div class="form-hint">
              例如：https://feeds.feedburner.com/ruanyifeng
            </div>
          </el-form-item>
          <el-form-item label="最大条目数">
            <el-input-number v-model="currentConfig.max_items" :min="1" :max="50" />
            <div class="form-hint">
              每次获取最多多少条RSS条目
            </div>
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'collection.topic_discovery'">
          <el-form-item label="数据源">
            <el-checkbox-group v-model="currentConfig.sources">
              <el-checkbox value="weibo">微博热搜</el-checkbox>
              <el-checkbox value="baidu">百度热搜</el-checkbox>
              <el-checkbox value="toutiao">头条热搜</el-checkbox>
            </el-checkbox-group>
            <div class="form-hint">
              选择热点数据来源，数据每天只爬取一次
            </div>
          </el-form-item>
          <el-form-item label="目标平台">
            <el-select v-model="currentConfig.platform" placeholder="选择目标平台">
              <el-option label="小红书" value="xiaohongshu">
                <div>
                  <div style="font-weight: 500">小红书</div>
                  <div style="font-size: 12px; color: #909399">年轻女性，关注美妆、穿搭、生活方式</div>
                </div>
              </el-option>
              <el-option label="微信公众号" value="weixin">
                <div>
                  <div style="font-weight: 500">微信公众号</div>
                  <div style="font-size: 12px; color: #909399">年龄层较广，关注深度内容、职场技能</div>
                </div>
              </el-option>
              <el-option label="抖音" value="douyin">
                <div>
                  <div style="font-weight: 500">抖音</div>
                  <div style="font-size: 12px; color: #909399">喜欢娱乐、搞笑、生活技巧、情感故事</div>
                </div>
              </el-option>
            </el-select>
            <div class="form-hint">
              根据平台用户特征智能推荐主题
            </div>
          </el-form-item>
          <el-form-item label="推荐数量">
            <el-input-number v-model="currentConfig.count" :min="1" :max="10" />
            <div class="form-hint">
              推荐主题的数量（1-10个）
            </div>
          </el-form-item>
          <el-form-item label="分析模式">
            <el-radio-group v-model="currentConfig.use_llm">
              <el-radio :label="true">LLM智能分析</el-radio>
              <el-radio :label="false">热度排序</el-radio>
            </el-radio-group>
            <div style="color: #909399; font-size: 12px; margin-top: 4px;">
              <span v-if="currentConfig.use_llm">🤖 使用LLM分析，根据平台用户特征选择主题</span>
              <span v-else>📊 仅按热度排序，速度快</span>
            </div>
          </el-form-item>
          <el-form-item label="强制刷新">
            <el-switch v-model="currentConfig.force_refresh" />
            <div class="form-hint">
              开启后将强制重新爬取数据（默认使用缓存）
            </div>
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'review.sensitive'">
          <el-form-item label="严格程度">
            <el-select v-model="currentConfig.strictness">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
            </el-select>
          </el-form-item>
          <el-form-item label="检测类别">
            <el-checkbox-group v-model="currentConfig.categories">
              <el-checkbox value="politics">政治</el-checkbox>
              <el-checkbox value="porn">色情</el-checkbox>
              <el-checkbox value="violence">暴力</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'review.quality'">
          <el-form-item label="审核模式">
            <el-radio-group v-model="currentConfig.use_ai">
              <el-radio :label="false">本地规则（快速）</el-radio>
              <el-radio :label="true">AI审核（智能）</el-radio>
            </el-radio-group>
            <div style="color: #909399; font-size: 12px; margin-top: 4px;">
              <span v-if="!currentConfig.use_ai">⚡ 本地规则审核，速度快、无费用</span>
              <span v-else>🤖 AI智能审核，更灵活、消耗tokens</span>
            </div>
          </el-form-item>
          <el-form-item label="平台">
            <el-select v-model="currentConfig.platform">
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="抖音" value="douyin" />
              <el-option label="通用" value="general" />
            </el-select>
          </el-form-item>
          <el-form-item label="评估维度" v-if="!currentConfig.use_ai">
            <el-checkbox-group v-model="currentConfig.dimensions">
              <el-checkbox value="readability">可读性</el-checkbox>
              <el-checkbox value="completeness">完整性</el-checkbox>
              <el-checkbox value="attractiveness">吸引力</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="最低分数">
            <el-input-number v-model="currentConfig.min_score" :min="0" :max="100" />
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'publishing.draft'">
          <el-form-item label="平台">
            <el-select v-model="currentConfig.platform">
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="抖音" value="douyin" />
            </el-select>
          </el-form-item>
        </div>

        <div v-else-if="currentSkill?.skill === 'conditional.save'">
          <el-form-item label="条件表达式">
            <el-input
              v-model="currentConfig.condition"
              type="textarea"
              :rows="3"
              placeholder="例如: quality_score >= 70 AND is_safe == true"
            />
            <div class="form-hint">
              可用变量: quality_score, is_safe, content_length
            </div>
          </el-form-item>
          <el-form-item label="条件为真时">
            <el-select v-model="currentConfig.true_action">
              <el-option label="保存为草稿" value="save_as_draft" />
              <el-option label="直接发布" value="publish" />
              <el-option label="继续执行" value="continue" />
            </el-select>
          </el-form-item>
          <el-form-item label="条件为假时">
            <el-select v-model="currentConfig.false_action">
              <el-option label="记录并丢弃" value="log_and_discard" />
              <el-option label="跳过此步骤" value="skip" />
              <el-option label="停止执行" value="stop" />
            </el-select>
          </el-form-item>
        </div>

        <div v-else>
          <el-alert type="info" :closable="false">
            此Skill使用默认配置，无需额外设置
          </el-alert>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { agents } from '@/api'
import { getTemplates } from '@/api/promptTemplates'
import yaml from 'js-yaml'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  account_id: {
    type: [Number, String],
    default: null
  },
  agentId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// 数据
const skillChain = ref([])
const allSkills = ref([])
const searchKeyword = ref('')
const configDialogVisible = ref(false)
const currentSkill = ref(null)
const currentConfig = ref({})
const promptTemplates = ref([])
const boundAccountName = ref('')
const renderTemplates = ref([])
const promptTemplateContent = ref('')

// 变量列表（用于配置界面）
const variablesList = ref([])

// 加载绑定账户信息
const loadBoundAccount = async () => {
  if (!props.account_id) {
    boundAccountName.value = ''
    return
  }
  try {
    const response = await fetch(`http://localhost:8000/api/accounts/${props.account_id}`)
    const data = await response.json()
    boundAccountName.value = data?.name || ''
  } catch (error) {
    console.error('加载账户信息失败:', error)
    boundAccountName.value = ''
  }
}

// 加载渲染模板列表
const loadRenderTemplates = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/render/templates/detail')
    const data = await response.json()
    if (data.status === 'success' && data.templates) {
      const templates = []
      for (const platform in data.templates) {
        data.templates[platform].forEach(t => {
          templates.push({
            name: t.name,
            label: t.label || t.name,
            platform: platform
          })
        })
      }
      renderTemplates.value = templates
    }
  } catch (error) {
    console.error('加载模板列表失败:', error)
  }
}

// 计算属性
const filteredCategories = computed(() => {
  if (!searchKeyword.value) return allSkills.value

  const keyword = searchKeyword.value.toLowerCase()
  return allSkills.value.map(category => ({
    ...category,
    skills: category.skills.filter(skill =>
      skill.name.toLowerCase().includes(keyword) ||
      skill.description.toLowerCase().includes(keyword)
    )
  })).filter(category => category.skills.length > 0)
})

const groupedTemplates = computed(() => {
  const groups = {}
  promptTemplates.value.forEach(template => {
    const category = template.category || '通用'
    if (!groups[category]) {
      groups[category] = {
        name: category,
        templates: []
      }
    }
    groups[category].templates.push(template)
  })
  return Object.values(groups)
})

// 方法
const isSkillAdded = (skillName) => {
  return skillChain.value.some(item => item.skill === skillName)
}

const addSkill = (skill) => {
  if (isSkillAdded(skill.name)) {
    ElMessage.warning('此Skill已在链中')
    return
  }

  skillChain.value.push({
    id: Date.now(),
    skill: skill.name,
    config: getDefaultConfig(skill.name)
  })

  emitChange()
}

const removeSkill = (index) => {
  skillChain.value.splice(index, 1)
  emitChange()
}

const clearChain = () => {
  skillChain.value = []
  emitChange()
}

const onChainChange = () => {
  emitChange()
}

const editConfig = (item) => {
  currentSkill.value = item
  
  // 如果配置为空，使用默认配置
  const defaultConfig = getDefaultConfig(item.skill)
  currentConfig.value = { ...defaultConfig, ...item.config }

  // 将 variables 对象转换为变量列表
  variablesList.value = []
  if (currentConfig.value.variables && typeof currentConfig.value.variables === 'object') {
    const vars = currentConfig.value.variables
    for (const [key, value] of Object.entries(vars)) {
      // 兼容所有格式，统一处理为手动输入
      variablesList.value.push({
        name: key,
        type: 'manual',
        manual_value: typeof value === 'object' ? value.value : String(value),
        template_id: '',
        template_preview: ''
      })
    }
    delete currentConfig.value.variables
  }

  // 恢复提示词模板
  if (currentConfig.value.prompt_template) {
    // 检查是否是模板ID（在模板列表中存在）
    const template = promptTemplates.value.find(t => t.id === currentConfig.value.prompt_template)
    if (template) {
      // 是模板ID，设置prompt_template_id以便下拉框默认选中
      currentConfig.value.prompt_template_id = template.id
      
      // 构建预览内容：模板内容 + 示例输出
      let previewContent = template.template_content
      if (template.example_output) {
        previewContent = `${previewContent}\n\n示例输出：\n${template.example_output}`
      }
      promptTemplateContent.value = previewContent
    } else {
      // 不是模板ID，说明是自定义提示词（旧配置）
      promptTemplateContent.value = currentConfig.value.prompt_template
    }
  } else {
    promptTemplateContent.value = ''
  }

  configDialogVisible.value = true
}

const onPromptTemplateSelect = (templateId) => {
  if (!templateId) {
    currentConfig.value.prompt_template = ''
    promptTemplateContent.value = ''
    return
  }

  const template = promptTemplates.value.find(t => t.id === templateId)
  if (template) {
    currentConfig.value.prompt_template = template.id
    
    // 构建预览内容：模板内容 + 示例输出
    let previewContent = template.template_content
    if (template.example_output) {
      previewContent = `${previewContent}\n\n示例输出：\n${template.example_output}`
    }
    promptTemplateContent.value = previewContent

    // 自动解析模板中的变量
    const variableMatches = template.template_content.match(/\{([^}]+)\}/g)
    if (variableMatches) {
      const varNames = [...new Set(variableMatches.map(m => m.replace(/[{}]/g, '')))]
      
      // 清空现有变量列表
      variablesList.value = []
      
      // 为每个变量添加到列表
      varNames.forEach(varName => {
        variablesList.value.push({
          name: varName,
          type: 'manual',
          manual_value: '',
          template_id: '',
          template_preview: ''
        })
      })
    }
  }
}

const saveConfig = async () => {
  const index = skillChain.value.findIndex(item => item.id === currentSkill.value.id)
  if (index !== -1) {
    const configToSave = { ...currentConfig.value }

    // 删除临时字段
    delete configToSave.prompt_template_id

    // 将变量列表转换为后端需要的格式
    configToSave.variables = {}
    for (const variable of variablesList.value) {
      // 统一保存为手动输入的值
      configToSave.variables[variable.name] = variable.manual_value
    }

    skillChain.value[index].config = configToSave
    emitChange()

    // 如果有 agentId，立即保存到后端
    if (props.agentId) {
      try {
        await saveToBackend()
        ElMessage.success('配置已保存')
      } catch (error) {
        ElMessage.error('保存失败: ' + error.message)
        return
      }
    }
  }
  configDialogVisible.value = false
}

const saveToBackend = async () => {
  if (!props.agentId) {
    console.warn('没有 agentId，跳过后端保存')
    return
  }

  // 从父组件获取 agent 信息
  const agentInfo = await agents.getAgent(props.agentId)

  // 构建完整的 agent 配置
  const config = {
    agent: {
      id: agentInfo.id,
      name: agentInfo.name,
      description: agentInfo.description,
      enabled: agentInfo.enabled,
      llm_provider: agentInfo.llm_provider,
      schedule: agentInfo.schedule,
      skill_chain: skillChain.value.map(item => ({
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
    id: agentInfo.id,
    name: agentInfo.name,
    enabled: agentInfo.enabled,
    config: yamlStr
  }

  await agents.updateAgent(props.agentId, payload)
}

const emitChange = () => {
  emit('update:modelValue', skillChain.value)
}

const onDragStart = (event, skill) => {
  event.dataTransfer.setData('skill', JSON.stringify(skill))
}

// 辅助方法
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

const getSkillDescription = (skillName) => {
  const skill = allSkills.value
    .flatMap(cat => cat.skills)
    .find(s => s.name === skillName)
  return skill?.description || ''
}

const getSkillIcon = (skillName) => {
  const iconMap = {
    'generation.text': '✍️',
    'generation.render': '🎨',
    'review.sensitive': '🛡️',
    'review.quality': '⭐',
    'publishing.draft': '📝',
    'publishing.publish': '📤',
    'collection.rss': '📡',
    'processing.clean': '🧹',
    'conditional.save': '✅'
  }
  return iconMap[skillName] || '⚙️'
}

const getConfigSummary = (item) => {
  const config = item.config || {}
  const parts = []

  // 不显示 platform，因为 Agent 已绑定平台
  if (config.template) parts.push(config.template)
  if (config['min_score']) parts.push(`≥${config['min_score']}分`)
  if (config.strictness) parts.push(config.strictness)

  // 显示RSS URL
  if (config.url) {
    const urlPreview = config.url.length > 30
      ? config.url.substring(0, 30) + '...'
      : config.url
    parts.push(`RSS: ${urlPreview}`)
  }
  if (config.max_items) parts.push(`最多${config.max_items}条`)

  // 显示条件表达式
  if (config.condition) {
    const conditionPreview = config.condition.length > 30 
      ? config.condition.substring(0, 30) + '...' 
      : config.condition
    parts.push(`条件: ${conditionPreview}`)
  }
  
  // 显示操作
  if (config.true_action || config.false_action) {
    const actions = []
    if (config.true_action) actions.push(`真:${config.true_action}`)
    if (config.false_action) actions.push(`假:${config.false_action}`)
    parts.push(actions.join(', '))
  }
  
  // 显示评估维度
  if (config.dimensions && Array.isArray(config.dimensions)) {
    const dimensionMap = {
      'readability': '可读性',
      'completeness': '完整性',
      'attractiveness': '吸引力'
    }
    const dimensionLabels = config.dimensions.map(d => dimensionMap[d] || d)
    parts.push(dimensionLabels.join('+'))
  }

  // 显示截断长度（渲染skill）
  if (config.max_length) parts.push(`截断${config.max_length}字`)

  // 处理变量配置显示
  if (config.variables && typeof config.variables === 'object') {
    const varNames = Object.keys(config.variables)
    if (varNames.length > 0) {
      const varDetails = varNames.map(name => {
        const value = config.variables[name]
        if (typeof value === 'object' && value.type === 'template') {
          return `${name}=[模板]`
        } else {
          const preview = String(value).substring(0, 20)
          return `${name}=${preview}${value.length > 20 ? '...' : ''}`
        }
      })
      parts.push(`变量: ${varDetails.join(', ')}`)
    }
  }

  if (config.prompt_template && !parts.some(p => p.startsWith('变量'))) parts.push('自定义提示词')
  if (config.max_tokens) parts.push(`${config.max_tokens} tokens`)

  return parts.length > 0 ? parts.join(' | ') : '默认配置'
}

const getDefaultConfig = (skillName) => {
  const defaultConfigs = {
    'generation.text': {
      prompt_template: '',
      max_tokens: 1200
    },
    'generation.render': {
      platform: 'xiaohongshu',
      template: 'minimal',
      split_long: true,
      max_length: 300
    },
    'collection.rss': {
      url: '',
      max_items: 5
    },
    'collection.topic_discovery': {
      sources: ['weibo', 'baidu', 'toutiao'],
      platform: 'xiaohongshu',
      count: 3,
      use_llm: true,
      force_refresh: false
    },
    'review.sensitive': {
      strictness: 'medium',
      categories: ['politics', 'porn', 'violence']
    },
    'review.quality': {
      platform: 'xiaohongshu',
      dimensions: ['readability', 'completeness', 'attractiveness'],
      'min_score': 60
    },
    'conditional.save': {
      condition: 'quality_score >= 60 AND is_safe == true',
      true_action: 'save_as_draft',
      false_action: 'log_and_discard'
    },
    'publishing.draft': {
      platform: 'xiaohongshu'
    }
  }

  return defaultConfigs[skillName] || {}
}

// 加载Skill列表
const loadSkills = async () => {
  try {
    const data = await agents.getSkillsList()
    allSkills.value = data
  } catch (error) {
    ElMessage.error('加载Skill列表失败: ' + error.message)
  }
}

// 加载提示词模板
const loadPromptTemplates = async () => {
  try {
    const data = await getTemplates({ active_only: true })
    promptTemplates.value = data
  } catch (error) {
    console.error('加载提示词模板失败:', error)
  }
}

// 添加变量
const addVariable = () => {
  variablesList.value.push({
    name: '',
    type: 'manual',
    manual_value: '',
    template_id: '',
    template_preview: ''
  })
}

// 删除变量
const removeVariable = (index) => {
  variablesList.value.splice(index, 1)
}

// 初始化
onMounted(() => {
  loadSkills()
  loadPromptTemplates()
  loadBoundAccount()
  loadRenderTemplates()

  // 如果有初始值，加载它
  if (props.modelValue && props.modelValue.length > 0) {
    skillChain.value = [...props.modelValue]
  }
})

// 监听外部变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== skillChain.value) {
    skillChain.value = newValue || []
  }
})

// 监听 account_id 变化
watch(() => props.account_id, () => {
  loadBoundAccount()
})
</script>

<style scoped>
.skill-chain-builder {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

/* 已选择的Skill链 */
.chain-list {
  min-height: 160px;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.chain-item {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  transition: all 0.3s;
}

.chain-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chain-item.error {
  border-color: #f56c6c;
  background: #fef0f0;
}

.drag-handle {
  cursor: move;
  color: #999;
  font-size: 18px;
  line-height: 24px;
  padding: 0 8px;
}

.item-content {
  flex: 1;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.skill-name {
  font-weight: 500;
  color: #333;
}

.item-description {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.item-config {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e0e0e0;
}

.config-summary {
  font-size: 12px;
  color: #666;
}

.remove-btn {
  padding: 4px 8px;
}

/* 可用Skill列表 */
.skills-section {
  /* Removed max-height and overflow-y for better vertical layout */
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-category {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.category-header {
  background: #f5f7fa;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
}

.category-label {
  font-weight: 500;
  color: #333;
}

.category-count {
  font-size: 12px;
  color: #999;
}

.category-skills {
  padding: 8px;
}

.skill-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-card:hover:not(.disabled) {
  border-color: var(--el-color-primary);
  background: #f0f9ff;
}

.skill-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.skill-icon {
  font-size: 24px;
}

.skill-info {
  flex: 1;
}

.skill-name-small {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.skill-desc {
  font-size: 11px;
  color: #999;
}

.check-indicator {
  margin-left: auto;
}

/* 提示词模板区域 */
.template-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 10px 12px;
  background: #f0f9ff;
  border-left: 3px solid var(--el-color-primary);
  border-radius: 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.template-hint code {
  background: rgba(64, 158, 255, 0.1);
  color: var(--el-color-primary);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  font-weight: 500;
}

/* 变量配置区域 */
.variables-config {
  width: 100%;
}

.no-variables {
  padding: 20px 0;
}

.no-variables .hint-text {
  font-size: 13px;
  color: #999;
  margin-top: 12px;
}

/* 变量卡片列表 */
.variables-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.variable-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.variable-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 变量名行 */
.var-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.var-prefix,
.var-suffix {
  font-size: 16px;
  font-weight: 600;
  color: #999;
  font-family: 'Monaco', 'Menlo', monospace;
}

.remove-btn {
  margin-left: 12px;
}

/* 变量值配置行 */
.var-value-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.value-type-selector {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.value-input {
  width: 100%;
}

/* 模板选择器 */
.template-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-name {
  font-size: 14px;
  color: #333;
}

.template-desc {
  font-size: 12px;
  color: #999;
}

/* 模板预览 */
.template-preview-box {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid var(--el-color-primary);
}

.template-preview-box .preview-header {
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.template-preview-box .preview-text {
  font-size: 12px;
  color: #333;
  line-height: 1.6;
  max-height: 120px;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* 配置对话框样式 */
.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.form-hint a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.form-hint code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #e83e8c;
}
</style>
