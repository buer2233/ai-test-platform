<template>
  <div class="test-case-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="header-title">
        <h3>{{ testCaseStore.currentTestCase?.name }}</h3>
        <el-tag size="small">{{ testCaseStore.currentTestCase?.project_name }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button @click="handleEdit">编辑</el-button>
        <el-button type="success" @click="handleRun" :loading="running">
          <el-icon><VideoPlay /></el-icon>
          运行测试
        </el-button>
      </div>
    </div>

    <!-- 用例详情卡片 -->
    <el-card class="detail-card" shadow="never">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用例名称">
          {{ testCaseStore.currentTestCase?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="所属项目">
          {{ testCaseStore.currentTestCase?.project_name }}
        </el-descriptions-item>
        <el-descriptions-item label="浏览器模式">
          <el-tag :type="testCaseStore.currentTestCase?.browser_mode === 'headless' ? 'info' : 'warning'">
            {{ testCaseStore.currentTestCase?.browser_mode === 'headless' ? '无头模式' : '有头模式' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="超时时间">
          {{ testCaseStore.currentTestCase?.timeout }}秒
        </el-descriptions-item>
        <el-descriptions-item label="重试次数">
          {{ testCaseStore.currentTestCase?.retry_count }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="testCaseStore.currentTestCase?.is_active ? 'success' : 'info'">
            {{ testCaseStore.currentTestCase?.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <el-tag
            v-for="tag in testCaseStore.currentTestCase?.tags"
            :key="tag"
            style="margin-right: 8px"
          >
            {{ tag }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="测试任务" :span="2">
          <div class="test-task-content">
            {{ testCaseStore.currentTestCase?.test_task }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ testCaseStore.currentTestCase?.description || '无' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(testCaseStore.currentTestCase?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDate(testCaseStore.currentTestCase?.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 执行历史 -->
    <el-card class="history-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>执行历史</span>
          <el-button link type="primary" @click="goToExecutions">
            查看全部
          </el-button>
        </div>
      </template>
      <el-table
        v-loading="loadingHistory"
        :data="executions"
        stripe
        @row-click="handleExecutionClick"
      >
        <el-table-column prop="id" label="执行ID" width="100" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="耗时(秒)" width="120" align="center">
          <template #default="{ row }">
            {{ row.duration_seconds || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleExecutionClick(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
/**
 * 测试用例详情页
 *
 * 展示单个 UI 测试用例的完整信息：
 * - 基本信息（名称、项目、浏览器模式、超时、重试次数、标签等）
 * - 测试任务描述（自然语言）
 * - 最近 5 条执行历史记录
 * - 支持编辑、运行测试操作
 */

import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay } from '@element-plus/icons-vue'

import { useUiTestCaseStore } from '../../stores/testCase'
import { uiTestCaseApi } from '../../api/testCase'
import type { ExecutionStatus, UiTestExecution } from '../../types/execution'

const route = useRoute()
const router = useRouter()
const testCaseStore = useUiTestCaseStore()

/** 当前用例 ID（从路由参数获取） */
const testCaseId = Number(route.params.id)
/** 是否正在运行测试 */
const running = ref(false)
/** 执行历史加载状态 */
const loadingHistory = ref(false)
/** 最近的执行记录列表 */
const executions = ref<UiTestExecution[]>([])

/* ---------- 状态映射 ---------- */

/** 执行状态 -> El-Tag 类型映射 */
const STATUS_TYPE_MAP: Record<ExecutionStatus, string> = {
  pending: 'info',
  running: 'warning',
  passed: 'success',
  failed: 'danger',
  error: 'danger',
  cancelled: 'info'
}

/** 执行状态 -> 中文文本映射 */
const STATUS_TEXT_MAP: Record<ExecutionStatus, string> = {
  pending: '待执行',
  running: '执行中',
  passed: '通过',
  failed: '失败',
  error: '错误',
  cancelled: '已取消'
}

const getStatusType = (status: ExecutionStatus) => {
  return STATUS_TYPE_MAP[status] || 'info'
}

const getStatusText = (status: ExecutionStatus) => {
  return STATUS_TEXT_MAP[status] || status
}

/**
 * 格式化日期为中文本地化字符串
 * 支持可选参数（用于 created_at 和 updated_at 字段）
 */
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/* ---------- 页面操作 ---------- */

/** 返回测试用例列表 */
const goBack = () => {
  router.push('/ui-automation/test-cases')
}

/** 跳转到编辑页面 */
const handleEdit = () => {
  router.push(`/ui-automation/test-cases/${testCaseId}/edit`)
}

/**
 * 运行测试
 * 检查启用状态后调用 run 端点，自动创建执行记录并启动测试，
 * 成功后跳转到执行监控页面
 */
const handleRun = async () => {
  if (!testCaseStore.currentTestCase) return

  if (!testCaseStore.currentTestCase.is_active) {
    ElMessage.warning('该测试用例未启用，请先启用后再执行')
    return
  }

  running.value = true
  try {
    const result = await uiTestCaseApi.run(testCaseId, {
      browser_mode: testCaseStore.currentTestCase.browser_mode
    })
    ElMessage.success(result.message || '开始执行测试')
    router.push(`/ui-automation/executions/${result.execution.id}`)
  } catch (error: any) {
    console.error('Run test failed:', error)
    const errorMsg = error?.response?.data?.error || error?.message || '执行失败'
    if (errorMsg.includes('OPENAI_API_KEY')) {
      ElMessage.error('执行失败：OPENAI_API_KEY 环境变量未配置，请联系管理员配置')
    } else {
      ElMessage.error(`执行失败：${errorMsg}`)
    }
  } finally {
    running.value = false
  }
}

/** 跳转到执行记录列表（查看全部历史） */
const goToExecutions = () => {
  router.push('/ui-automation/executions')
}

/** 点击执行记录行：跳转到执行监控页面 */
const handleExecutionClick = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

/* ---------- 数据加载 ---------- */

/** 加载该用例最近 5 条执行历史记录 */
const loadExecutionHistory = async () => {
  loadingHistory.value = true
  try {
    const result = testCaseStore.currentTestCase?.id
      ? await (await fetch(`/api/v1/ui-automation/test-cases/${testCaseId}/executions/`)).json()
      : { results: [] }
    executions.value = result.results?.slice(0, 5) || []
  } finally {
    loadingHistory.value = false
  }
}

/* ---------- 页面初始化 ---------- */
onMounted(async () => {
  await testCaseStore.fetchTestCase(testCaseId)
  loadExecutionHistory()
})
</script>

<style scoped>
.test-case-detail {
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

.test-task-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
