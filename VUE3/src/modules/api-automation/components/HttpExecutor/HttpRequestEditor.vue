<!--
  HttpRequestEditor.vue - HTTP 请求编辑器主组件

  提供完整的 HTTP 请求构建和发送功能：
  - 请求方法和 URL 输入（支持 Base URL + Path 拼接）
  - 查询参数编辑（KeyValueEditor）
  - 请求头编辑（KeyValueEditor，含常用 Header 快捷填充）
  - 请求体编辑（支持 JSON / 表单 / 原始文本 / 文件上传四种类型）
  - 变量配置（VariableEditor，支持 ${变量名} 语法）
  - 高级设置（超时、重定向、SSL 验证）
  - 响应结果展示（响应体、响应头、Cookie、测试断言结果）
  - 保存为测试用例功能

  请求通过后端代理接口发送，避免浏览器 CORS 限制。
-->
<template>
  <div class="http-request-editor">
    <el-card class="request-card">
      <template #header>
        <div class="card-header">
          <span>HTTP请求编辑器</span>
          <div class="header-actions">
            <el-button type="primary" @click="executeRequest" :loading="executing">
              <el-icon><CaretRight /></el-icon>
              发送请求
            </el-button>
            <el-button @click="saveAsTestCase">
              <el-icon><Document /></el-icon>
              保存为测试用例
            </el-button>
          </div>
        </div>
      </template>

      <!-- 请求方法和URL -->
      <div class="request-line">
        <div class="method-selector">
          <el-select v-model="request.method" placeholder="方法" style="width: 120px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="HEAD" value="HEAD" />
            <el-option label="OPTIONS" value="OPTIONS" />
          </el-select>
        </div>
        <div class="url-input">
          <el-input
            v-model="request.url"
            placeholder="输入请求URL，如：/api/users/${user_id}"
            @keyup.enter="executeRequest"
          >
            <template #prepend>
              <el-input
                v-model="request.baseUrl"
                placeholder="Base URL"
                style="width: 200px"
              />
            </template>
          </el-input>
        </div>
      </div>

      <!-- 请求配置标签页 -->
      <el-tabs v-model="activeTab" class="request-tabs" @tab-click="handleTabClick">
        <!-- 查询参数 -->
        <el-tab-pane label="查询参数" name="params">
          <KeyValueEditor
            v-model="request.params"
            placeholder-key="参数名"
            placeholder-value="参数值"
            :enable-variables="true"
          />
        </el-tab-pane>

        <!-- 请求头 -->
        <el-tab-pane label="请求头" name="headers">
          <KeyValueEditor
            v-model="request.headers"
            placeholder-key="Header名称"
            placeholder-value="Header值"
            :enable-variables="true"
            :common-headers="commonHeaders"
          />
        </el-tab-pane>

        <!-- 请求体 -->
        <el-tab-pane label="请求体" name="body" v-if="hasBody">
          <div class="body-editor">
            <div class="body-type-selector">
              <el-radio-group v-model="request.bodyType" @change="onBodyTypeChange">
                <el-radio label="none">无</el-radio>
                <el-radio label="json">JSON</el-radio>
                <el-radio label="form">表单数据</el-radio>
                <el-radio label="raw">原始文本</el-radio>
                <el-radio label="file">文件上传</el-radio>
              </el-radio-group>
            </div>

            <!-- JSON编辑器 -->
            <div v-if="request.bodyType === 'json'" class="json-editor">
              <el-input
                v-model="request.body.json"
                type="textarea"
                :rows="10"
                placeholder='{"key": "value"}'
                @blur="validateJson"
              />
              <div v-if="jsonError" class="error-text">
                {{ jsonError }}
              </div>
            </div>

            <!-- 表单数据编辑器 -->
            <div v-else-if="request.bodyType === 'form'" class="form-editor">
              <KeyValueEditor
                v-model="request.body.form"
                placeholder-key="字段名"
                placeholder-value="字段值"
                :enable-variables="true"
              />
            </div>

            <!-- 原始文本编辑器 -->
            <div v-else-if="request.bodyType === 'raw'" class="raw-editor">
              <el-input
                v-model="request.body.raw"
                type="textarea"
                :rows="10"
                placeholder="输入原始请求体内容"
              />
            </div>

            <!-- 文件上传 -->
            <div v-else-if="request.bodyType === 'file'" class="file-editor">
              <FileUploader v-model="request.body.files" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 变量配置 -->
        <el-tab-pane label="变量" name="variables">
          <VariableEditor v-model="request.variables" />
        </el-tab-pane>

        <!-- 高级设置 -->
        <el-tab-pane label="高级设置" name="advanced">
          <div class="advanced-settings">
            <el-form :model="request.settings" label-width="120px">
              <el-form-item label="请求超时">
                <el-input-number
                  v-model="request.settings.timeout"
                  :min="1"
                  :max="300"
                  controls-position="right"
                />
                <span class="unit">秒</span>
              </el-form-item>
              <el-form-item label="跟随重定向">
                <el-switch v-model="request.settings.followRedirects" />
              </el-form-item>
              <el-form-item label="验证SSL证书">
                <el-switch v-model="request.settings.verifySSL" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 响应结果 -->
    <el-card v-if="response" class="response-card">
      <template #header>
        <div class="response-header">
          <span>响应结果</span>
          <div class="response-stats">
            <el-tag
              :type="getResponseTagType(response.status)"
              size="large"
            >
              {{ response.status }}
            </el-tag>
            <span class="response-time">{{ response.response_time }}ms</span>
            <span class="response-size">{{ formatSize(response.body_size) }}</span>
          </div>
        </div>
      </template>

      <el-tabs v-model="responseActiveTab">
        <el-tab-pane label="响应体" name="body">
          <div class="response-body">
            <div class="response-actions">
              <el-button
                size="small"
                @click="copyResponseBody"
                :disabled="!response.body"
              >
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
              <el-button
                size="small"
                @click="downloadResponseBody"
                :disabled="!response.body"
              >
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button
                size="small"
                @click="formatResponseBody"
                v-if="isJsonResponse"
              >
                <el-icon><MagicStick /></el-icon>
                格式化
              </el-button>
            </div>
            <pre class="response-content" v-html="formattedResponse"></pre>
          </div>
        </el-tab-pane>

        <el-tab-pane label="响应头" name="headers">
          <KeyValueViewer
            :data="response.headers"
            :readonly="true"
          />
        </el-tab-pane>

        <el-tab-pane label="Cookie" name="cookies" v-if="responseCookies.length > 0">
          <KeyValueViewer
            :data="responseCookies"
            :readonly="true"
          />
        </el-tab-pane>

        <el-tab-pane label="测试结果" name="test" v-if="request.tests && request.tests.length > 0">
          <TestResults :tests="testResults" :response="response" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 保存为测试用例对话框 -->
    <SaveTestCaseDialog
      v-model="saveDialogVisible"
      :request="request"
      @saved="onTestCaseSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CaretRight,
  Document,
  DocumentCopy,
  Download,
  MagicStick
} from '@element-plus/icons-vue'
import KeyValueEditor from './KeyValueEditor.vue'
import VariableEditor from './VariableEditor.vue'
import FileUploader from './FileUploader.vue'
import KeyValueViewer from './KeyValueViewer.vue'
import TestResults from './TestResults.vue'
import SaveTestCaseDialog from './SaveTestCaseDialog.vue'
import { useHttpExecutor } from '../../composables/useHttpExecutor'
import type { HttpRequest, HttpResponse } from '../../types/http'

// 响应式数据
const activeTab = ref('params')
const responseActiveTab = ref('body')
const executing = ref(false)
const saveDialogVisible = ref(false)
const jsonError = ref('')

// HTTP执行器
const { executeHttpRequest } = useHttpExecutor()

// 请求数据
const request = reactive<HttpRequest>({
  method: 'GET',
  baseUrl: '',
  url: '',
  params: [],
  headers: [],
  bodyType: 'none',
  body: {
    json: '',
    form: [],
    raw: '',
    files: []
  },
  variables: [],
  settings: {
    timeout: 30,
    followRedirects: true,
    verifySSL: true
  }
})

// 响应数据
const response = ref<HttpResponse | null>(null)

// 计算属性
const hasBody = computed(() => {
  return ['POST', 'PUT', 'PATCH'].includes(request.method)
})

const commonHeaders = computed(() => [
  { key: 'Content-Type', value: 'application/json' },
  { key: 'Content-Type', value: 'application/x-www-form-urlencoded' },
  { key: 'Content-Type', value: 'multipart/form-data' },
  { key: 'Authorization', value: 'Bearer ${token}' },
  { key: 'Accept', value: 'application/json' },
  { key: 'User-Agent', value: 'API-Automation-Platform/1.0' }
])

const isJsonResponse = computed(() => {
  if (!response.value) return false
  const contentType = response.value.headers['content-type'] || ''
  return contentType.includes('application/json')
})

const formattedResponse = computed(() => {
  if (!response.value || !response.value.body) return ''

  if (isJsonResponse.value && typeof response.value.body === 'object') {
    return JSON.stringify(response.value.body, null, 2)
  }

  return response.value.body
})

const responseCookies = computed(() => {
  if (!response.value) return []

  const cookies: Array<{ key: string; value: string }> = []
  const setCookieHeader = response.value.headers['set-cookie']

  if (setCookieHeader) {
    const cookieArray = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader]
    cookieArray.forEach(cookie => {
      const [name, ...rest] = cookie.split(';')
      const [key, value] = name.split('=')
      if (key && value) {
        cookies.push({ key: key.trim(), value: value.trim() })
      }
    })
  }

  return cookies
})

const testResults = computed(() => {
  // 这里应该运行请求中定义的测试
  // 暂时返回空数组
  return []
})

// 方法
const executeRequest = async () => {
  try {
    executing.value = true
    response.value = await executeHttpRequest(request)

    if (response.value.error) {
      ElMessage.error(`请求失败: ${response.value.error}`)
    } else {
      ElMessage.success('请求发送成功')
      // 自动切换到响应结果标签
      responseActiveTab.value = 'body'
    }
  } catch (error) {
    console.error('执行请求失败:', error)
    ElMessage.error('执行请求失败')
  } finally {
    executing.value = false
  }
}

const saveAsTestCase = () => {
  saveDialogVisible.value = true
}

const onTestCaseSaved = () => {
  ElMessage.success('测试用例保存成功')
}

const handleTabClick = (tab: any) => {
  // 标签切换时的处理
}

const onBodyTypeChange = (type: string) => {
  // 清空之前的body数据
  request.body.json = ''
  request.body.form = []
  request.body.raw = ''
  request.body.files = []

  // 设置默认Content-Type
  if (type === 'json') {
    const existingContentType = request.headers.find(h => h.key.toLowerCase() === 'content-type')
    if (!existingContentType) {
      request.headers.push({ key: 'Content-Type', value: 'application/json' })
    }
  } else if (type === 'form') {
    const existingContentType = request.headers.find(h => h.key.toLowerCase() === 'content-type')
    if (existingContentType) {
      existingContentType.value = 'application/x-www-form-urlencoded'
    } else {
      request.headers.push({ key: 'Content-Type', value: 'application/x-www-form-urlencoded' })
    }
  }
}

const validateJson = () => {
  if (!request.body.json) {
    jsonError.value = ''
    return
  }

  try {
    JSON.parse(request.body.json)
    jsonError.value = ''
  } catch (error) {
    jsonError.value = 'JSON格式错误: ' + (error as Error).message
  }
}

const getResponseTagType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400 && status < 500) return 'danger'
  if (status >= 500) return 'danger'
  return 'info'
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const copyResponseBody = async () => {
  if (!response.value?.body) return

  try {
    const text = typeof response.value.body === 'string'
      ? response.value.body
      : JSON.stringify(response.value.body, null, 2)

    await navigator.clipboard.writeText(text)
    ElMessage.success('响应内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

const downloadResponseBody = () => {
  if (!response.value?.body) return

  try {
    const content = typeof response.value.body === 'string'
      ? response.value.body
      : JSON.stringify(response.value.body, null, 2)

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `response_${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    ElMessage.success('响应内容已下载')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const formatResponseBody = () => {
  if (!response.value?.body || typeof response.value.body !== 'object') return

  // 这个功能已经在formattedResponse计算属性中实现
  ElMessage.success('JSON已格式化')
}

// 监听方法变化，自动调整bodyType
watch(() => request.method, (newMethod) => {
  if (!['POST', 'PUT', 'PATCH'].includes(newMethod)) {
    request.bodyType = 'none'
  } else if (request.bodyType === 'none') {
    request.bodyType = 'json'
  }
})

// 监听URL变化，提取变量
watch([() => request.baseUrl, () => request.url], () => {
  extractVariablesFromUrl()
}, { deep: true })

const extractVariablesFromUrl = () => {
  const fullUrl = (request.baseUrl + request.url).match(/\$\{[^}]+\}/g)
  if (fullUrl) {
    fullUrl.forEach(match => {
      const varName = match.slice(2, -1)
      if (!request.variables.find(v => v.name === varName)) {
        request.variables.push({
          name: varName,
          value: '',
          description: `从URL提取的变量: ${varName}`
        })
      }
    })
  }
}
</script>

<style scoped>
.http-request-editor {
  padding: 20px;
}

.request-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.request-line {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 10px;
}

.method-selector {
  flex-shrink: 0;
}

.url-input {
  flex: 1;
}

.request-tabs {
  margin-top: 20px;
}

.body-editor {
  padding: 10px 0;
}

.body-type-selector {
  margin-bottom: 15px;
}

.json-editor {
  position: relative;
}

.form-editor {
  padding: 10px 0;
}

.raw-editor {
  padding: 10px 0;
}

.file-editor {
  padding: 10px 0;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

.response-card {
  margin-top: 20px;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.response-stats {
  display: flex;
  align-items: center;
  gap: 15px;
}

.response-time {
  color: #67c23a;
  font-weight: bold;
}

.response-size {
  color: #909399;
  font-size: 12px;
}

.response-body {
  position: relative;
}

.response-actions {
  position: absolute;
  top: -30px;
  right: 0;
  display: flex;
  gap: 5px;
}

.response-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 500px;
  overflow-y: auto;
}

.advanced-settings {
  padding: 10px 0;
}

.unit {
  margin-left: 10px;
  color: #909399;
}
</style>