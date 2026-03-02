<!--
  EnvironmentDetail.vue - 环境详情查看组件

  展示测试环境的完整信息，包含四个标签页：
  1. 基本信息：环境 ID、项目、Base URL、创建/更新时间
  2. 全局请求头：表格展示，支持复制
  3. 全局变量：表格展示，含使用示例（${变量名} 格式），支持复制
  4. 配置预览：JSON 配置和 cURL 示例，支持复制

  操作功能：
  - 测试连接：发送请求验证环境可达性，展示详细的请求/响应信息
  - 设为默认环境
  - 启用/禁用环境
  - 导出配置为 JSON 文件
-->
<template>
  <div class="environment-detail">
    <div class="detail-header">
      <div class="env-info">
        <el-icon class="env-icon" :size="40" color="#409eff"><Odometer /></el-icon>
        <div class="env-basic">
          <h3 class="env-name">
            {{ environment.name }}
            <el-tag v-if="environment.is_default" type="warning" size="small" style="margin-left: 8px;">
              <el-icon><Star /></el-icon>
              默认环境
            </el-tag>
            <el-tag :type="environment.is_active ? 'success' : 'danger'" size="small" style="margin-left: 8px;">
              {{ environment.is_active ? '已启用' : '已禁用' }}
            </el-tag>
          </h3>
          <p class="env-description">{{ environment.description || '暂无描述' }}</p>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="环境ID">
            #{{ environment.id }}
          </el-descriptions-item>
          <el-descriptions-item label="所属项目">
            <el-tag size="small">{{ environment.project_name }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Base URL" :span="2">
            <div class="url-display">
              <el-link :href="environment.base_url" target="_blank" type="primary">
                <el-icon><Link /></el-icon>
                {{ environment.base_url }}
              </el-link>
              <el-button size="small" text @click="copyToClipboard(environment.base_url)">
                <el-icon><DocumentCopy /></el-icon>
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(environment.created_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(environment.updated_time) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <el-tab-pane name="headers">
        <template #label>
          <span>
            <el-icon><DocumentCopy /></el-icon>
            全局请求头
            <el-badge :value="Object.keys(environment.global_headers || {}).length" :max="99" />
          </span>
        </template>
        <div class="tab-content">
          <div class="content-header">
            <span>全局请求头将在所有请求中自动添加</span>
            <el-button size="small" @click="copyHeaders" v-if="headersList.length > 0">
              <el-icon><DocumentCopy /></el-icon>
              复制全部
            </el-button>
          </div>
          <el-table
            :data="headersList"
            style="width: 100%"
            empty-text="暂无全局请求头"
            max-height="400"
          >
            <el-table-column prop="key" label="Header名称" min-width="150" />
            <el-table-column prop="value" label="Header值" min-width="250" show-overflow-tooltip />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button size="small" text @click="copyToClipboard(row.value)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane name="variables">
        <template #label>
          <span>
            <el-icon><Collection /></el-icon>
            全局变量
            <el-badge :value="Object.keys(environment.global_variables || {}).length" :max="99" />
          </span>
        </template>
        <div class="tab-content">
          <div class="content-header">
            <span>全局变量可在请求中使用 <code>${variable_name}</code> 格式引用</span>
            <el-button size="small" @click="copyVariables" v-if="variablesList.length > 0">
              <el-icon><DocumentCopy /></el-icon>
              复制全部
            </el-button>
          </div>
          <el-table
            :data="variablesList"
            style="width: 100%"
            empty-text="暂无全局变量"
            max-height="400"
          >
            <el-table-column prop="key" label="变量名称" min-width="150">
              <template #default="{ row }">
                <code>{{ row.key }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="value" label="变量值" min-width="250" show-overflow-tooltip />
            <el-table-column prop="usage" label="使用示例" min-width="180">
              <template #default="{ row }">
                <el-tag size="small" type="info">${{ row.key }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button size="small" text @click="copyToClipboard(row.value)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane name="preview">
        <template #label>
          <span>
            <el-icon><View /></el-icon>
            配置预览
          </span>
        </template>
        <div class="tab-content">
          <el-alert
            type="info"
            :closable="false"
            style="margin-bottom: 16px"
          >
            以下是该环境的完整配置，可用于复制或导出
          </el-alert>

          <div class="json-preview">
            <div class="preview-header">
              <span>JSON 配置</span>
              <el-button size="small" @click="copyConfigJson">
                <el-icon><DocumentCopy /></el-icon>
                复制 JSON
              </el-button>
            </div>
            <pre class="json-content">{{ configJson }}</pre>
          </div>

          <div class="cURL-preview" style="margin-top: 20px;">
            <div class="preview-header">
              <span>cURL 示例</span>
              <el-button size="small" @click="copyCurl">
                <el-icon><DocumentCopy /></el-icon>
                复制 cURL
              </el-button>
            </div>
            <pre class="curl-content">{{ curlCommand }}</pre>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-divider>操作</el-divider>

    <div class="actions-section">
      <el-space wrap>
        <el-button type="primary" @click="handleTestConnection">
          <el-icon><Connection /></el-icon>
          测试连接
        </el-button>
        <el-button v-if="!environment.is_default" type="warning" @click="handleSetDefault">
          <el-icon><Star /></el-icon>
          设为默认
        </el-button>
        <el-button :type="environment.is_active ? 'warning' : 'success'" @click="handleToggleStatus">
          <el-icon><Switch /></el-icon>
          {{ environment.is_active ? '禁用环境' : '启用环境' }}
        </el-button>
        <el-button type="info" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出配置
        </el-button>
      </el-space>
    </div>

    <!-- 连接测试结果对话框 -->
    <el-dialog
      v-model="showTestResultDialog"
      title="连接测试结果"
      width="900px"
    >
      <div v-if="testResult" class="test-result-content">
        <!-- 结果状态提示 -->
        <el-alert
          :type="testResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <template #title>
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </template>
        </el-alert>

        <!-- 基本信息 -->
        <el-descriptions :column="2" border style="margin-top: 20px" size="small">
          <el-descriptions-item label="目标URL" :span="2">
            <el-link :href="testResult.url" target="_blank" type="primary">
              {{ testResult.url }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="HTTP状态码">
            <el-tag v-if="testResult.status_code" :type="getStatusCodeColor(testResult.status_code)">
              {{ testResult.status_code }}
              <span v-if="testResult.response?.reason" style="margin-left: 4px">
                {{ testResult.response.reason }}
              </span>
            </el-tag>
            <el-tag v-else type="danger">无响应</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            <el-tag :type="getResponseTimeColor(testResult.response_time)">
              {{ testResult.response_time }}ms
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="消息" :span="2" v-if="testResult.message">
            {{ testResult.message }}
          </el-descriptions-item>
          <el-descriptions-item label="响应大小" v-if="testResult.response?.size">
            {{ formatBytes(testResult.response.size) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 请求信息 -->
        <el-divider content-position="left">
          <el-icon><View /></el-icon>
          请求信息
        </el-divider>
        <div class="request-info" v-if="testResult.request">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="请求方法">
              <el-tag type="primary">{{ testResult.request.method }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="请求URL">
              <code>{{ testResult.request.url }}</code>
            </el-descriptions-item>
          </el-descriptions>

          <div class="headers-section" style="margin-top: 12px">
            <div class="section-header">
              <span>请求头 (Request Headers)</span>
              <el-button size="small" text @click="copyToClipboard(JSON.stringify(testResult.request.headers, null, 2))">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatHeaders(testResult.request.headers) }}</pre>
            </div>
          </div>
        </div>

        <!-- 响应信息 -->
        <template v-if="testResult.response">
          <el-divider content-position="left">
            <el-icon><View /></el-icon>
            响应信息
          </el-divider>

          <!-- 响应头 -->
          <div class="response-headers">
            <div class="section-header">
              <span>响应头 (Response Headers)</span>
              <el-button size="small" text @click="copyToClipboard(JSON.stringify(testResult.response.headers, null, 2))">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatHeaders(testResult.response.headers) }}</pre>
            </div>
          </div>

          <!-- 响应体 -->
          <div class="response-body" style="margin-top: 16px" v-if="testResult.response.body !== null">
            <div class="section-header">
              <span>响应体 (Response Body)</span>
              <el-button size="small" text @click="copyToClipboard(typeof testResult.response.body === 'object' ? JSON.stringify(testResult.response.body, null, 2) : testResult.response.body)">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatResponseBody(testResult.response.body) }}</pre>
            </div>
          </div>
        </template>

        <!-- 错误信息 -->
        <template v-if="testResult.error">
          <el-divider content-position="left">
            <el-icon><Warning style="color: #f56c6c;" /></el-icon>
            错误详情
          </el-divider>
          <div class="error-info">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="错误类型">
                <el-tag type="danger">{{ testResult.error.type }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="错误消息">
                {{ testResult.error.message }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="error-details" style="margin-top: 12px" v-if="testResult.error.details">
              <div class="section-header">
                <span>详细错误日志</span>
                <el-button size="small" text @click="copyToClipboard(testResult.error.details)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
              <div class="code-block error-code">
                <pre>{{ testResult.error.details }}</pre>
              </div>
            </div>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Connection, Star, Switch, Odometer, Link, DocumentCopy,
  Collection, View, Download, Warning
} from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'

import { environmentApi } from '../api/environment'

import type { ApiTestEnvironment } from '../types/environment'

interface Props {
  environment: ApiTestEnvironment
}

const props = defineProps<Props>()

// 活动标签
const activeTab = ref('basic')
const showTestResultDialog = ref(false)
const testResult = ref<any>(null)

// 计算属性
const headersList = computed(() => {
  return Object.entries(props.environment.global_headers || {}).map(([key, value]) => ({
    key,
    value: typeof value === 'string' ? value : JSON.stringify(value)
  }))
})

const variablesList = computed(() => {
  return Object.entries(props.environment.global_variables || {}).map(([key, value]) => ({
    key,
    value: typeof value === 'string' ? value : JSON.stringify(value),
    usage: `\${${key}}`
  }))
})

const configJson = computed(() => {
  return JSON.stringify({
    name: props.environment.name,
    description: props.environment.description,
    base_url: props.environment.base_url,
    global_headers: props.environment.global_headers,
    global_variables: props.environment.global_variables
  }, null, 2)
})

const curlCommand = computed(() => {
  const baseUrl = props.environment.base_url
  const headers = Object.entries(props.environment.global_headers || {})
    .map(([key, value]) => `  -H '${key}: ${value}'`)
    .join(' \\\n')

  return `curl -X GET '${baseUrl}' \\\n${headers || ''}`
})

// 方法
const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const copyHeaders = () => {
  copyToClipboard(JSON.stringify(props.environment.global_headers, null, 2))
}

const copyVariables = () => {
  copyToClipboard(JSON.stringify(props.environment.global_variables, null, 2))
}

const copyConfigJson = () => {
  copyToClipboard(configJson.value)
}

const copyCurl = () => {
  copyToClipboard(curlCommand.value)
}

const handleTestConnection = async () => {
  try {
    ElMessage.info('正在测试连接...')
    const response = await environmentApi.testConnection(props.environment.id)

    testResult.value = response
    showTestResultDialog.value = true

    if (response.success) {
      ElMessage.success(`连接测试成功，响应时间: ${response.response_time}ms`)
    } else {
      ElMessage.warning(`连接测试完成: ${response.message || '请查看详情'}`)
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
    console.error('Test connection error:', error)
  }
}

const handleSetDefault = async () => {
  if (props.environment.is_default) {
    return
  }

  try {
    await environmentApi.setDefault(props.environment.id)
    ElMessage.success('设置默认环境成功')
  } catch (error) {
    ElMessage.error('设置默认环境失败')
    console.error('Set default environment error:', error)
  }
}

const handleToggleStatus = async () => {
  try {
    await environmentApi.updateEnvironment(props.environment.id, {
      is_active: !props.environment.is_active
    })

    ElMessage.success(props.environment.is_active ? '环境已禁用' : '环境已启用')
  } catch (error) {
    ElMessage.error('状态更新失败')
    console.error('Toggle environment status error:', error)
  }
}

const handleExport = () => {
  try {
    const blob = new Blob([configJson.value], { type: 'application/json' })
    saveAs(blob, `environment_${props.environment.name}_${Date.now()}.json`)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export environment error:', error)
  }
}

// 连接测试相关辅助方法
const getStatusCodeColor = (code: number | null) => {
  if (!code) return 'danger'
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  return 'danger'
}

const getResponseTimeColor = (time: number) => {
  if (time < 200) return 'success'
  if (time < 500) return 'warning'
  return 'danger'
}

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatHeaders = (headers: Record<string, string> | null) => {
  if (!headers) return ''
  return Object.entries(headers)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n')
}

const formatResponseBody = (body: any) => {
  if (body === null || body === undefined) return ''
  if (typeof body === 'object') {
    return JSON.stringify(body, null, 2)
  }
  return String(body)
}
</script>

<style scoped>
.environment-detail {
  padding: 0;
}

.detail-header {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.env-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.env-icon {
  flex-shrink: 0;
}

.env-basic {
  flex: 1;
}

.env-name {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.env-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.detail-tabs {
  margin-bottom: 20px;
}

.tab-content {
  padding: 16px 0;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f4f4f5;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
}

.content-header code {
  background-color: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #e83e8c;
}

.url-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.actions-section {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

/* 预览 */
.json-preview,
.cURL-preview {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
}

.json-content,
.curl-content {
  margin: 0;
  padding: 16px;
  background-color: #fafafa;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

/* 测试结果 */
.test-result-content {
  padding: 10px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px 4px 0 0;
  border: 1px solid #dcdfe6;
  border-bottom: none;
  font-weight: 500;
  font-size: 13px;
  color: #303133;
}

.code-block {
  background-color: #fafafa;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.code-block pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-code {
  background-color: #fef0f0;
  border-color: #fbc4c4;
}

.error-code pre {
  color: #f56c6c;
}

.request-info,
.error-info {
  margin-top: 12px;
}

.response-headers,
.response-body {
  margin-top: 12px;
}

.response-headers .code-block,
.response-body .code-block {
  max-height: 250px;
}

.headers-section {
  margin-top: 12px;
}

:deep(.el-descriptions) {
  .el-descriptions__label {
    font-weight: 600;
  }
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-tabs__item) {
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.el-table) {
  .el-table__header-wrapper {
    background-color: #f5f7fa;
  }
}

:deep(.el-badge) {
  margin-left: 4px;
}
</style>
