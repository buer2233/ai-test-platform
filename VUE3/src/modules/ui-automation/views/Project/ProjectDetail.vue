<template>
  <div class="project-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="header-title">
        <h3>{{ projectStore.currentProject?.name }}</h3>
        <el-text type="info">{{ projectStore.currentProject?.description }}</el-text>
      </div>
      <div class="header-actions">
        <el-button @click="handleEdit">编辑</el-button>
        <el-button type="primary" @click="goToTestCases">
          <el-icon><Plus /></el-icon>
          添加测试用例
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total_test_cases }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><VideoPlay /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total_executions }}</div>
              <div class="stat-label">执行次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><SuccessFilled /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.successful_executions }}</div>
              <div class="stat-label">成功次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C"><CircleCloseFilled /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.failed_executions }}</div>
              <div class="stat-label">失败次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tab页 -->
    <el-tabs v-model="activeTab" class="content-tabs">
      <el-tab-pane label="测试用例" name="testCases">
        <TestCaseListInProject :project-id="projectId" />
      </el-tab-pane>
      <el-tab-pane label="执行记录" name="executions">
        <ExecutionListInProject :project-id="projectId" />
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑项目" width="600px">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * 项目详情页
 *
 * 展示单个 UI 自动化测试项目的详细信息：
 * - 统计概览卡片（用例数、执行次数、成功/失败次数）
 * - 关联的测试用例列表（Tab 页）
 * - 关联的执行记录列表（Tab 页）
 * - 项目编辑对话框
 */

import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  ArrowLeft,
  CircleCloseFilled,
  Document,
  Plus,
  SuccessFilled,
  VideoPlay
} from '@element-plus/icons-vue'

import { useUiProjectStore } from '../../stores/project'
import type { UiProjectStatistics } from '../../types/project'
import TestCaseListInProject from './components/TestCaseList.vue'
import ExecutionListInProject from './components/ExecutionList.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useUiProjectStore()

/** 当前项目 ID（从路由参数获取） */
const projectId = Number(route.params.id)
/** 当前激活的 Tab 页 */
const activeTab = ref('testCases')

/** 项目统计数据 */
const statistics = ref<UiProjectStatistics>({
  total_test_cases: 0,
  total_executions: 0,
  successful_executions: 0,
  failed_executions: 0,
  success_rate: 0
})

/* ---------- 编辑项目对话框 ---------- */

const editDialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  name: '',
  description: ''
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

/* ---------- 页面操作 ---------- */

/** 返回项目列表 */
const goBack = () => {
  router.push('/ui-automation/projects')
}

/** 打开编辑对话框：回填当前项目数据 */
const handleEdit = () => {
  if (!projectStore.currentProject) return
  formData.name = projectStore.currentProject.name
  formData.description = projectStore.currentProject.description || ''
  editDialogVisible.value = true
}

/** 提交项目更新 */
const handleUpdate = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await projectStore.updateProject(projectId, formData)
      ElMessage.success('更新成功')
      editDialogVisible.value = false
    } catch {
      // 错误已由 Store 层处理
    } finally {
      submitting.value = false
    }
  })
}

/** 跳转到创建测试用例页面（自动关联当前项目） */
const goToTestCases = () => {
  router.push(`/ui-automation/test-cases/create?project=${projectId}`)
}

/* ---------- 数据加载 ---------- */

/** 加载项目详情和统计数据 */
const loadData = async () => {
  await projectStore.fetchProject(projectId)
  const stats = await projectStore.fetchProjectStatistics(projectId)
  if (stats) {
    statistics.value = stats
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.project-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  flex: 1;
}

.header-title h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.stats-row {
  margin-bottom: 0;
}

.stat-card {
  margin-bottom: 0;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 40px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 8px;
}

.content-tabs {
  flex: 1;
}

:deep(.el-tabs__content) {
  height: 100%;
}

:deep(.el-tab-pane) {
  height: 100%;
}
</style>
