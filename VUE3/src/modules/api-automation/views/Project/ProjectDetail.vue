<!--
  ProjectDetail.vue - 项目详情页面

  展示单个项目的完整信息，包含以下功能：
  - 项目基本信息：名称、创建人、集合/用例数量、创建/更新时间、描述
  - 统计卡片：集合总数、测试用例数、可用环境数
  - 集合列表：查看、执行、编辑、删除集合操作
  - 测试用例列表：支持搜索过滤、多选、分页、执行和查看
  - 执行配置对话框：选择测试环境后执行项目/集合/选中用例
  - 支持三种执行模式：整个项目、单个集合、选中的用例
  - 仅一个环境时自动选中并直接执行，多个环境时弹窗选择
-->
<template>
  <div class="project-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button type="primary" link @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">{{ project?.name || '加载中...' }}</h1>
      </div>
      <div class="header-right">
        <el-button type="success" @click="handleExecuteProject">
          <el-icon><VideoPlay /></el-icon>
          执行全部测试
        </el-button>
        <el-button type="primary" @click="handleEditProject">编辑</el-button>
      </div>
    </div>

    <!-- 项目信息 -->
    <el-card v-if="project" class="info-card">
      <el-descriptions title="项目信息" :column="2" border>
        <el-descriptions-item label="项目名称">
          {{ project.name }}
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ project.created_by_name }}
        </el-descriptions-item>
        <el-descriptions-item label="集合数量">
          {{ project.collections_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="测试用例数量">
          {{ project.test_cases_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(project.created_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(project.updated_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ project.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card collections">
          <div class="stat-number">{{ collections.length }}</div>
          <div class="stat-label">集合总数</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card testcases">
          <div class="stat-number">{{ project?.test_cases_count || 0 }}</div>
          <div class="stat-label">测试用例</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card environments">
          <div class="stat-number">{{ environmentCount }}</div>
          <div class="stat-label">可用环境</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 集合列表 -->
    <el-card class="collections-card">
      <template #header>
        <div class="card-header">
          <span>集合列表</span>
          <el-button type="primary" link @click="handleCreateCollection">新建集合</el-button>
        </div>
      </template>

      <el-table
        v-loading="collectionsLoading"
        :data="collections"
        @row-click="handleViewCollection"
        row-key="id"
        class="clickable-table"
      >
        <el-table-column prop="name" label="集合名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="test_cases_count" label="用例数量" width="100" align="center" />
        <el-table-column prop="created_time" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="handleViewCollection(row)">查看</el-button>
            <el-button type="success" link @click.stop="handleExecuteCollection(row)">执行</el-button>
            <el-button type="warning" link @click.stop="handleEditCollection(row)">编辑</el-button>
            <el-button type="danger" link @click.stop="handleDeleteCollection(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!collectionsLoading && collections.length === 0"
        description="暂无集合，点击上方按钮创建"
      />
    </el-card>

    <!-- 测试用例列表 -->
    <el-card class="testcases-card">
      <template #header>
        <div class="card-header">
          <span>测试用例</span>
          <div class="header-actions">
            <el-button type="primary" link @click="handleCreateTestCase">新建用例</el-button>
            <el-input
              v-model="testCasesSearchKeyword"
              placeholder="搜索用例名称或URL"
              prefix-icon="Search"
              clearable
              @input="handleTestCasesSearch"
              style="width: 250px"
            />
          </div>
        </div>
      </template>

      <el-table
        v-loading="testCasesLoading"
        :data="filteredTestCases"
        @selection-change="handleTestCasesSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="用例名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewTestCase(row)">{{ row.name }}</el-link>
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
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewTestCase(row)">查看</el-button>
            <el-button type="success" link @click="handleExecuteTestCase(row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="testCases.length > 0">
        <el-pagination
          v-model:current-page="testCasesPagination.page"
          v-model:page-size="testCasesPagination.size"
          :total="testCasesPagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadTestCases"
          @current-change="loadTestCases"
        />
      </div>

      <el-empty
        v-if="!testCasesLoading && testCases.length === 0"
        description="暂无测试用例，点击上方按钮创建"
      />
    </el-card>

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
  VideoPlay,
  Search
} from '@element-plus/icons-vue'
import { projectApi } from '../../api/project'
import { collectionApi } from '../../api/collection'
import { testCaseApi } from '../../api/testCase'
import { executionApi } from '../../api/execution'
import { useEnvironmentStore, useCollectionStore, useTestCaseStore } from '../../stores'
import type { ApiProject } from '../../types/project'
import type { ApiCollection } from '../../types/collection'
import type { ApiTestCaseList } from '../../types/testCase'

const router = useRouter()
const route = useRoute()
const environmentStore = useEnvironmentStore()
const collectionStore = useCollectionStore()
const testCaseStore = useTestCaseStore()

// 项目详情
const project = ref<ApiProject | null>(null)

// 集合相关
const collections = ref<ApiCollection[]>([])
const collectionsLoading = ref(false)

// 测试用例相关
const testCases = ref<ApiTestCaseList[]>([])
const testCasesLoading = ref(false)
const testCasesSearchKeyword = ref('')
const selectedTestCases = ref<ApiTestCaseList[]>([])
const testCasesPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 过滤后的测试用例
const filteredTestCases = computed(() => {
  if (!testCasesSearchKeyword.value) return testCases.value
  const keyword = testCasesSearchKeyword.value.toLowerCase()
  return testCases.value.filter(tc =>
    tc.name.toLowerCase().includes(keyword) ||
    tc.url.toLowerCase().includes(keyword)
  )
})

// 执行配置
const executeDialogVisible = ref(false)
const executing = ref(false)
const executeConfig = reactive({
  environment: null as number | null,
  name: ''
})
const executeMode = ref<'project' | 'collection' | 'testcases' | 'selected'>('project')
const executeTarget = ref<any>(null)

// 环境选项
const environmentOptions = computed(() =>
  environmentStore.environments.map(e => ({ label: e.name, value: e.id }))
)
const environmentCount = computed(() => environmentStore.environments.length)

// 获取项目ID
const projectId = computed(() => Number(route.params.id))

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

// 加载项目详情
const loadProjectDetail = async () => {
  try {
    project.value = await projectApi.getProject(projectId.value)
  } catch (error) {
    ElMessage.error('加载项目详情失败')
  }
}

// 加载集合列表
const loadCollections = async () => {
  collectionsLoading.value = true
  try {
    const response = await projectApi.getProjectCollections(projectId.value, { page_size: 1000 })
    collections.value = response.results
  } catch (error) {
    ElMessage.error('加载集合列表失败')
  } finally {
    collectionsLoading.value = false
  }
}

// 加载测试用例列表
const loadTestCases = async () => {
  testCasesLoading.value = true
  try {
    const response = await projectApi.getProjectTestCases(projectId.value, {
      page: testCasesPagination.page,
      page_size: testCasesPagination.size
    })
    testCases.value = response.results
    testCasesPagination.total = response.count
  } catch (error) {
    ElMessage.error('加载测试用例失败')
  } finally {
    testCasesLoading.value = false
  }
}

// 测试用例搜索
const handleTestCasesSearch = () => {
  // 计算属性会自动处理
}

// 测试用例选择变化
const handleTestCasesSelectionChange = (selection: ApiTestCaseList[]) => {
  selectedTestCases.value = selection
}

// 查看集合详情
const handleViewCollection = (collection: ApiCollection) => {
  router.push(`/collections/${collection.id}`)
}

// 创建集合
const handleCreateCollection = () => {
  router.push({ name: 'CollectionList', query: { action: 'create', projectId: projectId.value } })
}

// 编辑集合
const handleEditCollection = (collection: ApiCollection) => {
  ElMessage.info('请在集合列表页面编辑')
}

// 删除集合
const handleDeleteCollection = async (collection: ApiCollection) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除集合"${collection.name}"吗？`,
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await collectionApi.deleteCollection(collection.id)
    ElMessage.success('删除成功')
    await loadCollections()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 执行集合
const handleExecuteCollection = async (collection: ApiCollection) => {
  executeMode.value = 'collection'
  executeTarget.value = collection
  executeConfig.name = `执行集合: ${collection.name}`

  await environmentStore.fetchEnvironments({ page_size: 1000 })
  if (environmentStore.environments.length === 0) {
    ElMessage.warning('请先配置测试环境')
    return
  }

  if (environmentStore.environments.length === 1) {
    executeConfig.environment = environmentStore.environments[0].id
    await executeCollection()
  } else {
    executeDialogVisible.value = true
  }
}

// 查看测试用例详情
const handleViewTestCase = (testCase: ApiTestCaseList) => {
  router.push(`/test-cases/${testCase.id}`)
}

// 创建测试用例
const handleCreateTestCase = () => {
  router.push({ name: 'TestCaseCreate', query: { projectId: projectId.value } })
}

// 执行单个测试用例
const handleExecuteTestCase = (testCase: ApiTestCaseList) => {
  ElMessage.info('请在用例详情页面执行单个测试用例')
  router.push(`/test-cases/${testCase.id}`)
}

// 编辑项目
const handleEditProject = () => {
  ElMessage.info('请在项目列表页面编辑')
}

// 执行项目全部测试
const handleExecuteProject = async () => {
  executeMode.value = 'project'
  executeConfig.name = `执行项目: ${project.value?.name || ''}`

  await environmentStore.fetchEnvironments({ page_size: 1000 })
  if (environmentStore.environments.length === 0) {
    ElMessage.warning('请先配置测试环境')
    return
  }

  if (environmentStore.environments.length === 1) {
    executeConfig.environment = environmentStore.environments[0].id
    await executeProject()
  } else {
    executeDialogVisible.value = true
  }
}

// 确认执行
const confirmExecute = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  executeDialogVisible.value = false

  switch (executeMode.value) {
    case 'project':
      await executeProject()
      break
    case 'collection':
      await executeCollection()
      break
    case 'testcases':
      await executeSelectedTestCases()
      break
  }
}

// 执行项目
const executeProject = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  executing.value = true
  try {
    const execution = await projectApi.execute(
      projectId.value,
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

// 执行集合
const executeCollection = async () => {
  if (!executeConfig.environment || !executeTarget.value) {
    ElMessage.warning('请选择测试环境')
    return
  }

  executing.value = true
  try {
    const execution = await collectionApi.execute(
      executeTarget.value.id,
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

// 执行选中的测试用例
const executeSelectedTestCases = async () => {
  if (!executeConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return
  }

  executing.value = true
  try {
    const testCaseIds = selectedTestCases.value.map(tc => tc.id)
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
  await loadProjectDetail()
  await loadCollections()
  await loadTestCases()
  await environmentStore.fetchEnvironments({ page_size: 1000 })
})
</script>

<style scoped>
.project-detail-container {
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

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 15px 0;
}

.stat-card.collections {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.testcases {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.stat-card.environments {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-card .stat-label {
  color: inherit;
  font-size: 14px;
}

.collections-card,
.testcases-card {
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

.clickable-table :deep(.el-table__row) {
  cursor: pointer;
}

.clickable-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
