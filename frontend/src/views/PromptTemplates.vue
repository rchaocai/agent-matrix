<template>
  <div class="page-container zen-fade-in">
    <div class="page-header">
      <h1 class="page-title">提示词模板管理</h1>
      <p class="page-subtitle">言简意赅，字字珠玑</p>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar mb-md">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索模板名称..."
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <span>🔍</span>
        </template>
      </el-input>

      <el-select v-model="filterCategory" placeholder="选择分类" clearable style="width: 200px; margin-left: 12px">
        <el-option label="全部分类" value="" />
        <el-option
          v-for="category in categories"
          :key="category"
          :label="category"
          :value="category"
        />
      </el-select>

      <div style="flex: 1"></div>

      <el-button type="primary" @click="showCreateDialog">
        <span style="margin-right: 8px">➕</span>
        新建模板
      </el-button>
    </div>

    <!-- 模板列表 -->
    <div class="template-grid">
      <div
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-card"
        :class="{ 'template-card-inactive': !template.is_active }"
      >
        <div class="template-header">
          <div class="template-info">
            <h3 class="template-name">{{ template.name }}</h3>
            <el-tag size="small" type="info">{{ template.category }}</el-tag>
          </div>
          <div class="template-actions">
            <el-switch
              v-model="template.is_active"
              @change="toggleTemplate(template)"
              size="small"
            />
          </div>
        </div>

        <p class="template-description">{{ template.description }}</p>

        <div class="template-variables">
          <span class="variable-label">变量：</span>
          <el-tag
            v-for="variable in template.variables"
            :key="variable"
            size="small"
            type="warning"
            style="margin-right: 4px"
          >
            {{ variable }}
          </el-tag>
        </div>

        <div class="template-footer">
          <span class="template-time">{{ formatTime(template.updated_at) }}</span>
          <div class="template-buttons">
            <el-button size="small" @click="viewTemplate(template)">查看</el-button>
            <el-button size="small" type="primary" @click="editTemplate(template)">编辑</el-button>
            <el-button size="small" @click="duplicateTemplate(template)">复制</el-button>
            <el-button size="small" type="danger" @click="deleteTemplate(template)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="filteredTemplates.length === 0"
      description="暂无模板，点击新建模板创建"
    />

    <!-- 查看/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑模板' : '查看模板'"
      width="800px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="模板ID">
          <el-input v-model="formData.id" :disabled="isViewMode || isEditMode" />
        </el-form-item>

        <el-form-item label="模板名称">
          <el-input v-model="formData.name" :disabled="isViewMode" />
        </el-form-item>

        <el-form-item label="分类">
          <el-input v-model="formData.category" :disabled="isViewMode" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            :disabled="isViewMode"
          />
        </el-form-item>

        <el-form-item label="可用变量">
          <el-select
            v-model="formData.variables"
            multiple
            filterable
            allow-create
            placeholder="输入变量名并回车添加"
            :disabled="isViewMode"
            style="width: 100%"
          >
            <el-option
              v-for="v in commonVariables"
              :key="v"
              :label="v"
              :value="v"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="模板内容">
          <el-input
            v-model="formData.template_content"
            type="textarea"
            :rows="12"
            placeholder="使用 {变量名} 来标记可替换的变量"
            :disabled="isViewMode"
          />
        </el-form-item>

        <el-form-item label="示例输出">
          <el-input
            v-model="formData.example_output"
            type="textarea"
            :rows="6"
            placeholder="可选：提供示例输出，帮助理解模板效果"
            :disabled="isViewMode"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" :disabled="isViewMode" />
          <span style="margin-left: 12px">{{ formData.is_active ? '启用' : '禁用' }}</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          v-if="!isViewMode"
          type="primary"
          @click="saveTemplate"
          :loading="saving"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { promptTemplates } from '@/api'

const route = useRoute()
const templates = ref([])
const categories = ref([])
const searchKeyword = ref('')
const filterCategory = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false)
const isViewMode = ref(false)
const saving = ref(false)

const commonVariables = ['topic', 'platform', 'word_count', 'style', 'tone']

const formData = ref({
  id: '',
  name: '',
  description: '',
  category: '',
  template_content: '',
  variables: [],
  example_output: '',
  is_active: true
})

const filteredTemplates = computed(() => {
  let result = templates.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(t =>
      t.name.toLowerCase().includes(keyword) ||
      t.description.toLowerCase().includes(keyword)
    )
  }

  if (filterCategory.value) {
    result = result.filter(t => t.category === filterCategory.value)
  }

  return result
})

const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 1) {
    const minutes = Math.floor(diff / (1000 * 60))
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const loadTemplates = async () => {
  try {
    const data = await promptTemplates.getTemplates()
    templates.value = data

    // 提取分类
    const uniqueCategories = [...new Set(data.map(t => t.category))]
    categories.value = uniqueCategories
  } catch (error) {
    ElMessage.error('加载模板失败: ' + error.message)
  }
}

const showCreateDialog = () => {
  isEditMode.value = false
  isViewMode.value = false
  formData.value = {
    id: '',
    name: '',
    description: '',
    category: filterCategory.value || 'general',
    template_content: '',
    variables: [],
    example_output: '',
    is_active: true
  }
  dialogVisible.value = true
}

const viewTemplate = (template) => {
  isEditMode.value = false
  isViewMode.value = true
  formData.value = { ...template }
  dialogVisible.value = true
}

const editTemplate = (template) => {
  isEditMode.value = true
  isViewMode.value = false
  formData.value = { 
    ...template,
    _original: template 
  }
  dialogVisible.value = true
}

const saveTemplate = async () => {
  if (!formData.value.id || !formData.value.name) {
    ElMessage.warning('请填写模板ID和名称')
    return
  }

  saving.value = true
  try {
    if (isEditMode.value) {
      // 编辑模式：使用原始ID进行更新
      const originalTemplate = templates.value.find(t => t === formData.value._original)
      if (!originalTemplate) {
        ElMessage.error('找不到原始模板')
        return
      }

      console.log('更新模板，原始ID:', originalTemplate.id, '新数据:', formData.value)
      
      await promptTemplates.updateTemplate(originalTemplate.id, {
        id: formData.value.id,
        name: formData.value.name,
        description: formData.value.description,
        category: formData.value.category,
        template_content: formData.value.template_content,
        variables: formData.value.variables,
        example_output: formData.value.example_output,
        is_active: formData.value.is_active
      })
      ElMessage.success('更新成功')
    } else {
      // 新建模式
      console.log('创建新模板:', formData.value)
      
      await promptTemplates.createTemplate({
        id: formData.value.id,
        name: formData.value.name,
        description: formData.value.description,
        category: formData.value.category,
        template_content: formData.value.template_content,
        variables: formData.value.variables,
        example_output: formData.value.example_output,
        is_active: formData.value.is_active
      })
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    await loadTemplates()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const toggleTemplate = async (template) => {
  try {
    await promptTemplates.updateTemplate(template.id, {
      is_active: template.is_active
    })
    ElMessage.success(template.is_active ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
    template.is_active = !template.is_active // 恢复状态
  }
}

const deleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await promptTemplates.deleteTemplate(template.id)
    ElMessage.success('删除成功')
    await loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const duplicateTemplate = async (template) => {
  try {
    const newTemplate = await promptTemplates.duplicateTemplate(template.id)
    ElMessage.success('复制成功')
    await loadTemplates()
  } catch (error) {
    ElMessage.error('复制失败: ' + error.message)
  }
}

onMounted(async () => {
  await loadTemplates()
  
  // 检查URL参数中是否有templateId，如果有则自动打开编辑对话框
  const templateId = route.query.templateId
  if (templateId) {
    // 查找对应的模板
    const template = templates.value.find(t => t.id === templateId)
    if (template) {
      editTemplate(template)
    }
  }
})

</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.template-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  padding: 20px;
  transition: all 0.3s;
}

.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-card-inactive {
  opacity: 0.6;
  background: var(--color-bg-secondary);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.template-info {
  flex: 1;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--color-text-primary);
}

.template-description {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.template-variables {
  margin-bottom: 12px;
  font-size: 13px;
}

.variable-label {
  color: var(--color-text-secondary);
  margin-right: 8px;
}

.template-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--color-divider);
}

.template-time {
  font-size: 12px;
  color: var(--color-text-placeholder);
}

.template-buttons {
  display: flex;
  gap: 8px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}
</style>
