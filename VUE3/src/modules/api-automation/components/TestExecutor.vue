<template>
  <div class="test-executor">
    <div class="header">
      <h2>测试执行</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建执行
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ executionStore.total }}</div>
              <div class="stat-label">总执行数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ executionStore.runningExecutions.length }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ executionStore.passRate }}%</div>
              <div class="stat-label">通过率</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-button @click="refreshData" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 执行列表 -->
    <el-table :data="executionStore.executions" v-loading="executionStore.loading" stripe>
      <el-table-column prop="name" label="执行名称" />
      <el-table-column prop="project_name" label="所属项目" />
      <el-table-column prop="environment_name" label="执行环境" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="执行结果" width="150">
        <template #default="{ row }">
          <div class="result-summary">
            <span class="passed">{{ row.passed_count }}</span>/
            <span class="total">{{ row.total_count }}</span>
            <span class="failed">-{{ row.failed_count }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="100">
        <template #default="{ row }">
          {{ row.duration ? `${row.duration}s` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_by_name" label="创建者" />
      <el-table-column prop="created_time" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            @click="viewExecution(row)"
          >
            详情
          </el-button>
          <el-button
            v-if="row.status === 'PENDING'"
            size="small"
            type="success"
            @click="executeTest(row.id)"
          >
            执行
          </el-button>
          <el-button
            v-if="row.status === 'RUNNING'"
            size="small"
            type="warning"
            @click="cancelExecution(row.id)"
          >
            取消
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="deleteExecution(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="executionStore.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建执行对话框 -->
    <el-dialog
      title="新建测试执行"
      v-model="createDialogVisible"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form :model="createForm" :rules="createFormRules" ref="createFormRef" label-width="120px">
        <el-form-item label="执行名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入执行名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project">
          <el-select v-model="createForm.project" placeholder="请选择项目" style="width: 100%" @change="onProjectChange">
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行环境" prop="environment">
          <el-select v-model="createForm.environment" placeholder="请选择环境" style="width: 100%">
            <el-option
              v-for="env in filteredEnvironments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="测试用例" prop="test_cases">
          <el-transfer
            v-model="createForm.test_cases"
            :data="availableTestCases"
            :titles="['可用测试用例', '已选择测试用例']"
            :button-texts="['移除', '添加']"
            :format="{ noChecked: '${total}', hasChecked: '${checked}/${total}' }"
            @change="onTestCaseChange"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" rows="3" placeholder="请输入执行描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateExecution" :loading="submitting">
          创建并执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行详情对话框 -->
    <el-dialog
      title="执行详情"
      v-model="detailDialogVisible"
      width="80%"
      top="5vh"
    >
      <div v-if="currentExecution">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="执行名称">{{ currentExecution.name }}</el-descriptions-item>
              <el-descriptions-item label="项目">{{ currentExecution.project_name }}</el-descriptions-item>
              <el-descriptions-item label="环境">{{ currentExecution.environment_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(currentExecution.status)">
                  {{ getStatusText(currentExecution.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="总用例数">{{ currentExecution.total_count }}</el-descriptions-item>
              <el-descriptions-item label="通过数">{{ currentExecution.passed_count }}</el-descriptions-item>
              <el-descriptions-item label="失败数">{{ currentExecution.failed_count }}</el-descriptions-item>
              <el-descriptions-item label="跳过数">{{ currentExecution.skipped_count }}</el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ formatDateTime(currentExecution.start_time) }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ formatDateTime(currentExecution.end_time) }}</el-descriptions-item>
              <el-descriptions-item label="耗时">{{ currentExecution.duration ? `${currentExecution.duration}s` : '-' }}</el-descriptions-item>
              <el-descriptions-item label="创建者">{{ currentExecution.created_by_name }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="测试结果" name="results">
            <el-table :data="currentExecution.test_results" stripe>
              <el-table-column prop="test_case_name" label="测试用例" />
              <el-table-column prop="test_case_method" label="请求方法" width="100" />
              <el-table-column prop="test_case_url" label="请求URL" show-overflow-tooltip />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'PASSED' ? 'success' : 'danger'" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="response_status" label="状态码" width="100" />
              <el-table-column prop="response_time" label="响应时间" width="120">
                <template #default="{ row }">
                  {{ row.response_time }}ms
                </template>
              </el-table-column>
              <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { useExecutionStore } from '../stores/execution'
import { useProjectStore } from '../stores/project'
import { useTestCaseStore } from '../stores/testCase'
import { useEnvironmentStore } from '../stores/environment'
import type { ExecutionCreate } from '../types/execution'
import type { ExecutionDetail } from '../types/execution'

// Store
const executionStore = useExecutionStore()
const projectStore = useProjectStore()
const testCaseStore = useTestCaseStore()
const environmentStore = useEnvironmentStore()

// 响应式数据
const currentPage = ref(1)
const pageSize = ref(20)
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const activeTab = ref('basic')
const submitting = ref(false)
const refreshing = ref(false)
const createFormRef = ref()

// 当前执行详情
const currentExecution = ref<ExecutionDetail | null>(null)

// 表单数据
const createForm = reactive<ExecutionCreate>({
  name: '',
  description: '',
  project: 0,
  environment: undefined,
  test_cases: []
})

// 可用的测试用例（用于穿梭框）
const availableTestCases = ref<Array<{ key: number; label: string; disabled: boolean }>>([])

// 过滤后的环境列表
const filteredEnvironments = computed(() => {
  if (!createForm.project) return []
  return environmentStore.environments.filter(env => env.project === createForm.project)
})

// 表单验证规则
const createFormRules = {
  name: [
    { required: true, message: '请输入执行名称', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  test_cases: [
    { required: true, message: '请选择至少一个测试用例', trigger: 'change' }
  ]
}

// 方法
const fetchExecutions = () => {
  executionStore.fetchExecutions({
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const fetchProjects = () => {
  projectStore.fetchProjects()
}

const fetchEnvironments = () => {
  environmentStore.fetchEnvironments()
}

const fetchTestCases = () => {
  testCaseStore.fetchTestCases()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchExecutions()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchExecutions()
}

const refreshData = async () => {
  refreshing.value = true
  try {
    await fetchExecutions()
    await executionStore.refreshRunningExecutions()
    ElMessage.success('数据已刷新')
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    refreshing.value = false
  }
}

const showCreateDialog = () => {
  resetCreateForm()
  createDialogVisible.value = true
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    name: '',
    description: '',
    project: 0,
    environment: undefined,
    test_cases: []
  })
  availableTestCases.value = []
  if (createFormRef.value) {
    createFormRef.value.resetFields()
  }
}

const onProjectChange = (projectId: number) => {
  createForm.environment = undefined
  createForm.test_cases = []
  loadAvailableTestCases(projectId)
}

const loadAvailableTestCases = (projectId: number) => {
  const testCases = testCaseStore.testCases.filter(tc => tc.project === projectId)
  availableTestCases.value = testCases.map(tc => ({
    key: tc.id,
    label: `${tc.name} (${tc.method} ${tc.url})`,
    disabled: false
  }))
}

const onTestCaseChange = (value: number[]) => {
  createForm.test_cases = value
}

const handleCreateExecution = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    submitting.value = true

    const execution = await executionStore.createExecution(createForm)
    createDialogVisible.value = false
    fetchExecutions()

    // 自动执行测试
    await executeTest(execution.id)
  } catch (error) {
    console.error('创建执行失败:', error)
  } finally {
    submitting.value = false
  }
}

const viewExecution = async (execution: any) => {
  try {
    const details = await executionStore.fetchExecution(execution.id)
    currentExecution.value = details
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取执行详情失败:', error)
  }
}

const executeTest = async (id: number) => {
  try {
    await executionStore.executeTest(id)
    ElMessage.success('测试执行已开始')
    fetchExecutions()
  } catch (error) {
    console.error('执行测试失败:', error)
  }
}

const cancelExecution = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消正在执行的测试吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await executionStore.cancelExecution(id)
    fetchExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消执行失败:', error)
    }
  }
}

const deleteExecution = async (execution: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除执行 "${execution.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await executionStore.deleteExecution(execution.id)
    fetchExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除执行失败:', error)
    }
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'PENDING': 'info',
    'RUNNING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'danger',
    'CANCELLED': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'PENDING': '待执行',
    'RUNNING': '执行中',
    'COMPLETED': '已完成',
    'FAILED': '执行失败',
    'CANCELLED': '已取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

// 自动刷新正在运行的执行
let refreshTimer: number | null = null

const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    if (executionStore.runningExecutions.length > 0) {
      executionStore.refreshRunningExecutions()
    }
  }, 5000) // 每5秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(() => {
  fetchExecutions()
  fetchProjects()
  fetchEnvironments()
  fetchTestCases()
  startAutoRefresh()
})

// 监听运行中的执行数量变化
watch(() => executionStore.runningExecutions.length, (newVal, oldVal) => {
  if (newVal > 0 && oldVal === 0) {
    startAutoRefresh()
  } else if (newVal === 0 && oldVal > 0) {
    stopAutoRefresh()
  }
})
</script>

<style scoped>
.test-executor {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.result-summary {
  font-family: monospace;
}

.result-summary .passed {
  color: #67c23a;
}

.result-summary .total {
  color: #666;
}

.result-summary .failed {
  color: #f56c6c;
}
</style>