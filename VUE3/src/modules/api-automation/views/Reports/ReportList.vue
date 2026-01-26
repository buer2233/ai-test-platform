<template>
  <div class="report-list-container">
    <div class="page-header">
      <h1 class="page-title">测试报告</h1>
      <p class="page-description">查看和管理测试执行报告</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="table-toolbar-left">
        <el-button type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-dropdown
          split-button
          type="success"
          :disabled="!selectedReports.length"
          @click="handleBatchExport('json')"
          trigger="click"
        >
          <el-icon><Download /></el-icon>
          批量导出
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleBatchExport('json')">
                <el-icon><Document /></el-icon>
                导出为 JSON
              </el-dropdown-item>
              <el-dropdown-item @click="handleBatchExport('excel')">
                <el-icon><DocumentCopy /></el-icon>
                导出为 Excel
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="danger" :disabled="!selectedReports.length" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="table-toolbar-right">
        <el-select
          v-model="searchForm.project"
          placeholder="选择项目"
          clearable
          @change="handleProjectChange"
          style="width: 150px; margin-right: 10px"
        >
          <el-option
            v-for="project in projectOptions"
            :key="project.value"
            :label="project.label"
            :value="project.value"
          />
        </el-select>
        <el-select
          v-model="searchForm.environment"
          placeholder="选择环境"
          clearable
          @change="handleSearch"
          style="width: 150px; margin-right: 10px"
        >
          <el-option
            v-for="env in environmentOptions"
            :key="env.value"
            :label="env.label"
            :value="env.value"
          />
        </el-select>
        <el-select
          v-model="searchForm.status"
          placeholder="执行状态"
          clearable
          @change="handleSearch"
          style="width: 130px; margin-right: 10px"
        >
          <el-option label="待执行" value="PENDING" />
          <el-option label="运行中" value="RUNNING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="失败" value="FAILED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索执行名称"
          prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px"
        />
      </div>
    </div>

    <!-- 报告表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="executionList"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="执行名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="所属项目" width="150" />
        <el-table-column prop="environment_name" label="执行环境" width="150">
          <template #default="{ row }">
            {{ row.environment_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="用例数" width="80" align="center">
          <template #default="{ row }">
            {{ row.total_count }}
          </template>
        </el-table-column>
        <el-table-column label="通过率" width="100" align="center">
          <template #default="{ row }">
            <span :class="getPassRateClass(row)">
              {{ getPassRate(row) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="执行时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="执行人" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看详情</el-button>
            <el-dropdown @command="(cmd) => handleReportAction(cmd, row)">
              <el-button type="primary" link>
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="export_json" :disabled="row.status === 'RUNNING'">
                    <el-icon><Document /></el-icon>
                    导出 JSON
                  </el-dropdown-item>
                  <el-dropdown-item command="export_excel" :disabled="row.status === 'RUNNING'">
                    <el-icon><DocumentCopy /></el-icon>
                    导出 Excel
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" :disabled="row.status === 'RUNNING'">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Download,
  Delete,
  Search,
  Document,
  DocumentCopy,
  ArrowDown
} from '@element-plus/icons-vue'
import { useProjectStore, useEnvironmentStore } from '../../stores'
import { executionApi } from '../../api/execution'
import type { ApiTestExecution } from '../../types/execution'

const router = useRouter()
const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()

// 加载状态
const loading = ref(false)

// 执行列表
const executionList = ref<ApiTestExecution[]>([])
const selectedReports = ref<ApiTestExecution[]>([])

// 项目和环境选项
const projectOptions = computed(() => projectStore.projectOptions)
const environmentOptions = ref<Array<{ label: string; value: number }>>([])

// 搜索表单
const searchForm = reactive({
  keyword: '',
  project: null as number | null,
  environment: null as number | null,
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    PENDING: 'info',
    RUNNING: 'primary',
    COMPLETED: 'success',
    FAILED: 'danger',
    CANCELLED: 'warning'
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
    CANCELLED: '已取消'
  }
  return texts[status] || status
}

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

// 计算通过率
const getPassRate = (execution: ApiTestExecution) => {
  if (!execution.total_count || execution.total_count === 0) return '0%'
  const passRate = (execution.passed_count / execution.total_count) * 100
  return `${passRate.toFixed(1)}%`
}

// 获取通过率样式类
const getPassRateClass = (execution: ApiTestExecution) => {
  if (!execution.total_count || execution.total_count === 0) return ''
  const passRate = (execution.passed_count / execution.total_count) * 100
  if (passRate >= 90) return 'pass-rate-excellent'
  if (passRate >= 70) return 'pass-rate-good'
  if (passRate >= 50) return 'pass-rate-warning'
  return 'pass-rate-poor'
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.size,
      search: searchForm.keyword
    }
    if (searchForm.project) {
      params.project = searchForm.project
    }
    if (searchForm.environment) {
      params.environment = searchForm.environment
    }
    if (searchForm.status) {
      params.status = searchForm.status
    }
    const response = await executionApi.getExecutions(params)
    executionList.value = response.results
    pagination.total = response.count
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载项目列表
const loadProjects = async () => {
  try {
    await projectStore.fetchProjects({ page_size: 1000 })
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

// 加载环境列表
const loadEnvironments = async (projectId?: number) => {
  try {
    const params: any = { page_size: 1000 }
    if (projectId) {
      params.project = projectId
    }
    await environmentStore.fetchEnvironments(params)
    environmentOptions.value = environmentStore.environments.map(e => ({
      label: e.name,
      value: e.id
    }))
  } catch (error) {
    console.error('Failed to load environments:', error)
  }
}

// 项目改变时更新环境选项
const handleProjectChange = () => {
  searchForm.environment = null
  loadEnvironments(searchForm.project || undefined)
  loadData()
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 刷新处理
const handleRefresh = () => {
  loadData()
}

// 分页处理
const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

// 选择处理
const handleSelectionChange = (selection: ApiTestExecution[]) => {
  selectedReports.value = selection
}

// 查看详情
const handleView = (execution: ApiTestExecution) => {
  router.push(`/reports/${execution.id}`)
}

// 报告操作处理
const handleReportAction = async (command: string, execution: ApiTestExecution) => {
  switch (command) {
    case 'export_json':
      await handleExport(execution, 'json')
      break
    case 'export_excel':
      await handleExport(execution, 'excel')
      break
    case 'delete':
      await handleDelete(execution)
      break
  }
}

// 导出单个报告
const handleExport = async (execution: ApiTestExecution, format: 'json' | 'excel') => {
  try {
    const response = await executionApi.getExecution(execution.id)
    const data = response

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${execution.id}_${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } else if (format === 'excel') {
      const { saveAs } = await import('file-saver')
      const XLSX = await import('xlsx')

      const workbook = XLSX.utils.book_new()
      const summaryData = [
        ['执行名称', execution.name],
        ['所属项目', execution.project_name],
        ['执行环境', execution.environment_name || '-'],
        ['执行状态', getStatusText(execution.status)],
        ['总用例数', execution.total_count],
        ['通过数', execution.passed_count],
        ['失败数', execution.failed_count],
        ['跳过数', execution.skipped_count],
        ['通过率', getPassRate(execution)],
        ['执行耗时', formatDuration(execution.duration)],
        ['开始时间', formatDateTime(execution.start_time)],
        ['结束时间', formatDateTime(execution.end_time)],
        ['执行人', execution.created_by_name],
        ['创建时间', formatDateTime(execution.created_time)]
      ]

      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
      XLSX.utils.book_append_sheet(workbook, summarySheet, '执行摘要')

      XLSX.writeFile(workbook, `report_${execution.id}_${Date.now()}.xlsx`)
    }
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(`导出失败: ${error.message}`)
  }
}

// 删除单个报告
const handleDelete = async (execution: ApiTestExecution) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除执行记录"${execution.name}"吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await executionApi.deleteExecution(execution.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量导出
const handleBatchExport = async (format: 'json' | 'excel') => {
  if (!selectedReports.value.length) return

  try {
    for (const execution of selectedReports.value) {
      await handleExport(execution, format)
    }
    ElMessage.success(`成功导出 ${selectedReports.value.length} 个报告`)
  } catch (error: any) {
    ElMessage.error(`批量导出失败: ${error.message}`)
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!selectedReports.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedReports.value.length} 条执行记录吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const promises = selectedReports.value.map(e => executionApi.deleteExecution(e.id))
    await Promise.all(promises)
    ElMessage.success('批量删除成功')
    selectedReports.value = []
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadProjects()
  await loadEnvironments()
  loadData()
})
</script>

<style scoped>
.report-list-container {
  padding: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 通过率样式 */
.pass-rate-excellent {
  color: #67c23a;
  font-weight: bold;
}

.pass-rate-good {
  color: #409eff;
}

.pass-rate-warning {
  color: #e6a23c;
}

.pass-rate-poor {
  color: #f56c6c;
  font-weight: bold;
}
</style>
