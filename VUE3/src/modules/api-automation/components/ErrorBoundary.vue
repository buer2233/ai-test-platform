<template>
  <div class="error-boundary">
    <slot v-if="!hasError"></slot>
    <div v-else class="error-fallback">
      <el-result icon="error" title="组件加载失败" :sub-title="errorMessage">
        <template #extra>
          <el-button type="primary" @click="handleReload">重新加载</el-button>
          <el-button @click="handleGoHome">返回首页</el-button>
        </template>
      </el-result>
      <el-collapse v-if="errorDetails" class="error-details" style="margin-top: 20px">
        <el-collapse-item title="错误详情" name="details">
          <pre class="error-stack">{{ errorDetails }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, type Ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const hasError: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')
const errorDetails: Ref<string> = ref('')

/**
 * 捕获子组件错误
 */
onErrorCaptured((error: Error, instance, info) => {
  console.error('[ErrorBoundary] Caught error:', error)
  console.error('[ErrorBoundary] Component info:', info)

  hasError.value = true
  errorMessage.value = error.message || '未知错误'
  errorDetails.value = error.stack || ''

  // 返回 false 阻止错误继续传播
  return false
})

/**
 * 重新加载页面
 */
function handleReload(): void {
  window.location.reload()
}

/**
 * 返回首页
 */
function handleGoHome(): void {
  router.push('/api-automation/dashboard')
}
</script>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
}

.error-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 20px;
}

.error-details {
  width: 100%;
  max-width: 600px;
}

.error-stack {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}
</style>
