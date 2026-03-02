<!--
  CollectionList.vue - 集合列表管理页面

  管理 API 接口集合，支持以下功能：
  - 集合表格：展示名称、所属项目、描述、用例数量、创建人、创建时间
  - 创建/编辑集合：弹窗表单，含名称、所属项目、描述字段
  - 按项目筛选集合列表
  - 按名称关键字搜索
  - 删除/批量删除：带确认提示
  - 分页：支持自定义每页条数
  - 点击集合名称可跳转至集合详情页
-->
<template>
  <div class="collection-list-container">
    <div class="page-header">
      <h1 class="page-title">集合管理</h1>
      <p class="page-description">管理API接口集合</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="table-toolbar-left">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建集合
        </el-button>
        <el-button type="danger" :disabled="!selectedCollections.length" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="table-toolbar-right">
        <el-select
          v-model="searchForm.project"
          placeholder="选择项目"
          clearable
          @change="handleSearch"
          style="width: 200px; margin-right: 10px"
        >
          <el-option
            v-for="project in projectOptions"
            :key="project.value"
            :label="project.label"
            :value="project.value"
          />
        </el-select>
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索集合名称"
          prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px"
        />
        <el-button icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 集合表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="collectionList"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="集合名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="所属项目" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="用例数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.test_case_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="120" />
        <el-table-column prop="created_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
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

    <!-- 创建/编辑集合对话框 -->
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
        <el-form-item label="集合名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入集合名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project">
          <el-select v-model="form.project" placeholder="请选择项目" style="width: 100%">
            <el-option
              v-for="project in projectOptions"
              :key="project.value"
              :label="project.label"
              :value="project.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="集合描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入集合描述"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, Search } from '@element-plus/icons-vue'
import { useCollectionStore, useProjectStore } from '../../stores'
import type { ApiCollection, ApiCollectionCreate } from '../../types/collection'

const router = useRouter()
const collectionStore = useCollectionStore()
const projectStore = useProjectStore()

// 加载状态
const loading = ref(false)
const submitting = ref(false)

// 集合列表
const collectionList = computed(() => collectionStore.collections)
const selectedCollections = ref<ApiCollection[]>([])

// 项目选项
const projectOptions = computed(() => projectStore.projectOptions)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  project: null as number | null
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
const currentCollection = ref<ApiCollection | null>(null)

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive<ApiCollectionCreate>({
  name: '',
  description: '',
  project: 0
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入集合名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.size,
      search: searchForm.keyword
    }
    if (searchForm.project) {
      params.project = searchForm.project
    }
    const response = await collectionStore.fetchCollections(params)
    pagination.total = response.count
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
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
const handleSelectionChange = (selection: ApiCollection[]) => {
  selectedCollections.value = selection
}

// 创建集合
const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '创建集合'
  form.project = searchForm.project || (projectOptions.value[0]?.value || 0)
  dialogVisible.value = true
}

// 编辑集合
const handleEdit = (collection: ApiCollection) => {
  isEdit.value = true
  dialogTitle.value = '编辑集合'
  currentCollection.value = collection
  form.name = collection.name
  form.description = collection.description || ''
  form.project = collection.project
  dialogVisible.value = true
}

// 查看集合
const handleView = (collection: ApiCollection) => {
  router.push(`/collections/${collection.id}`)
}

// 删除集合
const handleDelete = async (collection: ApiCollection) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除集合"${collection.name}"吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await collectionStore.deleteCollection(collection.id)
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
  if (!selectedCollections.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCollections.value.length} 个集合吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const promises = selectedCollections.value.map(c => collectionStore.deleteCollection(c.id))
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

    if (isEdit.value && currentCollection.value) {
      await collectionStore.updateCollection(currentCollection.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await collectionStore.createCollection(form)
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

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.name = ''
  form.description = ''
  form.project = 0
  currentCollection.value = null
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadProjects()
  loadData()
})
</script>

<style scoped>
.collection-list-container {
  padding: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>