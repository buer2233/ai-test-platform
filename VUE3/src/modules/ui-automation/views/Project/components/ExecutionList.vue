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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { UiTestExecution, ExecutionStatus } from '../../../types/execution'
import { uiExecutionApi } from '../../../api/execution'

interface Props {
  projectId: number
}

const props = defineProps<Props>()

const router = useRouter()

const loading = ref(false)
const executions = ref<UiTestExecution[]>([])

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getStatusType = (status: ExecutionStatus) => {
  const types: Record<ExecutionStatus, any> = {
    pending: 'info',
    running: 'warning',
    passed: 'success',
    failed: 'danger',
    error: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: ExecutionStatus) => {
  const texts: Record<ExecutionStatus, string> = {
    pending: '待执行',
    running: '执行中',
    passed: '通过',
    failed: '失败',
    error: '错误',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const loadExecutions = async () => {
  loading.value = true
  try {
    const result = await uiExecutionApi.getExecutions({ project: props.projectId })
    executions.value = result.results.slice(0, 10)
  } finally {
    loading.value = false
  }
}

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
