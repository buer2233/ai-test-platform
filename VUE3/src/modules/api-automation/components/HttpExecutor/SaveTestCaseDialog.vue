<!--
  SaveTestCaseDialog.vue - 保存为测试用例对话框

  将当前 HTTP 执行器中的请求配置保存为测试用例：
  - 选择所属项目和集合（级联选择）
  - 填写用例名称、请求方法、URL、描述
  - 标签管理（动态添加/删除标签）
  - 高级选项：提取变量、保存响应、跳过 SSL 验证
  - 自动从当前请求继承方法、URL、请求头、参数、请求体等配置
-->
<template>
  <el-dialog
    title="保存为测试用例"
    v-model="dialogVisible"
    width="600px"
    @close="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="所属项目" prop="project">
        <el-select
          v-model="form.project"
          placeholder="请选择项目"
          style="width: 100%"
          @change="onProjectChange"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="所属集合" prop="collection">
        <el-select
          v-model="form.collection"
          placeholder="请选择集合"
          style="width: 100%"
          :disabled="!form.project"
        >
          <el-option
            v-for="collection in filteredCollections"
            :key="collection.id"
            :label="collection.name"
            :value="collection.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="用例名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入测试用例名称"
          clearable
        />
      </el-form-item>

      <el-form-item label="请求方法" prop="method">
        <el-select v-model="form.method" style="width: 120px">
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="PATCH" value="PATCH" />
          <el-option label="DELETE" value="DELETE" />
          <el-option label="HEAD" value="HEAD" />
          <el-option label="OPTIONS" value="OPTIONS" />
        </el-select>
      </el-form-item>

      <el-form-item label="请求URL" prop="url">
        <el-input
          v-model="form.url"
          placeholder="请输入请求URL"
          clearable
        />
      </el-form-item>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入测试用例描述"
        />
      </el-form-item>

      <el-form-item label="标签">
        <el-tag
          v-for="tag in form.tags"
          :key="tag"
          closable
          @close="removeTag(tag)"
          style="margin-right: 10px;"
        >
          {{ tag }}
        </el-tag>
        <el-input
          v-if="inputVisible"
          ref="inputRef"
          v-model="inputValue"
          size="small"
          style="width: 120px;"
          @keyup.enter="handleInputConfirm"
          @blur="handleInputConfirm"
        />
        <el-button
          v-else
          size="small"
          @click="showInput"
        >
          + 添加标签
        </el-button>
      </el-form-item>

      <el-form-item label="高级选项">
        <el-checkbox-group v-model="form.options">
          <el-checkbox label="extract_variables">提取变量</el-checkbox>
          <el-checkbox label="save_response">保存响应</el-checkbox>
          <el-checkbox label="skip_ssl_verify">跳过SSL验证</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSave"
          :loading="saving"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../../stores/project'
import { useCollectionStore } from '../../stores/collection'
import { useTestCaseStore } from '../../stores/testCase'
import type { HttpRequest } from '../../types/http'

interface Props {
  modelValue: boolean
  request: HttpRequest
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': [testCase: any]
}>()

// Store
const projectStore = useProjectStore()
const collectionStore = useCollectionStore()
const testCaseStore = useTestCaseStore()

// 响应式数据
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRef = ref()
const inputRef = ref()
const saving = ref(false)
const inputVisible = ref(false)
const inputValue = ref('')

// 表单数据
const form = reactive({
  project: null,
  collection: null,
  name: '',
  method: 'GET',
  url: '',
  description: '',
  tags: [],
  options: []
})

// 表单验证规则
const formRules = {
  project: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  collection: [
    { required: true, message: '请选择所属集合', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入请求URL', trigger: 'blur' }
  ]
}

// 计算属性
const projects = computed(() => projectStore.projects)

const filteredCollections = computed(() => {
  if (!form.project) return []
  return collectionStore.collections.filter(c => c.project === form.project)
})

// 方法
const resetForm = () => {
  Object.assign(form, {
    project: null,
    collection: null,
    name: '',
    method: props.request.method,
    url: props.request.baseUrl + props.request.url,
    description: '',
    tags: [],
    options: []
  })

  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const onProjectChange = () => {
  form.collection = null
  // 加载该项目的集合
  if (form.project) {
    collectionStore.fetchCollections({ project: form.project })
  }
}

const removeTag = (tag: string) => {
  const index = form.tags.indexOf(tag)
  if (index > -1) {
    form.tags.splice(index, 1)
  }
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value && !form.tags.includes(inputValue.value)) {
    form.tags.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const buildTestCaseData = () => {
  const { request } = props

  return {
    name: form.name,
    description: form.description,
    method: form.method,
    url: form.url,
    project: form.project,
    collection: form.collection,
    headers: request.headers || [],
    params: request.params || [],
    body_type: request.bodyType || 'none',
    body: JSON.stringify(request.body || {}),
    tests: request.tests || [],
    tags: form.tags,
    options: {
      extract_variables: form.options.includes('extract_variables'),
      save_response: form.options.includes('save_response'),
      skip_ssl_verify: form.options.includes('skip_ssl_verify')
    },
    timeout: request.settings?.timeout || 30,
    follow_redirects: request.settings?.followRedirects ?? true
  }
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    saving.value = true

    const testCaseData = buildTestCaseData()
    const testCase = await testCaseStore.createTestCase(testCaseData)

    emit('saved', testCase)
    dialogVisible.value = false
    ElMessage.success('测试用例保存成功')
  } catch (error) {
    console.error('保存测试用例失败:', error)
    ElMessage.error('保存测试用例失败')
  } finally {
    saving.value = false
  }
}

// 生命周期
const initialize = () => {
  // 加载项目列表
  projectStore.fetchProjects()

  // 设置默认值
  if (props.request) {
    form.method = props.request.method
    form.url = props.request.baseUrl + props.request.url
  }
}

initialize()
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>