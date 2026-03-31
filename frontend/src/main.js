import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

// 导入全局样式
import './styles/zen-theme.css'
import './styles/common.css'
import './styles/enhanced.css'

const app = createApp(App)
const pinia = createPinia()

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 在路由守卫设置之前同步初始化 authStore
const authStore = useAuthStore()
authStore.init()
console.log('Auth store initialized')

app.mount('#app')
