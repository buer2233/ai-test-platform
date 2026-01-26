<template>
  <div class="data-driven-config">
    <div class="header">
      <h2>数据驱动测试</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建数据源
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ dataDriverStore.dataDrivers.length }}</div>
              <div class="stat-label">总数据源</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ dataDriverStore.activeDataDrivers.length }}</div>
              <div class="stat-label">激活数据源</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ getDataTypeCount('JSON') }}</div>
              <div class="stat-label">JSON数据</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-button @click="fetchDataDrivers">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 数据源列表 -->
    <el-table :data="dataDriverStore.dataDrivers" v-loading="dataDriverStore.loading" stripe>
      <el-table-column prop="name" label="数据源名称" />
      <el-table-column prop="project_name" label="所属项目" />
      <el-table-column prop="test_case_name" label="关联用例" />
      <el-table-column label="数据类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getDataTypeColor(row.data_type)" size="small">
            {{ getDataTypeLabel(row.data_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="数据行数" width="120">
        <template #default="{ row }">
          {{ row.data_content?.length || 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handlePreview(row)">预览数据</el-button>
          <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteDataDriver(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="dataDriverStore.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      :title="dialogMode === 'create' ? '创建数据驱动' : '编辑数据驱动'"
      v-model="dialogVisible"
      width="800px"
      @close="resetForm"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入数据源名称" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project">
          <el-select v-model="formData.project" placeholder="请选择项目" style="width: 100%" @change="onProjectChange">
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联用例" prop="test_case">
          <el-select v-model="formData.test_case" placeholder="请选择测试用例" style="width: 100%" filterable>
            <el-option
              v-for="testCase in availableTestCases"
              :key="testCase.id"
              :label="`${testCase.name} (${testCase.method} ${testCase.url})`"
              :value="testCase.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据类型" prop="data_type">
          <el-select v-model="formData.data_type" placeholder="请选择数据类型" style="width: 100%">
            <el-option
              v-for="type in dataDriverStore.dataTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" rows="3" placeholder="请输入数据源描述" />
        </el-form-item>
        <el-form-item label="变量映射" v-if="formData.data_type !== 'DATABASE'">
          <el-button size="small" @click="addVariableMapping">添加映射</el-button>
          <div v-for="(mapping, index) in variableMappings" :key="index" class="mapping-item">
            <el-input v-model="mapping.key" placeholder="变量名" style="width: 35%" />
            <el-input v-model="mapping.value" placeholder="映射字段" style="width: 35%; margin-left: 10px;" />
            <el-button size="small" type="danger" @click="removeVariableMapping(index)" style="margin-left: 10px;">删除</el-button>
          </div>
        </el-form-item>

        <!-- JSON数据输入 -->
        <el-form-item label="JSON数据" v-if="formData.data_type === 'JSON'">
          <el-button size="small" @click="formatJsonData">格式化</el-button>
          <el-input
            v-model="jsonContent"
            type="textarea"
            :rows="8"
            placeholder="请输入JSON数据，格式如：[{\"key1\": \"value1\"}, {\"key2\": \"value2\"}]"
            @change="onJsonDataChange"
          />
        </el-form-item>

        <!-- 数据库配置 -->
        <el-form-item label="数据库配置" v-if="formData.data_type === 'DATABASE'">
          <el-form :model="dbConfig" label-width="100px">
            <el-form-item label="数据库类型">
              <el-select v-model="dbConfig.type" style="width: 100%">
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
                <el-option label="SQLite" value="sqlite" />
              </el-select>
            </el-form-item>
            <el-form-item label="主机地址">
              <el-input v-model="dbConfig.host" placeholder="localhost" />
            </el-form-item>
            <el-form-item label="端口">
              <el-input-number v-model="dbConfig.port" :min="1" :max="65535" placeholder="3306" />
            </el-form-item>
            <el-form-item label="数据库名">
              <el-input v-model="dbConfig.database" placeholder="test_db" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="dbConfig.username" placeholder="root" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="dbConfig.password" type="password" placeholder="password" show-password />
            </el-form-item>
            <el-form-item label="SQL查询">
              <el-input
                v-model="dbConfig.query"
                type="textarea"
                :rows="4"
                placeholder="SELECT * FROM table_name WHERE condition"
              />
            </el-form-item>
          </el-form>
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

    <!-- 数据预览对话框 -->
    <el-dialog title="数据预览" v-model="previewDialogVisible" width="80%">
      <div v-if="previewData">
        <el-descriptions title="数据源信息" border>
          <el-descriptions-item label="数据源名称">{{ previewData.name }}</el-descriptions-item>
          <el-descriptions-item label="数据类型">{{ getDataTypeLabel(previewData.data_type) }}</el-descriptions-item>
          <el-descriptions-item label="数据行数">{{ previewData.data_content.length }}</el-descriptions-item>
          <el-descriptions-item label="变量映射">
            <div class="variable-mapping-preview">
              <div v-for="(value, key) in previewData.variable_mapping" :key="key" class="mapping-item">
                <span class="key">{{ key }}</span> → <span class="value">{{ value }}</span>
              </div>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 数据表格 -->
        <div class="data-preview-table">
          <h4>数据内容预览（前10条）</h4>
          <el-table :data="previewData.sample_data" stripe max-height="400">
            <el-table-column
              v-for="(value, key) in Object.keys(previewData.sample_data[0] || {})"
              :key="key"
              :prop="key"
              :label="key"
              show-overflow-tooltip
            />
          </el-table>
          <div v-if="previewData.data_content.length > 10" class="more-data-tip">
            仅显示前10条数据，完整数据请查看详情
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { useDataDriverStore } from '../stores/dataDriver'
import { useProjectStore } from '../stores/project'
import { useTestCaseStore } from '../stores/testCase'
import type { DataDriverCreate } from '../types/dataDriver'

// Store
const dataDriverStore = useDataDriverStore()
const projectStore = useProjectStore()
const testCaseStore = useTestCaseStore()

// 响应式数据
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const previewDialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const formRef = ref()
const previewData = ref<any>(null)

// 表单数据
const formData = reactive<DataDriverCreate & { id?: number }>({
  name: '',
  description: '',
  project: 0,
  test_case: 0,
  data_type: 'JSON',
  data_source: {},
  data_content: [],
  variable_mapping: {},
  is_active: true
})

// 动态表单项
const variableMappings = ref<Array<{ key: string; value: string }>>([])
const jsonContent = ref('')
const dbConfig = reactive({
  type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: '',
  username: 'root',
  password: '',
  query: 'SELECT * FROM table_name'
})

// 可用的测试用例
const availableTestCases = computed(() => {
  if (!formData.project) return []
  return testCaseStore.testCases.filter(tc => tc.project === formData.project)
})

// 过滤后的环境列表
const filteredEnvironments = computed(() => {
  if (!formData.project) return []
  return testCaseStore.testCases.filter(tc => tc.project === formData.project)
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' }
  ],
  project: [
    { required: true, message: '请选择项目', trigger: 'change' }
  ],
  test_case: [
    { required: true, message: '请选择测试用例', trigger: 'change' }
  ],
  data_type: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ]
}

// 方法
const fetchDataDrivers = () => {
  dataDriverStore.fetchDataDrivers({
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const fetchProjects = () => {
  projectStore.fetchProjects()
}

const fetchTestCases = () => {
  testCaseStore.fetchTestCases()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchDataDrivers()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchDataDrivers()
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (dataDriver: any) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: dataDriver.id,
    name: dataDriver.name,
    description: dataDriver.description,
    project: dataDriver.project,
    test_case: dataDriver.test_case,
    data_type: dataDriver.data_type,
    data_source: dataDriver.data_source,
    data_content: dataDriver.data_content,
    variable_mapping: dataDriver.variable_mapping,
    is_active: dataDriver.is_active
  })

  // 将变量映射转换为数组
  variableMappings.value = Object.entries(dataDriver.variable_mapping).map(([key, value]) => ({ key, value }))

  if (dataDriver.data_type === 'JSON') {
    jsonContent.value = JSON.stringify(dataDriver.data_content, null, 2)
  } else if (dataDriver.data_type === 'DATABASE') {
    Object.assign(dbConfig, dataDriver.data_source)
  }

  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    project: 0,
    test_case: 0,
    data_type: 'JSON',
    data_source: {},
    data_content: [],
    variable_mapping: {},
    is_active: true
  })
  variableMappings.value = []
  jsonContent.value = ''
  Object.assign(dbConfig, {
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: '',
    username: 'root',
    password: '',
    query: 'SELECT * FROM table_name'
  })
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const onProjectChange = (projectId: number) => {
  formData.test_case = 0
  formData.variable_mapping = {}
  variableMappings.value = []
}

const addVariableMapping = () => {
  variableMappings.value.push({ key: '', value: '' })
}

const removeVariableMapping = (index: number) => {
  variableMappings.value.splice(index, 1)
}

const formatJsonData = () => {
  try {
    const parsed = JSON.parse(jsonContent.value)
    jsonContent.value = JSON.stringify(parsed, null, 2)
    ElMessage.success('JSON格式化成功')
  } catch (error) {
    ElMessage.error('JSON格式错误，请检查语法')
  }
}

const onJsonDataChange = () => {
  try {
    const parsed = JSON.parse(jsonContent.value)
    formData.data_content = parsed
  } catch (error) {
    // JSON格式错误时不更新
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    // 将变量映射数组转换为对象
    formData.variable_mapping = variableMappings.value
      .filter(mapping => mapping.key && mapping.value)
      .reduce((acc, mapping) => ({ ...acc, [mapping.key]: mapping.value }), {})

    if (formData.data_type === 'JSON') {
      try {
        formData.data_content = JSON.parse(jsonContent.value)
      } catch (error) {
        ElMessage.error('JSON数据格式错误')
        return
      }
    } else if (formData.data_type === 'DATABASE') {
      formData.data_source = { ...dbConfig }
    }

    submitting.value = true

    if (dialogMode.value === 'create') {
      await dataDriverStore.createDataDriver(formData)
    } else {
      await dataDriverStore.updateDataDriver(formData.id!, formData)
    }

    dialogVisible.value = false
    fetchDataDrivers()
  } catch (error) {
    console.error('表单提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const handlePreview = async (dataDriver: any) => {
  try {
    const preview = await dataDriverStore.previewData(dataDriver.id)
    previewData.value = preview
    previewDialogVisible.value = true
  } catch (error) {
    console.error('预览数据失败:', error)
  }
}

const deleteDataDriver = async (dataDriver: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${dataDriver.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await dataDriverStore.deleteDataDriver(dataDriver.id)
    fetchDataDrivers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除数据驱动失败:', error)
    }
  }
}

const getDataTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    'JSON': 'JSON数据',
    'CSV': 'CSV文件',
    'EXCEL': 'Excel文件',
    'DATABASE': '数据库'
  }
  return typeMap[type] || type
}

const getDataTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'JSON': 'success',
    'CSV': 'info',
    'EXCEL': 'warning',
    'DATABASE': 'danger'
  }
  return colorMap[type] || 'info'
}

const getDataTypeCount = (type: string) => {
  return dataDriverStore.dataDrivers.filter(driver => driver.data_type === type).length
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// 生命周期
onMounted(() => {
  fetchDataDrivers()
  fetchProjects()
  fetchTestCases()
})
</script>

<style scoped>
.data-driven-config {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.mapping-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.variable-mapping-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.mapping-item {
  background-color: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.mapping-item .key {
  color: #409eff;
  font-weight: bold;
  margin-right: 4px;
}

.mapping-item .value {
  color: #67c23a;
}

.data-preview-table {
  margin-top: 20px;
}

.data-preview-table h4 {
  margin-bottom: 10px;
  color: #333;
}

.more-data-tip {
  color: #666;
  font-size: 12px;
  text-align: center;
  margin-top: 10px;
}
</style>