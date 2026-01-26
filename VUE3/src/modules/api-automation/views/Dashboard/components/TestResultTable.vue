<template>
  <el-table :data="testResults" v-loading="loading" stripe @selection-change="handleSelectionChange">
    <el-table-column type="selection" width="55" />
    <el-table-column prop="test_case_name" label="用例名称" min-width="200">
      <template #default="{ row }">
        <el-link type="primary" @click="$emit('view-detail', row.id)">
          {{ row.test_case_name || row.test_case?.name }}
        </el-link>
      </template>
    </el-table-column>
    <el-table-column prop="collection_name" label="集合" width="150">
      <template #default="{ row }">
        {{ row.collection_name || row.test_case?.collection?.name || '-' }}
      </template>
    </el-table-column>
    <el-table-column prop="project_name" label="项目" width="150">
      <template #default="{ row }">
        {{ row.project_name || row.test_case?.collection?.project?.name || '-' }}
      </template>
    </el-table-column>
    <el-table-column prop="status" label="状态" width="100">
      <template #default="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusText(row.status) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="response_time" label="响应时间" width="120">
      <template #default="{ row }">
        {{ row.response_time }}ms
      </template>
    </el-table-column>
    <el-table-column prop="owner_name" label="负责人" width="120">
      <template #default="{ row }">
        {{ row.owner_name || row.test_case?.owner?.username || '-' }}
      </template>
    </el-table-column>
    <el-table-column prop="module" label="模块" width="120">
      <template #default="{ row }">
        {{ row.module || row.test_case?.module || '-' }}
      </template>
    </el-table-column>
    <el-table-column prop="start_time" label="执行时间" width="180">
      <template #default="{ row }">
        {{ formatTime(row.start_time) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <el-button type="primary" link size="small" @click="$emit('view-detail', row.id)">
          查看详情
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { watch } from 'vue'

interface Props {
  testResults: any[]
  loading: boolean
  selectedResults: Set<number>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectionChange: [ids: number[]]
  viewDetail: [id: number]
}>()

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
const formatTime = (time: string) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 选择变更处理
const handleSelectionChange = (selection: any[]) => {
  const ids = selection.map(row => row.id)
  emit('selectionChange', ids)
}

// 监听选中状态变化，同步表格选择状态
watch(() => props.selectedResults, (newVal) => {
  // 这里可以通过 ref 调用表格的 toggleRowSelection 方法来同步选中状态
  // 暂时留空，由父组件控制选中逻辑
}, { deep: true })
</script>

<style scoped>
/* 表格样式继承自父组件 */
</style>
