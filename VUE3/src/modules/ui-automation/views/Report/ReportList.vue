<template>
  <div class="report-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h3>测试报告</h3>
        <el-text type="info">查看UI自动化测试执行报告</el-text>
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
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="reportStore.loading"
        :data="reportStore.reports"
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="报告ID" width="100" />
        <el-table-column prop="project_name" label="项目" width="150" />
        <el-table-column prop="test_case_name" label="测试用例" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
              {{ row.status === 'passed' ? '通过' : row.status === 'failed' ? '失败' : '错误' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_seconds" label="耗时(秒)" width="100" align="center">
          <template #default="{ row }">
            {{ row.duration_seconds }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="reportStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchReports"
          @current-change="fetchReports"
        />
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ reportStore.total }}</div>
            <div class="stat-label">总报告数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card passed">
          <div class="stat-content">
            <div class="stat-value">{{ reportStore.passedReports.length }}</div>
            <div class="stat-label">通过数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card failed">
          <div class="stat-content">
            <div class="stat-value">{{ reportStore.failedReports.length }}</div>
            <div class="stat-label">失败数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card rate">
          <div class="stat-content">
            <div class="stat-value">{{ reportStore.passRate.toFixed(1) }}%</div>
            <div class="stat-label">通过率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * 测试报告列表页
 *
 * 展示所有 UI 自动化测试的执行报告，支持：
 * - 按项目、状态、时间范围筛选
 * - 分页浏览
 * - 底部统计卡片（总报告数、通过数、失败数、通过率）
 */

import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { View } from '@element-plus/icons-vue'

import { useUiProjectStore } from '../../stores/project'
import { useUiReportStore } from '../../stores/report'
import type { UiTestReport } from '../../types/report'

const router = useRouter()
const reportStore = useUiReportStore()
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
  dateRange: null as [string, string] | null
})

/* ---------- 工具函数 ---------- */

/**
 * 格式化日期为中文本地化字符串
 * 处理 null 和无效日期的边界情况
 */
const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN')
}

/* ---------- 数据加载 ---------- */

/** 根据筛选条件和分页参数获取报告列表 */
const fetchReports = async () => {
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
  if (filterForm.dateRange) {
    params.started_at__gte = filterForm.dateRange[0]
    params.started_at__lte = filterForm.dateRange[1]
  }
  await reportStore.fetchReports(params)
}

/** 筛选条件变更：重置到第一页后重新加载 */
const handleSearch = () => {
  pagination.page = 1
  fetchReports()
}

/* ---------- 行操作 ---------- */

/** 点击行：跳转到报告详情页 */
const handleRowClick = (row: UiTestReport) => {
  router.push(`/ui-automation/reports/${row.id}`)
}

/** 查看报告按钮 */
const handleView = (row: UiTestReport) => {
  router.push(`/ui-automation/reports/${row.id}`)
}

/* ---------- 页面初始化 ---------- */
onMounted(async () => {
  // 先加载项目列表（用于筛选下拉），再加载报告列表
  await projectStore.fetchProjects()
  fetchReports()
})
</script>

<style scoped>
.report-list {
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

.stats-row {
  margin-bottom: 0;
}

.stat-card {
  margin-bottom: 0;
  text-align: center;
}

.stat-card.passed {
  border-top: 3px solid var(--el-color-success);
}

.stat-card.failed {
  border-top: 3px solid var(--el-color-danger);
}

.stat-card.rate {
  border-top: 3px solid var(--el-color-primary);
}

.stat-content {
  padding: 16px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
