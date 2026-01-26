<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="900px"
    @close="handleClose"
  >
    <div v-loading="loading" class="detail-dialog-content">
      <!-- 筛选条件展示 -->
      <div v-if="appliedFilters && Object.keys(appliedFilters).length > 0" class="filter-info mb-20">
        <div class="filter-info-title">当前筛选条件：</div>
        <el-tag
          v-for="(value, key) in filterDisplay"
          :key="key"
          class="mr-10 mb-10"
          closable
          @close="handleRemoveFilter(key)"
        >
          {{ key }}: {{ value }}
        </el-tag>
      </div>

      <!-- 统计摘要 -->
      <div class="summary-section mb-20">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总用例</div>
              <div class="summary-value total">{{ summary.total }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">通过</div>
              <div class="summary-value success">{{ summary.passed }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">失败</div>
              <div class="summary-value danger">{{ summary.failed }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">通过率</div>
              <div class="summary-value">{{ summary.passRate }}%</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 测试结果列表 -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>测试结果详情</span>
            <el-button text link @click="exportData">导出数据</el-button>
          </div>
        </template>

        <el-table :data="tableData" stripe max-height="400">
          <el-table-column prop="test_case_name" label="用例名称" min-width="200" />
          <el-table-column prop="collection_name" label="集合" width="150" />
          <el-table-column prop="project_name" label="项目" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_time" label="响应时间" width="100" align="right">
            <template #default="{ row }">
              {{ row.response_time }}ms
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="执行时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button text link type="primary" @click="viewDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            small
            @size-change="loadData"
            @current-change="loadData"
          />
        </div>
      </el-card>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="exportData">导出全部数据</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { dashboardApi } from '../../../api/dashboard'
import type { DashboardFilterParams } from '../../../api/dashboard'

interface Props {
  modelValue: boolean
  dataType: 'all' | 'passed' | 'failed' | 'skipped' | 'error'
  filters?: DashboardFilterParams
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'remove-filter': [key: string]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const tableData = ref<any[]>([])
const appliedFilters = ref<DashboardFilterParams>({})

// 分页
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

// 统计摘要
const summary = ref({
  total: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  error: 0,
  passRate: 0
})

// 对话框标题
const dialogTitle = computed(() => {
  const titleMap = {
    all: '全部用例数据',
    passed: '通过用例数据',
    failed: '失败用例数据',
    skipped: '跳过用例数据',
    error: '错误用例数据'
  }
  return titleMap[props.dataType]
})

// 筛选条件显示
const filterDisplay = computed(() => {
  const display: Record<string, string> = {}
  if (appliedFilters.value.project_id) display['项目'] = `ID: ${appliedFilters.value.project_id}`
  if (appliedFilters.value.collection_id) display['集合'] = `ID: ${appliedFilters.value.collection_id}`
  if (appliedFilters.value.owner_id) display['负责人'] = `ID: ${appliedFilters.value.owner_id}`
  if (appliedFilters.value.module) display['模块'] = appliedFilters.value.module
  if (appliedFilters.value.start_date) display['开始日期'] = appliedFilters.value.start_date
  if (appliedFilters.value.end_date) display['结束日期'] = appliedFilters.value.end_date
  return display
})

// 加载数据
const loadData = async () => {
  if (!visible.value) return

  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      sort_by: '-start_time',
      ...appliedFilters.value
    }

    // 添加状态筛选
    const statusMap = {
      all: undefined,
      passed: 'PASSED',
      failed: 'FAILED',
      skipped: 'SKIPPED',
      error: 'ERROR'
    }
    const status = statusMap[props.dataType]
    if (status) params.status = status

    const response = await dashboardApi.getTestResults(params)
    tableData.value = response.results
    pagination.value.total = response.count

    // 计算统计摘要
    calculateSummary()
  } catch (error) {
    console.error('Failed to load detail data:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 计算统计摘要
const calculateSummary = () => {
  const statusCounts = {
    total: pagination.value.total,
    passed: 0,
    failed: 0,
    skipped: 0,
    error: 0
  }

  tableData.value.forEach(item => {
    if (item.status === 'PASSED') statusCounts.passed++
    else if (item.status === 'FAILED') statusCounts.failed++
    else if (item.status === 'SKIPPED') statusCounts.skipped++
    else if (item.status === 'ERROR') statusCounts.error++
  })

  summary.value = {
    ...statusCounts,
    passRate: statusCounts.total > 0
      ? Math.round((statusCounts.passed / statusCounts.total) * 100)
      : 0
  }
}

// 移除筛选条件
const handleRemoveFilter = (key: string) => {
  emit('remove-filter', key)
}

// 查看详情
const viewDetail = (row: any) => {
  // TODO: 跳转到测试结果详情页
  ElMessage.info('测试结果详情页开发中...')
}

// 导出数据
const exportData = () => {
  // 导出当前表格数据为 CSV
  const headers = ['用例名称', '集合', '项目', '状态', '响应时间', '执行时间']
  const csvContent = [
    headers.join(','),
    ...tableData.value.map(row => [
      row.test_case_name || '',
      row.collection_name || '',
      row.project_name || '',
      getStatusText(row.status),
      row.response_time || 0,
      formatTime(row.start_time)
    ].join(','))
  ].join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${dialogTitle.value}_${new Date().getTime()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success('数据导出成功')
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'ERROR': 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'PASSED': '通过',
    'FAILED': '失败',
    'SKIPPED': '跳过',
    'ERROR': '错误'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (time: string | null) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    appliedFilters.value = { ...props.filters } || {}
    pagination.value.page = 1
    loadData()
  }
})

// 监听筛选条件变化
watch(() => props.filters, (newVal) => {
  if (newVal && visible.value) {
    appliedFilters.value = { ...newVal }
    pagination.value.page = 1
    loadData()
  }
}, { deep: true })
</script>

<style scoped>
.detail-dialog-content {
  min-height: 400px;
}

.filter-info {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filter-info-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.summary-section {
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
}

.summary-value.total {
  color: #ffffff;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.danger {
  color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.mb-20 {
  margin-bottom: 20px;
}

.mr-10 {
  margin-right: 10px;
}
</style>
