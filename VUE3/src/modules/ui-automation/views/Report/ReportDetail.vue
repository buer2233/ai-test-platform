<template>
  <div class="report-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="header-title">
        <h3>测试报告 #{{ reportId }}</h3>
        <el-tag :type="isSuccess ? 'success' : 'danger'">
          {{ isSuccess ? '执行成功' : '执行失败' }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 报告概览 -->
    <el-card v-if="browserUseReport" class="overview-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>执行概览</span>
          <el-tag size="small">{{ browserUseReport.history?.length || 0 }} 步骤</el-tag>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="总步骤数">
          {{ totalSteps }}
        </el-descriptions-item>
        <el-descriptions-item label="执行状态">
          <el-tag :type="isSuccess ? 'success' : 'danger'">
            {{ isSuccess ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="截图数量">
          {{ screenshotCount }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 执行步骤时间线 -->
    <el-card class="steps-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>执行步骤</span>
          <div class="header-controls">
            <el-select v-model="stepFilter" size="small" style="width: 120px">
              <el-option label="全部步骤" value="all" />
              <el-option label="仅失败" value="failed" />
              <el-option label="仅成功" value="success" />
            </el-select>
            <el-button size="small" @click="toggleExpandAll">
              {{ allExpanded ? '全部折叠' : '全部展开' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="steps-container">
        <div
          v-for="(step, index) in filteredSteps"
          :key="index"
          class="step-item"
          :class="{ 'is-failed': stepHasError(step), 'is-expanded': expandedSteps[index] }"
        >
          <div class="step-header" @click="toggleStep(index)">
            <div class="step-number">步骤 {{ step.metadata.step_number }}</div>
            <div class="step-info">
              <div class="step-goal">{{ step.model_output.next_goal }}</div>
              <div class="step-meta">
                <span class="step-time">{{ formatStepTime(step.metadata) }}</span>
                <span v-if="stepHasError(step)" class="step-error-badge">
                  <el-icon><WarningFilled /></el-icon>
                  有错误
                </span>
              </div>
            </div>
            <el-icon class="expand-icon" :class="{ 'is-expanded': expandedSteps[index] }">
              <ArrowDown />
            </el-icon>
          </div>

          <div v-show="expandedSteps[index]" class="step-body">
            <!-- 模型输出 -->
            <div class="step-section">
              <div class="section-title">
                <el-icon><ChatDotRound /></el-icon>
                AI 决策
              </div>
              <div class="section-content">
                <div v-if="step.model_output.evaluation_previous_goal" class="evaluation">
                  <span class="label">上一步评估：</span>
                  <span class="value">{{ step.model_output.evaluation_previous_goal }}</span>
                </div>
                <div class="memory">
                  <span class="label">记忆：</span>
                  <span class="value">{{ step.model_output.memory }}</span>
                </div>
                <div class="actions">
                  <span class="label">执行操作：</span>
                  <div class="action-list">
                    <div v-for="(action, i) in step.model_output.action" :key="i" class="action-item">
                      <el-tag size="small" :type="getActionType(action)">
                        {{ getActionLabel(action) }}
                      </el-tag>
                      <span class="action-detail">{{ formatAction(action) }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="step.model_output.thinking" class="thinking">
                  <span class="label">思考过程：</span>
                  <span class="value">{{ step.model_output.thinking }}</span>
                </div>
              </div>
            </div>

            <!-- 执行结果 -->
            <div class="step-section">
              <div class="section-title">
                <el-icon><CircleCheck /></el-icon>
                执行结果
              </div>
              <div class="section-content">
                <div v-for="(result, i) in step.result" :key="i" class="result-item">
                  <div class="result-status">
                    <el-tag :type="result.is_done ? 'success' : 'info'" size="small">
                      {{ result.is_done ? '完成' : '进行中' }}
                    </el-tag>
                    <el-tag v-if="result.success !== undefined" :type="result.success ? 'success' : 'danger'" size="small">
                      {{ result.success ? '成功' : '失败' }}
                    </el-tag>
                  </div>
                  <div v-if="result.error" class="result-error">
                    <el-icon><WarningFilled /></el-icon>
                    {{ result.error }}
                  </div>
                  <div v-if="result.extracted_content" class="result-content">
                    <span class="label">提取内容：</span>
                    <span class="value">{{ result.extracted_content }}</span>
                  </div>
                  <div v-if="result.long_term_memory" class="result-memory">
                    <span class="label">长期记忆：</span>
                    <span class="value">{{ result.long_term_memory }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 浏览器状态 -->
            <div class="step-section">
              <div class="section-title">
                <el-icon><Monitor /></el-icon>
                浏览器状态
              </div>
              <div class="section-content">
                <div class="browser-state">
                  <div class="state-item">
                    <span class="label">URL：</span>
                    <el-link :href="step.state.url" target="_blank" type="primary">
                      {{ step.state.url }}
                    </el-link>
                  </div>
                  <div class="state-item">
                    <span class="label">标题：</span>
                    <span class="value">{{ step.state.title }}</span>
                  </div>
                  <div v-if="step.state.tabs?.length" class="state-item">
                    <span class="label">标签页：</span>
                    <span class="value">{{ step.state.tabs.length }} 个</span>
                  </div>
                  <div v-if="step.state.screenshot_path" class="state-item">
                    <span class="label">截图：</span>
                    <el-image
                      :src="getScreenshotUrl(step.state.screenshot_path)"
                      fit="contain"
                      class="screenshot-thumb"
                      :preview-src-list="[getScreenshotUrl(step.state.screenshot_path)]"
                      preview-teleported
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 最终结果 -->
    <el-card v-if="finalResult" class="final-result-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>最终结果</span>
        </div>
      </template>
      <div class="final-result" :class="{ 'is-success': isSuccess, 'is-failed': !isSuccess }">
        {{ finalResult }}
      </div>
    </el-card>

    <!-- 原始 JSON -->
    <el-card class="json-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>原始 JSON 数据</span>
          <el-button size="small" @click="showJson = !showJson">
            {{ showJson ? '隐藏' : '显示' }}
          </el-button>
        </div>
      </template>
      <el-collapse-transition>
        <div v-show="showJson" class="json-container">
          <pre class="json-content">{{ JSON.stringify(browserUseReport, null, 2) }}</pre>
        </div>
      </el-collapse-transition>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  ArrowDown,
  ChatDotRound,
  CircleCheck,
  Monitor,
  WarningFilled
} from '@element-plus/icons-vue'
import type { BrowserUseReport, AgentHistoryStep, Action } from '../../types'
import { http } from '@/shared/utils/http'
import { uiReportApi, getScreenshotUrl } from '../../api/report'
import type { UiTestReportSummary } from '../../types/report'

const route = useRoute()
const router = useRouter()

const reportId = Number(route.params.id)
const loading = ref(false)
const browserUseReport = ref<BrowserUseReport | null>(null)
const reportSummary = ref<UiTestReportSummary | null>(null)
const showJson = ref(false)
const stepFilter = ref<'all' | 'failed' | 'success'>('all')
const expandedSteps = ref<Record<number, boolean>>({})
const allExpanded = ref(false)

// 获取报告路径（优先 query，回退 summary）
const reportPath = computed(() => {
  return (route.query.report as string) || reportSummary.value?.json_report_path || ''
})

// 加载 JSON 报告
const loadReport = async () => {
  loading.value = true
  try {
    reportSummary.value = await uiReportApi.getReportSummary(reportId)
    if (!reportPath.value) {
      ElMessage.warning('未找到报告文件路径')
      return
    }

    // 使用 http 工具（自动携带认证信息）
    const data = await http.get<BrowserUseReport>(
      `/v1/ui-automation/reports/file`,
      { path: reportPath.value }
    )
    browserUseReport.value = data

    // 默认展开最后一步
    const lastStep = (browserUseReport.value.history?.length || 1) - 1
    expandedSteps.value[lastStep] = true
  } catch (error: any) {
    // http.ts 拦截器已通过 ElMessage.error 显示了后端返回的 message
    // 这里仅做日志记录，避免重复弹出消息
    console.error('加载报告失败:', error)
  } finally {
    loading.value = false
  }
}

// 总步骤数
const totalSteps = computed(() => {
  if (browserUseReport.value?.history?.length) return browserUseReport.value.history.length
  return reportSummary.value?.metrics.total_steps || 0
})

// 截图数量
const screenshotCount = computed(() => {
  if (browserUseReport.value?.history) {
    return browserUseReport.value.history.filter(step => step.state.screenshot_path).length
  }
  return reportSummary.value?.metrics.screenshot_count || 0
})

// 是否成功
const isSuccess = computed(() => {
  if (reportSummary.value) {
    return reportSummary.value.status === 'passed'
  }
  if (!browserUseReport.value?.history) return false
  const lastStep = browserUseReport.value.history[browserUseReport.value.history.length - 1]
  return lastStep?.result?.[0]?.success ?? false
})

// 最终结果
const finalResult = computed(() => {
  if (reportSummary.value?.final_result) return reportSummary.value.final_result
  if (!browserUseReport.value?.history) return ''
  const lastStep = browserUseReport.value.history[browserUseReport.value.history.length - 1]
  return lastStep?.result?.[0]?.extracted_content || ''
})

// 过滤后的步骤
const filteredSteps = computed(() => {
  if (!browserUseReport.value?.history) return []

  let steps = browserUseReport.value.history

  if (stepFilter.value === 'failed') {
    steps = steps.filter(step => stepHasError(step))
  } else if (stepFilter.value === 'success') {
    steps = steps.filter(step => !stepHasError(step))
  }

  return steps
})

// 判断步骤是否有错误
const stepHasError = (step: AgentHistoryStep) => {
  return step.result?.some(r => r.error)
}

// 切换步骤展开
const toggleStep = (index: number) => {
  expandedSteps.value[index] = !expandedSteps.value[index]
}

// 切换全部展开
const toggleExpandAll = () => {
  allExpanded.value = !allExpanded.value
  filteredSteps.value.forEach((_, index) => {
    expandedSteps.value[index] = allExpanded.value
  })
}

// 获取操作类型
const getActionType = (action: Action) => {
  if ('navigate' in action) return 'primary'
  if ('click' in action) return 'success'
  if ('input' in action) return 'info'
  if ('done' in action) return action.done?.success ? 'success' : 'danger'
  if ('search' in action) return 'warning'
  return ''
}

// 获取操作标签
const getActionLabel = (action: Action) => {
  if ('navigate' in action) return '导航'
  if ('click' in action) return '点击'
  if ('input' in action) return '输入'
  if ('done' in action) return '完成'
  if ('search' in action) return '搜索'
  if ('scroll' in action) return '滚动'
  if ('extract' in action) return '提取'
  if ('wait' in action) return '等待'
  if ('go_back' in action) return '返回'
  if ('switch_tab' in action) return '切换标签'
  if ('close_tab' in action) return '关闭标签'
  return '未知操作'
}

// 格式化操作详情
const formatAction = (action: Action) => {
  if ('navigate' in action) return action.navigate?.url || ''
  if ('click' in action) return action.click?.element || ''
  if ('input' in action) return `"${action.input?.text}"` || ''
  if ('search' in action) return action.search?.query || ''
  if ('done' in action) return action.done?.text || ''
  if ('scroll' in action) return action.scroll?.direction || ''
  if ('extract' in action) return action.extract || ''
  return JSON.stringify(action)
}

// 格式化步骤时间
const formatStepTime = (metadata: { step_start_time: number; step_end_time: number; step_interval: number | null }) => {
  const start = new Date(metadata.step_start_time * 1000)
  const end = new Date(metadata.step_end_time * 1000)
  const duration = metadata.step_interval ? `${metadata.step_interval.toFixed(2)}s` : '-'

  return `${start.toLocaleTimeString()} - ${end.toLocaleTimeString()} (${duration})`
}

// 刷新
const handleRefresh = () => {
  loadReport()
}

// 返回
const goBack = () => {
  router.back()
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.report-detail {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-controls {
  display: flex;
  gap: 8px;
}

/* 步骤列表 */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.step-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.step-item.is-failed {
  border-color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  background: var(--el-fill-color-light);
}

.step-header:hover {
  background: var(--el-fill-color);
}

.step-number {
  flex-shrink: 0;
  width: 80px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-goal {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.step-time {
  color: var(--el-text-color-secondary);
}

.step-error-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--el-color-danger);
}

.expand-icon {
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}

/* 步骤详情 */
.step-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px solid var(--el-border-color);
}

.step-section {
  background: var(--el-fill-color-extra-light);
  border-radius: 6px;
  overflow: hidden;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.section-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-content > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.value {
  font-size: 13px;
  color: var(--el-text-color-primary);
  line-height: 1.5;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-detail {
  font-size: 12px;
  font-family: var(--el-font-family-mono);
}

.result-item {
  padding: 8px;
  background: var(--el-color-white);
  border-radius: 4px;
}

.result-status {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.result-error {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px;
  background: var(--el-color-danger-light-9);
  border-radius: 4px;
  color: var(--el-color-danger);
  font-size: 12px;
}

.browser-state {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.state-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.screenshot-thumb {
  width: 60px;
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
}

/* 最终结果 */
.final-result {
  padding: 16px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
}

.final-result.is-success {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-5);
}

.final-result.is-failed {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
  border: 1px solid var(--el-color-danger-light-5);
}

/* JSON 容器 */
.json-container {
  max-height: 400px;
  overflow: auto;
  background: var(--el-fill-color-extra-light);
  border-radius: 4px;
  padding: 12px;
}

.json-content {
  margin: 0;
  font-size: 12px;
  font-family: var(--el-font-family-mono);
  color: var(--el-text-color-primary);
}
</style>
