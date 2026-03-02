<!--
  HttpExecutionRecordDetail.vue - HTTP 执行记录详情组件

  展示单次 HTTP 请求执行的完整记录，包含六个标签页：
  1. 请求信息：方法、URL、请求头、查询参数、请求体
  2. 响应信息：状态码、响应大小、响应时间、响应头、响应体
  3. 断言结果：通过数/失败数统计、每条断言的预期值/实际值对比
  4. 错误信息：错误类型、消息、堆栈跟踪（仅 ERROR/FAILED 状态显示）
  5. 数据提取：提取的变量名、路径、值、类型
  6. 元信息：执行来源、批次、重试次数、收藏状态、关联用例/环境

  操作功能：复制 cURL 命令、导出为 JSON、重新执行（开发中）
-->
<template>
  <div class="execution-record-detail">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 请求信息 -->
      <el-tab-pane label="请求信息" name="request">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="请求方法">
            <el-tag :type="getMethodTagType(record.request_method)" size="small">
              {{ record.request_method }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="请求URL">
            <el-link :href="record.request_url" target="_blank" type="primary">
              {{ record.request_url }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="基础URL">{{ record.request_base_url }}</el-descriptions-item>
          <el-descriptions-item label="请求路径">{{ record.request_path }}</el-descriptions-item>
          <el-descriptions-item label="请求大小" :span="2">
            {{ record.request_size_formatted || `${record.request_size} bytes` }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 请求头 -->
        <div class="section-title">请求头</div>
        <KeyValueViewer :data="record.request_headers" readonly />

        <!-- Query参数 -->
        <div v-if="Object.keys(record.request_params).length > 0" class="section-title">
          Query参数
        </div>
        <KeyValueViewer
          v-if="Object.keys(record.request_params).length > 0"
          :data="record.request_params"
          readonly
        />

        <!-- 请求体 -->
        <div v-if="record.request_body" class="section-title">请求体</div>
        <el-card v-if="record.request_body" shadow="never" class="json-viewer">
          <pre>{{ formatJson(record.request_body) }}</pre>
        </el-card>
      </el-tab-pane>

      <!-- 响应信息 -->
      <el-tab-pane label="响应信息" name="response">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="响应状态码">
            <el-tag :type="getStatusType(record.response_status)" size="small">
              {{ record.response_status }}
            </el-tag>
            <span v-if="record.response_status_text" class="status-text">
              {{ record.response_status_text }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="响应大小">
            {{ record.response_size_formatted || `${record.response_size} bytes` }}
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            {{ record.duration_formatted || `${record.duration}ms` }}
          </el-descriptions-item>
          <el-descriptions-item label="响应编码">{{ record.response_encoding }}</el-descriptions-item>
          <el-descriptions-item label="请求时间" :span="2">
            {{ formatDateTime(record.request_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="响应时间" :span="2">
            {{ formatDateTime(record.response_time) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 响应头 -->
        <div class="section-title">响应头</div>
        <KeyValueViewer :data="record.response_headers" readonly />

        <!-- 响应体 -->
        <div class="section-title">响应体</div>
        <el-card shadow="never" class="json-viewer">
          <pre v-if="record.response_body && typeof record.response_body === 'object'">{{ formatJson(record.response_body) }}</pre>
          <pre v-else-if="record.response_body_text">{{ record.response_body_text }}</pre>
          <pre v-else>{{ formatJson(record.response_body) }}</pre>
        </el-card>
      </el-tab-pane>

      <!-- 断言结果 -->
      <el-tab-pane name="assertions">
        <template #label>
          <span>断言结果</span>
          <el-badge
            :value="record.assertions_passed + record.assertions_failed"
            :type="record.assertions_failed > 0 ? 'danger' : 'success'"
            class="badge"
          />
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="总断言数">
            {{ record.assertions_passed + record.assertions_failed }}
          </el-descriptions-item>
          <el-descriptions-item label="通过数">
            <el-tag type="success">{{ record.assertions_passed }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败数">
            <el-tag type="danger">{{ record.assertions_failed }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="record.assertion_results" stripe border>
          <el-table-column prop="assertion_type" label="断言类型" width="150">
            <template #default="{ row }">
              {{ getAssertionTypeText(row.assertion_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="expected" label="预期值" min-width="150" show-overflow-tooltip />
          <el-table-column prop="actual" label="实际值" min-width="150" show-overflow-tooltip />
          <el-table-column prop="passed" label="结果" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                {{ row.passed ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <!-- 错误信息 -->
      <el-tab-pane label="错误信息" name="error" v-if="record.status === 'ERROR' || record.status === 'FAILED'">
        <el-alert
          :title="record.error_type || '错误'"
          :type="record.status === 'ERROR' ? 'error' : 'warning'"
          :description="record.error_message"
          :closable="false"
          show-icon
        />

        <div v-if="record.stack_trace" class="section-title" style="margin-top: 20px">
          错误堆栈
        </div>
        <el-card v-if="record.stack_trace" shadow="never" class="stack-trace">
          <pre>{{ record.stack_trace }}</pre>
        </el-card>
      </el-tab-pane>

      <!-- 数据提取 -->
      <el-tab-pane name="extraction" v-if="Object.keys(record.extraction_results).length > 0">
        <template #label>
          <span>数据提取</span>
          <el-badge :value="Object.keys(record.extraction_results).length" type="primary" class="badge" />
        </template>
        <el-table :data="extractionResultsList" stripe border>
          <el-table-column prop="key" label="变量名" width="200" />
          <el-table-column prop="path" label="提取路径" min-width="200" />
          <el-table-column prop="value" label="提取值" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 元信息 -->
      <el-tab-pane label="元信息" name="meta">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行来源">
            {{ getExecutionSourceText(record.execution_source) }}
          </el-descriptions-item>
          <el-descriptions-item label="执行批次">
            {{ record.execution_batch || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="重试次数">{{ record.retry_count }}</el-descriptions-item>
          <el-descriptions-item label="是否收藏">
            <el-tag :type="record.is_favorite ? 'warning' : 'info'" size="small">
              {{ record.is_favorite ? '已收藏' : '未收藏' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行者">
            {{ record.executed_by_name || `ID: ${record.executed_by}` }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ formatDateTime(record.created_time) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="record.test_case_name" class="section-title">关联测试用例</div>
        <el-descriptions v-if="record.test_case_name" :column="1" border>
          <el-descriptions-item label="测试用例">{{ record.test_case_name }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="record.environment_name" class="section-title">执行环境</div>
        <el-descriptions v-if="record.environment_name" :column="1" border>
          <el-descriptions-item label="环境">{{ record.environment_name }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">元数据</div>
        <el-card shadow="never" class="json-viewer">
          <pre>{{ formatJson(record.metadata) }}</pre>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('close')">关闭</el-button>
      <el-button type="primary" @click="handleCopyCurl" :icon="DocumentCopy">复制cURL</el-button>
      <el-button type="success" @click="handleExport" :icon="Download">导出</el-button>
      <el-button type="warning" @click="handleReExecute" :icon="RefreshRight">重新执行</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Download, RefreshRight } from '@element-plus/icons-vue'
import type { HttpExecutionRecord } from '../../types/http'
import KeyValueViewer from './KeyValueViewer.vue'

interface Props {
  record: HttpExecutionRecord
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const activeTab = ref('request')

// 提取结果列表
const extractionResultsList = computed(() => {
  return Object.entries(props.record.extraction_results).map(([key, value]) => ({
    key,
    path: value.path,
    value: value.value,
    type: value.type
  }))
})

// 格式化JSON
const formatJson = (data: any) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 获取方法标签类型
const getMethodTagType = (method: string) => {
  const types: Record<string, any> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info'
  }
  return types[method] || ''
}

// 获取状态类型
const getStatusType = (status: number | null) => {
  if (!status) return 'info'
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400 && status < 500) return 'danger'
  if (status >= 500) return 'danger'
  return 'info'
}

// 获取断言类型文本
const getAssertionTypeText = (type: string) => {
  const texts: Record<string, string> = {
    status_code: '状态码',
    response_time: '响应时间',
    response_body: '响应体',
    response_headers: '响应头',
    json_value: 'JSON值',
    text_contains: '文本包含',
    json_schema: 'JSON Schema'
  }
  return texts[type] || type
}

// 获取执行来源文本
const getExecutionSourceText = (source: string) => {
  const texts: Record<string, string> = {
    MANUAL: '手动执行',
    SCHEDULED: '定时执行',
    BATCH: '批量执行',
    API: 'API调用',
    DIRECT_HTTP: '直接HTTP'
  }
  return texts[source] || source
}

// 复制cURL命令
const handleCopyCurl = () => {
  let curl = `curl -X ${props.record.request_method}`

  // 添加请求头
  Object.entries(props.record.request_headers).forEach(([key, value]) => {
    curl += ` \\\n  -H '${key}: ${value}'`
  })

  // 添加请求体
  if (props.record.request_body) {
    const body = typeof props.record.request_body === 'string'
      ? props.record.request_body
      : JSON.stringify(props.record.request_body)
    curl += ` \\\n  -d '${body}'`
  }

  curl += ` \\\n  '${props.record.request_url}'`

  navigator.clipboard.writeText(curl).then(() => {
    ElMessage.success('cURL命令已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 导出
const handleExport = () => {
  const data = {
    request: {
      method: props.record.request_method,
      url: props.record.request_url,
      headers: props.record.request_headers,
      params: props.record.request_params,
      body: props.record.request_body
    },
    response: {
      status: props.record.response_status,
      headers: props.record.response_headers,
      body: props.record.response_body || props.record.response_body_text
    },
    assertions: props.record.assertion_results,
    execution: {
      status: props.record.status,
      duration: props.record.duration,
      error: props.record.error_message
    }
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution-record-${props.record.id}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 重新执行
const handleReExecute = () => {
  ElMessage.info('重新执行功能开发中')
}
</script>

<style scoped>
.execution-record-detail {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 20px 0 10px;
  color: #303133;
}

.status-text {
  margin-left: 10px;
  color: #909399;
}

.json-viewer {
  background: #f5f7fa;
}

.json-viewer pre {
  margin: 0;
  padding: 15px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
}

.stack-trace {
  background: #fef0f0;
}

.stack-trace pre {
  margin: 0;
  padding: 15px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #f56c6c;
  white-space: pre-wrap;
  word-break: break-all;
}

.badge {
  margin-left: 10px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #dcdfe6;
}
</style>
