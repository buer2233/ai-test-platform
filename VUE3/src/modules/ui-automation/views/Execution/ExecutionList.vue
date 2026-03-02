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
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
            <el-option label="错误" value="error" />
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
              v-if="row.status === 'passed' || row.status === 'failed' || row.status === 'error'"
              link
              type="success"
              @click.stop="handleViewReport(row)"
            >
              <el-icon><Document /></el-icon>
              报告
            </el-button>
            <el-button
              v-if="row.status === 'passed' || row.status === 'failed' || row.status === 'error'"
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
/**
 * 执行记录列表页
 *
 * 展示所有 UI 自动化测试的执行记录，支持：
 * - 按项目、状态、浏览器模式、创建时间筛选
 * - 分页浏览
 * - 查看详情、取消执行、查看报告、导出报告、删除等操作
 */

import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Document, Download, VideoPause, View } from '@element-plus/icons-vue'

import { useUiExecutionStore } from '../../stores/execution'
import { useUiProjectStore } from '../../stores/project'
import type { ExecutionStatus, UiTestExecution } from '../../types/execution'

const router = useRouter()
const executionStore = useUiExecutionStore()
const projectStore = useUiProjectStore()

/* ---------- 分页配置 ---------- */
const pagination = reactive({
  page: 1,
  pageSize: 20
})

/* ---------- 筛选表单 ---------- */
const filterForm = reactive({
  project: undefined as number | undefined,
  status: '',
  browser_mode: '',
  dateRange: [] as string[]
})

/* ---------- 状态映射（复用于模板中的标签展示） ---------- */

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

/** 获取状态对应的 El-Tag 类型 */
const getStatusType = (status: ExecutionStatus) => {
  return STATUS_TYPE_MAP[status] || 'info'
}

/** 获取状态对应的中文文本 */
const getStatusText = (status: ExecutionStatus) => {
  return STATUS_TEXT_MAP[status] || status
}

/** 格式化日期为中文本地化字符串 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/* ---------- 数据加载 ---------- */

/** 根据当前筛选条件和分页参数获取执行记录列表 */
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

/** 筛选条件变更：重置到第一页后重新加载 */
const handleSearch = () => {
  pagination.page = 1
  fetchExecutions()
}

/* ---------- 行操作 ---------- */

/** 点击行：跳转到执行监控详情页 */
const handleRowClick = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

/** 查看详情按钮 */
const handleView = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

/** 查看报告：跳转到报告详情页（需要有关联的 JSON 报告路径） */
const handleViewReport = (row: UiTestExecution) => {
  if (row.json_report_path) {
    router.push({
      path: `/ui-automation/reports/${row.id}`,
      query: { report: row.json_report_path }
    })
  } else {
    ElMessage.warning('该执行记录没有关联的报告')
  }
}

/** 取消正在运行的执行 */
const handleCancel = async (row: UiTestExecution) => {
  try {
    await ElMessageBox.confirm('确定要取消该执行吗？', '取消确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await executionStore.cancelExecution(row.id)
    ElMessage.success('已取消执行')
    fetchExecutions()
  } catch {
    // 用户取消确认操作
  }
}

/** 删除执行记录 */
const handleDelete = async (row: UiTestExecution) => {
  try {
    await ElMessageBox.confirm(`确定要删除执行记录 #${row.id} 吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await executionStore.deleteExecution(row.id)
    ElMessage.success('删除成功')
    fetchExecutions()
  } catch {
    // 用户取消确认操作
  }
}

/** 导出报告为 JSON 文件并触发下载 */
const handleExportReport = async (row: UiTestExecution) => {
  try {
    if (!row.json_report_path) {
      ElMessage.warning('该执行记录没有关联的报告')
      return
    }

    // 调用后端 API 获取报告文件内容
    const response = await fetch(`/api/v1/ui-automation/reports/file?path=${encodeURIComponent(row.json_report_path)}`)
    if (!response.ok) {
      throw new Error('获取报告失败')
    }

    const reportData = await response.json()

    // 构造 JSON Blob 并触发浏览器下载
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

/* ---------- 页面初始化 ---------- */
onMounted(async () => {
  // 先加载项目列表（用于筛选下拉），再加载执行记录
  await projectStore.fetchProjects()
  fetchExecutions()
})
</script>
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
