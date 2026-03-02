<!--
  EnvironmentForm.vue - 环境配置表单组件

  用于创建和编辑测试环境的表单：
  - 基本信息：环境名称、所属项目、描述、Base URL（带协议选择器）
  - 开关选项：默认环境、启用状态
  - 全局请求头配置（使用 KeyValueEditor 组件）
  - 全局变量配置（使用 KeyValueEditor 组件，支持描述字段）
  - 表单验证：名称必填、URL 格式校验
  - 数据格式转换：内部使用数组格式编辑，提交时转为对象格式
-->
<template>
  <div class="environment-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="环境名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入环境名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="所属项目" prop="project">
            <el-select
              v-model="formData.project"
              placeholder="请选择项目"
              style="width: 100%"
            >
              <el-option
                v-for="project in projects"
                :key="project.id"
                :label="project.name"
                :value="project.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="环境描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入环境描述"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="Base URL" prop="base_url">
        <el-input
          v-model="formData.base_url"
          placeholder="请输入Base URL，如：https://api.example.com"
        >
          <template #prepend>
            <el-select
              v-model="urlProtocol"
              style="width: 100px"
              @change="handleProtocolChange"
            >
              <el-option label="http://" value="http://" />
              <el-option label="https://" value="https://" />
            </el-select>
          </template>
        </el-input>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item>
            <el-checkbox v-model="formData.is_default">
              设为默认环境
            </el-checkbox>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item>
            <el-checkbox v-model="formData.is_active">
              启用环境
            </el-checkbox>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider>全局请求头</el-divider>

      <div class="section-content">
        <KeyValueEditor
          v-model="formData._global_headers"
          placeholder-key="Header名称"
          placeholder-value="Header值"
        />
      </div>

      <el-divider>全局变量</el-divider>

      <div class="section-content">
        <KeyValueEditor
          v-model="formData._global_variables"
          placeholder-key="变量名称"
          placeholder-value="变量值"
          :show-description="true"
        />
      </div>

      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import KeyValueEditor from './HttpExecutor/KeyValueEditor.vue'

import type { ApiTestEnvironment, EnvironmentCreate } from '../types/environment'

interface KeyValueItem {
  key: string
  value: string
  enabled?: boolean
  type?: string
  description?: string
}

interface Props {
  environment?: ApiTestEnvironment | null
  projects: Array<{ id: number; name: string }>
}

interface Emits {
  (e: 'submit', data: EnvironmentCreate): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 提交状态
const submitting = ref(false)

// URL协议
const urlProtocol = ref('https://')

// 将对象格式转换为数组格式供 KeyValueEditor 使用
const objectToArray = (obj: Record<string, any>): KeyValueItem[] => {
  if (!obj || typeof obj !== 'object') return []
  return Object.entries(obj).map(([key, value]) => ({
    key,
    value: String(value),
    enabled: true,
    type: 'text',
    description: ''
  }))
}

// 将数组格式转换回对象格式
const arrayToObject = (arr: KeyValueItem[]): Record<string, any> => {
  const obj: Record<string, any> = {}
  arr.forEach(item => {
    if (item.enabled !== false && item.key) {
      obj[item.key] = item.value
    }
  })
  return obj
}

// 表单数据
const formData = reactive<EnvironmentCreate & {
  _global_headers: KeyValueItem[]
  _global_variables: KeyValueItem[]
}>({
  name: '',
  description: '',
  project: undefined,
  base_url: '',
  global_headers: {},
  global_variables: {},
  _global_headers: [],
  _global_variables: [],
  is_default: false,
  is_active: true
})

// 是否为编辑模式
const isEdit = computed(() => !!props.environment)

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' },
    { min: 2, max: 50, message: '环境名称长度在2到50个字符', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  base_url: [
    { required: true, message: '请输入Base URL', trigger: 'blur' },
    {
      type: 'url',
      message: '请输入有效的URL地址',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!value) {
          callback()
          return
        }

        // Combine protocol with value for validation
        const fullUrl = value.startsWith('http://') || value.startsWith('https://')
          ? value
          : urlProtocol.value + value

        try {
          new URL(fullUrl)
          callback()
        } catch {
          callback(new Error('请输入有效的URL地址'))
        }
      }
    }
  ],
  description: [
    { max: 200, message: '描述长度不能超过200个字符', trigger: 'blur' }
  ]
}

// 计算属性
const currentProject = computed(() => {
  // 这里可以从store或其他地方获取当前项目ID
  return null
})

// 监听内部数组变化，更新对象格式
watch(() => formData._global_headers, (newVal) => {
  formData.global_headers = arrayToObject(newVal)
}, { deep: true })

watch(() => formData._global_variables, (newVal) => {
  formData.global_variables = arrayToObject(newVal)
}, { deep: true })

// 监听props变化
watch(() => props.environment, (newEnvironment) => {
  if (newEnvironment) {
    const headersArray = objectToArray(newEnvironment.global_headers)
    const variablesArray = objectToArray(newEnvironment.global_variables)

    Object.assign(formData, {
      name: newEnvironment.name,
      description: newEnvironment.description,
      project: newEnvironment.project,
      base_url: newEnvironment.base_url,
      global_headers: newEnvironment.global_headers || {},
      global_variables: newEnvironment.global_variables || {},
      _global_headers: headersArray,
      _global_variables: variablesArray,
      is_default: newEnvironment.is_default,
      is_active: newEnvironment.is_active
    })

    // 设置URL协议
    if (newEnvironment.base_url.startsWith('http://')) {
      urlProtocol.value = 'http://'
    } else if (newEnvironment.base_url.startsWith('https://')) {
      urlProtocol.value = 'https://'
    } else {
      urlProtocol.value = 'https://'
    }
  } else {
    // 重置表单
    Object.assign(formData, {
      name: '',
      description: '',
      project: currentProject.value || undefined,
      base_url: '',
      global_headers: {},
      global_variables: {},
      _global_headers: [],
      _global_variables: [],
      is_default: false,
      is_active: true
    })
    urlProtocol.value = 'https://'
  }
}, { immediate: true })

// 方法
const handleProtocolChange = () => {
  if (formData.base_url && !formData.base_url.startsWith(urlProtocol.value)) {
    // 移除现有协议前缀
    formData.base_url = formData.base_url.replace(/^https?:\/\//, '')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    // 确保URL包含协议
    if (!formData.base_url.startsWith('http://') && !formData.base_url.startsWith('https://')) {
      formData.base_url = urlProtocol.value + formData.base_url
    }

    submitting.value = true

    // 提交时确保对象格式是最新的
    formData.global_headers = arrayToObject(formData._global_headers)
    formData.global_variables = arrayToObject(formData._global_variables)

    // 提交数据（移除内部数组字段）
    const { _global_headers, _global_variables, ...submitData } = formData
    emit('submit', submitData as EnvironmentCreate)

  } catch (error) {
    console.error('Form validation error:', error)
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.environment-form {
  padding: 0;
}

.section-content {
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-divider) {
  margin: 20px 0;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-input-group__prepend) {
  background-color: #f5f7fa;
}
</style>