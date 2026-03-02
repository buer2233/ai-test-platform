<template>
  <div class="test-case-create">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="header-title">
        <h3>{{ isEdit ? '编辑UI测试用例' : '创建UI测试用例' }}</h3>
        <el-text type="info">使用自然语言描述测试场景，AI将自动执行浏览器操作</el-text>
      </div>
    </div>

    <!-- 表单卡片 -->
    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="test-case-form"
      >
        <el-form-item label="所属项目" prop="project">
          <el-select
            v-model="formData.project"
            placeholder="请选择项目"
            style="width: 100%"
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

        <el-form-item label="用例描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入用例描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="测试任务" prop="test_task">
          <NaturalLanguageEditor
            v-model="formData.test_task"
            placeholder="请用自然语言描述测试场景，例如：
1. 打开百度首页
2. 在搜索框中输入'browser_use'
3. 点击搜索按钮
4. 等待搜索结果加载
5. 验证页面标题包含'browser_use'"
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

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="浏览器模式">
              <el-radio-group v-model="formData.browser_mode">
                <el-radio label="headless">无头模式</el-radio>
                <el-radio label="headed">有头模式</el-radio>
              </el-radio-group>
              <div class="form-item-tip">
                无头模式不显示浏览器窗口，执行速度更快；有头模式可以看到浏览器操作过程
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="超时时间(秒)">
              <el-input-number
                v-model="formData.timeout"
                :min="30"
                :max="600"
                :step="10"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="重试次数">
              <el-input-number
                v-model="formData.retry_count"
                :min="0"
                :max="5"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="启用状态">
          <el-switch
            v-model="formData.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建用例' }}
          </el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
/**
 * 测试用例创建/编辑页
 *
 * 根据路由参数自动判断创建或编辑模式：
 * - 创建模式：/ui-automation/test-cases/create
 * - 编辑模式：/ui-automation/test-cases/:id/edit
 *
 * 表单字段包括：所属项目、用例名称、描述、测试任务（自然语言）、
 * 标签、浏览器模式、超时时间、重试次数、启用状态。
 */

import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

import { useUiProjectStore } from '../../stores/project'
import { useUiTestCaseStore } from '../../stores/testCase'
import type { UiTestCaseCreate, UiTestCaseUpdate } from '../../types/testCase'
import NaturalLanguageEditor from '@ui-automation/components/NaturalLanguageEditor.vue'

const router = useRouter()
const route = useRoute()
const testCaseStore = useUiTestCaseStore()
const projectStore = useUiProjectStore()

/** 是否为编辑模式（路由中包含 :id 参数） */
const isEdit = computed(() => !!route.params.id)
/** 编辑模式下的用例 ID */
const editingId = computed(() => isEdit.value ? Number(route.params.id) : null)

const formRef = ref<FormInstance>()
const submitting = ref(false)

/** 表单数据 */
const formData = reactive({
  project: route.query.project ? Number(route.query.project) : undefined,
  name: '',
  description: '',
  test_task: '',
  tags: [] as string[],
  browser_mode: 'headless' as 'headless' | 'headed',
  timeout: 120,
  retry_count: 0,
  is_active: true
})

/** 预设的常用标签选项 */
const commonTags = ref([
  '登录', '注册', '搜索', '表单提交',
  '导航', '购物车', '支付', '用户中心'
])

/** 表单验证规则 */
const formRules: FormRules = {
  project: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  test_task: [
    { required: true, message: '请输入测试任务描述', trigger: 'blur' },
    { min: 10, message: '测试任务描述至少10个字符', trigger: 'blur' }
  ]
}

/* ---------- 页面操作 ---------- */

/** 返回测试用例列表 */
const goBack = () => {
  router.push('/ui-automation/test-cases')
}

/** 提交表单：根据模式调用创建或更新接口 */
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && editingId.value) {
        // 编辑模式：仅提交可更新的字段
        const updateData: UiTestCaseUpdate = {
          name: formData.name,
          description: formData.description,
          test_task: formData.test_task,
          tags: formData.tags,
          browser_mode: formData.browser_mode,
          timeout: formData.timeout,
          retry_count: formData.retry_count,
          is_active: formData.is_active
        }
        await testCaseStore.updateTestCase(editingId.value, updateData)
        ElMessage.success('更新成功')
      } else {
        // 创建模式：包含所属项目
        const createData: UiTestCaseCreate = {
          project: formData.project as number,
          name: formData.name,
          description: formData.description,
          test_task: formData.test_task,
          tags: formData.tags,
          browser_mode: formData.browser_mode,
          timeout: formData.timeout,
          retry_count: formData.retry_count,
          is_active: formData.is_active
        }
        await testCaseStore.createTestCase(createData)
        ElMessage.success('创建成功')
      }
      goBack()
    } catch {
      // 错误已由 Store 层处理
    } finally {
      submitting.value = false
    }
  })
}

/* ---------- 数据加载 ---------- */

/** 编辑模式：加载已有用例数据填入表单 */
const loadEditData = async () => {
  if (isEdit.value && editingId.value) {
    const testCase = await testCaseStore.fetchTestCase(editingId.value)
    if (testCase) {
      formData.project = testCase.project
      formData.name = testCase.name
      formData.description = testCase.description || ''
      formData.test_task = testCase.test_task
      formData.tags = testCase.tags
      formData.browser_mode = testCase.browser_mode
      formData.timeout = testCase.timeout
      formData.retry_count = testCase.retry_count
      formData.is_active = testCase.is_active
    }
  }
}

/* ---------- 页面初始化 ---------- */
onMounted(async () => {
  // 加载项目列表（用于所属项目下拉选择）
  await projectStore.fetchProjects()
  // 编辑模式：加载用例数据
  await loadEditData()
})
</script>

<style scoped>
.test-case-create {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.form-card {
  max-width: 900px;
}

.form-item-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
