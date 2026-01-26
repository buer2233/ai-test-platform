<template>
  <div class="test-case-execution-records">
    <div class="records-header">
      <div class="header-left">
        <span class="record-count">共 {{ total }} 条执行记录</span>
        <el-button size="small" @click="loadRecords" :loading="loading" :icon="Refresh">
          刷新
        </el-button>
      </div>
      <div class="header-right">
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          size="small"
          style="width: 120px; margin-right: 10px"
          @change="loadRecords"
        >
          <el-option label="全部" value="" />
          <el-option label="成功" value="SUCCESS" />
          <el-option label="失败" value="FAILED" />
          <el-option label="错误" value="ERROR" />
        </el-select>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :span="6">
        <div class="stat-item total" @click="filterByStatus(null)">
          <div class="stat-value">{{ statistics.total }}</div>
          <div class="stat-label">总计</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-item success" @click="filterByStatus('SUCCESS')">
          <div class="stat-value">{{ statistics.success }}</div>
          <div class="stat-label">成功</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-item failed" @click="filterByStatus('FAILED')">
          <div class="stat-value">{{ statistics.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-item error" @click="filterByStatus('ERROR')">
          <div class="stat-value">{{ statistics.error }}</div>
          <div class="stat-label">错误</div>
        </div>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty
      v-if="!loading && records.length === 0"
      description="暂无执行记录"
      :image-size="100"
    />

    <!-- 记录列表 -->
    <div v-else class="records-list">
      <div
        v-for="record in records"
        :key="record.id"
        class="record-item"
        :class="`status-${record.status?.toLowerCase()}`"
      >
        <div class="record-main" @click="toggleExpand(record.id)">
          <div class="record-status">
            <el-icon v-if="record.status === 'SUCCESS'" class="success-icon"><CircleCheck /></el-icon>
            <el-icon v-else-if="record.status === 'FAILED'" class="failed-icon"><CircleClose /></el-icon>
            <el-icon v-else class="error-icon"><Warning /></el-icon>
          </div>
          <div class="record-info">
            <div class="record-url">
              <el-tag size="small" :type="getMethodTagType(record.request_method)">
                {{ record.request_method }}
              </el-tag>
              <span class="url-text">{{ record.request_url }}</span>
            </div>
            <div class="record-meta">
              <span class="status-tag">
                <el-tag :type="getStatusType(record.status)" size="small">
                  {{ getStatusText(record.status) }}
                </el-tag>
              </span>
              <span class="status-code">
                状态码: {{ record.response_status || '-' }}
              </span>
              <span class="duration">
                耗时: {{ record.duration }}ms
              </span>
              <span class="time">
                {{ formatDateTime(record.created_time) }}
              </span>
            </div>
          </div>
          <div class="record-expand">
            <el-icon :class="{ 'is-expanded': expandedIds.includes(record.id) }">
              <ArrowDown />
            </el-icon>
          </div>
        </div>

        <!-- 展开详情 -->
        <div v-show="expandedIds.includes(record.id)" class="record-detail">
          <el-tabs v-model="activeTab[record.id]">
            <el-tab-pane label="请求" :name="`request-${record.id}`">
              <div class="detail-section">
                <h4>请求头</h4>
                <pre class="code-block">{{ formatJson(record.request_headers) }}</pre>
                <h4>请求参数</h4>
                <pre class="code-block">{{ formatJson(record.request_params) }}</pre>
                <h4>请求体</h4>
                <pre class="code-block">{{ formatJson(record.request_body) }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="响应" :name="`response-${record.id}`">
              <div class="detail-section">
                <div class="response-info">
                  <span>状态码: <strong>{{ record.response_status }}</strong></span>
                  <span>响应时间: <strong>{{ record.duration }}ms</strong></span>
                  <span>响应大小: <strong>{{ formatSize(record.response_size) }}</strong></span>
                </div>
                <h4>响应头</h4>
                <pre class="code-block">{{ formatJson(record.response_headers) }}</pre>
                <h4>响应体</h4>
                <pre class="code-block response-body">{{ formatJson(record.response_body) }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="断言" :name="`assertions-${record.id}`">
              <div class="detail-section">
                <template v-if="getUniqueAssertions(record.assertion_results).length > 0">
                  <el-table :data="getUniqueAssertions(record.assertion_results)" stripe size="small">
                    <el-table-column prop="type" label="断言类型" width="120">
                      <template #default="{ row }">
                        <el-tag size="small">{{ row.type || row.assertion_type }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="expected" label="期望值" width="150">
                      <template #default="{ row }">
                        <code class="expect-value">{{ formatAssertionValue(row.expected || row.expected_value) }}</code>
                      </template>
                    </el-table-column>
                    <el-table-column prop="actual" label="实际值" width="150">
                      <template #default="{ row }">
                        <code class="actual-value">{{ formatAssertionValue(row.actual !== undefined ? row.actual : row.actual_value) }}</code>
                      </template>
                    </el-table-column>
                    <el-table-column label="断言消息" min-width="200" show-overflow-tooltip>
                      <template #default="{ row }">
                        <span>{{ row.message || row.error_message || '-' }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column label="状态" width="80" align="center">
                      <template #default="{ row }">
                        <el-icon v-if="isAssertionPassed(row)" color="#67c23a"><CircleCheck /></el-icon>
                        <el-icon v-else color="#f56c6c"><CircleClose /></el-icon>
                      </template>
                    </el-table-column>
                  </el-table>
                </template>
                <el-empty v-else description="无断言结果" :image-size="60" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        small
        @size-change="loadRecords"
        @current-change="loadRecords"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, CircleCheck, CircleClose, Warning, ArrowDown
} from '@element-plus/icons-vue'
import { apiClient } from '../api'
import type { HttpExecutionRecord } from '../types/http'

interface Props {
  testCaseId: number
}

const props = defineProps<Props>()

// 数据状态
const loading = ref(false)
const records = ref<HttpExecutionRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const statusFilter = ref('')
const expandedIds = ref<number[]>([])
const activeTab = ref<Record<number, string>>({})

// 统计信息
const statistics = reactive({
  total: 0,
  success: 0,
  failed: 0,
  error: 0
})

// 加载执行记录
const loadRecords = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
      test_case: props.testCaseId
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    console.log('Loading records with params:', params)
    const response = await apiClient.get('/v1/api-automation/http-execution-records/', params)
    console.log('API Response:', response)
    console.log('API Response type:', typeof response)
    console.log('API Response.results:', response?.results)

    if (response) {
      records.value = response.results || response || []
      total.value = response.count || records.value.length

      console.log('Records value:', records.value)
      console.log('First record:', records.value[0])
      console.log('First record assertion_results:', records.value[0]?.assertion_results)

      // 初始化每条记录的activeTab，防止多个记录共享同一个tab
      records.value.forEach(record => {
        if (!activeTab.value[record.id]) {
          activeTab.value[record.id] = `request-${record.id}`
        }
        // 调试：打印每条记录的断言结果数据
        console.log(`Record ${record.id}:`, {
          id: record.id,
          url: record.request_url,
          has_assertion_results: !!record.assertion_results,
          assertion_results_length: record.assertion_results?.length || 0,
          assertion_results: record.assertion_results
        })
      })

      // 计算统计
      updateStatistics()
    }
  } catch (error) {
    console.error('Failed to load execution records:', error)
    ElMessage.error('加载执行记录失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStatistics = () => {
  statistics.total = records.value.length
  statistics.success = records.value.filter(r => r.status === 'SUCCESS').length
  statistics.failed = records.value.filter(r => r.status === 'FAILED').length
  statistics.error = records.value.filter(r => r.status === 'ERROR').length
}

// 切换展开状态
const toggleExpand = (id: number) => {
  const index = expandedIds.value.indexOf(id)
  if (index > -1) {
    expandedIds.value.splice(index, 1)
  } else {
    expandedIds.value.push(id)
    if (!activeTab.value[id]) {
      activeTab.value[id] = `request-${id}`
    }
  }
}

// 按状态筛选
const filterByStatus = (status: string | null) => {
  statusFilter.value = status || ''
  loadRecords()
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  try {
    const date = new Date(dateTime)
    if (isNaN(date.getTime())) return '-'

    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch {
    return '-'
  }
}

// 格式化 JSON
const formatJson = (data: any) => {
  if (!data) return '{}'
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}

// 格式化文件大小
const formatSize = (bytes: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 格式化断言值
const formatAssertionValue = (value: any): string => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'boolean') return String(value)
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string') return value
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

// 安全地判断断言是否通过
const isAssertionPassed = (assertion: any): boolean => {
  // 处理各种可能的passed值格式
  if (typeof assertion.passed === 'boolean') return assertion.passed
  if (assertion.passed === 'true' || assertion.passed === '1') return true
  if (assertion.passed === 'false' || assertion.passed === '0') return false
  // 默认返回false（显示为失败）
  return false
}

// Python 字符串转 JSON 字符串
const pythonStringToJson = (pythonStr: string): string => {
  // 替换 Python 的 None 为 null
  let jsonStr = pythonStr.replace(/\bNone\b/g, 'null')
  // 替换 Python 的 True/False 为 true/false
  jsonStr = jsonStr.replace(/\bTrue\b/g, 'true')
  jsonStr = jsonStr.replace(/\bFalse\b/g, 'false')
  // 替换单引号为双引号（简单处理，假设没有嵌套引号冲突）
  jsonStr = jsonStr.replace(/'/g, '"')
  return jsonStr
}

// 获取唯一的断言列表（避免重复）
const getUniqueAssertions = (assertions: any): any[] => {
  console.log('getUniqueAssertions input:', assertions)
  console.log('getUniqueAssertions input type:', typeof assertions)

  // 处理各种可能的输入格式
  if (!assertions) {
    return []
  }

  let assertionsArray: any[] = []

  // 如果是字符串，尝试解析
  if (typeof assertions === 'string') {
    try {
      // 先尝试直接解析 JSON
      try {
        assertionsArray = JSON.parse(assertions)
      } catch {
        // 如果失败，尝试解析 Python 字符串格式
        const jsonStr = pythonStringToJson(assertions)
        assertionsArray = JSON.parse(jsonStr)
      }
      console.log('getUniqueAssertions: parsed string, length:', assertionsArray.length)
    } catch (e) {
      console.error('getUniqueAssertions: failed to parse string:', e)
      return []
    }
  }
  // 如果是数组，直接使用
  else if (Array.isArray(assertions)) {
    assertionsArray = assertions
  }
  // 如果是对象且有length属性，尝试转换
  else if (typeof assertions === 'object' && assertions !== null) {
    try {
      const length = (assertions as any).length
      if (typeof length === 'number' && length >= 0) {
        assertionsArray = Array.from(assertions)
      }
    } catch (e) {
      console.error('getUniqueAssertions: cannot convert to array:', e)
      return []
    }
  }

  if (!Array.isArray(assertionsArray) || assertionsArray.length === 0) {
    return []
  }

  // 使用Map来去重
  const uniqueMap = new Map()
  assertionsArray.forEach((assertion: any, idx: number) => {
    const key = `${assertion.type || assertion.assertion_type || ''}-${JSON.stringify(assertion.expected || assertion.expected_value)}-${JSON.stringify(assertion.actual || assertion.actual_value)}-${idx}`
    if (!uniqueMap.has(key)) {
      uniqueMap.set(key, { ...assertion, _originalIndex: idx })
    }
  })

  const result = Array.from(uniqueMap.values()).sort((a, b) => a._originalIndex - b._originalIndex)
  console.log('getUniqueAssertions output:', result)
  return result
}

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

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    SUCCESS: 'success',
    FAILED: 'danger',
    ERROR: 'warning',
    TIMEOUT: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    SUCCESS: '成功',
    FAILED: '失败',
    ERROR: '错误',
    TIMEOUT: '超时'
  }
  return texts[status] || status
}

// 组件挂载时加载数据
onMounted(() => {
  loadRecords()
})

// 暴露刷新方法
defineExpose({
  refresh: loadRecords
})
</script>

<style scoped>
.test-case-execution-records {
  padding: 0;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.record-count {
  font-size: 14px;
  color: #606266;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-item {
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  background-color: #f5f7fa;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-item.total:hover {
  background-color: #d3e4fd;
}

.stat-item.success:hover {
  background-color: #dcedc8;
}

.stat-item.failed:hover {
  background-color: #fdd;
}

.stat-item.error:hover {
  background-color: #ffe6cc;
}

.stat-item.total {
  background-color: #e3f0ff;
}

.stat-item.success {
  background-color: #e8f5e9;
}

.stat-item.failed {
  background-color: #ffebee;
}

.stat-item.error {
  background-color: #fff3e0;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.record-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.record-item.status-success {
  border-left: 4px solid #67c23a;
}

.record-item.status-failed {
  border-left: 4px solid #f56c6c;
}

.record-item.status-error {
  border-left: 4px solid #e6a23c;
}

.record-main {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background-color: #fff;
}

.record-main:hover {
  background-color: #f5f7fa;
}

.record-status {
  margin-right: 12px;
}

.record-status .success-icon {
  color: #67c23a;
  font-size: 20px;
}

.record-status .failed-icon {
  color: #f56c6c;
  font-size: 20px;
}

.record-status .error-icon {
  color: #e6a23c;
  font-size: 20px;
}

.record-info {
  flex: 1;
}

.record-url {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.url-text {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.record-expand .el-icon {
  transition: transform 0.3s;
}

.record-expand .el-icon.is-expanded {
  transform: rotate(180deg);
}

.record-detail {
  border-top: 1px solid #ebeef5;
  background-color: #fafafa;
}

.detail-section {
  padding: 16px;
}

.detail-section h4 {
  margin: 12px 0 8px 0;
  font-size: 13px;
  color: #606266;
  font-weight: 600;
}

.detail-section h4:first-child {
  margin-top: 0;
}

.code-block {
  background-color: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.response-info {
  display: flex;
  gap: 20px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
}

/* 断言结果表格样式 */
.expect-value {
  background-color: #e7f7ff;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #91d5ff;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.actual-value {
  background-color: #f6ffed;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #b7eb8f;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 0 4px;
}
</style>
