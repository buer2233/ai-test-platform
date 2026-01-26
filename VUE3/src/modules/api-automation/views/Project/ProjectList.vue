<template>
  <div class="project-list-container">
    <div class="page-header">
      <h1 class="page-title">项目管理</h1>
      <p class="page-description">管理所有API测试项目</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="table-toolbar-left">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建项目
        </el-button>
        <el-button type="danger" :disabled="!selectedProjects.length" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="table-toolbar-right">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索项目名称"
          prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px"
        />
        <el-button icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 项目表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="projectList"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="项目名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="owner_name" label="创建人" width="120" />
        <el-table-column label="集合数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.collection_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用例数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success">{{ row.test_case_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link @click="handleClone(row)">克隆</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 克隆项目对话框 -->
    <el-dialog
      v-model="cloneDialogVisible"
      title="克隆项目"
      width="500px"
    >
      <el-form
        ref="cloneFormRef"
        :model="cloneForm"
        :rules="cloneRules"
        label-width="100px"
      >
        <el-form-item label="新项目名称" prop="name">
          <el-input v-model="cloneForm.name" placeholder="请输入新项目名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cloneDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="cloning" @click="handleCloneSubmit">
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
import { Plus, Delete, Search } from '@element-plus/icons-vue'
import { useProjectStore } from '../../stores'
import type { ApiProject, ApiProjectCreate } from '../../types/project'

const router = useRouter()
const projectStore = useProjectStore()

// 加载状态
const loading = ref(false)
const submitting = ref(false)
const cloning = ref(false)

// 项目列表
const projectList = computed(() => projectStore.projects)
const selectedProjects = ref<ApiProject[]>([])

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentProject = ref<ApiProject | null>(null)

// 表单引用
const formRef = ref<FormInstance>()
const cloneFormRef = ref<FormInstance>()

// 表单数据
const form = reactive<ApiProjectCreate>({
  name: '',
  description: ''
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 克隆对话框状态
const cloneDialogVisible = ref(false)
const cloneForm = reactive({
  name: ''
})

const cloneRules: FormRules = {
  name: [
    { required: true, message: '请输入新项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.size,
      search: searchForm.keyword
    }
    const response = await projectStore.fetchProjects(params)
    pagination.total = response.count
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 分页处理
const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

// 选择处理
const handleSelectionChange = (selection: ApiProject[]) => {
  selectedProjects.value = selection
}

// 创建项目
const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '创建项目'
  dialogVisible.value = true
}

// 编辑项目
const handleEdit = (project: ApiProject) => {
  isEdit.value = true
  dialogTitle.value = '编辑项目'
  currentProject.value = project
  form.name = project.name
  form.description = project.description || ''
  dialogVisible.value = true
}

// 查看项目
const handleView = (project: ApiProject) => {
  router.push(`/projects/${project.id}`)
}

// 克隆项目
const handleClone = (project: ApiProject) => {
  currentProject.value = project
  cloneForm.name = `${project.name} - 副本`
  cloneDialogVisible.value = true
}

// 删除项目
const handleDelete = async (project: ApiProject) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${project.name}"吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await projectStore.deleteProject(project.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!selectedProjects.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedProjects.value.length} 个项目吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const promises = selectedProjects.value.map(p => projectStore.deleteProject(p.id))
    await Promise.all(promises)
    ElMessage.success('批量删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && currentProject.value) {
      await projectStore.updateProject(currentProject.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await projectStore.createProject(form)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 提交克隆
const handleCloneSubmit = async () => {
  if (!cloneFormRef.value || !currentProject.value) return

  try {
    await cloneFormRef.value.validate()
    cloning.value = true

    await projectStore.cloneProject(currentProject.value.id, cloneForm.name)
    ElMessage.success('克隆成功')
    cloneDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error('克隆失败')
  } finally {
    cloning.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.name = ''
  form.description = ''
  currentProject.value = null
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.project-list-container {
  padding: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>