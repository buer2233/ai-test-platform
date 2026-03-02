<!--
  CollectionDetail.vue - 集合详情页面

  展示单个集合的完整信息和测试用例管理，包含以下功能：
  - 集合基本信息：名称、所属项目、用例数量、创建时间、描述
  - 测试用例列表：支持搜索过滤、多选、查看详情、单个执行、移除
  - 添加用例对话框：从项目中选择未添加的用例批量添加到集合
  - 批量移除已有用例
  - 执行配置对话框：选择测试环境后执行全部或选中用例
  - 两种执行模式：执行全部用例、仅执行选中用例
  - 仅一个环境时自动选中并直接执行，多个环境时弹窗选择
-->
<template>
  <div class="collection-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">{{ collection?.name || '加载中...' }}</h1>
      </div>
      <div class="header-right">
        <el-button type="success" @click="handleBatchAddTestCases">
          <el-icon><Plus /></el-icon>
          添加用例
        </el-button>
        <el-dropdown
          split-button
          type="primary"
          :disabled="!selectedCases.length"
          @click="handleBatchExecute"
          trigger="click"
        >
          <el-icon><VideoPlay /></el-icon>
          批量执行 ({{ selectedCases.length }})
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleExecuteAll">
                <el-icon><VideoPlay /></el-icon>
                执行全部用例
              </el-dropdown-item>
              <el-dropdown-item @click="handleBatchExecuteSelected">
                <el-icon><Check /></el-icon>
                仅执行选中的 ({{ selectedCases.length }})
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 集合信息 -->
    <el-card v-if="collection" class="info-card">
      <el-descriptions title="集合信息" :column="2" border>
        <el-descriptions-item label="集合名称">
          {{ collection.name }}
        </el-descriptions-item>
        <el-descriptions-item label="所属项目">
          {{ collection.project_name }}
        </el-descriptions-item>
        <el-descriptions-item label="用例数量">
          {{ collection.test_cases_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(collection.created_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ collection.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 测试用例列表 -->
    <el-card class="test-cases-card">
      <template #header>
        <div class="card-header">
          <span>测试用例</span>
          <div class="header-actions">
            <el-button
              v-if="selectedCases.length > 0"
              type="danger"
              link
              @click="handleBatchRemove"
            >
              <el-icon><Delete /></el-icon>
              移除选中的 ({{ selectedCases.length }})
            </el-button>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索用例名称或URL"
              prefix-icon="Search"
              clearable
              @input="handleSearch"
              style="width: 250px"
            />
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="filteredTestCases"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="用例名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewCase(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="请求方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.method)">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="请求URL" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_by_name" label="创建人" width="120" />
        <el-table-column prop="created_time" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewCase(row)">查看</el-button>
            <el-button type="success" link @click="handleExecuteCase(row)">执行</el-button>
            <el-button type="danger" link @click="handleRemoveCase(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && (!collection?.test_cases || collection.test_cases.length === 0)"
        description="集合中暂无测试用例，点击上方按钮添加"
      />
    </el-card>

    <!-- 添加用例对话框 -->
    <el-dialog
      v-model="addCasesDialogVisible"
      title="添加测试用例"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="add-cases-content">
        <el-input
          v-model="addCasesSearchKeyword"
          placeholder="搜索用例名称或URL"
          prefix-icon="Search"
          clearable
          @input="handleAddCasesSearch"
          style="margin-bottom: 15px"
        />
        <el-table
          v-loading="addCasesLoading"
          :data="availableTestCases"
          @selection-change="handleAddCasesSelectionChange"
          row-key="id"
          max-height="400"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="用例名称" min-width="200" />
          <el-table-column prop="method" label="请求方法" width="100">
            <template #default="{ row }">
              <el-tag :type="getMethodTagType(row.method)">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="请求URL" min-width="300" show-overflow-tooltip />
        </el-table>

        <el-empty
          v-if="!addCasesLoading && availableTestCases.length === 0"
          description="没有可添加的用例"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addCasesDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="confirmAddCases"
            :loading="addCasesSubmitting"
            :disabled="selectedCasesToAdd.length === 0"
          >
            添加选中的 ({{ selectedCasesToAdd.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 执行配置对话框 -->
    <el-dialog
      v-model="executeDialogVisible"
      title="执行配置"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="测试环境">
          <el-select
            v-model="executeConfig.environment"
            placeholder="请选择测试环境"
            style="width: 100%"
          >
            <el-option
              v-for="env in environmentOptions"
              :key="env.value"
              :label="env.label"
              :value="env.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行名称">
          <el-input
            v-model="executeConfig.name"
            placeholder="可选，留空自动生成"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExecute" :loading="executing">
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Delete,
  Search,
  VideoPlay,
  Check
} from '@element-plus/icons-vue'
import { collectionApi } from '../../api/collection'
import { testCaseApi } from '../../api/testCase'
import { executionApi } from '../../api/execution'
import { useProjectStore, useEnvironmentStore, useCollectionStore } from '../../stores'
import type { ApiCollectionDetail } from '../../types/collection'
import type { ApiTestCaseList } from '../../types/testCase'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()
const collectionStore = useCollectionStore()

// 集合详情
const collection = ref<ApiCollectionDetail | null>(null)
const loading = ref(false)

// 测试用例相关
const selectedCases = ref<ApiTestCaseList[]>([])
const searchKeyword = ref('')

// 过滤后的测试用例
const filteredTestCases = computed(() => {
  if (!collection.value?.test_cases) return []
  if (!searchKeyword.value) return collection.value.test_cases

  const keyword = searchKeyword.value.toLowerCase()
  return collection.value.test_cases.filter(tc =>
    tc.name.toLowerCase().includes(keyword) ||
    tc.url.toLowerCase().includes(keyword)
  )
})

// 添加用例对话框
const addCasesDialogVisible = ref(false)
const addCasesLoading = ref(false)
const addCasesSubmitting = ref(false)
const addCasesSearchKeyword = ref('')
const availableTestCases = ref<ApiTestCaseList[]>([])
const selectedCasesToAdd = ref<ApiTestCaseList[]>([])

// 执行配置
const executeDialogVisible = ref(false)
const executing = ref(false)
const executeConfig = reactive({
  environment: null as number | null,
  name: ''
})
const executeMode = ref<'all' | 'selected'>('all')

// 环境选项
const environmentOptions = computed(() =>
  environmentStore.environments.map(e => ({ label: e.name, value: e.id }))
)

// 获取集合ID
const collectionId = computed(() => Number(route.params.id))

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

// 获取方法标签类型
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    PATCH: 'danger',
    DELETE: 'info'
  }
  return types[method] || 'info'
}

// 加载集合详情
const loadCollectionDetail = async () => {
  loading.value = true
  try {
    collection.value = await collectionApi.getCollection(collectionId.value)
  } catch (error) {
    ElMessage.error('加载集合详情失败')
  } finally {
    loading.value = false
  }
}

// 加载可用测试用例
const loadAvailableTestCases = async () => {
  addCasesLoading.value = true
  try {
    const projectId = collection.value?.project || 0
    const response = await testCaseApi.getTestCases({
      project: projectId,
      page_size: 1000
    })

    // 过滤掉已经在集合中的用例
    const existingCaseIds = new Set(collection.value?.test_cases?.map(tc => tc.id) || [])
    availableTestCases.value = response.results.filter(tc => !existingCaseIds.has(tc.id))
  } catch (error) {
    ElMessage.error('加载测试用例失败')
  } finally {
    addCasesLoading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 计算属性会自动处理
}

// 选择处理
const handleSelectionChange = (selection: ApiTestCaseList[]) => {
  selectedCases.value = selection
}

// 查看用例详情
const handleViewCase = (testCase: ApiTestCaseList) => {
  router.push(`/test-cases/${testCase.id}`)
}

// 执行单个用例
const handleExecuteCase = (testCase: ApiTestCaseList) => {
  ElMessage.info('请在用例详情页面执行单个测试用例')
  router.push(`/test-cases/${testCase.id}`)
}

// 移除单个用例
const handleRemoveCase = async (testCase: ApiTestCaseList) => {
  try {
    await ElMessageBox.confirm(
      `确定要从集合中移除用例"${testCase.name}"吗？`,
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await collectionApi.batchRemoveTestCases(collectionId.value, [testCase.id])
    ElMessage.success('移除成功')
    await loadCollectionDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// 批量添加用例
const handleBatchAddTestCases = async () => {
  addCasesDialogVisible.value = true
  addCasesSearchKeyword.value = ''
  selectedCasesToAdd.value = []
  await loadAvailableTestCases()
}

// 添加用例搜索
const handleAddCasesSearch = () => {
  const keyword = addCasesSearchKeyword.value.toLowerCase()
  if (!keyword) {
    loadAvailableTestCases()
    return
  }
  // 简单客户端过滤
  availableTestCases.value = availableTestCases.value.filter(tc =>
    tc.name.toLowerCase().includes(keyword) ||
    tc.url.toLowerCase().includes(keyword)
  )
}

// 添加用例选择变化
const handleAddCasesSelectionChange = (selection: ApiTestCaseList[]) => {
  selectedCasesToAdd.value = selection
}

// 确认添加用例
const confirmAddCases = async () => {
  if (selectedCasesToAdd.value.length === 0) {
    ElMessage.warning('请选择要添加的用例')
    return
  }

  addCasesSubmitting.value = true
  try {
    const testCaseIds = selectedCasesToAdd.value.map(tc => tc.id)
    await collectionApi.batchAddTestCases(collectionId.value, testCaseIds)
    ElMessage.success(`成功添加 ${testCaseIds.length} 个用例`)
    addCasesDialogVisible.value = false
    await loadCollectionDetail()
  } catch (error) {
    ElMessage.error('添加用例失败')
  } finally {
    addCasesSubmitting.value = false
  }
}

// 批量移除用例
const handleBatchRemove = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要移除的用例')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要从集合中移除选中的 ${selectedCases.value.length} 个用例吗？`,
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const testCaseIds = selectedCases.value.map(tc => tc.id)
    await collectionApi.batchRemoveTestCases(collectionId.value, testCaseIds)
    ElMessage.success('移除成功')
    selectedCases.value = []
    await loadCollectionDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// 执行全部用例
const handleExecuteAll = async () => {
  executeMode.value = 'all'
  executeConfig.name = `执行集合: ${collection.value?.name || ''}`

  // 检查环境
  await environmentStore.fetchEnvironments({ page_size: 1000 })
  if (environmentStore.environments.length === 0) {
    ElMessage.warning('请先配置测试环境')
    return
  }

  // 如果只有一个环境，自动选择
  if (environmentStore.environments.length === 1) {
    executeConfig.environment = environmentStore.environments[0].id
    await executeAllTests()
  } else {
    executeDialogVisible.value = true
  }
}

// 执行选中的用例
const handleBatchExecuteSelected = async () => {
  executeMode.value = 'selected'
  executeConfig.name = `执行集合中的 ${selectedCases.value.length} 个用例`

  // 检查环境
  await environmentStore.fetchEnvironments({ page_size: 1000 })
  if (environmentStore.environments.length === 0) {
    ElMessage.warning('请先配置测试环境')
    return
  }

  // 如果只有一个环境，自动选择
  if (environmentStore.environments.length === 1) {
    executeConfig.environment = environmentStore.environments[0].id
    await executeSelectedTests()
  } else {
    executeDialogVisible.value = true
  }
}

// 批量执行按钮点击
const handleBatchExecute = async () => {
  handleBatchExecuteSelected()
}

// 确认执行
const confirmExecute = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  executeDialogVisible.value = false

  if (executeMode.value === 'all') {
    await executeAllTests()
  } else {
    await executeSelectedTests()
  }
}

// 执行全部用例
const executeAllTests = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  executing.value = true
  try {
    const execution = await collectionApi.execute(
      collectionId.value,
      executeConfig.environment,
      executeConfig.name || undefined
    )
    ElMessage.success('执行任务已创建')
    router.push(`/reports/${execution.id}`)
  } catch (error: any) {
    ElMessage.error(`执行失败: ${error.message || '未知错误'}`)
  } finally {
    executing.value = false
  }
}

// 执行选中的用例
const executeSelectedTests = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return
  }

  executing.value = true
  try {
    const testCaseIds = selectedCases.value.map(tc => tc.id)
    const execution = await executionApi.executeBySelection(
      testCaseIds,
      executeConfig.environment,
      executeConfig.name || undefined
    )
    ElMessage.success('执行任务已创建')
    router.push(`/reports/${execution.id}`)
  } catch (error: any) {
    ElMessage.error(`执行失败: ${error.message || '未知错误'}`)
  } finally {
    executing.value = false
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadCollectionDetail()
  await environmentStore.fetchEnvironments({ page_size: 1000 })
})
</script>

<style scoped>
.collection-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-card {
  margin-bottom: 20px;
}

.test-cases-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.add-cases-content {
  max-height: 500px;
  overflow-y: auto;
}
</style>
