<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">Agent管理</h1>
      <p class="page-subtitle">万物并作，皆是因缘</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar mb-lg">
      <div class="filter-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索Agent名称..."
          prefix-icon="Search"
          style="width: 240px"
          clearable
        />
        <el-select v-model="filterPlatform" placeholder="全部平台" style="width: 120px">
          <el-option label="全部平台" value="" />
          <el-option label="小红书" value="xiaohongshu" />
          <el-option label="抖音" value="douyin" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="全部状态" style="width: 120px">
          <el-option label="全部状态" value="" />
          <el-option label="开启" value="enabled" />
          <el-option label="暂停" value="disabled" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-button type="primary" @click="createAgent">
          <span class="btn-icon">+</span>
          新建Agent
        </el-button>
      </div>
    </div>

    <!-- Agent卡片列表 -->
    <div v-loading="loading" v-if="agentsList.length > 0" class="agent-grid grid-4">
      <div
        v-for="agent in filteredAgents"
        :key="agent.id"
        class="agent-card"
        @click="viewAgent(agent)"
      >
        <!-- 卡片头部 -->
        <div class="agent-header">
          <div class="agent-avatar">{{ agent.avatar }}</div>
          <div class="agent-info">
            <div class="agent-name">{{ agent.name }}</div>
          </div>
          <el-switch
            v-model="agent.enabled"
            @change="toggleAgent(agent)"
            @click.stop
            size="small"
            active-color="#a88f6e"
            inline-prompt
          />
        </div>

        <!-- 卡片主体 -->
        <div class="agent-body">
          <!-- 平台标识 -->
          <div class="agent-platforms">
            <span v-if="agent.platforms.includes('xiaohongshu')" class="platform-tag">
              <span class="platform-icon">📕</span>
              小红书
            </span>
            <span v-if="agent.platforms.includes('douyin')" class="platform-tag">
              <span class="platform-icon">🎵</span>
              抖音
            </span>
          </div>

          <!-- 发文进度 -->
          <div class="agent-progress">
            <div class="progress-text">
              今日发文 {{ agent.todayPublished }}/{{ agent.dailyTarget }}
            </div>
            <div class="zen-progress">
              <div
                class="zen-progress-bar"
                :style="{ width: (agent.todayPublished / agent.dailyTarget * 100) + '%' }"
              ></div>
            </div>
          </div>

          <!-- 最后发文时间 -->
          <div class="agent-time">
            <span class="time-text">最后发文: {{ agent.lastPublishTime }}</span>
          </div>

          <!-- 审核状态 -->
          <div class="agent-review-status">
            <span class="review-icon">🛡️</span>
            <span class="review-rate">通过率: {{ agent.approvalRate }}%</span>
          </div>

          <!-- 绑定账户 -->
          <div class="agent-bound-account" v-if="agent.boundAccount">
            <span class="account-icon">🔗</span>
            <span class="account-name">{{ agent.boundAccount.name }}</span>
          </div>
          <div class="agent-bound-account no-account" v-else>
            <span class="account-icon">⚠️</span>
            <span class="account-name">未绑定账户</span>
          </div>
        </div>

        <!-- 卡片底部 -->
        <div class="agent-footer">
          <div class="action-buttons">
            <button class="action-btn" @click.stop="editAgent(agent)">
              <span>✏️</span>
              编辑
            </button>
            <button class="action-btn" @click.stop="runAgent(agent)">
              <span>▶️</span>
              运行
            </button>
            <button class="action-btn" @click.stop="viewData(agent)">
              <span>📊</span>
              历史
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="zen-empty">
      <div class="zen-empty-icon">⏳</div>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="agentsList.length === 0" class="zen-empty">
      <div class="zen-empty-icon">🤖</div>
      <p>还没有Agent</p>
      <el-button type="primary" @click="createAgent">点击新建Agent开始</el-button>
    </div>

    <!-- 执行历史对话框 -->
    <el-dialog
      v-model="historyDialog"
      :title="`执行历史 - ${currentAgent?.name || ''}`"
      width="80%"
      top="5vh"
    >
      <div v-if="currentAgent" class="history-container">
        <!-- 筛选栏 -->
        <div class="history-filter mb-md">
          <el-select v-model="historyStatus" placeholder="全部状态" clearable style="width: 120px" @change="loadHistory">
            <el-option label="全部状态" value="" />
            <el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button @click="loadHistory" :loading="historyLoading">刷新</el-button>
          <el-button @click="clearHistory" type="danger" plain>清空历史</el-button>
        </div>

        <!-- 执行记录列表 -->
        <div v-loading="historyLoading" class="history-list">
          <div
            v-for="task in historyList"
            :key="task.id"
            class="history-item"
            @click="viewTaskDetail(task)"
          >
            <div class="history-header">
              <div class="history-status">
                <span
                  class="status-dot"
                  :class="{
                    'success': task.status === 'completed',
                    'error': task.status === 'failed',
                    'running': task.status === 'running'
                  }"
                ></span>
                <span class="status-text">{{ getStatusText(task.status) }}</span>
              </div>
              <div class="history-time">{{ formatTime(task.started_at) }}</div>
              <button
                class="delete-task-btn"
                @click.stop="deleteTask(task)"
                title="删除此记录"
              >
                🗑️
              </button>
            </div>

            <div class="history-body">
              <div class="history-skills">
                <div
                  v-for="(skill, idx) in task.skill_results"
                  :key="idx"
                  class="skill-item"
                  :class="{ failed: skill.status === 'failed' }"
                >
                  <span class="skill-number">{{ idx + 1 }}</span>
                  <span class="skill-name">{{ skill.skill }}</span>
                  <span class="skill-status">
                    <span v-if="skill.status === 'success'" class="skill-success">✓</span>
                    <span v-else-if="skill.status === 'failed'" class="skill-failed">✗</span>
                    <span v-else class="skill-running">⟳</span>
                  </span>
                  <span v-if="skill.error" class="skill-error">{{ skill.error }}</span>
                </div>
              </div>

              <div v-if="task.status === 'failed' && task.error" class="history-error">
                <strong>错误：</strong>{{ task.error }}
              </div>

              <div v-if="task.result" class="history-result">
                <details>
                  <summary>执行结果</summary>
                  <pre>{{ JSON.stringify(task.result, null, 2) }}</pre>
                </details>
              </div>
            </div>
          </div>

          <el-empty v-if="!historyLoading && historyList.length === 0" description="暂无执行记录" />
        </div>
      </div>
    </el-dialog>

    <!-- Task详情对话框 -->
    <el-dialog
      v-model="taskDetailDialog"
      title="执行详情"
      width="60%"
      top="5vh"
    >
      <div v-if="currentTask" class="task-detail">
        <div class="detail-section">
          <h4 class="detail-title">基本信息</h4>
          <div class="detail-row">
            <span class="detail-label">Agent:</span>
            <span class="detail-value">{{ currentTask.agent_name || currentTask.agent_id }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态:</span>
            <span class="detail-value">
              <el-tag :type="getStatusType(currentTask.status)">
                {{ getStatusText(currentTask.status) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">开始时间:</span>
            <span class="detail-value">{{ formatTime(currentTask.started_at) }}</span>
          </div>
          <div class="detail-row" v-if="currentTask.completed_at">
            <span class="detail-label">完成时间:</span>
            <span class="detail-value">{{ formatTime(currentTask.completed_at) }}</span>
          </div>
        </div>

        <div class="detail-section" v-if="currentTask.skill_results && currentTask.skill_results.length > 0">
          <h4 class="detail-title">Skill执行流水线</h4>
          <el-timeline class="skill-timeline">
            <el-timeline-item
              v-for="(skill, idx) in currentTask.skill_results"
              :key="idx"
              :timestamp="formatTime(skill.started_at)"
              placement="top"
              :type="getSkillTimelineType(skill)"
            >
              <div class="timeline-content">
                <div class="skill-name">{{ skill.skill }}</div>
                <div v-if="skill.status === 'success'" class="skill-success">
                  ✓ 执行成功
                </div>
                <div v-else-if="skill.status === 'failed'" class="skill-failed">
                  ✗ 执行失败
                  <div v-if="skill.error" class="skill-error-detail">{{ skill.error }}</div>
                </div>
                <div v-else class="skill-running">
                  ⟳ 执行中...
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <div class="detail-section" v-if="currentTask.error">
          <h4 class="detail-title error-title">错误信息</h4>
          <div class="error-message">{{ currentTask.error }}</div>
        </div>

        <div class="detail-section" v-if="currentTask.result">
          <h4 class="detail-title">执行结果</h4>
          <pre class="result-json">{{ JSON.stringify(currentTask.result, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { agents, tasks } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// 数据加载状态
const loading = ref(false)

// Agent列表
const agentsList = ref([])

// 执行历史相关
const historyDialog = ref(false)
const taskDetailDialog = ref(false)
const currentAgent = ref(null)
const currentTask = ref(null)
const historyList = ref([])
const historyLoading = ref(false)
const historyStatus = ref('')

// 根据名称生成头像
const getAgentAvatar = (name) => {
  const avatarMap = {
    '佛学号Agent': '📿',
    '内容审核Agent': '🛡️'
  }
  return avatarMap[name] || name.charAt(0)
}

// 加载Agent列表
const loadAgents = async () => {
  loading.value = true
  try {
    const data = await agents.getAgents()
    agentsList.value = data.map(agent => ({
      ...agent,
      avatar: getAgentAvatar(agent.name),
      platforms: ['xiaohongshu'], // TODO: 从config中读取
      todayPublished: agent.today_published || 0,
      dailyTarget: agent.daily_target || 3,
      lastPublishTime: agent.last_publish_time || '未运行',
      approvalRate: agent.approval_rate || 0,
      boundAccount: agent.bound_account || null
    }))
  } catch (error) {
    ElMessage.error('加载Agent列表失败: ' + error.message)
    console.error('Load agents error:', error)
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAgents()
})

const searchQuery = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')

const filteredAgents = computed(() => {
  return agentsList.value.filter(agent => {
    const matchSearch = !searchQuery.value || agent.name.includes(searchQuery.value)
    const matchPlatform = !filterPlatform.value || agent.platforms.includes(filterPlatform.value)
    const matchStatus = !filterStatus.value ||
      (filterStatus.value === 'enabled' && agent.enabled) ||
      (filterStatus.value === 'disabled' && !agent.enabled)

    return matchSearch && matchPlatform && matchStatus
  })
})

const createAgent = () => {
  router.push('/agents/new')
}

const viewAgent = (agent) => {
  console.log('查看Agent:', agent)
  // TODO: 跳转到Agent详情页
}

const viewData = async (agent) => {
  // 改为打开执行历史
  currentAgent.value = agent
  historyDialog.value = true
  await loadHistory()
}

// 加载执行历史
const loadHistory = async () => {
  if (!currentAgent.value) return

  historyLoading.value = true
  try {
    const data = await tasks.getAgentTasks(currentAgent.value.id, {
      status: historyStatus.value || undefined,
      limit: 20
    })
    historyList.value = data
  } catch (error) {
    ElMessage.error('加载执行历史失败: ' + error.message)
  } finally {
    historyLoading.value = false
  }
}

// 查看Task详情
const viewTaskDetail = (task) => {
  currentTask.value = task
  taskDetailDialog.value = true
}

// 删除单个任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确认删除此执行记录？`,
      '确认删除',
      { type: 'warning' }
    )

    await tasks.deleteTask(task.id)
    ElMessage.success('删除成功')

    // 刷新列表
    await loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || error))
    }
  }
}

// 清空历史记录
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      `确认清空 "${currentAgent.value.name}" 的所有执行历史？此操作不可恢复！`,
      '确认清空',
      { type: 'error', confirmButtonText: '确认清空', cancelButtonText: '取消' }
    )

    await tasks.deleteAgentTasks(currentAgent.value.id)
    ElMessage.success('历史记录已清空')

    // 刷新列表
    await loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败: ' + (error.message || error))
    }
  }
}

// 转换状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取状态类型（Element Plus Tag）
const getStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'failed': 'danger',
    'running': 'warning',
    'pending': 'info'
  }
  return typeMap[status] || ''
}

// 获取Skill时间线类型
const getSkillTimelineType = (skill) => {
  if (skill.status === 'success') return 'success'
  if (skill.status === 'failed') return 'danger'
  return 'primary'
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'

  // 解析ISO时间字符串，确保正确处理时区
  const date = new Date(timeStr)
  const now = new Date()

  // 检查日期是否有效
  if (isNaN(date.getTime())) return '-'

  const diff = (now - date) / 1000

  // 如果差值为负（时间在未来），显示具体日期时间
  if (diff < 0) {
    return date.toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (diff < 60) return `${Math.floor(diff)}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const editAgent = (agent) => {
  router.push(`/agents/${agent.id}/edit`)
}

const runAgent = async (agent) => {
  try {
    await ElMessageBox.confirm(
      `确认运行 Agent "${agent.name}"？`,
      '确认运行',
      { type: 'warning' }
    )

    const result = await agents.runAgent(agent.id)
    ElMessage.success(result.message || 'Agent 已开始运行')

    // 延迟刷新
    setTimeout(() => {
      loadAgents()
    }, 2000)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('运行失败: ' + (error.message || error))
    }
  }
}

const toggleAgent = async (agent) => {
  try {
    const result = await agents.toggleAgent(agent.id)
    agent.enabled = result.enabled
    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error('切换Agent状态失败: ' + error.message)
    // 回滚UI状态
    agent.enabled = !agent.enabled
  }
}
</script>

<style scoped>
/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-icon {
  font-size: 16px;
  margin-right: 6px;
}

/* Agent网格 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

/* Agent卡片 */
.agent-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.agent-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--color-accent);
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-divider);
}

.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.agent-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

/* 平台标识 */
.agent-platforms {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.platform-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-small);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.platform-icon {
  font-size: 14px;
}

/* 发文进度 */
.agent-progress {
  margin-top: 4px;
}

.progress-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

/* Agent时间 */
.agent-time {
  font-size: 12px;
  color: var(--color-text-placeholder);
}

/* 审核状态 */
.agent-review-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.review-icon {
  font-size: 14px;
}

.agent-bound-account {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.agent-bound-account.no-account {
  color: var(--color-warning);
}

.account-icon {
  font-size: 14px;
}

.account-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.review-rate {
  color: var(--color-success);
  font-weight: 500;
}

/* Agent底部 */
.agent-footer {
  padding-top: 16px;
  border-top: 1px solid var(--color-divider);
}

/* 响应式 */
@media (max-width: 900px) {
  .agent-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media (max-width: 600px) {
  .filter-bar {
    flex-direction: column;
    gap: 12px;
  }

  .filter-left {
    width: 100%;
    flex-wrap: wrap;
  }

  .el-input,
  .el-select {
    flex: 1;
    min-width: 120px;
  }
}

/* 执行历史对话框 */
.history-filter {
  display: flex;
  gap: 12px;
  align-items: center;
}

.history-list {
  max-height: 500px;
  overflow-y: auto;
}

.history-item {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-item:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(168, 143, 110, 0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.success {
  background: var(--color-success);
}

.status-dot.error {
  background: var(--color-danger);
}

.status-dot.running {
  background: var(--color-warning);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-weight: 500;
  font-size: 13px;
}

.history-time {
  font-size: 12px;
  color: var(--color-text-placeholder);
}

.delete-task-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 4px;
}

.delete-task-btn:hover {
  background: rgba(220, 53, 69, 0.1);
}

.history-item:hover .delete-task-btn {
  opacity: 1;
}

.history-body {
  font-size: 13px;
}

.history-skills {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  background: var(--color-bg-secondary);
}

.skill-item.failed {
  background: rgba(245, 108, 108, 0.1);
}

.skill-number {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.skill-name {
  flex: 1;
  font-family: monospace;
  font-size: 12px;
}

.skill-status {
  font-size: 14px;
}

.skill-success {
  color: var(--color-success);
}

.skill-failed {
  color: var(--color-danger);
}

.skill-running {
  color: var(--color-warning);
}

.skill-error {
  color: var(--color-danger);
  font-size: 11px;
  font-family: monospace;
}

.history-error {
  margin-top: 8px;
  padding: 8px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
  color: var(--color-danger);
  font-size: 12px;
}

.history-result {
  margin-top: 8px;
}

.history-result details {
  cursor: pointer;
}

.history-result summary {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.history-result pre {
  background: var(--color-bg-secondary);
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  max-height: 200px;
  overflow: auto;
}

/* Task详情对话框 */
.task-detail {
  font-size: 13px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text-primary);
}

.detail-title.error-title {
  color: var(--color-danger);
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
}

.detail-label {
  min-width: 80px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.detail-value {
  color: var(--color-text-primary);
}

.skill-timeline {
  padding-left: 20px;
}

.timeline-content {
  font-size: 13px;
}

.skill-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.skill-success {
  color: var(--color-success);
}

.skill-failed {
  color: var(--color-danger);
}

.skill-running {
  color: var(--color-warning);
}

.skill-error-detail {
  margin-top: 4px;
  color: var(--color-danger);
  font-size: 12px;
  font-family: monospace;
}

.error-message {
  padding: 12px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
  color: var(--color-danger);
  white-space: pre-wrap;
}

.result-json {
  background: var(--color-bg-secondary);
  padding: 12px;
  border-radius: 4px;
  font-size: 11px;
  max-height: 300px;
  overflow: auto;
}
</style>
