<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    width="90%"
    @update:model-value="$emit('update:visible', $event)"
    class="test-result-dialog"
  >
    <div v-if="result" class="result-detail">
      <!-- 基本信息 -->
      <el-descriptions title="基本信息" :column="2" border>
        <el-descriptions-item label="用例名称">
          {{ result.test_case_name }}
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">
          <el-tag :type="getMethodTagType(result.test_case_method)">
            {{ result.test_case_method }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="请求URL" :span="2">
          {{ result.test_case_url }}
        </el-descriptions-item>
        <el-descriptions-item label="执行状态">
          <el-tag :type="getStatusTagType(result.status)">
            {{ getStatusText(result.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="HTTP状态码">
          <el-tag
            v-if="result.response_status"
            :type="result.response_status >= 200 && result.response_status < 300 ? 'success' : 'danger'"
          >
            {{ result.response_status }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="响应时间">
          {{ result.response_time }}ms
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(result.start_time) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 数据存储级别提示 -->
      <el-alert
        v-if="storageLevel"
        :title="storageLevel.message"
        :type="storageLevel.level === 'full' ? 'warning' : 'info'"
        :closable="false"
        style="margin: 20px 0"
      >
        <template #default>
          <span v-if="storageLevel.level === 'full'">
            HTTP状态码非200，已保存完整的请求和响应信息，方便排查问题
          </span>
          <span v-else>
            HTTP状态码为200，仅保存摘要信息以节省存储空间
          </span>
        </template>
      </el-alert>

      <!-- 请求信息 -->
      <el-collapse v-model="activeNames" class="detail-collapse">
        <el-collapse-item title="请求信息" name="request">
          <el-tabs v-model="requestTab">
            <el-tab-pane label="摘要" name="summary">
              <JsonViewer
                v-if="requestData.summary"
                :data="requestData.summary"
                :expanded="true"
                copyable
                sort
              />
              <el-empty v-else description="无摘要数据" />
            </el-tab-pane>
            <el-tab-pane label="完整" name="full">
              <div v-if="storageLevel.level === 'full' && requestData.full">
                <JsonViewer
                  :data="requestData.full"
                  :expanded="true"
                  copyable
                  sort
                />
              </div>
              <el-empty v-else description="HTTP状态码为200，未保存完整请求数据" />
            </el-tab-pane>
          </el-tabs>
        </el-collapse-item>

        <!-- 响应信息 -->
        <el-collapse-item title="响应信息" name="response">
          <el-tabs v-model="responseTab">
            <el-tab-pane label="摘要" name="summary">
              <JsonViewer
                v-if="responseData.summary"
                :data="responseData.summary"
                :expanded="true"
                copyable
                sort
              />
              <el-empty v-else description="无摘要数据" />
            </el-tab-pane>
            <el-tab-pane label="完整" name="full">
              <div v-if="storageLevel.level === 'full' && responseData.full">
                <JsonViewer
                  :data="responseData.full"
                  :expanded="true"
                  copyable
                  sort
                />
              </div>
              <el-empty v-else description="HTTP状态码为200，未保存完整响应数据" />
            </el-tab-pane>
          </el-tabs>
        </el-collapse-item>

        <!-- 断言结果 -->
        <el-collapse-item v-if="result.assertion_results && result.assertion_results.length > 0" name="assertions">
          <template #title>
            <span>断言结果 ({{ result.assertion_results.length }})</span>
          </template>
          <el-table :data="result.assertion_results" size="small">
            <el-table-column prop="assertion_type" label="断言类型" width="150" />
            <el-table-column prop="target" label="断言目标" width="200" show-overflow-tooltip />
            <el-table-column prop="operator" label="操作符" width="120" />
            <el-table-column prop="expected_value" label="期望值" width="150" show-overflow-tooltip />
            <el-table-column prop="actual_value" label="实际值" width="150" show-overflow-tooltip />
            <el-table-column prop="passed" label="结果" width="80">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
          </el-table>
        </el-collapse-item>

        <!-- 提取的变量 -->
        <el-collapse-item v-if="result.extracted_variables && Object.keys(result.extracted_variables).length > 0" name="extractions">
          <template #title>
            <span>提取的变量 ({{ Object.keys(result.extracted_variables).length }})</span>
          </template>
          <JsonViewer
            :data="result.extracted_variables"
            :expanded="true"
            copyable
            sort
          />
        </el-collapse-item>

        <!-- 错误信息 -->
        <el-collapse-item v-if="result.error_info && Object.keys(result.error_info).length > 0" name="error">
          <template #title>
            <span style="color: #f56c6c">错误信息</span>
          </template>
          <JsonViewer
            :data="result.error_info"
            :expanded="true"
            copyable
          />
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-empty v-else description="未选择测试结果" />

    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import JsonViewer from 'vue-json-viewer'
import 'vue-json-viewer/style.css'
import type { TestResult } from '../types/report'

interface Props {
  visible: boolean
  result?: TestResult | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const activeNames = ref(['request', 'response'])
const requestTab = ref('summary')
const responseTab = ref('summary')

// 对话框标题
const title = computed(() => {
  return `测试结果详情 - ${props.result?.test_case_name || ''}`
})

// 存储级别
const storageLevel = computed(() => {
  if (!props.result) return null

  const hasFullData = props.result.request_full || props.result.response_full
  const hasSummaryData = props.result.request_summary || props.result.response_summary

  if (hasFullData) {
    return {
      level: 'full',
      message: '完整数据模式 - HTTP状态码非200'
    }
  } else if (hasSummaryData) {
    return {
      level: 'summary',
      message: '摘要数据模式 - HTTP状态码为200'
    }
  } else {
    return {
      level: 'legacy',
      message: '历史数据格式'
    }
  }
})

// 请求数据
const requestData = computed(() => {
  if (!props.result) return { summary: null, full: null }

  return {
    summary: props.result.request_summary || null,
    full: props.result.request_full || null
  }
})

// 响应数据
const responseData = computed(() => {
  if (!props.result) return { summary: null, full: null }

  return {
    summary: props.result.response_summary || null,
    full: props.result.response_full || null
  }
})

// 格式化日期时间
const formatDateTime = (dateTime: string | null) => {
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

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    PENDING: 'info',
    RUNNING: 'primary',
    COMPLETED: 'success',
    FAILED: 'danger',
    CANCELLED: 'warning',
    PASSED: 'success',
    SKIPPED: 'warning',
    ERROR: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    PENDING: '待执行',
    RUNNING: '运行中',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消',
    PASSED: '通过',
    SKIPPED: '跳过',
    ERROR: '错误'
  }
  return texts[status] || status
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
</script>

<style scoped>
.test-result-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

.result-detail {
  padding: 10px 0;
}

.detail-collapse {
  margin-top: 20px;
}

.detail-collapse :deep(.el-collapse-item__header) {
  font-weight: 500;
}

.detail-collapse :deep(.el-collapse-item__content) {
  padding: 15px 20px;
}

/* JSON Viewer样式调整 */
:deep(.jv-container) {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
}

:deep(.jv-key) {
  color: #303133;
}

:deep(.jv-item.jv-string) {
  color: #67c23a;
}

:deep(.jv-item.jv-number) {
  color: #409eff;
}

:deep(.jv-item.jv-boolean) {
  color: #e6a23c;
}

:deep(.jv-item.jv-null) {
  color: #909399;
}
</style>
