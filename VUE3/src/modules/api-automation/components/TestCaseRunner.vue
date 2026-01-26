<template>
  <div class="test-case-runner">
    <!-- 执行按钮 (可选显示) -->
    <el-button
      v-if="showButton"
      type="primary"
      size="small"
      @click="showRunDialog"
      :loading="running"
    >
      <el-icon><VideoPlay /></el-icon>
      执行测试
    </el-button>

    <!-- 执行对话框 -->
    <el-dialog
      title="执行测试用例"
      v-model="dialogVisible"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      append-to-body
      destroy-on-close
      :z-index="2000"
      :modal="true"
      :lock-scroll="true"
    >
      <div v-if="testCase">
        <!-- 测试用例信息 -->
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>测试用例信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用例名称">{{ testCase.name }}</el-descriptions-item>
            <el-descriptions-item label="请求方法">
              <el-tag :type="getMethodTagType(testCase.method)" size="small">
                {{ testCase.method }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="请求URL" :span="2">{{ testCase.url }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ testCase.project_name }}</el-descriptions-item>
            <el-descriptions-item label="集合名称">{{ testCase.collection_name || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 环境选择 -->
        <el-card class="mb-4" v-if="!executionResult">
          <template #header>
            <div class="card-header">
              <span>执行环境</span>
            </div>
          </template>

          <!-- 环境列表为空时显示提示 -->
          <el-alert
            v-if="!loadingEnvironments && availableEnvironments.length === 0"
            title="该项目暂无测试环境"
            type="warning"
            :closable="false"
            show-icon
            class="mb-3"
          >
            <template #default>
              <p>请先为该项目配置测试环境后再执行测试用例。</p>
              <el-button type="primary" link @click="goToEnvironmentPage">
                <el-icon><Setting /></el-icon>
                前往创建测试环境
              </el-button>
            </template>
          </el-alert>

          <!-- 加载中提示 -->
          <el-alert
            v-if="loadingEnvironments"
            title="正在加载测试环境..."
            type="info"
            :closable="false"
            show-icon
            class="mb-3"
          />

          <el-form :model="runForm" :rules="formRules" ref="formRef" label-width="100px">
            <el-form-item label="测试环境" prop="environment_id">
              <el-select
                v-model="runForm.environment_id"
                placeholder="请选择测试环境"
                style="width: 100%"
                :disabled="running || loadingEnvironments"
                :loading="loadingEnvironments"
              >
                <el-option
                  v-for="env in availableEnvironments"
                  :key="env.id"
                  :label="`${env.name} (${env.base_url})`"
                  :value="env.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                @click="executeTest"
                :loading="running"
                :disabled="!runForm.environment_id || loadingEnvironments"
              >
                <el-icon><VideoPlay /></el-icon>
                开始执行
              </el-button>
              <el-button @click="dialogVisible = false" :disabled="running">
                取消
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 执行结果 -->
        <div v-if="executionResult">
          <!-- 执行状态 -->
          <el-card class="mb-4">
            <template #header>
              <div class="card-header">
                <span>执行结果</span>
                <el-tag
                  :type="getStatusType(executionResult.status)"
                  size="large"
                  class="ml-2"
                >
                  {{ getStatusText(executionResult.status) }}
                </el-tag>
                <div class="header-actions">
                  <el-button size="small" @click="clearResults">
                    <el-icon><Refresh /></el-icon>
                    重新执行
                  </el-button>
                </div>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="执行时间" :value="executionResult.duration" suffix="ms" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="断言通过" :value="executionResult.assertions_passed ? '是' : '否'" />
              </el-col>
              <el-col :span="8">
                <el-statistic
                  title="响应时间"
                  :value="executionResult.response.response_time"
                  suffix="ms"
                />
              </el-col>
            </el-row>

            <el-alert
              v-if="executionResult.error_message"
              :title="executionResult.error_message"
              type="error"
              show-icon
              class="mt-3"
            />
          </el-card>

          <!-- 请求详情 -->
          <el-card class="mb-4">
            <template #header>
              <div class="card-header">
                <span>请求详情</span>
              </div>
            </template>
            <el-tabs v-model="requestActiveTab">
              <el-tab-pane label="基本信息" name="basic">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="请求URL">{{ executionResult.request.url }}</el-descriptions-item>
                  <el-descriptions-item label="请求方法">
                    <el-tag :type="getMethodTagType(executionResult.request.method)" size="small">
                      {{ executionResult.request.method }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="环境">
                    {{ executionResult.environment.name }} ({{ executionResult.environment.base_url }})
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              <el-tab-pane label="请求头" name="headers">
                <pre class="json-preview">{{ formatJson(executionResult.request.headers) }}</pre>
              </el-tab-pane>
              <el-tab-pane label="请求参数" name="params">
                <pre class="json-preview">{{ formatJson(executionResult.request.params) }}</pre>
              </el-tab-pane>
              <el-tab-pane label="请求体" name="body">
                <pre class="json-preview">{{ formatJson(executionResult.request.body) }}</pre>
              </el-tab-pane>
            </el-tabs>
          </el-card>

          <!-- 响应详情 -->
          <el-card class="mb-4">
            <template #header>
              <div class="card-header">
                <span>响应详情</span>
                <el-tag
                  :type="executionResult.response.status_code >= 200 && executionResult.response.status_code < 300 ? 'success' : 'danger'"
                  size="small"
                  class="ml-2"
                >
                  {{ executionResult.response.status_code }}
                </el-tag>
              </div>
            </template>
            <el-tabs v-model="responseActiveTab">
              <el-tab-pane label="基本信息" name="basic">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="状态码">{{ executionResult.response.status_code }}</el-descriptions-item>
                  <el-descriptions-item label="响应时间">{{ executionResult.response.response_time }}ms</el-descriptions-item>
                  <el-descriptions-item label="响应大小">{{ executionResult.response.size }} bytes</el-descriptions-item>
                  <el-descriptions-item label="响应时间戳">{{ formatDateTime(executionResult.start_time) }}</el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              <el-tab-pane label="响应头" name="headers">
                <pre class="json-preview">{{ formatJson(executionResult.response.headers) }}</pre>
              </el-tab-pane>
              <el-tab-pane label="响应体" name="body">
                <pre class="json-preview">{{ formatJson(executionResult.response.body) }}</pre>
              </el-tab-pane>
            </el-tabs>
          </el-card>

          <!-- 断言结果 -->
          <el-card>
            <template #header>
              <div class="card-header">
                <span>断言结果</span>
                <el-tag
                  :type="executionResult.assertions_passed ? 'success' : 'danger'"
                  size="small"
                  class="ml-2"
                >
                  {{ executionResult.assertions_passed ? '全部通过' : '存在失败' }}
                </el-tag>
              </div>
            </template>
            <el-table :data="executionResult.assertions" stripe>
              <el-table-column prop="type" label="断言类型" width="120">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="expected" label="期望值" width="150">
                <template #default="{ row }">
                  <code class="expect-value">{{ formatValue(row.expected) }}</code>
                </template>
              </el-table-column>
              <el-table-column prop="actual" label="实际值" width="150">
                <template #default="{ row }">
                  <code class="actual-value">{{ formatValue(row.actual) }}</code>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="断言消息" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-icon v-if="row.passed" color="#67c23a"><CircleCheck /></el-icon>
                  <el-icon v-else color="#f56c6c"><CircleClose /></el-icon>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Refresh, CircleCheck, CircleClose, Setting } from '@element-plus/icons-vue'
import { testCaseApi } from '../api/testCase'
import { environmentApi } from '../api/environment'
import type { ApiTestCase, TestCaseExecution } from '../types/testCase'

const router = useRouter()

// Props
interface Props {
  testCase: ApiTestCase
  showButton?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  showButton: true
})

// 响应式数据
const dialogVisible = ref(false)
const running = ref(false)
const loadingEnvironments = ref(false)
const executionResult = ref<TestCaseExecution | null>(null)
const requestActiveTab = ref('basic')
const responseActiveTab = ref('basic')
const formRef = ref()

// 表单数据
const runForm = reactive({
  environment_id: null as number | null
})

// 可用的环境列表
const availableEnvironments = ref<any[]>([])

// 表单验证规则
const formRules = {
  environment_id: [
    { required: true, message: '请选择测试环境', trigger: 'change' }
  ]
}

// 计算属性
const showRunDialog = () => {
  dialogVisible.value = true
  executionResult.value = null
  loadEnvironments()
}

// 方法
const loadEnvironments = async () => {
  loadingEnvironments.value = true
  try {
    console.log('Loading environments for project:', props.testCase.project)
    const response = await environmentApi.getEnvironments({ project: props.testCase.project })
    console.log('Environment response:', response)

    const envList = response.results || response
    availableEnvironments.value = Array.isArray(envList) ? envList : []

    if (availableEnvironments.value.length === 0) {
      console.warn(`No environments found for project ${props.testCase.project}`)
    }
  } catch (error: any) {
    console.error('加载环境列表失败:', error)
    ElMessage.error(error.message || '加载环境列表失败')
    availableEnvironments.value = []
  } finally {
    loadingEnvironments.value = false
  }
}

const goToEnvironmentPage = () => {
  // 跳转到环境管理页面
  router.push({
    path: '/environments',
    query: { projectId: props.testCase.project }
  })
}

const executeTest = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    running.value = true

    const result = await testCaseApi.runTestCase(props.testCase.id, runForm)
    executionResult.value = result

    const statusText = result.assertions_passed ? '测试通过' : '测试失败'
    const messageType = result.assertions_passed ? 'success' : 'warning'
    ElMessage({
      type: messageType,
      message: `测试执行完成: ${statusText}`
    })
  } catch (error: any) {
    console.error('执行测试失败:', error)
    ElMessage.error(error.message || '执行测试失败')
  } finally {
    running.value = false
  }
}

const clearResults = () => {
  executionResult.value = null
  runForm.environment_id = null
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'ERROR': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'PASSED': '通过',
    'FAILED': '失败',
    'ERROR': '错误'
  }
  return statusMap[status] || status
}

const getMethodTagType = (method: string) => {
  const methodMap: Record<string, string> = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'PATCH': 'info',
    'DELETE': 'danger'
  }
  return methodMap[method] || 'info'
}

const formatJson = (obj: any) => {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const formatValue = (value: any) => {
  if (value === null || value === undefined) {
    return 'null'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// 暴露方法给父组件
defineExpose({
  showRunDialog
})
</script>

<style scoped>
.test-case-runner {
  display: inline-block;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.json-preview {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.expect-value {
  background-color: #e7f7ff;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #91d5ff;
}

.actual-value {
  background-color: #f6ffed;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #b7eb8f;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-3 {
  margin-top: 12px;
}

.ml-2 {
  margin-left: 8px;
}
</style>