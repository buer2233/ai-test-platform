<template>
  <div class="project-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h3>UI测试项目</h3>
        <el-text type="info">管理基于browser_use的UI自动化测试项目</el-text>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建项目
        </el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="项目名称">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索项目名称"
            clearable
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.is_active" placeholder="全部" clearable @change="handleSearch">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 项目列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="projectStore.loading"
        :data="projectStore.projects"
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="owner.username" label="负责人" width="120" />
        <el-table-column prop="test_cases_count" label="用例数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.test_cases_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executions_count" label="执行次数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.executions_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button link type="primary" @click.stop="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="projectStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchProjects"
          @current-change="fetchProjects"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
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
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, View, Edit, Delete } from '@element-plus/icons-vue'
import { useUiProjectStore } from '../../stores/project'
import type { UiProject, UiProjectCreate } from '../../types/project'

const router = useRouter()
const projectStore = useUiProjectStore()

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 筛选表单
const filterForm = reactive({
  search: '',
  is_active: undefined as boolean | undefined
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑项目' : '创建项目')
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive<UiProjectCreate>({
  name: '',
  description: '',
  is_active: true
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取项目列表
const fetchProjects = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.pageSize
  }
  if (filterForm.search) {
    params.search = filterForm.search
  }
  if (filterForm.is_active !== undefined) {
    params.is_active = filterForm.is_active
  }
  await projectStore.fetchProjects(params)
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchProjects()
}

// 行点击
const handleRowClick = (row: UiProject) => {
  router.push(`/ui-automation/projects/${row.id}`)
}

// 查看详情
const handleView = (row: UiProject) => {
  router.push(`/ui-automation/projects/${row.id}`)
}

// 编辑
const handleEdit = (row: UiProject) => {
  isEdit.value = true
  editingId.value = row.id
  formData.name = row.name
  formData.description = row.description || ''
  formData.is_active = row.is_active
  dialogVisible.value = true
}

// 删除
const handleDelete = async (row: UiProject) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${row.name}" 吗？删除后将同时删除该项目下的所有测试用例和执行记录。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    await projectStore.deleteProject(row.id)
    ElMessage.success('删除成功')
    fetchProjects()
  } catch {
    // 用户取消
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  formData.name = ''
  formData.description = ''
  formData.is_active = true
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && editingId.value) {
        await projectStore.updateProject(editingId.value, formData)
        ElMessage.success('更新成功')
      } else {
        await projectStore.createProject(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchProjects()
    } catch (error) {
      // Error already handled by store
    } finally {
      submitting.value = false
    }
  })
}

// 对话框关闭
const handleDialogClose = () => {
  formRef.value?.resetFields()
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.project-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 0;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  flex: 1;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
