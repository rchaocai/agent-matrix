<template>
  <div class="page-container zen-fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">账号管理</h1>
      <p class="page-subtitle">运筹帷幄，决胜千里</p>
    </div>

    <!-- 绑定账号按钮 -->
    <div class="action-bar mb-lg">
      <el-button type="primary" @click="showBindDialog">
        <span class="btn-icon">+</span>
        绑定新账号
      </el-button>
    </div>

    <!-- 账号列表 -->
    <div class="accounts-grid grid-3">
      <div
        v-for="account in accounts"
        :key="account.id"
        class="account-card"
      >
        <!-- 卡片头部 -->
        <div class="account-header">
          <div class="platform-icon">
            <span v-if="account.platform === 'xiaohongshu'">📕</span>
            <span v-if="account.platform === 'douyin'">🎵</span>
          </div>
          <div class="account-info">
            <div class="account-name">{{ account.name }}</div>
            <div class="account-platform">
              {{ account.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
            </div>
          </div>
          <el-switch
            v-model="account.enabled"
            @change="toggleAccount(account)"
            active-color="#a88f6e"
          />
        </div>

        <!-- 卡片内容 -->
        <div class="account-body">
          <!-- 账号状态 -->
          <div class="account-status">
            <span
              class="status-dot"
              :class="{ online: account.status === 'online', offline: account.status === 'offline' }"
            ></span>
            <span class="status-text">
              {{ account.status === 'online' ? '在线' : '离线' }}
            </span>
            <span class="status-time">{{ account.lastActive }}</span>
          </div>

          <!-- 账号统计 -->
          <div class="account-stats">
            <div class="stat-item">
              <span class="stat-label">粉丝数</span>
              <span class="stat-number">{{ formatNumber(account.followers) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">今日发文</span>
              <span class="stat-number">{{ account.todayPosts }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总发文</span>
              <span class="stat-number">{{ account.totalPosts }}</span>
            </div>
          </div>

          <!-- 绑定的Agent -->
          <div class="account-agents">
            <div class="agents-title">绑定Agent ({{ account.agents.length }})</div>
            <div class="agents-list">
              <span
                v-for="agent in account.agents"
                :key="agent.id"
                :class="['agent-tag', { 'agent-disabled': !agent.enabled }]"
                :title="agent.enabled ? '已启用' : '已禁用'"
              >
                {{ agent.avatar }} {{ agent.name }}
                <el-icon v-if="!agent.enabled" style="margin-left: 4px;"><Warning /></el-icon>
              </span>
              <span v-if="account.agents.length === 0" class="agents-empty">
                暂无绑定
              </span>
            </div>
          </div>
        </div>

        <!-- 卡片底部 -->
        <div class="account-footer">
          <el-button size="small" @click="editAccount(account)">编辑</el-button>
          <el-button
            size="small"
            :type="!account.hasCookie ? 'warning' : 'default'"
            @click="loginAccount(account)"
          >
            {{ account.hasCookie ? '重新登录' : '扫码登录' }}
          </el-button>
          <el-button size="small" @click="refreshAccount(account)">刷新状态</el-button>
          <el-button size="small" type="danger" @click="unbindAccount(account)">解绑</el-button>
        </div>
      </div>
    </div>

    <!-- 扫码登录对话框 -->
    <el-dialog
      v-model="loginDialog"
      title="扫码登录小红书"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="login-content">
        <div v-if="loginStatus === 'loading'" class="login-step">
          <el-icon class="is-loading"><Loading /></el-icon>
          <p>正在启动浏览器...</p>
        </div>
        <div v-else-if="loginStatus === 'qrcode'" class="login-step">
          <p class="step-title">请使用小红书APP扫描二维码</p>
          <div class="qrcode-container" ref="qrcodeContainer"></div>
          <p class="step-hint">打开小红书 → 扫一扫 → 扫描二维码</p>
        </div>
        <div v-else-if="loginStatus === 'checking'" class="login-step">
          <el-icon class="is-loading"><Loading /></el-icon>
          <p>等待扫码...</p>
        </div>
        <div v-else-if="loginStatus === 'success'" class="login-step success">
          <el-icon><SuccessFilled /></el-icon>
          <p>登录成功！Cookie已保存</p>
        </div>
        <div v-else-if="loginStatus === 'error'" class="login-step error">
          <el-icon><CircleCloseFilled /></el-icon>
          <p>{{ loginError }}</p>
        </div>
      </div>

      <template #footer>
        <el-button @click="cancelLogin" :disabled="loginStatus === 'loading' || loginStatus === 'checking'">
          取消
        </el-button>
      </template>
    </el-dialog>

    <!-- 绑定账号对话框 -->
    <el-dialog
      v-model="bindDialog"
      :title="isEdit ? '编辑账号' : '绑定新账号'"
      width="500px"
      class="bind-dialog"
    >
      <el-form :model="accountForm" label-width="100px">
        <el-form-item label="平台">
          <el-radio-group v-model="accountForm.platform">
            <el-radio label="xiaohongshu">
              <span class="radio-icon">📕</span>
              小红书
            </el-radio>
            <el-radio label="douyin">
              <span class="radio-icon">🎵</span>
              抖音
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="账号名称">
          <el-input v-model="accountForm.name" placeholder="请输入账号名称" />
        </el-form-item>

        <el-form-item label="手机号">
          <el-input v-model="accountForm.phone" placeholder="请输入绑定的手机号" />
        </el-form-item>

        <el-form-item label="登录方式">
          <el-radio-group v-model="accountForm.loginType">
            <el-radio label="cookie">Cookie</el-radio>
            <el-radio label="qrcode">扫码登录</el-radio>
            <el-radio label="sms">短信验证码</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="accountForm.loginType === 'cookie'" label="Cookie">
          <el-input
            v-model="accountForm.cookie"
            type="textarea"
            :rows="4"
            placeholder="请粘贴Cookie内容"
          />
          <div class="form-hint">
            获取方式：浏览器开发者工具 → Application → Cookies → 复制所有Cookie
          </div>
        </el-form-item>

        <el-form-item label="绑定Agent">
          <el-select
            v-model="accountForm.boundAgents"
            multiple
            placeholder="选择要绑定的Agent"
            style="width: 100%"
          >
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="bindDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAccount">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { accounts as accountsAPI, agents as agentsAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, SuccessFilled, CircleCloseFilled, Warning } from '@element-plus/icons-vue'

const loading = ref(false)

// 账号列表
const accounts = ref([])

const availableAgents = ref([])

const bindDialog = ref(false)
const isEdit = ref(false)

// 扫码登录相关
const loginDialog = ref(false)
const loginStatus = ref('idle') // idle, loading, qrcode, checking, success, error
const loginError = ref('')
const currentLoginAccount = ref(null)
const qrcodeContainer = ref(null)
const accountForm = ref({
  platform: 'xiaohongshu',
  name: '',
  phone: '',
  loginType: 'cookie',
  cookie: '',
  boundAgents: []
})

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

// 加载可用Agent列表
const loadAgents = async () => {
  try {
    const data = await agentsAPI.getAgents()
    // 处理返回数据，支持items或直接数组
    availableAgents.value = data.items || data || []
  } catch (error) {
    console.error('加载Agent列表失败:', error)
    availableAgents.value = []
  }
}

const showBindDialog = () => {
  isEdit.value = false
  accountForm.value = {
    platform: 'xiaohongshu',
    name: '',
    phone: '',
    loginType: 'cookie',
    cookie: '',
    boundAgents: []
  }
  bindDialog.value = true
}

const editAccount = (account) => {
  console.log('Edit account:', account) // 调试日志
  isEdit.value = true
  const accountId = account.id || account.account_id

  // 从agents数组中提取ID
  const boundAgentIds = (account.agents || []).map(a => a.id || a.agent_id)
  console.log('Bound agent IDs:', boundAgentIds) // 调试日志

  accountForm.value = {
    account_id: accountId,
    platform: account.platform,
    name: account.name,
    phone: account.phone || '',
    loginType: account.login_type || 'cookie',
    cookie: account.cookie || '',
    boundAgents: boundAgentIds
  }
  bindDialog.value = true
}

const saveAccount = async () => {
  if (!accountForm.value.name) {
    ElMessage.warning('请输入账号名称')
    return
  }

  loading.value = true
  try {
    const accountData = {
      platform: accountForm.value.platform,
      name: accountForm.value.name,
      phone: accountForm.value.phone,
      login_type: accountForm.value.loginType,
      cookie: accountForm.value.cookie,
      bound_agents: accountForm.value.boundAgents
    }

    if (isEdit.value) {
      await accountsAPI.updateAccount(accountForm.value.account_id, accountData)
      ElMessage.success('账号更新成功')
    } else {
      await accountsAPI.createAccount(accountData)
      ElMessage.success('账号绑定成功')
    }

    bindDialog.value = false
    await loadAccounts()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const toggleAccount = async (account) => {
  try {
    await accountsAPI.toggleAccount(account.id || account.account_id)
    account.enabled = !account.enabled
    ElMessage.success(account.enabled ? '账号已启用' : '账号已禁用')
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  }
}

const refreshAccount = async (account) => {
  try {
    await accountsAPI.refreshAccount(account.id || account.account_id)
    ElMessage.success('状态已刷新')
    await loadAccounts()
  } catch (error) {
    ElMessage.error('刷新失败: ' + error.message)
  }
}

const unbindAccount = async (account) => {
  try {
    await ElMessageBox.confirm(
      `确认解绑账号"${account.name}"？此操作不可恢复。`,
      '解绑确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await accountsAPI.deleteAccount(account.id || account.account_id)
    ElMessage.success('账号已解绑')
    await loadAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解绑失败: ' + error.message)
    }
  }
}

const loadAccounts = async () => {
  loading.value = true
  try {
    const data = await accountsAPI.getAccounts()
    const accountsList = data.items || data || []

    // 为每个账号添加agents和hasCookie字段（如果后端没有返回）
    accounts.value = accountsList.map(account => ({
      ...account,
      agents: account.agents || [],
      hasCookie: account.hasCookie || false
    }))

    console.log('Loaded accounts:', accounts.value)
  } catch (error) {
    ElMessage.error('加载账号列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 扫码登录
const loginAccount = async (account) => {
  currentLoginAccount.value = account
  loginDialog.value = true
  loginStatus.value = 'loading'
  loginError.value = ''

  try {
    // 调用后端扫码登录API
    const response = await fetch(`http://localhost:8000/api/publish/qrcode-login?account_id=${account.id}&wait_time=120`, {
      method: 'POST'
    })

    const result = await response.json()

    if (result.success) {
      loginStatus.value = 'success'
      ElMessage.success('登录成功！')
      // 刷新账号列表
      setTimeout(() => {
        loadAccounts()
        cancelLogin()
      }, 2000)
    } else {
      loginStatus.value = 'error'
      loginError.value = result.error || '登录失败'
    }
  } catch (error) {
    loginStatus.value = 'error'
    loginError.value = error.message || '登录失败'
    console.error('Login error:', error)
  }
}

const cancelLogin = () => {
  loginDialog.value = false
  loginStatus.value = 'idle'
  loginError.value = ''
  currentLoginAccount.value = null
}

onMounted(() => {
  loadAccounts()
  loadAgents()
})
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: flex-end;
}

.btn-icon {
  font-size: 16px;
  margin-right: 6px;
}

/* 账号网格 */
.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* 账号卡片 */
.account-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
}

.account-card:hover {
  box-shadow: var(--shadow-hover);
}

.account-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid var(--color-divider);
}

.platform-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.account-info {
  flex: 1;
}

.account-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.account-platform {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.account-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 账号状态 */
.account-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--color-success);
}

.status-dot.offline {
  background: var(--color-text-placeholder);
}

.status-text {
  color: var(--color-text-primary);
  font-weight: 500;
}

.status-time {
  color: var(--color-text-placeholder);
  margin-left: auto;
}

/* 账号统计 */
.account-stats {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-base);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.stat-number {
  font-family: var(--font-family-title);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-accent);
}

/* 绑定的Agent */
.account-agents {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agents-title {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.agents-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.agent-tag {
  padding: 4px 10px;
  background: var(--color-accent-light);
  border-radius: var(--border-radius-small);
  font-size: 12px;
  color: var(--color-text-primary);
}

.agent-tag.agent-disabled {
  background: #f5f5f5;
  color: #999;
  border: 1px dashed #ddd;
}

.agents-empty {
  font-size: 12px;
  color: var(--color-text-placeholder);
}

/* 账号底部 */
.account-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-divider);
}

/* 对话框样式 */
.radio-icon {
  font-size: 18px;
  margin-right: 4px;
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-placeholder);
  margin-top: 4px;
  line-height: 1.4;
}

/* 响应式 */
@media (max-width: 900px) {
  .accounts-grid {
    grid-template-columns: 1fr;
  }
}

.mb-lg {
  margin-bottom: 32px;
}

/* 扫码登录对话框 */
.login-content {
  padding: 20px 0;
}

.login-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 20px;
}

.login-step .el-icon {
  font-size: 48px;
}

.login-step.success .el-icon {
  color: #67c23a;
}

.login-step.error .el-icon {
  color: #f56c6c;
}

.step-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}

.step-hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.6;
  margin: 0;
}

.qrcode-container {
  width: 200px;
  height: 200px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
}

.qrcode-container img {
  max-width: 100%;
  max-height: 100%;
}
</style>
