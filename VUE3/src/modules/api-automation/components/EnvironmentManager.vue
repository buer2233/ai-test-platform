<!--
  EnvironmentManager.vue - 测试环境管理组件

  提供测试环境的完整 CRUD 功能：
  - 环境列表展示（表格形式，含分页）
  - 创建/编辑环境（对话框表单）
  - 连接测试：验证环境 Base URL 是否可达
  - 设为默认环境
  - 删除环境（带确认提示）
  - 支持全局请求头和全局变量的动态配置
-->
<template>
  <div class="environment-manager">
    <div class="header">
      <h2>测试环境管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建环境
      </el-button>
    </div>

    <!-- 环境列表 -->
    <el-table :data="environmentStore.environments" v-loading="environmentStore.loading" stripe>
      <el-table-column prop="name" label="环境名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="project_name" label="所属项目" />
      <el-table-column prop="base_url" label="基础URL" show-overflow-tooltip />
      <el-table-column label="默认环境" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_default ? 'success' : 'info'" size="small">
            {{ row.is_default ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="testConnection(row.id)">测试连接</el-button>
          <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
          <el-button
            size="small"
            type="primary"
            v-if="!row.is_default"
            @click="setDefaultEnvironment(row.id)"
          >
            设为默认
          </el-button>
          <el-button size="small" type="danger" @click="deleteEnvironment(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="environmentStore.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      :title="dialogMode === 'create' ? '创建环境' : '编辑环境'"
      v-model="dialogVisible"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入环境名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project">
          <el-select v-model="formData.project" placeholder="请选择项目" style="width: 100%">
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="formData.base_url" placeholder="http://example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" rows="3" placeholder="请输入环境描述" />
        </el-form-item>
        <el-form-item label="全局请求头">
          <el-button size="small" @click="addGlobalHeader">添加请求头</el-button>
          <div v-for="(header, index) in globalHeaders" :key="index" class="header-item">
            <el-input v-model="header.key" placeholder="Header名称" style="width: 40%" />
            <el-input v-model="header.value" placeholder="Header值" style="width: 40%; margin-left: 10px;" />
            <el-button size="small" type="danger" @click="removeGlobalHeader(index)" style="margin-left: 10px;">删除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="全局变量">
          <el-button size="small" @click="addGlobalVariable">添加变量</el-button>
          <div v-for="(variable, index) in globalVariables" :key="index" class="variable-item">
            <el-input v-model="variable.key" placeholder="变量名" style="width: 40%" />
            <el-input v-model="variable.value" placeholder="变量值" style="width: 40%; margin-left: 10px;" />
            <el-button size="small" type="danger" @click="removeGlobalVariable(index)" style="margin-left: 10px;">删除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="设为默认环境">
          <el-switch v-model="formData.is_default" />
        </el-form-item>
        <el-form-item label="激活状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '更新' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useEnvironmentStore } from '../stores/environment'
import { useProjectStore } from '../stores/project'
import type { EnvironmentCreate } from '../types/environment'

// Store
const environmentStore = useEnvironmentStore()
const projectStore = useProjectStore()

// 响应式数据
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const formRef = ref()

// 表单数据
const formData = reactive<EnvironmentCreate & { id?: number }>({
  name: '',
  project: 0,
  base_url: '',
  description: '',
  global_headers: {},
  global_variables: {},
  is_default: false,
  is_active: true
})

// 动态表单项
const globalHeaders = ref<Array<{ key: string; value: string }>>([])
const globalVariables = ref<Array<{ key: string; value: string }>>([])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 方法
const fetchEnvironments = () => {
  environmentStore.fetchEnvironments({
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const fetchProjects = () => {
  projectStore.fetchProjects()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchEnvironments()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchEnvironments()
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (environment: any) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: environment.id,
    name: environment.name,
    project: environment.project,
    base_url: environment.base_url,
    description: environment.description,
    global_headers: environment.global_headers,
    global_variables: environment.global_variables,
    is_default: environment.is_default,
    is_active: environment.is_active
  })

  // 将全局对象转换为数组
  globalHeaders.value = Object.entries(environment.global_headers).map(([key, value]) => ({ key, value }))
  globalVariables.value = Object.entries(environment.global_variables).map(([key, value]) => ({ key, value }))

  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    project: 0,
    base_url: '',
    description: '',
    global_headers: {},
    global_variables: {},
    is_default: false,
    is_active: true
  })
  globalHeaders.value = []
  globalVariables.value = []
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const addGlobalHeader = () => {
  globalHeaders.value.push({ key: '', value: '' })
}

const removeGlobalHeader = (index: number) => {
  globalHeaders.value.splice(index, 1)
}

const addGlobalVariable = () => {
  globalVariables.value.push({ key: '', value: '' })
}

const removeGlobalVariable = (index: number) => {
  globalVariables.value.splice(index, 1)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    // 将数组转换为对象
    formData.global_headers = globalHeaders.value
      .filter(item => item.key && item.value)
      .reduce((acc, item) => ({ ...acc, [item.key]: item.value }), {})

    formData.global_variables = globalVariables.value
      .filter(item => item.key && item.value)
      .reduce((acc, item) => ({ ...acc, [item.key]: item.value }), {})

    submitting.value = true

    if (dialogMode.value === 'create') {
      await environmentStore.createEnvironment(formData)
    } else {
      await environmentStore.updateEnvironment(formData.id!, formData)
    }

    dialogVisible.value = false
    fetchEnvironments()
  } catch (error) {
    console.error('表单提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const testConnection = async (id: number) => {
  try {
    await environmentStore.testConnection(id)
  } catch (error) {
    console.error('连接测试失败:', error)
  }
}

const setDefaultEnvironment = async (id: number) => {
  try {
    await environmentStore.setDefault(id)
    fetchEnvironments()
  } catch (error) {
    console.error('设置默认环境失败:', error)
  }
}

const deleteEnvironment = async (environment: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除环境 "${environment.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await environmentStore.deleteEnvironment(environment.id)
    fetchEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除环境失败:', error)
    }
  }
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// 生命周期
onMounted(() => {
  fetchEnvironments()
  fetchProjects()
})
</script>

<style scoped>
.environment-manager {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.header-item, .variable-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}
</style>