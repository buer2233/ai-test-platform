<!--
  TestCaseDetail.vue - 接口详情页面

  展示和编辑单个 API 接口的完整配置，包含两个主要选项卡：
  1. 用例配置：
     - 基本信息：名称、请求方法、所属项目/集合、URL、描述
     - 请求配置：Headers、Query 参数、请求体（JSON/Form/Raw 三种模式）
     - 断言配置：通过 AssertionConfig 组件管理断言规则
     - 变量提取：通过 VariableExtraction 组件管理提取规则
  2. 执行记录：通过 TestCaseExecutionRecords 展示历史执行记录

  操作功能：编辑/保存、执行测试、克隆用例、删除用例
  保存时会同步更新断言和变量提取配置（先删除旧配置再创建新配置）
-->
<template>
  <div class="testcase-detail-container">
    <div class="page-header">
      <el-button type="primary" link @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1 class="page-title">接口详情</h1>
      <div class="header-actions">
        <el-button v-if="!isEditing" type="primary" @click="startEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button v-if="isEditing" @click="cancelEdit">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button v-if="isEditing" type="success" @click="saveTestCase" :loading="saving">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
        <el-button v-if="!isEditing" type="success" @click="handleShowExecution">
          <el-icon><VideoPlay /></el-icon>
          执行测试
        </el-button>
        <el-dropdown trigger="click">
          <el-button>
            更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="cloneTestCase">
                <el-icon><CopyDocument /></el-icon>
                克隆用例
              </el-dropdown-item>
              <el-dropdown-item @click="deleteTestCase" divided>
                <el-icon><Delete /></el-icon>
                删除用例
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <!-- 用例配置选项卡 -->
      <el-tab-pane label="用例配置" name="config">
        <el-row :gutter="24">
          <!-- 基本信息 -->
          <el-col :span="24">
            <el-card class="detail-card">
              <template #header>
                <span class="card-header">
                  <el-icon><Document /></el-icon>
                  基本信息
                </span>
              </template>

              <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px" v-if="testCase">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="用例名称" prop="name">
                      <el-input v-model="formData.name" :disabled="!isEditing" placeholder="请输入用例名称" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="请求方法" prop="method">
                      <el-select v-model="formData.method" :disabled="!isEditing" placeholder="请选择请求方法" style="width: 100%">
                        <el-option label="GET" value="GET" />
                        <el-option label="POST" value="POST" />
                        <el-option label="PUT" value="PUT" />
                        <el-option label="PATCH" value="PATCH" />
                        <el-option label="DELETE" value="DELETE" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="所属项目">
                      <el-input :value="testCase?.project_name || ''" disabled />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="所属集合">
                      <el-input :value="testCase?.collection_name || ''" disabled />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="请求URL" prop="url">
                  <el-input v-model="formData.url" :disabled="!isEditing" placeholder="请输入请求URL" />
                </el-form-item>

                <el-form-item label="用例描述">
                  <el-input
                    v-model="formData.description"
                    :disabled="!isEditing"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入用例描述"
                  />
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <!-- 请求配置 -->
          <el-col :span="24" v-if="testCase">
            <el-card class="detail-card">
              <template #header>
                <span class="card-header">
                  <el-icon><Setting /></el-icon>
                  请求配置
                </span>
              </template>

              <el-tabs v-model="activeRequestTab">
            <el-tab-pane label="Headers" name="headers">
              <KeyValueEditor
                v-model="formData.headers"
                :disabled="!isEditing"
                placeholder-key="Header名称"
                placeholder-value="Header值"
              />
            </el-tab-pane>

            <el-tab-pane label="Query参数" name="params">
              <KeyValueEditor
                v-model="formData.params"
                :disabled="!isEditing"
                placeholder-key="参数名称"
                placeholder-value="参数值"
              />
            </el-tab-pane>

            <el-tab-pane label="请求体" name="body" v-if="['POST', 'PUT', 'PATCH'].includes(formData.method)">
              <el-form-item label="Body类型">
                <el-radio-group v-model="bodyType" :disabled="!isEditing">
                  <el-radio label="json">JSON</el-radio>
                  <el-radio label="form">Form Data</el-radio>
                  <el-radio label="raw">Raw</el-radio>
                </el-radio-group>
              </el-form-item>

              <div v-if="bodyType === 'json'">
                <el-input
                  v-model="jsonBody"
                  type="textarea"
                  :rows="10"
                  :disabled="!isEditing"
                  placeholder='{"key": "value"}'
                  @blur="validateJsonBody"
                />
              </div>

              <KeyValueEditor
                v-else-if="bodyType === 'form'"
                v-model="formData.body"
                :disabled="!isEditing"
                placeholder-key="参数名称"
                placeholder-value="参数值"
              />

              <el-input
                v-else
                v-model="rawBody"
                type="textarea"
                :rows="10"
                :disabled="!isEditing"
                placeholder="请输入原始请求体"
              />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 断言配置 -->
      <el-col :span="24" v-if="testCase">
        <el-card class="detail-card">
          <template #header>
            <span class="card-header">
              <el-icon><Check /></el-icon>
              断言配置
            </span>
          </template>

          <AssertionConfig v-model="testCase.assertions" :disabled="!isEditing" />
        </el-card>
      </el-col>

      <!-- 变量提取 -->
      <el-col :span="24" v-if="testCase">
        <el-card class="detail-card">
          <template #header>
            <span class="card-header">
              <el-icon><Download /></el-icon>
              变量提取
            </span>
          </template>

          <VariableExtraction v-model="testCase.extractions" :disabled="!isEditing" />
        </el-card>
      </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 执行记录选项卡 -->
      <el-tab-pane label="执行记录" name="records">
        <TestCaseExecutionRecords
          v-if="testCase"
          :test-case-id="testCase.id"
          ref="executionRecordsRef"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 测试执行器（通过ref控制） -->
    <TestCaseRunner
      v-if="testCase"
      :test-case="testCase"
      :show-button="false"
      ref="testCaseRunnerRef"
      @execution-completed="handleExecutionCompleted"
      @execution-error="handleExecutionError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Edit, Check, Close, VideoPlay, ArrowDown,
  CopyDocument, Delete, Document, Setting, Check as CheckIcon, Download
} from '@element-plus/icons-vue'

import { testCaseApi } from '../../api/testCase'
import { environmentApi } from '../../api/environment'
import { assertionApi, extractionApi } from '../../api'
import KeyValueEditor from '../../components/HttpExecutor/KeyValueEditor.vue'
import AssertionConfig from '../../components/AssertionConfig.vue'
import VariableExtraction from '../../components/VariableExtraction.vue'
import TestCaseRunner from '../../components/TestCaseRunner.vue'
import TestCaseExecutionRecords from '../../components/TestCaseExecutionRecords.vue'

import type { ApiTestCase, ApiTestCaseCreate } from '../../types/testCase'

const router = useRouter()
const route = useRoute()

// 数据状态
const testCase = ref<ApiTestCase | null>(null)
const loading = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const showExecutionDialog = ref(false)
const environments = ref([])

// 表单数据
const formRef = ref()
const formData = reactive<ApiTestCaseCreate>({
  name: '',
  description: '',
  project: 0,
  collection: null,
  method: 'GET',
  url: '',
  headers: {},
  params: {},
  body: {}
})

const bodyType = ref('json')
const jsonBody = ref('{}')
const rawBody = ref('')
const activeRequestTab = ref('headers')
const activeTab = ref('config')
const executionRecordsRef = ref()
const testCaseRunnerRef = ref()

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入请求URL', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (!value) {
          callback(new Error('请输入请求URL'))
          return
        }
        // 允许相对路径（以 / 开头）和完整 URL
        if (!value.startsWith('/')) {
          // 如果不是相对路径，检查是否是有效的完整 URL
          try {
            new URL(value)
          } catch {
            callback(new Error('请输入有效的URL地址（以 / 开头的相对路径或完整 URL）'))
            return
          }
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const pageTitle = computed(() => {
  return testCase.value ? `接口详情 - ${testCase.value.name}` : '接口详情'
})

// 生命周期
onMounted(() => {
  loadTestCase()
  loadEnvironments()
})

// 方法
const loadTestCase = async () => {
  const id = Number(route.params.id)
  if (!id) {
    ElMessage.error('无效的接口ID')
    router.back()
    return
  }

  try {
    loading.value = true
    const response = await testCaseApi.getTestCase(id)

    // 由于HTTP拦截器已经返回了data，response就是实际的接口数据
    if (!response) {
      throw new Error('接口数据不存在')
    }

    testCase.value = response

    // 初始化表单数据
    Object.assign(formData, {
      name: testCase.value.name || '',
      description: testCase.value.description || '',
      project: testCase.value.project || 0,
      collection: testCase.value.collection || null,
      method: testCase.value.method || 'GET',
      url: testCase.value.url || '',
      headers: testCase.value.headers || {},
      params: testCase.value.params || {},
      body: testCase.value.body || {}
    })

    // 初始化请求体
    if (['POST', 'PUT', 'PATCH'].includes(testCase.value.method)) {
      if (typeof testCase.value.body === 'object' && testCase.value.body !== null) {
        jsonBody.value = JSON.stringify(testCase.value.body, null, 2)
        bodyType.value = 'json'
      } else {
        rawBody.value = String(testCase.value.body || '')
        bodyType.value = 'raw'
      }
    }

    // 额外加载断言和提取配置（后端API不直接返回这些字段）
    await loadAssertionsAndExtractions(id)

  } catch (error) {
    ElMessage.error('加载接口详情失败')
    console.error('Load test case error:', error)
  } finally {
    loading.value = false
  }
}

// 加载断言和提取配置
const loadAssertionsAndExtractions = async (testCaseId: number) => {
  try {
    // 加载断言配置
    const assertionsResponse = await assertionApi.getAssertions(testCaseId)
    if (testCase.value) {
      testCase.value.assertions = assertionsResponse.results || assertionsResponse || []
    }

    // 加载提取配置
    const extractionsResponse = await extractionApi.getExtractions(testCaseId)
    if (testCase.value) {
      testCase.value.extractions = extractionsResponse.results || extractionsResponse || []
    }
  } catch (error) {
    console.error('Failed to load assertions and extractions:', error)
  }
}

const loadEnvironments = async () => {
  try {
    const response = await environmentApi.getEnvironments()

    // 由于HTTP拦截器已经返回了data，response就是实际的响应数据
    if (!response || !response.results) {
      environments.value = []
      return
    }

    environments.value = response.results
  } catch (error) {
    console.error('Load environments error:', error)
    environments.value = []
  }
}

const startEdit = () => {
  isEditing.value = true
  // 备份原始数据
  Object.assign(formData, {
    name: testCase.value!.name,
    description: testCase.value!.description || '',
    method: testCase.value!.method,
    url: testCase.value!.url,
    headers: testCase.value!.headers || {},
    params: testCase.value!.params || {},
    body: testCase.value!.body || {}
  })
}

const cancelEdit = () => {
  isEditing.value = false
  // 恢复原始数据
  if (testCase.value) {
    Object.assign(formData, {
      name: testCase.value.name,
      description: testCase.value.description || '',
      method: testCase.value.method,
      url: testCase.value.url,
      headers: testCase.value.headers || {},
      params: testCase.value.params || {},
      body: testCase.value.body || {}
    })
  }
}

const saveTestCase = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    saving.value = true

    // 处理请求体
    let bodyToSave = formData.body
    if (['POST', 'PUT', 'PATCH'].includes(formData.method)) {
      if (bodyType.value === 'json') {
        try {
          bodyToSave = JSON.parse(jsonBody.value)
        } catch (error) {
          ElMessage.error('JSON格式错误，请检查')
          return
        }
      } else if (bodyType.value === 'raw') {
        bodyToSave = rawBody.value
      }
    }

    // 将 headers/params 从数组格式转换为字典格式（如果是数组）
    const formatToDict = (data: any): any => {
      if (Array.isArray(data)) {
        const result: Record<string, string> = {}
        data.forEach((item: any) => {
          if (item.enabled !== false && item.key) {
            result[item.key] = item.value || ''
          }
        })
        return result
      }
      return data
    }

    const updateData = {
      name: formData.name,
      description: formData.description,
      method: formData.method,
      url: formData.url,
      project: formData.project,
      collection: formData.collection,
      headers: formatToDict(formData.headers),
      params: formatToDict(formData.params),
      body: bodyToSave
    }

    await testCaseApi.updateTestCase(testCase.value!.id, updateData)

    // 保存断言配置和变量提取配置
    await saveAssertionsAndExtractions()

    // 重新加载数据
    await loadTestCase()

    isEditing.value = false
    ElMessage.success('保存成功')

  } catch (error) {
    ElMessage.error('保存失败')
    console.error('Save test case error:', error)
  } finally {
    saving.value = false
  }
}

// 保存断言配置和变量提取配置
const saveAssertionsAndExtractions = async () => {
  if (!testCase.value) return

  const testCaseId = testCase.value.id

  // 删除现有的断言和提取
  try {
    // 获取现有列表
    const existingAssertions = await assertionApi.getAssertions(testCaseId)
    const existingExtractions = await extractionApi.getExtractions(testCaseId)

    // 删除现有配置
    const assertionsList = existingAssertions.results || existingAssertions || []
    const extractionsList = existingExtractions.results || existingExtractions || []

    for (const item of assertionsList) {
      await assertionApi.deleteAssertion(testCaseId, item.id)
    }
    for (const item of extractionsList) {
      await extractionApi.deleteExtraction(testCaseId, item.id)
    }
  } catch (error) {
    console.error('Failed to delete old configs:', error)
  }

  // 保存新的断言配置
  if (testCase.value.assertions && testCase.value.assertions.length > 0) {
    for (const assertion of testCase.value.assertions) {
      try {
        const { id, test_case, ...assertionData } = assertion as any
        await assertionApi.createAssertion(testCaseId, assertionData)
      } catch (error) {
        console.error('Failed to save assertion:', error)
      }
    }
  }

  // 保存新的提取配置
  if (testCase.value.extractions && testCase.value.extractions.length > 0) {
    for (const extraction of testCase.value.extractions) {
      try {
        const { id, test_case, ...extractionData } = extraction as any
        await extractionApi.createExtraction(testCaseId, extractionData)
      } catch (error) {
        console.error('Failed to save extraction:', error)
      }
    }
  }
}

const validateJsonBody = () => {
  if (bodyType.value === 'json') {
    try {
      JSON.parse(jsonBody.value)
    } catch (error) {
      ElMessage.warning('JSON格式不正确')
    }
  }
}

const cloneTestCase = async () => {
  if (!testCase.value) return

  try {
    const { value: name } = await ElMessageBox.prompt(
      '请输入克隆后的接口名称',
      '克隆接口',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${testCase.value.name}_副本`,
        inputValidator: (value) => {
          if (!value) {
            return '接口名称不能为空'
          }
          return true
        }
      }
    )

    await testCaseApi.cloneTestCase(testCase.value.id, { name })
    ElMessage.success('克隆成功')
    router.push('/api-automation/test-cases')

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('克隆失败')
      console.error('Clone test case error:', error)
    }
  }
}

const deleteTestCase = async () => {
  if (!testCase.value) return

  try {
    await ElMessageBox.confirm(
      `确定要删除接口"${testCase.value.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await testCaseApi.deleteTestCase(testCase.value.id)
    ElMessage.success('删除成功')
    router.push('/api-automation/test-cases')

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete test case error:', error)
    }
  }
}

const handleShowExecution = () => {
  if (testCaseRunnerRef.value?.showRunDialog) {
    testCaseRunnerRef.value.showRunDialog()
  }
}

const handleExecutionCompleted = (result: any) => {
  ElMessage.success('测试执行完成')
  // 刷新执行记录
  if (executionRecordsRef.value?.refresh) {
    executionRecordsRef.value.refresh()
    // 切换到执行记录选项卡
    activeTab.value = 'records'
  }
}

const handleExecutionError = (error: any) => {
  ElMessage.error('测试执行失败')
  console.error('Execution error:', error)
}
</script>

<style scoped>
.testcase-detail-container {
  padding: 20px;
}

.detail-tabs {
  background-color: #fff;
  padding: 0;
}

.detail-tabs :deep(.el-tabs__header) {
  margin: 0 0 20px 0;
}

.detail-tabs :deep(.el-tabs__content) {
  overflow: visible;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

:deep(.el-tabs__header) {
  margin: 0 0 16px 0;
}

:deep(.el-tabs__content) {
  min-height: 200px;
}

:deep(.el-card__header) {
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}
</style>