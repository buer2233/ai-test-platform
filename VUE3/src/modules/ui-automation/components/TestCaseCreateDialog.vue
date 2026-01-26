<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑测试用例' : '创建测试用例'"
    width="700px"
    @update:model-value="handleClose"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="所属项目" prop="project">
        <el-select
          v-model="formData.project"
          placeholder="请选择项目"
          style="width: 100%"
          :disabled="isEdit"
        >
          <el-option
            v-for="project in projectStore.activeProjects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="用例名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入测试用例名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="测试任务" prop="test_task">
        <NaturalLanguageEditor
          v-model="formData.test_task"
          :rows="6"
        />
      </el-form-item>

      <el-form-item label="标签">
        <el-select
          v-model="formData.tags"
          multiple
          filterable
          allow-create
          placeholder="请输入或选择标签"
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

      <el-form-item label="浏览器模式">
        <el-radio-group v-model="formData.browser_mode">
          <el-radio label="headless">无头模式</el-radio>
          <el-radio label="headed">有头模式</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUiTestCaseStore } from '../stores/testCase'
import { useUiProjectStore } from '../stores/project'
import type { UiTestCase, UiTestCaseCreate, UiTestCaseUpdate } from '../types/testCase'
import NaturalLanguageEditor from './NaturalLanguageEditor.vue'

interface Props {
  modelValue: boolean
  testCaseId: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const testCaseStore = useUiTestCaseStore()
const projectStore = useUiProjectStore()

const isEdit = computed(() => props.testCaseId !== null)

const formRef = ref<FormInstance>()
const submitting = ref(false)

const formData = reactive({
  project: undefined as number | undefined,
  name: '',
  test_task: '',
  tags: [] as string[],
  browser_mode: 'headless' as 'headless' | 'headed'
})

const commonTags = ref(['登录', '搜索', '表单', '导航', '注册'])

const formRules: FormRules = {
  project: [{ required: true, message: '请选择项目', trigger: 'change' }],
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  test_task: [
    { required: true, message: '请输入测试任务', trigger: 'blur' },
    { min: 10, message: '至少10个字符', trigger: 'blur' }
  ]
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && props.testCaseId) {
        const updateData: UiTestCaseUpdate = {
          name: formData.name,
          test_task: formData.test_task,
          tags: formData.tags,
          browser_mode: formData.browser_mode
        }
        await testCaseStore.updateTestCase(props.testCaseId, updateData)
        ElMessage.success('更新成功')
      } else {
        const createData: UiTestCaseCreate = {
          project: formData.project as number,
          name: formData.name,
          test_task: formData.test_task,
          tags: formData.tags,
          browser_mode: formData.browser_mode
        }
        await testCaseStore.createTestCase(createData)
        ElMessage.success('创建成功')
      }
      emit('success')
      handleClose()
    } catch {
      // Error already handled
    } finally {
      submitting.value = false
    }
  })
}

// 加载编辑数据
const loadEditData = async () => {
  if (isEdit.value && props.testCaseId) {
    const testCase = await testCaseStore.fetchTestCase(props.testCaseId)
    if (testCase) {
      formData.project = testCase.project
      formData.name = testCase.name
      formData.test_task = testCase.test_task
      formData.tags = testCase.tags
      formData.browser_mode = testCase.browser_mode
    }
  }
}

// 重置表单
const resetForm = () => {
  formData.project = undefined
  formData.name = ''
  formData.test_task = ''
  formData.tags = []
  formData.browser_mode = 'headless'
  formRef.value?.clearValidate()
}

watch(() => props.modelValue, (val) => {
  if (val) {
    if (isEdit.value) {
      loadEditData()
    } else {
      resetForm()
    }
    projectStore.fetchProjects()
  }
})
</script>

<style scoped>
/* 对话框样式 */
</style>
