<template>
  <div class="test-case-list-in-project">
    <div class="list-header">
      <el-button type="primary" size="small" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        添加用例
      </el-button>
      <el-input
        v-model="searchText"
        placeholder="搜索用例"
        size="small"
        clearable
        style="width: 200px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    <el-table
      v-loading="loading"
      :data="filteredTestCases"
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="test_task" label="测试任务" min-width="300" show-overflow-tooltip />
      <el-table-column prop="tags" label="标签" width="150">
        <template #default="{ row }">
          <el-tag
            v-for="tag in row.tags"
            :key="tag"
            size="small"
            style="margin-right: 4px"
          >
            {{ tag }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" @click.stop="handleRun(row)" :loading="running.has(row.id)">
            <el-icon v-if="!running.has(row.id)"><VideoPlay /></el-icon>
          </el-button>
          <el-button link type="primary" @click.stop="handleEdit(row)">
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button link type="danger" @click.stop="handleDelete(row)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
/**
 * 项目内测试用例列表组件
 *
 * 嵌入在项目详情页的 Tab 页中，展示该项目下所有测试用例。
 * 支持搜索过滤、运行测试、编辑和删除操作。
 */

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Edit, Plus, Search, VideoPlay } from '@element-plus/icons-vue'

import { uiTestCaseApi } from '../../../api/testCase'
import type { UiTestCase } from '../../../types/testCase'

interface Props {
  /** 所属项目 ID */
  projectId: number
}

const props = defineProps<Props>()
const router = useRouter()

const loading = ref(false)
const searchText = ref('')
const testCases = ref<UiTestCase[]>([])
/** 正在运行测试的用例 ID 集合（用于显示加载状态） */
const running = ref<Set<number>>(new Set())

/** 前端搜索过滤：按用例名称和测试任务描述匹配 */
const filteredTestCases = computed(() => {
  if (!searchText.value) return testCases.value
  const search = searchText.value.toLowerCase()
  return testCases.value.filter(tc =>
    tc.name.toLowerCase().includes(search) ||
    tc.test_task.toLowerCase().includes(search)
  )
})

/** 格式化日期为中文本地化字符串 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/* ---------- 数据加载 ---------- */

/** 加载该项目下所有测试用例 */
const loadTestCases = async () => {
  loading.value = true
  try {
    const result = await uiTestCaseApi.getTestCases({ project: props.projectId })
    testCases.value = result.results
  } finally {
    loading.value = false
  }
}

/* ---------- 操作处理 ---------- */

/** 跳转到创建用例页面（自动关联当前项目） */
const handleCreate = () => {
  router.push(`/ui-automation/test-cases/create?project=${props.projectId}`)
}

/** 点击行：跳转到用例详情页 */
const handleRowClick = (row: UiTestCase) => {
  router.push(`/ui-automation/test-cases/${row.id}`)
}

/**
 * 运行测试用例
 * 调用后端 run 端点自动创建执行记录并启动测试，
 * 成功后跳转到执行监控页面
 */
const handleRun = async (row: UiTestCase) => {
  if (!row.is_active) {
    ElMessage.warning('该测试用例未启用，请先启用后再执行')
    return
  }

  running.value.add(row.id)
  try {
    const result = await uiTestCaseApi.run(row.id, { browser_mode: row.browser_mode })
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
    running.value.delete(row.id)
  }
}

/** 跳转到用例编辑页 */
const handleEdit = (row: UiTestCase) => {
  router.push(`/ui-automation/test-cases/${row.id}/edit`)
}

/** 删除用例并刷新列表 */
const handleDelete = async (row: UiTestCase) => {
  await uiTestCaseApi.deleteTestCase(row.id)
  ElMessage.success('删除成功')
  loadTestCases()
}

onMounted(() => {
  loadTestCases()
})
</script>

<style scoped>
.test-case-list-in-project {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-header {
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
