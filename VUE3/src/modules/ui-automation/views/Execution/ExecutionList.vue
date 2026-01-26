<template>
  <div class="execution-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h3>执行记录</h3>
        <el-text type="info">查看UI自动化测试执行历史</el-text>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="项目">
          <el-select
            v-model="filterForm.project"
            placeholder="全部项目"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="project in projectStore.projectOptions"
              :key="project.value"
              :label="project.label"
              :value="project.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable @change="handleSearch">
            <el-option label="待执行" value="pending" />
            <el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器模式">
          <el-select v-model="filterForm.browser_mode" placeholder="全部" clearable @change="handleSearch">
            <el-option label="无头模式" value="headless" />
            <el-option label="有头模式" value="headed" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleSearch"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 执行记录列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="executionStore.loading"
        :data="executionStore.executions"
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="执行ID" width="100" />
        <el-table-column prop="project_name" label="项目" width="150" />
        <el-table-column prop="test_case_name" label="测试用例" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="browser_mode" label="浏览器" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.browser_mode === 'headless' ? 'info' : 'warning'" size="small">
              {{ row.browser_mode === 'headless' ? '无头' : '有头' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="耗时(秒)" width="100" align="center">
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
        <el-table-column label="操作" width="260" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'running'"
              link
              type="warning"
              @click.stop="handleCancel(row)"
            >
              <el-icon><VideoPause /></el-icon>
              取消
            </el-button>
            <el-button link type="primary" @click.stop="handleView(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button
              v-if="row.status === 'completed' || row.status === 'failed'"
              link
              type="success"
              @click.stop="handleViewReport(row)"
            >
              <el-icon><Document /></el-icon>
              报告
            </el-button>
            <el-button
              v-if="row.status === 'completed' || row.status === 'failed'"
              link
              type="info"
              @click.stop="handleExportReport(row)"
            >
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="executionStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchExecutions"
          @current-change="fetchExecutions"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPause, View, Document, Delete, Download } from '@element-plus/icons-vue'
import { useUiExecutionStore } from '../../stores/execution'
import { useUiProjectStore } from '../../stores/project'
import type { ExecutionStatus, UiTestExecution } from '../../types/execution'

const router = useRouter()
const executionStore = useUiExecutionStore()
const projectStore = useUiProjectStore()

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 筛选表单
const filterForm = reactive({
  project: undefined as number | undefined,
  status: '',
  browser_mode: '',
  dateRange: [] as string[]
})

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取状态类型
const getStatusType = (status: ExecutionStatus) => {
  const types: Record<ExecutionStatus, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: ExecutionStatus) => {
  const texts: Record<ExecutionStatus, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 获取执行记录列表
const fetchExecutions = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.pageSize
  }
  if (filterForm.project) {
    params.project = filterForm.project
  }
  if (filterForm.status) {
    params.status = filterForm.status
  }
  if (filterForm.browser_mode) {
    params.browser_mode = filterForm.browser_mode
  }
  if (filterForm.dateRange && filterForm.dateRange.length === 2) {
    params.created_after = filterForm.dateRange[0]
    params.created_before = filterForm.dateRange[1]
  }
  await executionStore.fetchExecutions(params)
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchExecutions()
}

// 行点击
const handleRowClick = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

// 查看详情
const handleView = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

// 查看报告
const handleViewReport = (row: UiTestExecution) => {
  if (row.json_report_path) {
    // 使用 JSON 报告路径跳转到报告详情页
    router.push({
      path: `/ui-automation/reports/${row.id}`,
      query: { report: row.json_report_path }
    })
  } else {
    ElMessage.warning('该执行记录没有关联的报告')
  }
}

// 取消执行
const handleCancel = async (row: UiTestExecution) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消该执行吗？',
      '取消确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    await executionStore.cancelExecution(row.id)
    ElMessage.success('已取消执行')
    fetchExecutions()
  } catch {
    // 用户取消
  }
}

// 删除
const handleDelete = async (row: UiTestExecution) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除执行记录 #${row.id} 吗？`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    await executionStore.deleteExecution(row.id)
    ElMessage.success('删除成功')
    fetchExecutions()
  } catch {
    // 用户取消
  }
}

// 导出报告
const handleExportReport = async (row: UiTestExecution) => {
  try {
    if (!row.json_report_path) {
      ElMessage.warning('该执行记录没有关联的报告')
      return
    }

    // 调用后端API获取报告文件
    const response = await fetch(`/api/v1/ui-automation/reports/file?path=${encodeURIComponent(row.json_report_path)}`)
    if (!response.ok) {
      throw new Error('获取报告失败')
    }

    const reportData = await response.json()

    // 创建JSON文件并下载
    const jsonString = JSON.stringify(reportData, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_execution_${row.id}_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出报告失败:', error)
    ElMessage.error('导出报告失败')
  }
}

onMounted(async () => {
  await projectStore.fetchProjects()
  fetchExecutions()
})
</script>

<style scoped>
.execution-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 0;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  flex: 1;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
