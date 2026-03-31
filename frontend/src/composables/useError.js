/**
 * 错误处理
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useError() {
  const error = ref(null)

  const handleError = (err, showMessage = true) => {
    console.error('Error:', err)

    const message = err?.response?.data?.detail || err?.message || '操作失败'

    if (showMessage) {
      ElMessage.error(message)
    }

    error.value = message
    return message
  }

  const clearError = () => {
    error.value = null
  }

  return {
    error,
    handleError,
    clearError
  }
}
