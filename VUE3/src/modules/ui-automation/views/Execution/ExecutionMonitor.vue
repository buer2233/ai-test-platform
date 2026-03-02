<template>
  <div class="execution-monitor">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="header-title">
        <h3>执行监控 #{{ executionId }}</h3>
        <ExecutionStatusBadge :status="executionStore.currentExecution?.status" />
      </div>
      <div class="header-actions">
        <el-button
          v-if="executionStore.currentExecution?.status === 'running'"
          type="warning"
          @click="handleCancel"
        >
          <el-icon><VideoPause /></el-icon>
          取消执行
        </el-button>
        <el-button
          v-if="executionStore.currentExecution?.status === 'passed' || executionStore.currentExecution?.status === 'failed' || executionStore.currentExecution?.status === 'error'"
          type="success"
          @click="handleViewReport"
        >
          <el-icon><Document /></el-icon>
          查看报告
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 执行信息卡片 -->
    <el-row :gutter="16" class="info-row">
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-label">测试用例</div>
          <div class="info-value">{{ executionStore.currentExecution?.test_case_name }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-label">所属项目</div>
          <div class="info-value">{{ executionStore.currentExecution?.project_name }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-label">执行时间</div>
          <div class="info-value">
            {{ executionStore.currentExecution?.duration_seconds || '-' }} 秒
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-label">浏览器模式</div>
          <div class="info-value">
            {{ executionStore.currentExecution?.browser_mode === 'headless' ? '无头' : '有头' }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 执行进度和日志 -->
    <el-row :gutter="16" class="content-row">
      <el-col :span="14">
        <el-card class="log-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>执行日志</span>
              <el-switch
                v-model="autoScroll"
                active-text="自动滚动"
                size="small"
              />
            </div>
          </template>
          <div ref="logContainer" class="log-container">
            <div
              v-for="(log, index) in logs"
              :key="index"
              :class="['log-entry', `log-${log.type}`]"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div v-if="logs.length === 0" class="log-empty">
              暂无日志
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="screenshot-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>执行截图</span>
              <span class="screenshot-count">{{ screenshots.length }} 张</span>
            </div>
          </template>
          <div class="screenshot-container">
            <div
              v-for="(screenshot, index) in screenshots"
              :key="index"
              class="screenshot-item"
              @click="handlePreviewScreenshot(screenshot)"
            >
              <img :src="screenshot.data" :alt="screenshot.description" />
              <div class="screenshot-desc">{{ screenshot.description }}</div>
            </div>
            <div v-if="screenshots.length === 0" class="screenshot-empty">
              暂无截图
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 错误信息 -->
    <el-card
      v-if="executionStore.currentExecution?.error_message"
      class="error-card"
      shadow="never"
    >
      <template #header>
        <span class="error-title">错误信息</span>
      </template>
      <div class="error-message">
        {{ executionStore.currentExecution.error_message }}
      </div>
    </el-card>

    <!-- 截图预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="截图预览" width="800px">
      <img :src="previewScreenshot?.data" style="width: 100%" />
      <template #footer>
        <el-text>{{ previewScreenshot?.description }}</el-text>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * 执行监控页
 *
 * 实时展示 UI 自动化测试执行过程：
 * - 基本信息卡片（用例名、项目名、耗时、浏览器模式）
 * - 实时日志面板（支持自动滚动）
 * - 执行截图面板（支持点击预览）
 * - 错误信息展示
 * - 通过 WebSocket 接收实时进度推送
 */

import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Document,
  Refresh,
  VideoPause
} from '@element-plus/icons-vue'

import { useUiExecutionStore } from '../../stores/execution'
import { getScreenshotUrl, uiReportApi } from '../../api/report'
import type { BrowserUseReport } from '../../types/report'
import ExecutionStatusBadge from '@ui-automation/components/ExecutionStatusBadge.vue'

const route = useRoute()
const router = useRouter()
const executionStore = useUiExecutionStore()

/** 当前执行记录 ID（从路由参数获取） */
const executionId = Number(route.params.id)

/** 日志容器 DOM 引用（用于自动滚动） */
const logContainer = ref<HTMLElement>()
/** 是否启用自动滚动到日志底部 */
const autoScroll = ref(true)
/** 截图预览对话框是否显示 */
const previewDialogVisible = ref(false)
/** 当前预览的截图数据 */
const previewScreenshot = ref<{ data: string; description: string } | null>(null)

/** 实时日志数据 */
const logs = ref<Array<{ time: string; message: string; type: string }>>([])

/** 执行截图数据 */
const screenshots = ref<Array<{ data: string; description: string; timestamp: string }>>([])

/** WebSocket 连接实例 */
let ws: WebSocket | null = null

/* ---------- 页面操作 ---------- */

/** 返回执行记录列表 */
const goBack = () => {
  router.push('/ui-automation/executions')
}

/** 刷新执行数据并重新解析日志和截图 */
const refreshData = async () => {
  await executionStore.fetchExecution(executionId)
  parseAgentHistory()
}

/** 取消当前执行（需二次确认） */
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该执行吗？', '取消确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await executionStore.cancelExecution(executionId)
    ElMessage.success('已取消执行')
    await refreshData()
  } catch {
    // 用户取消确认操作
  }
}

/** 跳转到关联的测试报告页面 */
const handleViewReport = () => {
  const report = executionStore.currentExecution?.report
  if (report) {
    // report 可能是对象（嵌套序列化）或纯 ID
    const reportId = typeof report === 'object' ? report.id : report
    router.push(`/ui-automation/reports/${reportId}`)
  } else {
    ElMessage.warning('该执行记录没有关联的报告')
  }
}

/* ---------- 日志和截图解析 ---------- */

/**
 * 解析 Agent 历史记录
 * 将 JSON 格式的 agent_history 转换为日志列表，
 * 同时从关联报告中加载截图数据
 */
const parseAgentHistory = () => {
  const execution = executionStore.currentExecution
  if (!execution) return

  // 解析执行日志
  if (execution.agent_history) {
    try {
      const history = JSON.parse(execution.agent_history)
      logs.value = history.map((step: any) => ({
        time: new Date(step.timestamp).toLocaleTimeString('zh-CN'),
        message: step.action || JSON.stringify(step),
        type: step.error ? 'error' : 'info'
      }))
    } catch {
      // agent_history 不是有效 JSON，作为纯文本显示
      logs.value = [{
        time: new Date().toLocaleTimeString('zh-CN'),
        message: execution.agent_history,
        type: 'info'
      }]
    }
  }

  // 从关联报告中加载截图
  if (execution.report) {
    loadScreenshotsFromReport(execution.report)
  }
}

/**
 * 从 browser_use JSON 报告中提取截图数据
 * @param report - 报告 ID 或报告对象
 */
const loadScreenshotsFromReport = async (report: any) => {
  try {
    const reportId = typeof report === 'object' ? report.id : report
    const summary = await uiReportApi.getReportSummary(reportId)
    if (!summary.json_report_path) return

    const reportData = await uiReportApi.getReportFile(summary.json_report_path) as BrowserUseReport
    if (!reportData?.history) return

    // 遍历步骤，提取包含截图路径的步骤信息
    const loaded: Array<{ data: string; description: string; timestamp: string }> = []
    for (const step of reportData.history) {
      if (step.state?.screenshot_path) {
        loaded.push({
          data: getScreenshotUrl(step.state.screenshot_path),
          description: step.model_output?.next_goal || `步骤 ${step.metadata?.step_number || ''}`,
          timestamp: step.metadata?.step_start_time
            ? new Date(step.metadata.step_start_time * 1000).toISOString()
            : '',
        })
      }
    }
    screenshots.value = loaded
  } catch (error) {
    console.error('加载报告截图失败:', error)
  }
}

/** 点击截图缩略图：打开预览对话框 */
const handlePreviewScreenshot = (screenshot: { data: string; description: string }) => {
  previewScreenshot.value = screenshot
  previewDialogVisible.value = true
}

/* ---------- WebSocket 实时通信 ---------- */

/** 建立 WebSocket 连接，接收执行进度推送 */
const connectWebSocket = () => {
  const wsUrl = `ws://127.0.0.1:8000/ws/ui-automation/${executionId}/`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'ui_automation.progress') {
      // 追加日志条目
      logs.value.push({
        time: new Date(data.data.timestamp).toLocaleTimeString('zh-CN'),
        message: data.message,
        type: data.data.status === 'failed' ? 'error' : 'info'
      })

      // 自动滚动到最新日志
      if (autoScroll.value) {
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      }

      // 执行结束：刷新数据并断开 WebSocket
      const terminalStatuses = ['passed', 'failed', 'error']
      if (terminalStatuses.includes(data.data.status)) {
        refreshData()
        disconnectWebSocket()
      }

      // 接收到新截图
      if (data.data.screenshot) {
        screenshots.value.push({
          data: data.data.screenshot,
          description: data.message,
          timestamp: data.data.timestamp
        })
      }
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected')
  }
}

/** 断开 WebSocket 连接 */
const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

/* ---------- 状态变化监听 ---------- */

/** 监听执行状态：变为 running 时自动建立 WebSocket 连接 */
watch(() => executionStore.currentExecution?.status, (newStatus) => {
  if (newStatus === 'running' && !ws) {
    connectWebSocket()
  }
})

/* ---------- 生命周期 ---------- */

onMounted(async () => {
  await refreshData()
  // 如果当前正在执行，立即建立 WebSocket 连接
  if (executionStore.currentExecution?.status === 'running') {
    connectWebSocket()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.execution-monitor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.info-row {
  margin-bottom: 0;
}

.info-card {
  margin-bottom: 0;
  text-align: center;
}

.info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.content-row {
  flex: 1;
  margin-bottom: 0;
}

.log-card,
.screenshot-card {
  height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-container {
  height: 430px;
  overflow-y: auto;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 12px;
}

.log-entry {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-time {
  color: var(--el-text-color-secondary);
  min-width: 80px;
}

.log-message {
  flex: 1;
}

.log-info {
  color: var(--el-text-color-primary);
}

.log-error {
  color: var(--el-color-danger);
}

.log-empty {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 40px 0;
}

.screenshot-container {
  height: 430px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screenshot-item {
  cursor: pointer;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s;
}

.screenshot-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.screenshot-item img {
  width: 100%;
  height: auto;
  display: block;
}

.screenshot-desc {
  padding: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
}

.screenshot-empty {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 40px 0;
}

.screenshot-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.error-card {
  margin-bottom: 0;
}

.error-title {
  color: var(--el-color-danger);
  font-weight: 600;
}

.error-message {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 4px;
}
</style>
