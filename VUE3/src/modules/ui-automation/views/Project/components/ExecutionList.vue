<template>
  <div class="execution-list-in-project">
    <el-table
      v-loading="loading"
      :data="executions"
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="执行ID" width="100" />
      <el-table-column prop="test_case_name" label="测试用例" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
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
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="handleRowClick(row)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
/**
 * 项目内执行记录列表组件
 *
 * 嵌入在项目详情页的 Tab 页中，展示该项目最近 10 条执行记录。
 * 点击行可跳转到执行监控详情页。
 */

import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { uiExecutionApi } from '../../../api/execution'
import type { ExecutionStatus, UiTestExecution } from '../../../types/execution'

interface Props {
  /** 所属项目 ID */
  projectId: number
}

const props = defineProps<Props>()
const router = useRouter()

const loading = ref(false)
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

/** 格式化日期为中文本地化字符串 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/* ---------- 数据加载 ---------- */

/** 加载该项目最近 10 条执行记录 */
const loadExecutions = async () => {
  loading.value = true
  try {
    const result = await uiExecutionApi.getExecutions({ project: props.projectId })
    executions.value = result.results.slice(0, 10)
  } finally {
    loading.value = false
  }
}

/** 点击行：跳转到执行监控页面 */
const handleRowClick = (row: UiTestExecution) => {
  router.push(`/ui-automation/executions/${row.id}`)
}

onMounted(() => {
  loadExecutions()
})
</script>

<style scoped>
.execution-list-in-project {
  display: flex;
  flex-direction: column;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
