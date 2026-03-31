import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // 开发环境不使用 base 路径，生产环境使用
  const isDev = mode === 'development'

  return {
    plugins: [vue()],
    base: isDev ? '/' : '/zen-matrix-frontend',
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5173,
      host: '0.0.0.0',
      open: true
    }
  }
})
