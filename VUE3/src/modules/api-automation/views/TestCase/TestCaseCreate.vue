<template>
  <div class="testcase-create-container">
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? '编辑接口' : '创建接口' }}</h1>
      <p class="page-description">{{ isEdit ? '使用增强编辑器修改接口配置' : '使用增强编辑器创建新接口' }}</p>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="testcase-form"
    >
      <!-- 基本信息 -->
      <el-card class="mb-20">
        <template #header>
          <span><el-icon><InfoFilled /></el-icon> 基本信息</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="接口名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入接口名称">
                <template #prepend>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属项目" prop="project">
              <el-select
                v-model="form.project"
                placeholder="请选择项目"
                style="width: 100%"
                @change="handleProjectChange"
              >
                <el-option
                  v-for="project in projectOptions"
                  :key="project.value"
                  :label="project.label"
                  :value="project.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属集合">
              <el-select
                v-model="form.collection"
                placeholder="请选择集合（可选）"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="collection in collectionOptions"
                  :key="collection.value"
                  :label="collection.label"
                  :value="collection.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用例标签">
              <el-select
                v-model="form.tags"
                multiple
                filterable
                allow-create
                placeholder="选择或创建标签"
                style="width: 100%"
              >
                <el-option
                  v-for="tag in commonTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="用例描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入接口描述，说明接口功能"
          />
        </el-form-item>
      </el-card>

      <!-- 增强的请求编辑器 -->
      <el-card class="mb-20">
        <template #header>
          <span><el-icon><Edit /></el-icon> 请求配置</span>
        </template>

        <TestCaseEditor
          v-model="requestConfig"
          :environment-options="environmentOptionsWithBaseUrl"
          @test="handleTestResult"
        />
      </el-card>

      <!-- 断言配置 -->
      <el-card class="mb-20">
        <template #header>
          <span><el-icon><Select /></el-icon> 断言配置</span>
        </template>
        <AssertionConfig v-model="assertions" />
      </el-card>

      <!-- 数据提取配置 -->
      <el-card class="mb-20">
        <template #header>
          <span><el-icon><Download /></el-icon> 数据提取配置</span>
        </template>
        <VariableExtraction v-model="extractions" />
      </el-card>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button @click="handleCancel">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          <el-icon><Check /></el-icon>
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  InfoFilled, Document, Edit, Select, Download, Check, Close
} from '@element-plus/icons-vue'
import { useTestCaseStore, useProjectStore, useCollectionStore, useEnvironmentStore } from '../../stores'
import type { ApiTestCaseCreate } from '../../types/testCase'
import TestCaseEditor from '../../components/TestCaseEditor.vue'
import AssertionConfig from '../../components/AssertionConfig.vue'
import VariableExtraction from '../../components/VariableExtraction.vue'
import { assertionApi } from '../../api/assertion'
import { extractionApi } from '../../api/extraction'
import type { TestCaseAssertion, TestCaseExtraction } from '../../types/testCase'

const router = useRouter()
const route = useRoute()
const testCaseStore = useTestCaseStore()
const projectStore = useProjectStore()
const collectionStore = useCollectionStore()
const environmentStore = useEnvironmentStore()

// 表单引用
const formRef = ref<FormInstance>()

// 加载状态
const submitting = ref(false)

// 是否编辑模式
const isEdit = computed(() => !!route.params.id)

// 项目和集合选项
const projectOptions = computed(() => projectStore.projectOptions)
const collectionOptions = ref<Array<{ label: string; value: number }>>([])

// 环境选项（带base_url）
const environmentOptionsWithBaseUrl = computed(() =>
  environmentStore.environments.map(e => ({
    label: e.name,
    value: e.id,
    base_url: e.base_url
  }))
)

// 常用标签
const commonTags = ['冒烟测试', '回归测试', '接口测试', '性能测试', '安全测试', '验收测试']

// 表单数据
const form = reactive<ApiTestCaseCreate & { tags?: string[] }>({
  name: '',
  description: '',
  project: 0,
  collection: null,
  tags: []
})

// 请求配置（传递给TestCaseEditor）
const requestConfig = ref({
  method: 'GET',
  url: '',
  headers: {},
  params: {},
  body: {}
})

// 断言配置数据
const assertions = ref<TestCaseAssertion[]>([])

// 数据提取配置数据
const extractions = ref<TestCaseExtraction[]>([])

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入接口名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ]
}

// 项目改变时更新集合选项
const handleProjectChange = async () => {
  form.collection = null
  if (form.project) {
    await loadCollections(form.project)
  }
}

// 加载集合列表
const loadCollections = async (projectId: number) => {
  try {
    await collectionStore.fetchCollections({ project: projectId, page_size: 1000 })
    collectionOptions.value = collectionStore.collections.map(c => ({
      label: c.name,
      value: c.id
    }))
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
}

// 加载项目列表
const loadProjects = async () => {
  try {
    await projectStore.fetchProjects({ page_size: 1000 })
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  try {
    await environmentStore.fetchEnvironments({ page_size: 1000 })
  } catch (error) {
    console.error('Failed to load environments:', error)
  }
}

// 处理测试结果
const handleTestResult = (result: any) => {
  console.log('Test result:', result)
  // 可以在这里添加结果处理逻辑
}

// 取消操作
const handleCancel = () => {
  router.back()
}

// 将 headers/params 从数组格式转换为字典格式
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

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // 从requestConfig构建表单数据
    const submitData: ApiTestCaseCreate = {
      name: form.name,
      description: form.description,
      project: form.project,
      collection: form.collection,
      method: requestConfig.value.method,
      url: requestConfig.value.url,
      headers: formatToDict(requestConfig.value.headers),
      params: formatToDict(requestConfig.value.params),
      body: requestConfig.value.body || {}
    }

    let testCaseId: number

    if (isEdit.value) {
      await testCaseStore.updateTestCase(Number(route.params.id), submitData)
      testCaseId = Number(route.params.id)
      ElMessage.success('更新成功')
    } else {
      const testCase = await testCaseStore.createTestCase(submitData)
      testCaseId = testCase.id
      ElMessage.success('创建成功')
    }

    // 保存断言配置
    if (assertions.value.length > 0) {
      try {
        for (const assertion of assertions.value) {
          // 移除id字段，让后端自动生成；设置正确的test_case
          const { id, ...assertionData } = assertion
          await assertionApi.createAssertion(testCaseId, {
            ...assertionData,
            test_case: testCaseId
          })
        }
      } catch (error) {
        console.error('Failed to save assertions:', error)
      }
    }

    // 保存数据提取配置
    if (extractions.value.length > 0) {
      try {
        for (const extraction of extractions.value) {
          // 移除id字段，让后端自动生成；设置正确的test_case
          const { id, ...extractionData } = extraction
          await extractionApi.createExtraction(testCaseId, {
            ...extractionData,
            test_case: testCaseId
          })
        }
      } catch (error) {
        console.error('Failed to save extractions:', error)
      }
    }

    router.push('/test-cases')
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 加载断言配置
const loadAssertions = async (testCaseId: number) => {
  try {
    const response = await assertionApi.getAssertions(testCaseId)
    assertions.value = response.results || response
  } catch (error) {
    console.error('Failed to load assertions:', error)
  }
}

// 加载数据提取配置
const loadExtractions = async (testCaseId: number) => {
  try {
    const response = await extractionApi.getExtractions(testCaseId)
    extractions.value = response.results || response
  } catch (error) {
    console.error('Failed to load extractions:', error)
  }
}

// 加载接口数据
const loadTestCase = async () => {
  if (!isEdit.value) return

  try {
    const testCase = await testCaseStore.fetchTestCase(Number(route.params.id))

    // 填充表单
    form.name = testCase.name
    form.description = testCase.description || ''
    form.project = testCase.project
    form.collection = testCase.collection
    form.tags = testCase.tags || []

    // 填充请求配置
    requestConfig.value = {
      method: testCase.method,
      url: testCase.url,
      headers: testCase.headers || {},
      params: testCase.params || {},
      body: testCase.body || {}
    }

    // 加载集合选项
    await loadCollections(testCase.project)

    // 加载断言配置
    await loadAssertions(Number(route.params.id))

    // 加载数据提取配置
    await loadExtractions(Number(route.params.id))
  } catch (error) {
    ElMessage.error('加载接口失败')
    router.push('/test-cases')
  }
}

// 监听项目选项变化
watch(projectOptions, (newOptions) => {
  if (newOptions.length > 0 && !form.project && !isEdit.value) {
    form.project = newOptions[0].value
    loadCollections(form.project)
  }
})

// 组件挂载时执行
onMounted(async () => {
  await loadProjects()
  await loadEnvironments()
  if (isEdit.value) {
    await loadTestCase()
  }
})
</script>

<style scoped>
.testcase-create-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.testcase-form {
  width: 100%;
}

.mb-20 {
  margin-bottom: 20px;
}

.form-actions {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.form-actions .el-button {
  margin: 0 10px;
  min-width: 120px;
}

/* 卡片头部样式 */
:deep(.el-card__header) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
  background-color: #fafafa;
}

/* 表单项样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

/* 输入框样式 */
:deep(.el-input__wrapper) {
  transition: all 0.3s;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

/* 标签选择器样式 */
:deep(.el-select__tags) {
  max-width: 100%;
}
</style>