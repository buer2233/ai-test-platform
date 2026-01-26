<template>
  <div class="realtime-execution-status">
    <!-- 执行头部 -->
    <div class="execution-header">
      <div class="header-left">
        <!-- WebSocket 连接状态 -->
        <div class="ws-status" :class="wsStatusClass" @click="toggleWebSocket">
          <div class="ws-indicator"></div>
          <span class="ws-label">{{ wsStatusLabel }}</span>
        </div>

        <div class="status-badge" :class="statusClass">
          <el-icon v-if="status === 'RUNNING'" class="rotating"><Refresh /></el-icon>
          <el-icon v-else-if="status === 'COMPLETED'"><CircleCheck /></el-icon>
          <el-icon v-else-if="status === 'FAILED'"><CircleClose /></el-icon>
          <el-icon v-else><Clock /></el-icon>
          <span>{{ statusText }}</span>
        </div>
        <h3 class="execution-title">{{ execution?.name || '测试执行' }}</h3>
      </div>
      <div class="header-actions">
        <el-button
          v-if="status === 'RUNNING'"
          type="danger"
          size="small"
          @click="handleCancel"
          :loading="cancelling"
        >
          <el-icon><CloseBold /></el-icon>
          取消执行
        </el-button>
        <el-button
          v-if="status === 'COMPLETED' || status === 'FAILED' || status === 'CANCELLED'"
          type="primary"
          size="small"
          @click="handleRetry"
        >
          <el-icon><Refresh /></el-icon>
          重新执行
        </el-button>
        <el-dropdown trigger="click" @command="handleMoreAction">
          <el-button size="small">
            <el-icon><MoreFilled /></el-icon>
            更多
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="exportLogs">
                <el-icon><Download /></el-icon>
                导出日志
              </el-dropdown-item>
              <el-dropdown-item command="exportReport">
                <el-icon><Document /></el-icon>
                导出报告
              </el-dropdown-item>
              <el-dropdown-item command="copySummary" divided>
                <el-icon><DocumentCopy /></el-icon>
                复制摘要
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button size="small" @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 统计面板 -->
    <div class="statistics-panel">
      <div class="stat-item">
        <div class="stat-icon" :style="{ backgroundColor: '#ecf5ff' }">
          <el-icon :size="20" color="#409eff"><Files /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.total }}</div>
          <div class="stat-label">总用例</div>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon" :style="{ backgroundColor: '#f0f9ff' }">
          <el-icon :size="20" color="#67c23a"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value success">{{ statistics.passed }}</div>
          <div class="stat-label">通过</div>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon" :style="{ backgroundColor: '#fef0f0' }">
          <el-icon :size="20" color="#f56c6c"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value failed">{{ statistics.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon" :style="{ backgroundColor: '#f4f4f5' }">
          <el-icon :size="20" color="#909399"><RemoveFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.skipped }}</div>
          <div class="stat-label">跳过</div>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-icon" :style="{ backgroundColor: '#fdf6ec' }">
          <el-icon :size="20" color="#e6a23c"><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formattedDuration }}</div>
          <div class="stat-label">耗时</div>
        </div>
      </div>
      <div class="stat-item progress-item">
        <div class="progress-wrapper">
          <div class="progress-header">
            <span>执行进度</span>
            <span class="progress-percent">{{ progressPercent }}%</span>
          </div>
          <el-progress
            :percentage="progressPercent"
            :status="progressStatus"
            :stroke-width="12"
            :show-text="false"
          />
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content" :class="{ 'fullscreen': isFullscreen }">
      <!-- 左侧：测试用例列表 -->
      <div class="test-cases-panel">
        <div class="panel-header">
          <span>测试用例</span>
          <div class="header-controls">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索用例..."
              size="small"
              clearable
              style="width: 120px"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-radio-group v-model="filterStatus" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="running">运行中</el-radio-button>
              <el-radio-button label="passed">通过</el-radio-button>
              <el-radio-button label="failed">失败</el-radio-button>
            </el-radio-group>
          </div>
        </div>

        <!-- 快捷键提示 -->
        <div v-if="!hasKeyboardInteracted" class="keyboard-hint">
          <el-icon><Keyboard /></el-icon>
          按 ? 查看快捷键
        </div>

        <div class="test-cases-list" ref="casesListRef" tabindex="0" @keydown="handleListKeydown">
          <div
            v-for="(result, index) in filteredTestResults"
            :key="result.id"
            class="test-case-item"
            :class="{
              'running': result.status === 'RUNNING',
              'passed': result.status === 'PASSED',
              'failed': result.status === 'FAILED',
              'skipped': result.status === 'SKIPPED',
              'current': currentTestCaseIndex === index
            }"
            @click="selectTestCase(index)"
            @dblclick="goToTestCaseDetail(result)"
          >
            <div class="case-number">{{ index + 1 }}</div>
            <div class="case-info">
              <div class="case-name" :title="result.test_case_name">{{ result.test_case_name }}</div>
              <div class="case-method">
                <el-tag :type="getMethodTagType(result.test_case_method)" size="small">
                  {{ result.test_case_method }}
                </el-tag>
                <span class="case-url" :title="result.test_case_url">{{ result.test_case_url }}</span>
              </div>
            </div>
            <div class="case-status">
              <el-icon v-if="result.status === 'RUNNING'" class="rotating"><Loading /></el-icon>
              <el-icon v-else-if="result.status === 'PASSED'"><CircleCheck /></el-icon>
              <el-icon v-else-if="result.status === 'FAILED'"><CircleClose /></el-icon>
              <el-icon v-else-if="result.status === 'SKIPPED'"><RemoveFilled /></el-icon>
              <el-icon v-else><Clock /></el-icon>
            </div>
            <div class="case-time">
              {{ result.response_time ? result.response_time + 'ms' : '-' }}
            </div>
            <div class="case-actions" v-if="result.status === 'FAILED'">
              <el-button
                size="small"
                text
                @click.stop="retrySingleCase(result)"
                title="重试此用例"
              >
                <el-icon><RefreshRight /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：详情和日志 -->
      <div class="details-panel">
        <el-tabs v-model="activeTab" class="details-tabs">
          <el-tab-pane name="detail" label="执行详情">
            <div v-if="currentResult" class="detail-content">
              <!-- 请求信息 -->
              <div class="section">
                <div class="section-header">
                  <el-icon><Promotion /></el-icon>
                  <span>请求信息</span>
                </div>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="请求方法">
                    <el-tag :type="getMethodTagType(currentResult.test_case_method)">
                      {{ currentResult.test_case_method }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="请求URL">
                    {{ currentResult.test_case_url }}
                  </el-descriptions-item>
                  <el-descriptions-item label="环境" :span="2">
                    {{ execution?.environment_name || '-' }}
                  </el-descriptions-item>
                </el-descriptions>

                <el-collapse v-model="requestCollapse" class="mt-3">
                  <el-collapse-item title="请求头" name="headers">
                    <pre class="json-content">{{ formatJson(currentResult.request_headers) }}</pre>
                  </el-collapse-item>
                  <el-collapse-item title="请求参数" name="params">
                    <pre class="json-content">{{ formatJson(currentResult.request_params) }}</pre>
                  </el-collapse-item>
                  <el-collapse-item title="请求体" name="body">
                    <pre class="json-content">{{ formatJson(currentResult.request_body) }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 响应信息 -->
              <div class="section" v-if="currentResult.status !== 'PENDING'">
                <div class="section-header">
                  <el-icon><Download /></el-icon>
                  <span>响应信息</span>
                  <el-button
                    v-if="currentResult.response_body"
                    size="small"
                    text
                    @click="copyResponseBody"
                    style="margin-left: auto"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                    复制
                  </el-button>
                </div>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="状态码">
                    <el-tag :type="getStatusCodeColor(currentResult.response_status)">
                      {{ currentResult.response_status }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="响应时间">
                    <el-tag :type="getResponseTypeColor(currentResult.response_time)">
                      {{ currentResult.response_time }}ms
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="响应大小" :span="2">
                    {{ formatBytes(currentResult.response_size) }}
                  </el-descriptions-item>
                </el-descriptions>

                <el-collapse v-model="responseCollapse" class="mt-3">
                  <el-collapse-item title="响应头" name="headers">
                    <pre class="json-content">{{ formatJson(currentResult.response_headers) }}</pre>
                  </el-collapse-item>
                  <el-collapse-item title="响应体" name="body">
                    <div class="response-body-wrapper">
                      <div class="response-body-toolbar">
                        <el-radio-group v-model="responseBodyFormat" size="small">
                          <el-radio-button label="formatted">格式化</el-radio-button>
                          <el-radio-button label="raw">原始</el-radio-button>
                          <el-radio-button label="preview">预览</el-radio-button>
                        </el-radio-group>
                        <el-button
                          v-if="responseBodyFormat === 'preview'"
                          size="small"
                          text
                          @click="expandPreview"
                        >
                          {{ previewExpanded ? '收起' : '展开' }}
                        </el-button>
                      </div>
                      <pre
                        v-if="responseBodyFormat !== 'preview'"
                        class="json-content response-body"
                        :class="{ 'highlighted': highlightSyntax }"
                      >{{ formattedResponseBody }}</pre>
                      <pre
                        v-else
                        class="json-content response-body"
                        :class="{ 'expanded': previewExpanded }"
                      >{{ previewResponseBody }}</pre>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 断言结果 -->
              <div class="section" v-if="currentResult.assertions && currentResult.assertions.length > 0">
                <div class="section-header">
                  <el-icon><DocumentChecked /></el-icon>
                  <span>断言结果 ({{ currentResult.assertions.length }})</span>
                  <el-button
                    size="small"
                    text
                    @click="expandAllAssertions"
                    style="margin-left: auto"
                  >
                    全部展开
                  </el-button>
                </div>
                <el-collapse v-model="assertionsCollapse" class="assertions-collapse">
                  <el-collapse-item
                    v-for="(assertion, idx) in currentResult.assertions"
                    :key="idx"
                    :name="idx"
                  >
                    <template #title>
                      <div class="assertion-collapse-title" :class="{ 'passed': assertion.passed, 'failed': !assertion.passed }">
                        <el-icon :class="assertion.passed ? 'success' : 'error'">
                          <CircleCheck v-if="assertion.passed" />
                          <CircleClose v-else />
                        </el-icon>
                        <span class="assertion-type-text">{{ assertion.type || assertion.assertion_type }}</span>
                        <el-tag :type="assertion.passed ? 'success' : 'danger'" size="small">
                          {{ assertion.passed ? '通过' : '失败' }}
                        </el-tag>
                      </div>
                    </template>
                    <div class="assertion-detail-content">
                      <el-descriptions :column="1" border size="small">
                        <el-descriptions-item label="断言类型">
                          {{ assertion.type || assertion.assertion_type }}
                        </el-descriptions-item>
                        <el-descriptions-item label="目标字段">
                          <code>{{ assertion.target || assertion.field || '-' }}</code>
                        </el-descriptions-item>
                        <el-descriptions-item label="操作符">
                          <el-tag size="small">{{ assertion.operator || '-' }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="期望值">
                          <code>{{ formatValue(assertion.expected) }}</code>
                        </el-descriptions-item>
                        <el-descriptions-item label="实际值">
                          <code>{{ formatValue(assertion.actual) }}</code>
                        </el-descriptions-item>
                        <el-descriptions-item v-if="assertion.message" label="消息">
                          <span :class="{ 'error-text': !assertion.passed }">{{ assertion.message }}</span>
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 错误信息 -->
              <div class="section" v-if="currentResult.error_message">
                <div class="section-header error">
                  <el-icon><Warning /></el-icon>
                  <span>错误信息</span>
                </div>
                <el-alert type="error" :closable="false">
                  <pre class="error-message">{{ currentResult.error_message }}</pre>
                </el-alert>
              </div>

              <!-- 提取的变量 -->
              <div class="section" v-if="currentResult.extracted_variables && Object.keys(currentResult.extracted_variables).length > 0">
                <div class="section-header">
                  <el-icon><Collection /></el-icon>
                  <span>提取的变量</span>
                </div>
                <div class="extracted-variables-grid">
                  <div
                    v-for="(value, key) in currentResult.extracted_variables"
                    :key="key"
                    class="extracted-variable-item"
                  >
                    <span class="variable-name">${{ key }}</span>
                    <span class="variable-value">{{ truncateValue(value) }}</span>
                    <el-button size="small" text @click="copyToClipboard(String(value))">
                      <el-icon><DocumentCopy /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="no-selection">
              <el-empty description="请选择测试用例查看详情" />
              <div class="keyboard-hints">
                <p>快捷键：</p>
                <p><kbd>↑</kbd> <kbd>↓</kbd> 选择用例</p>
                <p><kbd>Enter</kbd> 查看详情</p>
                <p><kbd>?</kbd> 查看所有快捷键</p>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane name="charts" label="响应时间">
            <div class="charts-content">
              <div ref="responseTimeChartRef" class="chart-container"></div>
            </div>
          </el-tab-pane>

          <el-tab-pane name="logs" label="执行日志">
            <div class="logs-content">
              <div class="logs-header">
                <el-radio-group v-model="logLevel" size="small">
                  <el-radio-button label="all">全部</el-radio-button>
                  <el-radio-button label="info">信息</el-radio-button>
                  <el-radio-button label="success">成功</el-radio-button>
                  <el-radio-button label="warning">警告</el-radio-button>
                  <el-radio-button label="error">错误</el-radio-button>
                </el-radio-group>
                <el-button size="small" @click="clearLogs">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
                <el-button size="small" @click="exportLogs">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
                <el-switch v-model="autoScroll" size="small" active-text="自动滚动" />
              </div>
              <div class="logs-list" ref="logsListRef">
                <div
                  v-for="(log, index) in filteredLogs"
                  :key="index"
                  class="log-item"
                  :class="log.level"
                >
                  <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                  <span class="log-level">{{ log.level.toUpperCase() }}</span>
                  <span class="log-message">{{ log.message }}</span>
                  <el-button
                    size="small"
                    text
                    @click="copyToClipboard(log.message)"
                    class="log-copy"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：全局提取的变量 -->
      <div class="variables-panel">
        <div class="panel-header">
          <span>
            <el-icon><Collection /></el-icon>
            提取的变量
          </span>
          <span class="variables-count">({{ Object.keys(extractedVariables).length }})</span>
        </div>
        <div class="variables-list">
          <div
            v-for="(value, key) in extractedVariables"
            :key="key"
            class="variable-item"
          >
            <div class="variable-name" :title="'${' + key + '}'">${{ key }}</div>
            <div class="variable-value">
              <code :title="String(value)">{{ truncateValue(value) }}</code>
              <el-button size="small" text @click="copyToClipboard(String(value))">
                <el-icon><DocumentCopy /></el-icon>
              </el-button>
            </div>
          </div>
          <el-empty v-if="Object.keys(extractedVariables).length === 0" description="暂无提取的变量" :image-size="60" />
        </div>
      </div>
    </div>

    <!-- 底部：时间线 -->
    <div class="timeline-section">
      <div class="timeline-header">
        <span>执行时间线</span>
        <el-button size="small" text @click="scrollToCurrent">
          <el-icon><Pointer /></el-icon>
          定位当前
        </el-button>
      </div>
      <el-timeline class="execution-timeline">
        <el-timeline-item
          v-for="(result, index) in execution?.test_results || []"
          :key="result.id"
          :type="getTimelineType(result.status)"
          :icon="getTimelineIcon(result.status)"
          :size="currentTestCaseIndex === index ? 'large' : 'normal'"
          :hollow="currentTestCaseIndex === index"
          @click="selectTestCase(index)"
          class="timeline-item"
        >
          <div class="timeline-content">
            <div class="timeline-case-name">{{ result.test_case_name }}</div>
            <div class="timeline-case-url">{{ result.test_case_method }} {{ result.test_case_url }}</div>
            <div class="timeline-result">
              <el-tag :type="getStatusTagType(result.status)" size="small">
                {{ getStatusText(result.status) }}
              </el-tag>
              <span v-if="result.response_time" class="timeline-time">
                {{ result.response_time }}ms
              </span>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 快捷键帮助对话框 -->
    <el-dialog
      v-model="showKeyboardHelp"
      title="快捷键"
      width="500px"
    >
      <div class="keyboard-shortcuts">
        <div class="shortcut-item">
          <kbd>?</kbd>
          <span>显示/隐藏快捷键帮助</span>
        </div>
        <div class="shortcut-item">
          <kbd>↑</kbd> <kbd>↓</kbd>
          <span>选择上/下个测试用例</span>
        </div>
        <div class="shortcut-item">
          <kbd>Enter</kbd>
          <span>查看当前用例详情</span>
        </div>
        <div class="shortcut-item">
          <kbd>F</kbd>
          <span>切换全屏模式</span>
        </div>
        <div class="shortcut-item">
          <kbd>Esc</kbd>
          <span>退出全屏</span>
        </div>
        <div class="shortcut-item">
          <kbd>1</kbd>-<kbd>4</kbd>
          <span>切换过滤器 (全部/运行中/通过/失败)</span>
        </div>
        <div class="shortcut-item">
          <kbd>Ctrl</kbd>+<kbd>C</kbd>
          <span>复制当前选中的内容</span>
        </div>
        <div class="shortcut-item">
          <kbd>L</kbd>
          <span>切换到日志标签</span>
        </div>
        <div class="shortcut-item">
          <kbd>D</kbd>
          <span>切换到详情标签</span>
        </div>
        <div class="shortcut-item">
          <kbd>C</kbd>
          <span>切换到图表标签</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, CircleCheck, CircleClose, Clock, CloseBold, FullScreen,
  Files, RemoveFilled, Timer, Loading, Promotion, Download,
  DocumentChecked, Warning, Delete, Collection, DocumentCopy,
  DCaret, Keyboard, Search, MoreFilled, Document, RefreshRight,
  Pointer
} from '@element-plus/icons-vue'
import { executionApi } from '../api/execution'
import type { ApiTestExecution, TestResult } from '../types/execution'
import { saveAs } from 'file-saver'
import * as echarts from 'echarts'

interface Props {
  execution: ApiTestExecution | null
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true
})

const emit = defineEmits<{
  'cancel': []
  'retry': []
  'finish': []
  'viewCase': [testCase: any]
}>()

// 响应式数据
const status = ref('PENDING')
const cancelling = ref(false)
const filterStatus = ref('all')
const activeTab = ref('detail')
const currentTestCaseIndex = ref(0)
const requestCollapse = ref(['headers'])
const responseCollapse = ref(['headers'])
const assertionsCollapse = ref<number[]>([])
const logLevel = ref('all')
const autoScroll = ref(true)
const isFullscreen = ref(false)
const extractedVariables = ref<Record<string, any>>({})
const searchKeyword = ref('')
const responseBodyFormat = ref('formatted')
const highlightSyntax = ref(true)
const previewExpanded = ref(false)
const showKeyboardHelp = ref(false)
const hasKeyboardInteracted = ref(false)

// WebSocket 状态
const wsConnected = ref(false)
const wsConnecting = ref(false)

// 日志数据
const logs = ref<Array<{
  timestamp: Date
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
}>>([])

// 组件引用
const casesListRef = ref<HTMLElement>()
const logsListRef = ref<HTMLElement>()
const responseTimeChartRef = ref<HTMLElement>()

// 图表实例
let responseTimeChart: echarts.ECharts | null = null

// WebSocket连接
let websocket: WebSocket | null = null
let refreshTimer: number | null = null

// 计算属性
const statusClass = computed(() => {
  const classes = {
    'PENDING': 'pending',
    'RUNNING': 'running',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled'
  }
  return classes[status.value] || 'pending'
})

const statusText = computed(() => {
  const texts = {
    'PENDING': '待执行',
    'RUNNING': '执行中',
    'COMPLETED': '已完成',
    'FAILED': '执行失败',
    'CANCELLED': '已取消'
  }
  return texts[status.value] || status.value
})

const wsStatusClass = computed(() => {
  if (wsConnecting.value) return 'connecting'
  if (wsConnected.value) return 'connected'
  return 'disconnected'
})

const wsStatusLabel = computed(() => {
  if (wsConnecting.value) return '连接中...'
  if (wsConnected.value) return '已连接'
  return '未连接'
})

const statistics = computed(() => {
  const results = props.execution?.test_results || []
  return {
    total: results.length,
    passed: results.filter(r => r.status === 'PASSED').length,
    failed: results.filter(r => r.status === 'FAILED').length,
    skipped: results.filter(r => r.status === 'SKIPPED').length
  }
})

const formattedDuration = computed(() => {
  const duration = props.execution?.duration || 0
  if (duration < 60) return `${duration}s`
  if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`
  return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`
})

const progressPercent = computed(() => {
  const total = statistics.value.total
  const completed = statistics.value.passed + statistics.value.failed + statistics.value.skipped
  return total > 0 ? Math.round((completed / total) * 100) : 0
})

const progressStatus = computed(() => {
  if (progressPercent.value === 100) {
    return statistics.value.failed > 0 ? 'exception' : 'success'
  }
  return undefined
})

const filteredTestResults = computed(() => {
  const results = props.execution?.test_results || []
  let filtered = results

  // 状态过滤
  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(r => r.status === filterStatus.value.toUpperCase())
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(r =>
      r.test_case_name?.toLowerCase().includes(keyword) ||
      r.test_case_url?.toLowerCase().includes(keyword)
    )
  }

  return filtered
})

const currentResult = computed(() => {
  const results = props.execution?.test_results || []
  return results[currentTestCaseIndex.value] || null
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

const formattedResponseBody = computed(() => {
  if (!currentResult.value?.response_body) return 'null'
  if (responseBodyFormat.value === 'raw') {
    return typeof currentResult.value.response_body === 'string'
      ? currentResult.value.response_body
      : JSON.stringify(currentResult.value.response_body)
  }
  return formatJson(currentResult.value.response_body)
})

const previewResponseBody = computed(() => {
  const body = formattedResponseBody.value
  if (previewExpanded.value) return body
  return body.length > 500 ? body.substring(0, 500) + '\n... (内容已截断)' : body
})

// 方法
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'PATCH': 'info',
    'DELETE': 'danger'
  }
  return types[method] || 'info'
}

const getStatusCodeColor = (code: number) => {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  return 'danger'
}

const getResponseTypeColor = (time: number) => {
  if (time < 200) return 'success'
  if (time < 500) return 'warning'
  return 'danger'
}

const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'PENDING': 'info',
    'RUNNING': 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'PASSED': '通过',
    'FAILED': '失败',
    'SKIPPED': '跳过',
    'PENDING': '待执行',
    'RUNNING': '执行中'
  }
  return texts[status] || status
}

const getTimelineType = (status: string) => {
  const types: Record<string, any> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'PENDING': 'info',
    'RUNNING': 'primary'
  }
  return types[status] || 'info'
}

const getTimelineIcon = (status: string) => {
  const icons: Record<string, any> = {
    'PASSED': CircleCheck,
    'FAILED': CircleClose,
    'SKIPPED': RemoveFilled,
    'PENDING': Clock,
    'RUNNING': Loading
  }
  return icons[status] || Clock
}

const selectTestCase = (index: number) => {
  currentTestCaseIndex.value = index
  activeTab.value = 'detail'
}

const goToTestCaseDetail = (result: any) => {
  emit('viewCase', result)
}

const formatJson = (obj: any) => {
  if (!obj) return 'null'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const formatValue = (value: any) => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatLogTime = (timestamp: Date) => {
  return new Date(timestamp).toLocaleTimeString()
}

const truncateValue = (value: any) => {
  const str = typeof value === 'object' ? JSON.stringify(value) : String(value)
  return str.length > 50 ? str.substring(0, 50) + '...' : str
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const copyResponseBody = () => {
  if (currentResult.value?.response_body) {
    copyToClipboard(formattedResponseBody.value)
  }
}

const clearLogs = () => {
  logs.value = []
}

const expandPreview = () => {
  previewExpanded.value = !previewExpanded.value
}

const expandAllAssertions = () => {
  const count = currentResult.value?.assertions?.length || 0
  assertionsCollapse.value = Array.from({ length: count }, (_, i) => i)
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const scrollToCurrent = () => {
  nextTick(() => {
    const items = document.querySelectorAll('.timeline-item')
    const currentItem = items[currentTestCaseIndex.value] as HTMLElement
    currentItem?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

const addLog = (level: 'info' | 'success' | 'warning' | 'error', message: string) => {
  logs.value.push({
    timestamp: new Date(),
    level,
    message
  })

  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      if (logsListRef.value) {
        logsListRef.value.scrollTop = logsListRef.value.scrollHeight
      }
    })
  }
}

const exportLogs = () => {
  const logText = logs.value.map(log =>
    `[${formatLogTime(log.timestamp)}] [${log.level.toUpperCase()}] ${log.message}`
  ).join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  saveAs(blob, `execution_logs_${Date.now()}.txt`)
  ElMessage.success('日志已导出')
}

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'exportLogs':
      exportLogs()
      break
    case 'exportReport':
      ElMessage.info('报告导出功能开发中')
      break
    case 'copySummary':
      copySummary()
      break
  }
}

const copySummary = () => {
  const summary = `
执行名称: ${props.execution?.name}
状态: ${statusText.value}
总用例: ${statistics.value.total}
通过: ${statistics.value.passed}
失败: ${statistics.value.failed}
跳过: ${statistics.value.skipped}
耗时: ${formattedDuration.value}
通过率: ${progressPercent.value}%
  `.trim()
  copyToClipboard(summary)
}

const retrySingleCase = async (result: any) => {
  ElMessage.info(`重试用例 "${result.test_case_name}" 功能开发中`)
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消正在执行的测试吗？',
      '确认取消',
      { type: 'warning' }
    )
    cancelling.value = true
    if (props.execution) {
      await executionApi.cancel(props.execution.id)
      addLog('warning', '测试执行已取消')
    }
    emit('cancel')
  } catch {
    // 取消
  } finally {
    cancelling.value = false
  }
}

const handleRetry = () => {
  emit('retry')
}

const handleListKeydown = (event: KeyboardEvent) => {
  hasKeyboardInteracted.value = true

  const results = filteredTestResults.value
  const currentIndex = results.findIndex((_, i) => {
    const allResults = props.execution?.test_results || []
    return allResults[currentTestCaseIndex.value]?.id === results[i]?.id
  })

  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      if (currentIndex > 0) {
        const newIndex = currentIndex - 1
        selectTestCase(newIndex)
      }
      break
    case 'ArrowDown':
      event.preventDefault()
      if (currentIndex < results.length - 1) {
        const newIndex = currentIndex + 1
        selectTestCase(newIndex)
      }
      break
    case 'Enter':
      event.preventDefault()
      if (currentResult.value) {
        goToTestCaseDetail(currentResult.value)
      }
      break
  }
}

const handleGlobalKeydown = (event: KeyboardEvent) => {
  // 如果在输入框中，不处理快捷键
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
    return
  }

  switch (event.key) {
    case '?':
      showKeyboardHelp.value = !showKeyboardHelp.value
      break
    case 'f':
    case 'F':
      toggleFullscreen()
      break
    case 'Escape':
      if (isFullscreen.value) {
        toggleFullscreen()
      }
      break
    case '1':
      filterStatus.value = 'all'
      break
    case '2':
      filterStatus.value = 'running'
      break
    case '3':
      filterStatus.value = 'passed'
      break
    case '4':
      filterStatus.value = 'failed'
      break
    case 'l':
    case 'L':
      activeTab.value = 'logs'
      break
    case 'd':
    case 'D':
      activeTab.value = 'detail'
      break
    case 'c':
    case 'C':
      activeTab.value = 'charts'
      break
  }
}

// WebSocket
const toggleWebSocket = () => {
  if (wsConnected.value) {
    closeWebSocket()
  } else if (props.execution) {
    connectWebSocket()
  }
}

const connectWebSocket = () => {
  if (!props.execution) return

  wsConnecting.value = true

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsHost = window.location.host
  const wsUrl = `${wsProtocol}//${wsHost}/ws/execution/${props.execution.id}/`

  websocket = new WebSocket(wsUrl)

  websocket.onopen = () => {
    wsConnected.value = true
    wsConnecting.value = false
    addLog('info', 'WebSocket连接已建立')
  }

  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    } catch (error) {
      console.error('WebSocket消息解析失败:', error)
    }
  }

  websocket.onerror = (error) => {
    console.error('WebSocket错误:', error)
    wsConnected.value = false
    wsConnecting.value = false
    addLog('error', 'WebSocket连接错误')
  }

  websocket.onclose = () => {
    wsConnected.value = false
    wsConnecting.value = false
    addLog('warning', 'WebSocket连接已关闭')
    // 5秒后尝试重连
    setTimeout(() => {
      if (status.value === 'RUNNING' && !wsConnected.value) {
        connectWebSocket()
      }
    }, 5000)
  }
}

const closeWebSocket = () => {
  if (websocket) {
    websocket.close()
    websocket = null
    wsConnected.value = false
  }
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'status':
      status.value = data.status
      addLog('info', `执行状态更新: ${data.status}`)
      if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'CANCELLED') {
        emit('finish')
        updateResponseTimeChart()
      }
      break

    case 'test_result':
      // 更新测试结果
      if (props.execution && data.result) {
        const index = props.execution.test_results.findIndex(r => r.id === data.result.id)
        if (index !== -1) {
          props.execution.test_results[index] = data.result
        }
        updateResponseTimeChart()
      }
      addLog(data.result.status === 'PASSED' ? 'success' : 'error',
        `测试用例 "${data.result.test_case_name}" ${data.result.status === 'PASSED' ? '通过' : '失败'}`)
      break

    case 'log':
      addLog(data.level || 'info', data.message)
      break

    case 'variable_extracted':
      if (data.variable && data.value !== undefined) {
        extractedVariables.value[data.variable] = data.value
        addLog('success', `提取变量: ${data.variable} = ${data.value}`)
      }
      break

    case 'assertion_result':
      if (data.assertion) {
        addLog(data.assertion.passed ? 'success' : 'error',
          `断言 ${data.assertion.passed ? '通过' : '失败'}: ${data.assertion.type}`)
      }
      break
  }
}

// 图表
const initResponseTimeChart = () => {
  if (!responseTimeChartRef.value) return

  responseTimeChart = echarts.init(responseTimeChartRef.value)
  updateResponseTimeChart()

  window.addEventListener('resize', () => {
    responseTimeChart?.resize()
  })
}

const updateResponseTimeChart = () => {
  if (!responseTimeChart || !props.execution?.test_results) return

  const results = props.execution.test_results.filter(r => r.response_time > 0)
  const names = results.map((r, i) => `${i + 1}. ${r.test_case_name?.substring(0, 20)}`)
  const times = results.map(r => r.response_time)
  const colors = results.map(r => {
    if (r.response_time < 200) return '#67c23a'
    if (r.response_time < 500) return '#e6a23c'
    return '#f56c6c'
  })

  const option: echarts.EChartsOption = {
    title: {
      text: '响应时间趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        interval: 0,
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '响应时间 (ms)',
      axisLine: {
        show: true
      },
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [{
      data: times,
      type: 'bar',
      itemStyle: {
        color: (params: any) => colors[params.dataIndex]
      },
      label: {
        show: true,
        position: 'top',
        fontSize: 10
      }
    }]
  }

  responseTimeChart.setOption(option)
}

const startPolling = () => {
  if (!props.execution) return

  refreshTimer = window.setInterval(async () => {
    try {
      const updated = await executionApi.getExecution(props.execution.id)
      if (updated) {
        status.value = updated.status
      }
    } catch (error) {
      console.error('轮询执行状态失败:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听执行变化
watch(() => props.execution, (newExecution) => {
  if (newExecution) {
    status.value = newExecution.status || 'PENDING'
    extractedVariables.value = {}
    logs.value = []
    addLog('info', `开始执行: ${newExecution.name}`)

    if (props.autoRefresh) {
      connectWebSocket()
    }

    // 切换到图表标签时初始化图表
    nextTick(() => {
      if (activeTab.value === 'charts') {
        initResponseTimeChart()
      }
    })
  } else {
    closeWebSocket()
    stopPolling()
  }
})

watch(activeTab, (newTab) => {
  if (newTab === 'charts') {
    nextTick(() => {
      initResponseTimeChart()
    })
  }
})

// 生命周期
onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)

  if (props.execution && props.autoRefresh) {
    connectWebSocket()
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  closeWebSocket()
  stopPolling()
  responseTimeChart?.dispose()
})
</script>

<style scoped>
.realtime-execution-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 600px;
}

/* 头部 */
.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* WebSocket 状态 */
.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.ws-status.disconnected {
  background-color: #fef0f0;
  color: #f56c6c;
}

.ws-status.connecting {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.ws-status.connected {
  background-color: #f0f9ff;
  color: #67c23a;
}

.ws-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.ws-status.connecting .ws-indicator {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-badge.pending {
  background-color: #f4f4f5;
  color: #909399;
}

.status-badge.running {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.status-badge.completed {
  background-color: #f0f9ff;
  color: #67c23a;
}

.status-badge.failed {
  background-color: #fef0f0;
  color: #f56c6c;
}

.status-badge.cancelled {
  background-color: #f4f4f5;
  color: #909399;
}

.execution-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 统计面板 */
.statistics-panel {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  line-height: 1;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.failed {
  color: #f56c6c;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.progress-item {
  flex: 1;
  min-width: 150px;
}

.progress-wrapper {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.progress-percent {
  font-weight: 600;
  color: #409eff;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 300px 1fr 250px;
  gap: 16px;
  flex: 1;
  min-height: 400px;
}

.main-content.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  padding: 20px;
  background-color: #f5f7fa;
}

/* 测试用例列表 */
.test-cases-panel,
.details-panel,
.variables-panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.variables-count {
  color: #909399;
  font-size: 12px;
}

.header-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.keyboard-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: #f4f4f5;
  font-size: 12px;
  color: #606266;
}

.keyboard-hints {
  margin-top: 20px;
  text-align: center;
  color: #909399;
}

.keyboard-hints p {
  margin: 4px 0;
}

.keyboard-hints kbd {
  background-color: #f4f4f5;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  font-family: monospace;
}

.test-cases-list {
  flex: 1;
  overflow-y: auto;
  outline: none;
}

.test-case-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  transition: all 0.2s;
}

.test-case-item:hover {
  background-color: #f5f7fa;
}

.test-case-item.current {
  background-color: #e6f7ff;
  border-left: 3px solid #409eff;
}

.test-case-item.running {
  background-color: #fdf6ec;
}

.test-case-item.passed {
  background-color: #f0f9ff;
}

.test-case-item.failed {
  background-color: #fef0f0;
}

.case-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: #606266;
  flex-shrink: 0;
}

.case-info {
  flex: 1;
  min-width: 0;
}

.case-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-method {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.case-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-status {
  font-size: 18px;
  flex-shrink: 0;
}

.case-time {
  font-size: 12px;
  color: #909399;
  min-width: 50px;
  text-align: right;
  flex-shrink: 0;
}

.case-actions {
  flex-shrink: 0;
}

/* 详情面板 */
.details-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

.detail-content {
  padding: 16px;
}

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 12px;
}

.section-header.error {
  color: #f56c6c;
}

.json-content {
  background-color: #f5f7fa;
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.json-content.highlighted {
  color: #303133;
}

.json-content:not(.expanded) {
  max-height: 200px;
}

.response-body {
  max-height: 400px;
}

.response-body-wrapper {
  display: flex;
  flex-direction: column;
}

.response-body-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

/* 断言列表 */
.assertions-collapse {
  margin-top: 8px;
}

.assertion-collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.assertion-collapse-title.passed {
  color: #67c23a;
}

.assertion-collapse-title.failed {
  color: #f56c6c;
}

.assertion-type-text {
  flex: 1;
}

.assertion-detail-content code {
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.error-message {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
}

.error-text {
  color: #f56c6c;
}

/* 提取的变量 */
.extracted-variables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.extracted-variable-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.extracted-variable-item .variable-name {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #409eff;
  font-weight: 500;
}

.extracted-variable-item .variable-value {
  flex: 1;
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 日志 */
.logs-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap;
}

.logs-list {
  flex: 1;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f7fa;
  position: relative;
}

.log-item:hover .log-copy {
  opacity: 1;
}

.log-time {
  color: #909399;
  min-width: 80px;
}

.log-level {
  min-width: 60px;
  font-weight: 500;
}

.log-item.info .log-level {
  color: #409eff;
}

.log-item.success .log-level {
  color: #67c23a;
}

.log-item.warning .log-level {
  color: #e6a23c;
}

.log-item.error .log-level {
  color: #f56c6c;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

.log-copy {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

/* 图表 */
.charts-content {
  padding: 16px;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 400px;
}

/* 变量面板 */
.variables-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.variable-item {
  margin-bottom: 16px;
}

.variable-name {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
  margin-bottom: 6px;
}

.variable-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.variable-value code {
  flex: 1;
  background-color: #f4f4f5;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #606266;
  word-break: break-all;
}

/* 时间线 */
.timeline-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.execution-timeline {
  max-height: 300px;
  overflow-y: auto;
}

.timeline-item {
  cursor: pointer;
}

.timeline-content {
  cursor: pointer;
}

.timeline-case-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.timeline-case-url {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.timeline-result {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-time {
  font-size: 12px;
  color: #909399;
}

/* 快捷键帮助 */
.keyboard-shortcuts {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 16px;
  align-items: center;
}

.shortcut-item {
  display: contents;
}

.shortcut-item kbd {
  background-color: #f4f4f5;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  font-family: monospace;
  display: inline-block;
}

.shortcut-item span {
  font-size: 14px;
  color: #606266;
}

/* 动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
}
</style>
