<!--
  ReportDetail.vue - 测试报告详情页面

  展示单次测试执行的完整报告，包含以下功能：
  - 执行摘要：项目、环境、执行人、创建时间、执行状态
  - 统计卡片：总用例数、通过数、失败数、跳过数、通过率
  - 时间信息：开始时间、结束时间、执行耗时
  - 测试结果列表：用例名称(含请求方法标签)、URL、状态、状态码、响应时间、数据级别
  - 结果筛选：按状态过滤、按用例名称搜索
  - 数据级别标识：完整数据(失败/错误用例) vs 摘要数据(通过/跳过用例)
  - 导出功能：JSON、Excel、CSV 三种格式
  - 可取消正在运行的执行任务
  - 点击行或查看按钮可打开 TestResultDetail 详情弹窗
-->
<template>
  <div class="report-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h1 class="page-title">{{ execution?.name || '加载中...' }}</h1>
      </div>
      <div class="header-right">
        <el-button
          v-if="execution?.status === 'RUNNING'"
          type="danger"
          @click="handleCancel"
        >
          <el-icon><VideoPause /></el-icon>
          取消执行
        </el-button>
        <el-dropdown
          split-button
          type="success"
          @click="handleExport('json')"
          trigger="click"
        >
          <el-icon><Download /></el-icon>
          导出报告
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleExport('json')">
                <el-icon><Document /></el-icon>
                导出为 JSON
              </el-dropdown-item>
              <el-dropdown-item @click="handleExport('excel')">
                <el-icon><DocumentCopy /></el-icon>
                导出为 Excel
              </el-dropdown-item>
              <el-dropdown-item @click="handleExport('csv')">
                <el-icon><Tickets /></el-icon>
                导出为 CSV
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 执行摘要 -->
    <el-card v-if="execution" class="summary-card">
      <template #header>
        <div class="card-header">
          <span>执行摘要</span>
          <el-tag :type="getStatusTagType(execution.status)">
            {{ getStatusText(execution.status) }}
          </el-tag>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">所属项目</div>
            <div class="stat-value">{{ execution.project_name }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">执行环境</div>
            <div class="stat-value">{{ execution.environment_name || '-' }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">执行人</div>
            <div class="stat-value">{{ execution.created_by_name }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">创建时间</div>
            <div class="stat-value small">{{ formatDateTime(execution.created_time) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4">
        <el-card class="stat-card total">
          <div class="stat-number">{{ execution?.total_count || 0 }}</div>
          <div class="stat-label">总用例数</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="stat-card passed">
          <div class="stat-number">{{ execution?.passed_count || 0 }}</div>
          <div class="stat-label">通过</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="stat-card failed">
          <div class="stat-number">{{ execution?.failed_count || 0 }}</div>
          <div class="stat-label">失败</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="stat-card skipped">
          <div class="stat-number">{{ execution?.skipped_count || 0 }}</div>
          <div class="stat-label">跳过</div>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card class="stat-card rate">
          <div class="stat-number">{{ getPassRate() }}</div>
          <div class="stat-label">通过率</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 时间和耗时 -->
    <el-row :gutter="20" class="time-row">
      <el-col :span="8">
        <el-card>
          <div class="time-item">
            <div class="time-label">开始时间</div>
            <div class="time-value">{{ formatDateTime(execution?.start_time) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="time-item">
            <div class="time-label">结束时间</div>
            <div class="time-value">{{ formatDateTime(execution?.end_time) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="time-item">
            <div class="time-label">执行耗时</div>
            <div class="time-value">{{ formatDuration(execution?.duration) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 测试结果列表 -->
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span>测试结果</span>
          <div class="header-actions">
            <el-select
              v-model="resultFilter.status"
              placeholder="筛选状态"
              clearable
              @change="loadTestResults"
              style="width: 120px; margin-right: 10px"
            >
              <el-option label="全部" value="" />
              <el-option label="通过" value="PASSED" />
              <el-option label="失败" value="FAILED" />
              <el-option label="跳过" value="SKIPPED" />
              <el-option label="错误" value="ERROR" />
            </el-select>
            <el-input
              v-model="resultFilter.keyword"
              placeholder="搜索用例名称"
              prefix-icon="Search"
              clearable
              @input="loadTestResults"
              style="width: 250px"
            />
          </div>
        </div>
      </template>

      <el-table
        v-loading="resultsLoading"
        :data="testResults"
        @row-click="handleRowClick"
        row-key="id"
        class="results-table"
      >
        <el-table-column prop="test_case_name" label="用例名称" min-width="200">
          <template #default="{ row }">
            <div class="case-name">
              <el-tag :type="getMethodTagType(row.test_case_method)" size="small">
                {{ row.test_case_method }}
              </el-tag>
              <span class="name-text">{{ row.test_case_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="test_case_url" label="请求URL" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_status" label="状态码" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.response_status"
              :type="row.response_status >= 200 && row.response_status < 300 ? 'success' : 'danger'"
            >
              {{ row.response_status }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间" width="120" align="center">
          <template #default="{ row }">
            {{ row.response_time }}ms
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="数据级别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.response_full ? 'warning' : 'info'" size="small">
              {{ row.response_full ? '完整' : '摘要' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="handleViewResult(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="resultPagination.page"
          v-model:page-size="resultPagination.size"
          :total="resultPagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTestResults"
          @current-change="loadTestResults"
        />
      </div>
    </el-card>

    <!-- 测试结果详情对话框 -->
    <TestResultDetail
      v-model:visible="resultDetailVisible"
      :result="selectedResult"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  VideoPause,
  Download,
  Document,
  DocumentCopy,
  Tickets,
  Search
} from '@element-plus/icons-vue'
import { executionApi, testResultApi } from '../../api'
import type { ApiTestExecution } from '../../types/execution'
import type { TestResult } from '../../types/report'
import TestResultDetail from '../../components/TestResultDetail.vue'

const router = useRouter()
const route = useRoute()

// 执行详情
const execution = ref<ApiTestExecution | null>(null)
const loading = ref(false)

// 测试结果
const testResults = ref<TestResult[]>([])
const resultsLoading = ref(false)
const selectedResult = ref<TestResult | null>(null)
const resultDetailVisible = ref(false)

// 结果过滤
const resultFilter = reactive({
  status: '',
  keyword: ''
})

// 结果分页
const resultPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取执行ID
const executionId = computed(() => Number(route.params.id))

// 格式化日期时间
const formatDateTime = (dateTime: string | null) => {
  if (!dateTime) return '-'
  try {
    const date = new Date(dateTime)
    if (isNaN(date.getTime())) return '-'

    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    return '-'
  }
}

// 格式化耗时
const formatDuration = (duration: number | null) => {
  if (!duration) return '-'
  if (duration < 60) return `${duration}秒`
  const minutes = Math.floor(duration / 60)
  const seconds = duration % 60
  return `${minutes}分${seconds}秒`
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    PENDING: 'info',
    RUNNING: 'primary',
    COMPLETED: 'success',
    FAILED: 'danger',
    CANCELLED: 'warning',
    PASSED: 'success',
    SKIPPED: 'warning',
    ERROR: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    PENDING: '待执行',
    RUNNING: '运行中',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消',
    PASSED: '通过',
    SKIPPED: '跳过',
    ERROR: '错误'
  }
  return texts[status] || status
}

// 获取方法标签类型
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    PATCH: 'danger',
    DELETE: 'info'
  }
  return types[method] || 'info'
}

// 计算通过率
const getPassRate = () => {
  if (!execution.value || !execution.value.total_count || execution.value.total_count === 0) {
    return '0%'
  }
  const passRate = (execution.value.passed_count / execution.value.total_count) * 100
  return `${passRate.toFixed(1)}%`
}

// 加载执行详情
const loadExecutionDetail = async () => {
  loading.value = true
  try {
    execution.value = await executionApi.getExecution(executionId.value)
  } catch (error) {
    ElMessage.error('加载执行详情失败')
  } finally {
    loading.value = false
  }
}

// 加载测试结果
const loadTestResults = async () => {
  resultsLoading.value = true
  try {
    const params: any = {
      page: resultPagination.page,
      page_size: resultPagination.size,
      execution: executionId.value
    }
    if (resultFilter.status) {
      params.status = resultFilter.status
    }
    if (resultFilter.keyword) {
      params.search = resultFilter.keyword
    }

    const response = await testResultApi.getTestResults(params)
    testResults.value = response.results
    resultPagination.total = response.count
  } catch (error) {
    ElMessage.error('加载测试结果失败')
  } finally {
    resultsLoading.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/reports')
}

// 取消执行
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消当前执行吗？',
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await executionApi.cancel(executionId.value)
    ElMessage.success('已取消执行')
    loadExecutionDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消执行失败')
    }
  }
}

// 导出报告
const handleExport = async (format: 'json' | 'excel' | 'csv') => {
  try {
    const response = await executionApi.getExecution(executionId.value)
    const data = response

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${executionId.value}_${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } else if (format === 'excel') {
      const { saveAs } = await import('file-saver')
      const XLSX = await import('xlsx')

      const workbook = XLSX.utils.book_new()

      // 摘要工作表
      const summaryData = [
        ['执行名称', data.name],
        ['所属项目', data.project_name],
        ['执行环境', data.environment_name || '-'],
        ['执行状态', getStatusText(data.status)],
        ['总用例数', data.total_count],
        ['通过数', data.passed_count],
        ['失败数', data.failed_count],
        ['跳过数', data.skipped_count],
        ['通过率', getPassRate()],
        ['执行耗时', formatDuration(data.duration)],
        ['开始时间', formatDateTime(data.start_time)],
        ['结束时间', formatDateTime(data.end_time)],
        ['执行人', data.created_by_name],
        ['创建时间', formatDateTime(data.created_time)]
      ]

      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
      XLSX.utils.book_append_sheet(workbook, summarySheet, '执行摘要')

      // 测试结果工作表
      const resultsData = [
        ['用例名称', '请求方法', '请求URL', '状态', '状态码', '响应时间', '开始时间']
      ]

      testResults.value.forEach(result => {
        resultsData.push([
          result.test_case_name,
          result.test_case_method,
          result.test_case_url,
          getStatusText(result.status),
          result.response_status || '-',
          result.response_time,
          formatDateTime(result.start_time)
        ])
      })

      const resultsSheet = XLSX.utils.aoa_to_sheet(resultsData)
      XLSX.utils.book_append_sheet(workbook, resultsSheet, '测试结果')

      XLSX.writeFile(workbook, `report_${executionId.value}_${Date.now()}.xlsx`)
    } else if (format === 'csv') {
      const { saveAs } = await import('file-saver')

      const headers = ['用例名称,请求方法,请求URL,状态,状态码,响应时间,开始时间']
      const rows = testResults.value.map(result =>
        [
          result.test_case_name,
          result.test_case_method,
          result.test_case_url,
          getStatusText(result.status),
          result.response_status || '-',
          result.response_time,
          formatDateTime(result.start_time)
        ].join(',')
      )

      const csvContent = [...headers, ...rows].join('\n')
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
      saveAs(blob, `report_${executionId.value}_${Date.now()}.csv`)
    }
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(`导出失败: ${error.message}`)
  }
}

// 行点击处理
const handleRowClick = (row: TestResult) => {
  handleViewResult(row)
}

// 查看结果详情
const handleViewResult = (result: TestResult) => {
  selectedResult.value = result
  resultDetailVisible.value = true
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadExecutionDetail()
  await loadTestResults()
})
</script>

<style scoped>
.report-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.stat-value.small {
  font-size: 14px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 15px 0;
}

.stat-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.passed {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.stat-card.failed {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
}

.stat-card.skipped {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.stat-card.rate {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-card .stat-label {
  color: inherit;
  font-size: 14px;
}

.time-row {
  margin-bottom: 20px;
}

.time-item {
  text-align: center;
  padding: 10px 0;
}

.time-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.time-value {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.results-card {
  margin-bottom: 20px;
}

.results-table {
  cursor: pointer;
}

.results-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.case-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
