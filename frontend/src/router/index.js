import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from '../middleware/auth'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Agents from '../views/Agents.vue'
import AgentEdit from '../views/AgentEdit.vue'
import Content from '../views/Content.vue'
import Review from '../views/Review.vue'
import Published from '../views/Published.vue'
import Accounts from '../views/Accounts.vue'
import Statistics from '../views/Statistics.vue'
import Settings from '../views/Settings.vue'
import Render from '../views/Render.vue'
import PromptTemplates from '../views/PromptTemplates.vue'
import HotSearch from '../views/HotSearch.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { public: true }
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'dashboard',
        name: 'DashboardAlt',
        component: Dashboard
      },
      {
        path: 'agents',
        name: 'Agents',
        component: Agents
      },
      {
        path: 'agents/new',
        name: 'AgentNew',
        component: AgentEdit
      },
      {
        path: 'agents/:id/edit',
        name: 'AgentEdit',
        component: AgentEdit
      },
      {
        path: 'workspace',
        redirect: '/workspace/generate'
      },
      {
        path: 'workspace/generate',
        name: 'WorkspaceGenerate',
        component: Content
      },
      {
        path: 'workspace/review',
        name: 'WorkspaceReview',
        component: Review
      },
      {
        path: 'workspace/published',
        name: 'WorkspacePublished',
        component: Published
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: Accounts
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: Statistics
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings
      },
      {
        path: 'render',
        name: 'Render',
        component: Render
      },
      {
        path: 'content',
        name: 'Content',
        component: Content
      },
      {
        path: 'review',
        name: 'Review',
        component: Review
      },
      {
        path: 'prompt-templates',
        name: 'PromptTemplates',
        component: PromptTemplates
      },
      {
        path: 'hot-search',
        name: 'HotSearch',
        component: HotSearch
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 设置认证守卫
setupAuthGuard(router)

export default router
