<template>
  <div class="testcase-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button
            :type="editorMode === 'builder' ? 'primary' : ''"
            @click="editorMode = 'builder'"
          >
            <el-icon><Edit /></el-icon>
            请求构建器
          </el-button>
          <el-button
            :type="editorMode === 'code' ? 'primary' : ''"
            @click="editorMode = 'code'"
          >
            <el-icon><Document /></el-icon>
            代码编辑
          </el-button>
          <el-button
            :type="editorMode === 'split' ? 'primary' : ''"
            @click="editorMode = 'split'"
          >
            <el-icon><Grid /></el-icon>
            分屏预览
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button @click="showCurlImportDialog = true">
          <el-icon><Download /></el-icon>
          导入cURL
        </el-button>
        <el-button @click="exportAsCurl">
          <el-icon><Upload /></el-icon>
          导出cURL
        </el-button>
        <el-button @click="showTemplateDialog = true">
          <el-icon><Tickets /></el-icon>
          从模板加载
        </el-button>
      </div>

      <div class="toolbar-right">
        <el-button
          type="success"
          :loading="testing"
          @click="handleTest"
          :disabled="!localForm.url"
        >
          <el-icon><Connection /></el-icon>
          测试请求
        </el-button>
      </div>
    </div>

    <!-- 请求构建器模式 -->
    <div v-show="editorMode === 'builder' || editorMode === 'split'" class="editor-content">
      <!-- 请求配置 -->
      <el-card class="request-line-card" shadow="never">
        <div class="request-line">
          <el-select v-model="localForm.method" style="width: 120px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="PATCH" value="PATCH" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
          <el-input
            v-model="localForm.url"
            placeholder="输入请求URL，如 /api/v1/users"
            class="url-input"
          >
            <template #prepend>
              <el-dropdown trigger="click" @command="handleBaseUrlSelect">
                <span class="base-url-selector">
                  {{ selectedBaseUrlLabel }}
                  <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="env in environmentOptions"
                      :key="env.value"
                      :command="env.value"
                    >
                      <el-icon v-if="selectedBaseUrl === env.value"><Check /></el-icon>
                      {{ env.label }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-input>
        </div>
      </el-card>

      <!-- 参数编辑器 -->
      <el-row :gutter="20" class="params-section">
        <el-col :span="editorMode === 'split' ? 12 : 24">
          <!-- Query参数 -->
          <el-card class="param-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span><el-icon><Collection /></el-icon> Query参数</span>
                <el-badge :value="queryParams.filter(p => p.key).length" :max="99" />
              </div>
            </template>
            <KeyValueEditor
              v-model="queryParams"
              :show-variables="true"
              @variable-click="handleVariableClick"
            />
          </el-card>

          <!-- Headers -->
          <el-card class="param-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span><el-icon><DocumentCopy /></el-icon> Headers</span>
                <el-badge :value="headers.filter(h => h.key).length" :max="99" />
              </div>
            </template>
            <KeyValueEditor
              v-model="headers"
              :show-variables="true"
              :common-headers="commonHeaders"
              @variable-click="handleVariableClick"
            />
          </el-card>

          <!-- Body -->
          <el-card
            v-if="['POST', 'PUT', 'PATCH'].includes(localForm.method)"
            class="param-card"
            shadow="never"
          >
            <template #header>
              <div class="card-header">
                <span><el-icon><Box /></el-icon> Request Body</span>
                <el-select v-model="bodyType" size="small" style="width: 120px">
                  <el-option label="JSON" value="json" />
                  <el-option label="Form Data" value="form" />
                  <el-option label="Raw" value="raw" />
                </el-select>
              </div>
            </template>

            <!-- JSON编辑器 -->
            <div v-if="bodyType === 'json'" class="json-editor-container">
              <div class="editor-toolbar-mini">
                <el-button size="small" text @click="formatJsonBody">
                  <el-icon><MagicStick /></el-icon>
                  格式化
                </el-button>
                <el-button size="small" text @click="minifyJsonBody">
                  <el-icon><Crop /></el-icon>
                  压缩
                </el-button>
                <el-button size="small" text @click="showJsonSchema = !showJsonSchema">
                  <el-icon><Document /></el-icon>
                  JSON Schema
                </el-button>
                <span v-if="jsonError" class="json-error">{{ jsonError }}</span>
              </div>
              <textarea
                ref="jsonEditorRef"
                v-model="jsonBody"
                class="code-editor"
                :class="{ 'has-error': jsonError }"
                placeholder="输入JSON格式的请求体"
                @input="handleJsonInput"
                @keydown="handleEditorKeydown"
              ></textarea>
            </div>

            <!-- Form Data编辑器 -->
            <KeyValueEditor
              v-else-if="bodyType === 'form'"
              v-model="formBody"
              :show-type="true"
              :show-variables="true"
              @variable-click="handleVariableClick"
            />

            <!-- Raw 编辑器 -->
            <textarea
              v-else
              v-model="rawBody"
              class="code-editor"
              placeholder="输入原始请求体"
              @keydown="handleEditorKeydown"
            ></textarea>
          </el-card>
        </el-col>

        <!-- 预览面板 (分屏模式) -->
        <el-col v-if="editorMode === 'split'" :span="12">
          <el-card class="preview-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span><el-icon><View /></el-icon> 请求预览</span>
                <el-button-group size="small">
                  <el-button
                    :type="previewTab === 'curl' ? 'primary' : ''"
                    @click="previewTab = 'curl'"
                  >
                    cURL
                  </el-button>
                  <el-button
                    :type="previewTab === 'http' ? 'primary' : ''"
                    @click="previewTab = 'http'"
                  >
                    HTTP
                  </el-button>
                  <el-button
                    :type="previewTab === 'json' ? 'primary' : ''"
                    @click="previewTab = 'json'"
                  >
                    JSON
                  </el-button>
                </el-button-group>
              </div>
            </template>

            <div class="preview-content">
              <div v-if="previewTab === 'curl'" class="curl-preview">
                <pre class="preview-code">{{ generatedCurl }}</pre>
                <el-button size="small" @click="copyToClipboard(generatedCurl)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>

              <div v-else-if="previewTab === 'http'" class="http-preview">
                <div class="http-request-line">
                  <span class="http-method">{{ localForm.method }}</span>
                  <span class="http-url">{{ fullUrl }}</span>
                </div>
                <div class="http-headers" v-if="headers.some(h => h.key)">
                  <div v-for="header in headers.filter(h => h.key)" :key="header.key" class="http-header">
                    <span class="header-key">{{ header.key }}:</span>
                    <span class="header-value">{{ header.value }}</span>
                  </div>
                </div>
                <div v-if="requestBodyPreview" class="http-body">
                  <pre>{{ requestBodyPreview }}</pre>
                </div>
              </div>

              <div v-else-if="previewTab === 'json'" class="json-preview">
                <pre class="preview-code">{{ requestBodyJsonPreview }}</pre>
              </div>
            </div>
          </el-card>

          <!-- 响应预览 (如果有测试结果) -->
          <el-card v-if="testResult" class="preview-card response-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span><el-icon><SuccessFilled /></el-icon> 响应预览</span>
                <el-tag :type="testResult.response?.status === 200 ? 'success' : 'danger'">
                  {{ testResult.response?.status }}
                </el-tag>
              </div>
            </template>
            <div class="response-preview">
              <el-tabs v-model="responseTab">
                <el-tab-pane label="Body" name="body">
                  <pre class="response-body">{{ formatResponse(testResult.response?.body) }}</pre>
                </el-tab-pane>
                <el-tab-pane label="Headers" name="headers">
                  <pre class="response-headers">{{ formatHeaders(testResult.response?.headers) }}</pre>
                </el-tab-pane>
              </el-tabs>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 代码编辑模式 -->
    <div v-show="editorMode === 'code'" class="code-mode-container">
      <el-card class="code-editor-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span><el-icon><Document /></el-icon> 完整请求配置 (JSON)</span>
            <div>
              <el-button size="small" @click="validateCodeJson">
                <el-icon><Check /></el-icon>
                验证
              </el-button>
              <el-button size="small" @click="formatCodeJson">
                <el-icon><MagicStick /></el-icon>
                格式化
              </el-button>
            </div>
          </div>
        </template>
        <textarea
          ref="codeEditorRef"
          v-model="codeJson"
          class="code-editor full-editor"
          placeholder="输入完整的请求配置JSON"
          @input="handleCodeJsonInput"
          @keydown="handleEditorKeydown"
        ></textarea>
        <div v-if="codeJsonError" class="json-error-message">
          <el-icon><Warning /></el-icon>
          {{ codeJsonError }}
        </div>
      </el-card>
    </div>

    <!-- cURL导入对话框 -->
    <el-dialog
      v-model="showCurlImportDialog"
      title="导入cURL命令"
      width="600px"
    >
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        粘贴cURL命令，系统将自动解析并填充表单
      </el-alert>
      <el-input
        v-model="curlInput"
        type="textarea"
        :rows="10"
        placeholder="curl -X POST &apos;http://example.com/api&apos; -H &apos;Content-Type: application/json&apos; -d &apos;{&quot;key&quot;:&quot;value&quot;}&apos;"
      />
      <template #footer>
        <el-button @click="showCurlImportDialog = false">取消</el-button>
        <el-button type="primary" @click="importFromCurl">导入</el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplateDialog"
      title="从模板加载"
      width="700px"
    >
      <div class="template-grid">
        <div
          v-for="template in requestTemplates"
          :key="template.name"
          class="template-card"
          @click="loadFromTemplate(template)"
        >
          <div class="template-icon">
            <el-icon><component :is="template.icon" /></el-icon>
          </div>
          <div class="template-name">{{ template.name }}</div>
          <div class="template-desc">{{ template.description }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <!-- 变量选择器对话框 -->
    <el-dialog
      v-model="showVariableDialog"
      title="插入变量"
      width="500px"
    >
      <el-tabs v-model="variableTab">
        <el-tab-pane label="环境变量" name="env">
          <div class="variable-list">
            <div
              v-for="variable in environmentVariables"
              :key="variable.key"
              class="variable-item"
              @click="insertVariable('env.' + variable.key)"
            >
              <code>${{ 'env.' + variable.key }}</code>
              <span class="variable-desc">{{ variable.desc }}</span>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="全局变量" name="global">
          <div class="variable-list">
            <div
              v-for="variable in globalVariables"
              :key="variable.key"
              class="variable-item"
              @click="insertVariable('global.' + variable.key)"
            >
              <code>${{ 'global.' + variable.key }}</code>
              <span class="variable-desc">{{ variable.desc }}</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showVariableDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Edit, Document, Grid, Download, Upload, Tickets, Connection,
  ArrowDown, Collection, DocumentCopy, Box, View, MagicStick,
  Crop, Check, SuccessFilled, Warning, Plus, Delete
} from '@element-plus/icons-vue'
import KeyValueEditor from './KeyValueEditor.vue'
import { httpExecutorApi } from '../api/httpExecutor'

// Props
interface Props {
  modelValue: any
  environmentOptions?: Array<{ label: string; value: number; base_url?: string }>
}

const props = withDefaults(defineProps<Props>(), {
  environmentOptions: () => []
})

// Emits
const emit = defineEmits(['update:modelValue', 'test'])

// Refs
const jsonEditorRef = ref<HTMLTextAreaElement>()
const codeEditorRef = ref<HTMLTextAreaElement>()

// Editor mode
const editorMode = ref<'builder' | 'code' | 'split'>('builder')

// Form data
const localForm = reactive({
  method: 'GET',
  url: '',
  headers: {} as Record<string, string>,
  params: {} as Record<string, string>,
  body: {} as any
})

// Query params
const queryParams = ref<Array<{ key: string; value: string; description: string }>>([])

// Headers
const headers = ref<Array<{ key: string; value: string; description: string }>>([])

// Body
const bodyType = ref('json')
const jsonBody = ref('')
const rawBody = ref('')
const formBody = ref<Array<{ key: string; value: string; type: string }>>([])

// Base URL selection
const selectedBaseUrl = ref<number | null>(null)
const selectedBaseUrlLabel = ref('选择环境')

// JSON validation
const jsonError = ref('')

// Code mode
const codeJson = ref('')
const codeJsonError = ref('')

// Preview
const previewTab = ref('curl')
const responseTab = ref('body')
const testResult = ref<any>(null)

// Dialogs
const showCurlImportDialog = ref(false)
const curlInput = ref('')
const showTemplateDialog = ref(false)
const showVariableDialog = ref(false)
const variableTab = ref('env')

// Testing
const testing = ref(false)

// Common headers for quick add
const commonHeaders = [
  { key: 'Content-Type', value: 'application/json' },
  { key: 'Content-Type', value: 'application/x-www-form-urlencoded' },
  { key: 'Content-Type', value: 'multipart/form-data' },
  { key: 'Accept', value: 'application/json' },
  { key: 'Authorization', value: 'Bearer ${token}' },
  { key: 'User-Agent', value: 'API-Automation-Platform' }
]

// Environment variables for insertion
const environmentVariables = ref([
  { key: 'base_url', desc: '当前环境的基础URL' },
  { key: 'api_key', desc: 'API密钥' },
  { key: 'token', desc: '认证令牌' }
])

// Global variables
const globalVariables = ref([
  { key: 'user_id', desc: '当前用户ID' },
  { key: 'timestamp', desc: '当前时间戳' }
])

// Request templates
const requestTemplates = [
  {
    name: 'GET请求',
    description: '简单的GET请求示例',
    icon: 'Connection',
    template: {
      method: 'GET',
      url: '/api/v1/users',
      headers: { 'Accept': 'application/json' },
      params: { page: '1', limit: '10' }
    }
  },
  {
    name: 'POST JSON',
    description: '发送JSON数据的POST请求',
    icon: 'Plus',
    template: {
      method: 'POST',
      url: '/api/v1/users',
      headers: { 'Content-Type': 'application/json' },
      body: { name: 'Test User', email: 'test@example.com' }
    }
  },
  {
    name: 'PUT更新',
    description: '更新资源的PUT请求',
    icon: 'Edit',
    template: {
      method: 'PUT',
      url: '/api/v1/users/1',
      headers: { 'Content-Type': 'application/json' },
      body: { name: 'Updated Name' }
    }
  },
  {
    name: 'DELETE删除',
    description: '删除资源的DELETE请求',
    icon: 'Delete',
    template: {
      method: 'DELETE',
      url: '/api/v1/users/1',
      headers: {}
    }
  }
]

// Computed
const fullUrl = computed(() => {
  const baseUrl = selectedBaseUrl.value
    ? props.environmentOptions.find(e => e.value === selectedBaseUrl.value)?.base_url || ''
    : ''
  return baseUrl + localForm.url
})

const generatedCurl = computed(() => {
  let curl = `curl -X ${localForm.method} '${fullUrl.value}'`

  // Add headers
  headers.value.filter(h => h.key).forEach(h => {
    curl += ` \\\n  -H '${h.key}: ${h.value}'`
  })

  // Add body
  if (['POST', 'PUT', 'PATCH'].includes(localForm.method)) {
    if (bodyType.value === 'json' && jsonBody.value) {
      curl += ` \\\n  -d '${jsonBody.value}'`
    } else if (bodyType.value === 'raw' && rawBody.value) {
      curl += ` \\\n  -d '${rawBody.value}'`
    } else if (bodyType.value === 'form') {
      const formData = formBody.value
        .filter(f => f.key)
        .map(f => `${f.key}=${f.value}`)
        .join('&')
      if (formData) {
        curl += ` \\\n  -d '${formData}'`
      }
    }
  }

  return curl
})

const requestBodyPreview = computed(() => {
  if (bodyType.value === 'json') return jsonBody.value
  if (bodyType.value === 'raw') return rawBody.value
  if (bodyType.value === 'form') {
    return formBody.value
      .filter(f => f.key)
      .map(f => `${f.key}: ${f.value}`)
      .join('\n')
  }
  return ''
})

const requestBodyJsonPreview = computed(() => {
  if (bodyType.value === 'json' && jsonBody.value) {
    try {
      return JSON.stringify(JSON.parse(jsonBody.value), null, 2)
    } catch {
      return jsonBody.value
    }
  }
  if (bodyType.value === 'form') {
    const obj = formBody.value
      .filter(f => f.key)
      .reduce((acc, f) => ({ ...acc, [f.key]: f.value }), {})
    return JSON.stringify(obj, null, 2)
  }
  return ''
})

// Methods
const handleBaseUrlSelect = (envId: number) => {
  selectedBaseUrl.value = envId
  const env = props.environmentOptions.find(e => e.value === envId)
  if (env) {
    selectedBaseUrlLabel.value = env.label
  }
}

const handleJsonInput = () => {
  if (!jsonBody.value.trim()) {
    jsonError.value = ''
    return
  }
  try {
    JSON.parse(jsonBody.value)
    jsonError.value = ''
    localForm.body = JSON.parse(jsonBody.value)
  } catch (e: any) {
    jsonError.value = 'JSON格式错误: ' + e.message
  }
}

const formatJsonBody = () => {
  try {
    const parsed = JSON.parse(jsonBody.value)
    jsonBody.value = JSON.stringify(parsed, null, 2)
    jsonError.value = ''
  } catch {
    ElMessage.error('无效的JSON格式')
  }
}

const minifyJsonBody = () => {
  try {
    const parsed = JSON.parse(jsonBody.value)
    jsonBody.value = JSON.stringify(parsed)
    jsonError.value = ''
  } catch {
    ElMessage.error('无效的JSON格式')
  }
}

const handleCodeJsonInput = () => {
  try {
    const parsed = JSON.parse(codeJson.value)
    codeJsonError.value = ''
    // Update form from code JSON
    Object.assign(localForm, parsed)
  } catch (e: any) {
    codeJsonError.value = 'JSON格式错误: ' + e.message
  }
}

const validateCodeJson = () => {
  handleCodeJsonInput()
  if (!codeJsonError.value) {
    ElMessage.success('JSON格式正确')
  }
}

const formatCodeJson = () => {
  try {
    const parsed = JSON.parse(codeJson.value)
    codeJson.value = JSON.stringify(parsed, null, 2)
    codeJsonError.value = ''
  } catch {
    ElMessage.error('无效的JSON格式')
  }
}

const handleEditorKeydown = (e: KeyboardEvent) => {
  // Tab key for indentation
  if (e.key === 'Tab') {
    e.preventDefault()
    const target = e.target as HTMLTextAreaElement
    const start = target.selectionStart
    const end = target.selectionEnd
    target.value = target.value.substring(0, start) + '  ' + target.value.substring(end)
    target.selectionStart = target.selectionEnd = start + 2
    target.dispatchEvent(new Event('input'))
  }
}

const handleVariableClick = () => {
  showVariableDialog.value = true
}

const insertVariable = (variable: string) => {
  // Insert variable at cursor position
  showVariableDialog.value = false
  // TODO: Implement proper cursor position insertion
  ElMessage.success(`已选择变量: \${${variable}}`)
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const exportAsCurl = () => {
  copyToClipboard(generatedCurl.value)
}

const importFromCurl = () => {
  try {
    const parsed = parseCurl(curlInput.value)
    Object.assign(localForm, parsed)
    showCurlImportDialog.value = false
    curlInput.value = ''
    ElMessage.success('cURL导入成功')
  } catch (e: any) {
    ElMessage.error('cURL解析失败: ' + e.message)
  }
}

const parseCurl = (curl: string): any => {
  const result: any = {
    method: 'GET',
    url: '',
    headers: {},
    body: {}
  }

  // Extract method
  const methodMatch = curl.match(/-X\s+(\w+)/)
  if (methodMatch) {
    result.method = methodMatch[1]
  }

  // Extract URL
  const urlMatch = curl.match(/['"]([^'"]+)['"]/)
  if (urlMatch) {
    result.url = urlMatch[1]
  }

  // Extract headers
  const headerMatches = curl.matchAll(/-H\s+['"]([^:]+):\s*([^'"]+)['"]/g)
  for (const match of headerMatches) {
    result.headers[match[1]] = match[2]
  }

  // Extract body
  const dataMatch = curl.match(/-d\s+['"](.+)['"]/s)
  if (dataMatch) {
    try {
      result.body = JSON.parse(dataMatch[1])
      bodyType.value = 'json'
      jsonBody.value = dataMatch[1]
    } catch {
      result.body = { raw: dataMatch[1] }
      bodyType.value = 'raw'
      rawBody.value = dataMatch[1]
    }
  }

  return result
}

const loadFromTemplate = (template: any) => {
  Object.assign(localForm, template.template)

  // Populate headers
  headers.value = Object.entries(template.template.headers || {}).map(([key, value]) => ({
    key,
    value: String(value),
    description: ''
  }))

  // Populate params
  queryParams.value = Object.entries(template.template.params || {}).map(([key, value]) => ({
    key,
    value: String(value),
    description: ''
  }))

  // Populate body
  if (template.template.body) {
    bodyType.value = 'json'
    jsonBody.value = JSON.stringify(template.template.body, null, 2)
  }

  showTemplateDialog.value = false
  ElMessage.success(`已加载模板 ${template.name}`)
}

const handleTest = async () => {
  // Build request data
  const paramsArray = queryParams.value
    .filter(item => item.key)
    .map(item => ({ key: item.key, value: item.value, enabled: true }))

  const headersArray = headers.value
    .filter(item => item.key)
    .map(item => ({ key: item.key, value: item.value, enabled: true }))

  let requestBody: any = null
  if (['POST', 'PUT', 'PATCH'].includes(localForm.method)) {
    if (bodyType.value === 'json') {
      requestBody = jsonBody.value
    } else if (bodyType.value === 'raw') {
      requestBody = rawBody.value
    }
  }

  const baseUrl = selectedBaseUrl.value
    ? props.environmentOptions.find(e => e.value === selectedBaseUrl.value)?.base_url || ''
    : ''

  testing.value = true
  try {
    const response = await httpExecutorApi.execute({
      method: localForm.method,
      url: localForm.url,
      baseUrl,
      headers: headersArray,
      params: paramsArray,
      body: requestBody,
      variables: [],
      settings: { timeout: 30000, follow_redirects: true, verify_ssl: false }
    })
    testResult.value = response
    ElMessage.success('请求执行成功')
    emit('test', response)
  } catch (e: any) {
    ElMessage.error('请求执行失败: ' + e.message)
  } finally {
    testing.value = false
  }
}

const formatResponse = (body: any) => {
  if (!body) return ''
  if (typeof body === 'string') return body
  return JSON.stringify(body, null, 2)
}

const formatHeaders = (headers: any) => {
  if (!headers) return ''
  if (typeof headers === 'string') return headers
  return JSON.stringify(headers, null, 2)
}

// Sync with v-model
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    Object.assign(localForm, newVal)
    // Convert dict to array for KeyValueEditor
    headers.value = Object.entries(newVal.headers || {}).map(([key, value]) => ({
      key,
      value: String(value),
      description: ''
    }))
    queryParams.value = Object.entries(newVal.params || {}).map(([key, value]) => ({
      key,
      value: String(value),
      description: ''
    }))
  }
}, { deep: true, immediate: true })

// Sync array data to localForm dict format
watch(headers, (newHeaders) => {
  const dict: Record<string, string> = {}
  newHeaders.forEach(item => {
    if (item.key) {
      dict[item.key] = item.value || ''
    }
  })
  localForm.headers = dict
}, { deep: true })

watch(queryParams, (newParams) => {
  const dict: Record<string, string> = {}
  newParams.forEach(item => {
    if (item.key) {
      dict[item.key] = item.value || ''
    }
  })
  localForm.params = dict
}, { deep: true })

watch(localForm, () => {
  emit('update:modelValue', { ...localForm })
}, { deep: true })
</script>

<style scoped>
.testcase-editor {
  width: 100%;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-content {
  margin-top: 16px;
}

.request-line-card {
  margin-bottom: 16px;
}

.request-line {
  display: flex;
  gap: 12px;
  align-items: center;
}

.url-input {
  flex: 1;
}

.base-url-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 0 8px;
}

.params-section {
  margin-top: 16px;
}

.param-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.preview-card {
  position: sticky;
  top: 20px;
}

.response-card {
  margin-top: 16px;
}

.json-editor-container {
  position: relative;
}

.editor-toolbar-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.json-error {
  margin-left: auto;
  color: #f56c6c;
  font-size: 12px;
}

.code-editor {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fafafa;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
}

.code-editor.has-error {
  border-color: #f56c6c;
}

.code-editor.full-editor {
  min-height: 400px;
}

.json-error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-top: 12px;
  background-color: #fef0f0;
  border-radius: 4px;
  color: #f56c6c;
  font-size: 13px;
}

.preview-content {
  min-height: 200px;
}

.curl-preview,
.http-preview,
.json-preview {
  position: relative;
}

.preview-code {
  background-color: #2d2d2d;
  color: #cccccc;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.http-request-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

.http-method {
  padding: 4px 12px;
  background-color: #409eff;
  color: white;
  border-radius: 4px;
  font-weight: 600;
}

.http-url {
  font-family: 'Consolas', 'Monaco', monospace;
  color: #303133;
}

.http-headers {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.http-header {
  display: flex;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
}

.http-header:last-child {
  border-bottom: none;
}

.header-key {
  font-weight: 600;
  color: #606266;
  min-width: 150px;
}

.header-value {
  color: #303133;
  font-family: 'Consolas', 'Monaco', monospace;
}

.http-body {
  margin-top: 12px;
}

.http-body pre {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  overflow-x: auto;
}

.response-preview {
  min-height: 200px;
}

.response-body,
.response-headers {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
  word-break: break-all;
  white-space: pre-wrap;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.template-card {
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.template-icon {
  font-size: 32px;
  color: #409eff;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.template-desc {
  font-size: 12px;
  color: #909399;
}

.variable-list {
  max-height: 300px;
  overflow-y: auto;
}

.variable-item {
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.variable-item:hover {
  background-color: #f5f7fa;
}

.variable-item code {
  font-family: 'Consolas', 'Monaco', monospace;
  color: #409eff;
  font-size: 13px;
}

.variable-desc {
  font-size: 12px;
  color: #909399;
}

.code-mode-container {
  margin-top: 16px;
}
</style>
