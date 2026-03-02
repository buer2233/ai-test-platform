<!--
  TestCaseList.vue - 接口管理列表页面

  管理所有 API 接口测试用例，支持以下功能：
  - 接口表格：名称、请求方法、URL、所属项目/集合、创建人、创建时间
  - 多维度筛选：按项目、集合、请求方法过滤，按名称/URL 搜索
  - 创建/编辑/克隆/删除接口
  - 批量操作：批量执行（支持并发/串行模式）、批量删除
  - 批量导出：JSON、CSV、Excel 三种格式（Excel 含详细工作表）
  - 内嵌 TestCaseRunner 组件支持单个接口快速执行
  - 分页：支持自定义每页条数
-->
<template>
  <div class="testcase-list-container">
    <div class="page-header">
      <h1 class="page-title">接口管理</h1>
      <p class="page-description">管理 API 接口测试</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="table-toolbar-left">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建接口
        </el-button>
        <el-dropdown
          split-button
          type="primary"
          :disabled="!selectedTestCases.length"
          @click="handleBatchExecute"
          trigger="click"
        >
          <el-icon><VideoPlay /></el-icon>
          批量执行 ({{ selectedTestCases.length }})
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleBatchExecute">
                <el-icon><VideoPlay /></el-icon>
                立即执行
              </el-dropdown-item>
              <el-dropdown-item @click="showBatchExecuteDialog = true">
                <el-icon><Setting /></el-icon>
                执行配置...
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown
          split-button
          type="success"
          :disabled="!selectedTestCases.length"
          @click="handleBatchExport('json')"
          trigger="click"
        >
          <el-icon><Download /></el-icon>
          批量导出
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleBatchExport('json')">
                <el-icon><Document /></el-icon>
                导出为 JSON
              </el-dropdown-item>
              <el-dropdown-item @click="handleBatchExport('csv')">
                <el-icon><Tickets /></el-icon>
                导出为 CSV
              </el-dropdown-item>
              <el-dropdown-item @click="handleBatchExport('excel')">
                <el-icon><DocumentCopy /></el-icon>
                导出为 Excel
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="danger" :disabled="!selectedTestCases.length" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="table-toolbar-right">
        <el-select
          v-model="searchForm.project"
          placeholder="选择项目"
          clearable
          @change="handleProjectChange"
          style="width: 150px; margin-right: 10px"
        >
          <el-option
            v-for="project in projectOptions"
            :key="project.value"
            :label="project.label"
            :value="project.value"
          />
        </el-select>
        <el-select
          v-model="searchForm.collection"
          placeholder="选择集合"
          clearable
          @change="handleSearch"
          style="width: 150px; margin-right: 10px"
        >
          <el-option
            v-for="collection in collectionOptions"
            :key="collection.value"
            :label="collection.label"
            :value="collection.value"
          />
        </el-select>
        <el-select
          v-model="searchForm.method"
          placeholder="请求方法"
          clearable
          @change="handleSearch"
          style="width: 120px; margin-right: 10px"
        >
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="PATCH" value="PATCH" />
          <el-option label="DELETE" value="DELETE" />
        </el-select>
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索用例名称或URL"
          prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 250px"
        />
        <el-button icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 接口表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="testCaseList"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="接口名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="请求方法" width="100">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.method)">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="请求URL" min-width="250" show-overflow-tooltip />
        <el-table-column prop="project_name" label="所属项目" width="150" />
        <el-table-column prop="collection_name" label="所属集合" width="150" />
        <el-table-column prop="created_by_name" label="创建人" width="120" />
        <el-table-column prop="created_time" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link @click="handleClone(row)">克隆</el-button>
            <TestCaseRunner :test-case="row" />
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

    <!-- 批量执行配置对话框 -->
    <el-dialog
      v-model="showBatchExecuteDialog"
      title="批量执行配置"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="测试环境">
          <el-select
            v-model="batchExecuteConfig.environment"
            placeholder="请选择测试环境"
            style="width: 100%"
          >
            <el-option
              v-for="env in environmentOptions"
              :key="env.value"
              :label="env.label"
              :value="env.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-radio-group v-model="batchExecuteConfig.concurrent">
            <el-radio :label="true">并发执行</el-radio>
            <el-radio :label="false">串行执行</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="batchExecuteConfig.concurrent" label="并发数量">
          <el-input-number
            v-model="batchExecuteConfig.maxConcurrency"
            :min="1"
            :max="10"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="执行说明">
          <el-text size="small" type="info">
            {{ batchExecuteConfig.concurrent
              ? '并发执行可以更快完成测试，但可能增加服务器负载'
              : '串行执行按顺序执行，便于排查问题' }}
          </el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchExecuteDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchExecute" :loading="batchExecuting">
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search, VideoPlay, Setting, Download, Document, Tickets, DocumentCopy } from '@element-plus/icons-vue'
import { useTestCaseStore, useProjectStore, useCollectionStore, useEnvironmentStore, useExecutionStore } from '../../stores'
import TestCaseRunner from '../../components/TestCaseRunner.vue'
import type { ApiTestCaseList, ApiTestCase } from '../../types/testCase'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { testCaseApi } from '../../api/testCase'

const router = useRouter()
const testCaseStore = useTestCaseStore()
const projectStore = useProjectStore()
const collectionStore = useCollectionStore()
const environmentStore = useEnvironmentStore()
const executionStore = useExecutionStore()

// 加载状态
const loading = ref(false)
const batchExecuting = ref(false)

// 批量执行对话框
const showBatchExecuteDialog = ref(false)
const batchExecuteConfig = reactive({
  environment: null as number | null,
  concurrent: true,
  maxConcurrency: 5
})

// 接口列表
const testCaseList = computed(() => testCaseStore.testCases)
const selectedTestCases = ref<ApiTestCaseList[]>([])

// 项目和集合选项
const projectOptions = computed(() => projectStore.projectOptions)
const collectionOptions = ref<Array<{ label: string; value: number }>>([])
const environmentOptions = computed(() =>
  environmentStore.environments.map(e => ({ label: e.name, value: e.id }))
)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  project: null as number | null,
  collection: null as number | null,
  method: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取方法标签类型
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    PATCH: 'danger',
    DELETE: 'info'
  }
  return types[method] || 'info'
}

// 格式化日期时间
const formatDateTime = (dateTime: string | null) => {
  if (!dateTime) return '-'
  try {
    const date = new Date(dateTime)
    // 检查日期是否有效
    if (isNaN(date.getTime())) return '-'

    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    return '-'
  }
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
    if (searchForm.collection) {
      params.collection = searchForm.collection
    }
    if (searchForm.method) {
      params.method = searchForm.method
    }
    const response = await testCaseStore.fetchTestCases(params)
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

// 加载集合列表
const loadCollections = async (projectId?: number) => {
  try {
    const params: any = { page_size: 1000 }
    if (projectId) {
      params.project = projectId
    }
    await collectionStore.fetchCollections(params)
    collectionOptions.value = collectionStore.collections.map(c => ({
      label: c.name,
      value: c.id
    }))
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
}

// 项目改变时更新集合选项
const handleProjectChange = () => {
  searchForm.collection = null
  loadCollections(searchForm.project || undefined)
  loadData()  // 重新加载数据
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
const handleSelectionChange = (selection: ApiTestCaseList[]) => {
  selectedTestCases.value = selection
}

// 创建接口
const handleCreate = () => {
  router.push('/test-cases/create')
}

// 编辑接口
const handleEdit = (testCase: ApiTestCaseList) => {
  router.push(`/test-cases/${testCase.id}/edit`)
}

// 查看接口
const handleView = (testCase: ApiTestCaseList) => {
  router.push(`/test-cases/${testCase.id}`)
}

// 克隆接口
const handleClone = async (testCase: ApiTestCaseList) => {
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入新接口名称',
      '克隆接口',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${testCase.name} - 副本`,
        inputValidator: (value) => {
          if (!value || value.trim().length < 2) {
            return '名称长度至少为2个字符'
          }
          return true
        }
      }
    )
    await testCaseStore.cloneTestCase(testCase.id, value)
    ElMessage.success('克隆成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('克隆失败')
    }
  }
}


// 删除接口
const handleDelete = async (testCase: ApiTestCaseList) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除接口"${testCase.name}"吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await testCaseStore.deleteTestCase(testCase.id)
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
  if (!selectedTestCases.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTestCases.value.length} 个接口吗？删除后不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const promises = selectedTestCases.value.map(tc => testCaseStore.deleteTestCase(tc.id))
    await Promise.all(promises)
    ElMessage.success('批量删除成功')
    selectedTestCases.value = []
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 批量执行接口测试
 */
const handleBatchExecute = async () => {
  if (!selectedTestCases.value.length) return

  // 检查是否有环境配置
  await environmentStore.fetchEnvironments({ page_size: 1000 })
  const environments = environmentStore.environments

  if (environments.length === 0) {
    ElMessage.warning('请先配置测试环境')
    return
  }

  // 如果只有一个环境，直接执行
  if (environments.length === 1) {
    batchExecuteConfig.environment = environments[0].id
    await executeBatchTests()
  } else {
    // 显示环境选择对话框
    showBatchExecuteDialog.value = true
  }
}

/**
 * 确认批量执行配置并执行
 */
const confirmBatchExecute = async () => {
  showBatchExecuteDialog.value = false
  await executeBatchTests()
}

/**
 * 执行批量测试
 */
const executeBatchTests = async () => {
  if (!batchExecuteConfig.environment) {
    ElMessage.warning('请选择测试环境')
    return
  }

  batchExecuting.value = true
  let successCount = 0
  let failCount = 0
  const results: Array<{ name: string; status: string; message?: string }> = []

  try {
    // 获取项目ID（从选中的第一个用例）
    const projectId = selectedTestCases.value[0]?.project || 0

    // 创建执行记录
    const execution = await executionStore.createExecution({
      name: `批量执行 - ${new Date().toLocaleString()}`,
      project: projectId,
      environment: batchExecuteConfig.environment,
      test_cases: selectedTestCases.value.map(tc => tc.id)
    })

    if (batchExecuteConfig.concurrent) {
      // 并发执行
      const concurrency = batchExecuteConfig.maxConcurrency || 5
      for (let i = 0; i < selectedTestCases.value.length; i += concurrency) {
        const batch = selectedTestCases.value.slice(i, i + concurrency)
        const promises = batch.map(async (tc) => {
          try {
            await executionStore.executeTest(execution.id)
            successCount++
            results.push({ name: tc.name, status: 'SUCCESS' })
          } catch (error: any) {
            failCount++
            results.push({ name: tc.name, status: 'FAILED', message: error.message })
          }
        })
        await Promise.all(promises)
      }
    } else {
      // 串行执行
      for (const tc of selectedTestCases.value) {
        try {
          await executionStore.executeTest(execution.id)
          successCount++
          results.push({ name: tc.name, status: 'SUCCESS' })
        } catch (error: any) {
          failCount++
          results.push({ name: tc.name, status: 'FAILED', message: error.message })
        }
      }
    }

    // 显示执行结果
    ElMessageBox.alert(
      `执行完成！\n成功: ${successCount}\n失败: ${failCount}\n总计: ${selectedTestCases.value.length}`,
      '批量执行结果',
      { type: successCount === selectedTestCases.value.length ? 'success' : 'warning' }
    )

    // 跳转到执行详情页面
    router.push(`/executions/${execution.id}`)
  } catch (error: any) {
    ElMessage.error(`批量执行失败: ${error.message}`)
  } finally {
    batchExecuting.value = false
  }
}

/**
 * 批量导出接口
 */
const handleBatchExport = async (format: 'json' | 'csv' | 'excel') => {
  if (!selectedTestCases.value.length) return

  const loading = ElMessage({
    message: '正在获取接口详情...',
    type: 'info',
    duration: 0
  })

  try {
    // 获取每个接口的完整详情
    const detailedCases: ApiTestCase[] = []
    for (const tc of selectedTestCases.value) {
      const detail = await testCaseApi.getTestCase(tc.id)
      detailedCases.push(detail)
    }

    loading.close()

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    const filename = `api_interfaces_${timestamp}`

    switch (format) {
      case 'json':
        exportToJSON(filename, detailedCases)
        break
      case 'csv':
        exportToCSV(filename, detailedCases)
        break
      case 'excel':
        exportToExcel(filename, detailedCases)
        break
    }

    ElMessage.success('导出成功')
  } catch (error: any) {
    loading.close()
    ElMessage.error(`导出失败: ${error.message}`)
  }
}

/**
 * 导出为JSON
 */
const exportToJSON = (filename: string, cases: ApiTestCase[]) => {
  const data = cases.map(tc => ({
    id: tc.id,
    name: tc.name,
    description: tc.description,
    project: tc.project,
    project_name: tc.project_name,
    collection: tc.collection,
    collection_name: tc.collection_name,
    method: tc.method,
    url: tc.url,
    headers: tc.headers,
    params: tc.params,
    body: tc.body,
    assertions: tc.assertions || [],
    extractions: tc.extractions || [],
    created_by: tc.created_by,
    created_by_name: tc.created_by_name,
    created_time: tc.created_time,
    updated_time: tc.updated_time
  }))

  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' })
  saveAs(blob, `${filename}.json`)
}

/**
 * 导出为CSV
 */
const exportToCSV = (filename: string, cases: ApiTestCase[]) => {
  const headers = [
    '接口名称', '描述', '请求方法', '请求URL',
    'Headers', 'Params', 'Body',
    '项目', '集合',
    '断言数量', '提取数量',
    '创建人', '创建时间'
  ]

  const rows = cases.map(tc => {
    const escapeCsv = (value: any) => {
      if (value === null || value === undefined) return '""'
      const str = typeof value === 'object' ? JSON.stringify(value) : String(value)
      return `"${str.replace(/"/g, '""')}"`
    }

    return [
      escapeCsv(tc.name),
      escapeCsv(tc.description),
      escapeCsv(tc.method),
      escapeCsv(tc.url),
      escapeCsv(tc.headers),
      escapeCsv(tc.params),
      escapeCsv(tc.body),
      escapeCsv(tc.project_name),
      escapeCsv(tc.collection_name),
      escapeCsv(tc.assertions?.length || 0),
      escapeCsv(tc.extractions?.length || 0),
      escapeCsv(tc.created_by_name),
      escapeCsv(tc.created_time)
    ]
  })

  const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
  saveAs(blob, `${filename}.csv`)
}

/**
 * 导出为Excel
 */
const exportToExcel = (filename: string, cases: ApiTestCase[]) => {
  const workbook = XLSX.utils.book_new()

  // 主工作表 - 接口基本信息
  const casesData = [
    ['接口名称', '描述', '请求方法', '请求URL', '项目', '集合', '断言数', '提取数', '创建人', '创建时间']
  ]

  cases.forEach(tc => {
    casesData.push([
      tc.name || '-',
      tc.description || '-',
      tc.method || '-',
      tc.url || '-',
      tc.project_name || '-',
      tc.collection_name || '-',
      tc.assertions?.length || 0,
      tc.extractions?.length || 0,
      tc.created_by_name || '-',
      formatDateTime(tc.created_time)
    ])
  })

  const casesSheet = XLSX.utils.aoa_to_sheet(casesData)
  casesSheet['!cols'] = [
    { wch: 30 }, { wch: 30 }, { wch: 10 }, { wch: 50 },
    { wch: 20 }, { wch: 20 }, { wch: 10 }, { wch: 10 },
    { wch: 15 }, { wch: 20 }
  ]
  XLSX.utils.book_append_sheet(workbook, casesSheet, '接口列表')

  // 为每个接口创建详细工作表
  cases.forEach((tc, index) => {
    const detailData = [
      [`接口: ${tc.name}`],
      [''],
      ['基本信息'],
      ['字段', '值'],
      ['ID', tc.id],
      ['名称', tc.name],
      ['描述', tc.description || '-'],
      ['项目', tc.project_name],
      ['集合', tc.collection_name || '-'],
      ['请求方法', tc.method],
      ['请求URL', tc.url],
      ['创建人', tc.created_by_name],
      ['创建时间', formatDateTime(tc.created_time)],
      ['更新时间', formatDateTime(tc.updated_time)],
      [''],
      ['请求配置'],
      ['Headers', JSON.stringify(tc.headers, null, 2)],
      ['Params', JSON.stringify(tc.params, null, 2)],
      ['Body', JSON.stringify(tc.body, null, 2)],
    ]

    // 添加断言信息
    if (tc.assertions && tc.assertions.length > 0) {
      detailData.push([''], ['断言配置'])
      detailData.push(['类型', '目标', '操作符', '期望值', '启用', '排序'])
      tc.assertions.forEach(assertion => {
        detailData.push([
          assertion.assertion_type,
          assertion.target || '-',
          assertion.operator,
          assertion.expected_value || '-',
          assertion.is_enabled ? '是' : '否',
          assertion.order
        ])
      })
    }

    // 添加提取信息
    if (tc.extractions && tc.extractions.length > 0) {
      detailData.push([''], ['数据提取配置'])
      detailData.push(['变量名', '提取类型', '提取表达式', '默认值', '启用', '作用域'])
      tc.extractions.forEach(extraction => {
        detailData.push([
          extraction.variable_name,
          extraction.extract_type,
          extraction.extract_expression,
          extraction.default_value || '-',
          extraction.is_enabled ? '是' : '否',
          extraction.scope
        ])
      })
    }

    const detailSheet = XLSX.utils.aoa_to_sheet(detailData)
    // Excel 工作表名称最多31个字符
    const sheetName = `${index + 1}-${tc.name.slice(0, 25)}`.replace(/[\\/?*\[\]]/g, '_')
    XLSX.utils.book_append_sheet(workbook, detailSheet, sheetName)
  })

  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadProjects()
  await environmentStore.fetchEnvironments({ page_size: 1000 })
  await loadCollections()  // 加载所有集合
  loadData()
})
</script>

<style scoped>
.testcase-list-container {
  padding: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>