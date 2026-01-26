<template>
  <div class="test-case-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h3>UI测试用例</h3>
        <el-text type="info">使用自然语言描述测试场景</el-text>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建用例
        </el-button>
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
            style="width: 180px"
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
        <el-form-item label="用例名称">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索用例名称或任务描述"
            clearable
            style="width: 240px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.is_enabled"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用例列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="testCaseStore.loading"
        :data="testCaseStore.testCases"
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="用例名称" min-width="200" />
        <el-table-column prop="project_name" label="所属项目" width="150" />
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
        <el-table-column prop="browser_mode" label="浏览器模式" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.browser_mode === 'headless' ? 'info' : 'warning'" size="small">
              {{ row.browser_mode === 'headless' ? '无头' : '有头' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executions_count" label="执行次数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.executions_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click.stop="handleRun(row)">
              <el-icon><VideoPlay /></el-icon>
            </el-button>
            <el-button link type="primary" @click.stop="handleView(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button link type="primary" @click.stop="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button link type="info" @click.stop="handleCopy(row)">
              <el-icon><DocumentCopy /></el-icon>
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
          :total="testCaseStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchTestCases"
          @current-change="fetchTestCases"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <TestCaseCreateDialog
      v-model="dialogVisible"
      :test-case-id="editingId"
      @success="handleDialogSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, VideoPlay, View, Edit, Delete, DocumentCopy } from '@element-plus/icons-vue'
import { useUiTestCaseStore } from '../../stores/testCase'
import { useUiProjectStore } from '../../stores/project'
import { uiTestCaseApi } from '../../api/testCase'
import type { UiTestCase } from '../../types/testCase'
import TestCaseCreateDialog from '@ui-automation/components/TestCaseCreateDialog.vue'

const router = useRouter()
const testCaseStore = useUiTestCaseStore()
const projectStore = useUiProjectStore()

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 筛选表单
const filterForm = reactive({
  project: undefined as number | undefined,
  search: '',
  is_enabled: undefined as boolean | undefined
})

// 对话框
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取测试用例列表
const fetchTestCases = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.pageSize
  }
  if (filterForm.project) {
    params.project = filterForm.project
  }
  if (filterForm.search) {
    params.search = filterForm.search
  }
  if (filterForm.is_enabled !== undefined) {
    params.is_enabled = filterForm.is_enabled
  }
  await testCaseStore.fetchTestCases(params)
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTestCases()
}

// 重置筛选
const handleReset = () => {
  filterForm.project = undefined
  filterForm.search = ''
  filterForm.is_enabled = undefined
  pagination.page = 1
  fetchTestCases()
}

// 行点击
const handleRowClick = (row: UiTestCase) => {
  router.push(`/ui-automation/test-cases/${row.id}`)
}

// 运行测试
const handleRun = async (row: UiTestCase) => {
  if (!row.is_enabled) {
    ElMessage.warning('该测试用例未启用，请先启用后再执行')
    return
  }

  try {
    // 直接调用 run 端点（自动创建执行记录并启动测试）
    const result = await uiTestCaseApi.run(row.id, { browser_mode: row.browser_mode })
    ElMessage.success(result.message || '开始执行测试')
    // 跳转到执行监控页面
    router.push(`/ui-automation/executions/${result.execution.id}`)
  } catch (error: any) {
    console.error('Run test failed:', error)
    const errorMsg = error?.response?.data?.error || error?.message || '执行失败'
    if (errorMsg.includes('OPENAI_API_KEY')) {
      ElMessage.error('执行失败：OPENAI_API_KEY 环境变量未配置，请联系管理员配置')
    } else {
      ElMessage.error(`执行失败：${errorMsg}`)
    }
  }
}

// 查看详情
const handleView = (row: UiTestCase) => {
  router.push(`/ui-automation/test-cases/${row.id}`)
}

// 编辑
const handleEdit = (row: UiTestCase) => {
  editingId.value = row.id
  dialogVisible.value = true
}

// 复制
const handleCopy = async (row: UiTestCase) => {
  try {
    const newTestCase = await testCaseStore.copyTestCase(row.id)
    ElMessage.success(`已复制用例: ${newTestCase.name}`)
    fetchTestCases()
  } catch {
    ElMessage.error('复制用例失败')
  }
}

// 删除
const handleDelete = async (row: UiTestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例 "${row.name}" 吗？`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    await testCaseStore.deleteTestCase(row.id)
    ElMessage.success('删除成功')
    fetchTestCases()
  } catch {
    // 用户取消
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  editingId.value = null
  dialogVisible.value = true
}

// 对话框成功回调
const handleDialogSuccess = () => {
  fetchTestCases()
}

onMounted(async () => {
  await projectStore.fetchProjects()
  fetchTestCases()
})
</script>

<style scoped>
.test-case-list {
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
