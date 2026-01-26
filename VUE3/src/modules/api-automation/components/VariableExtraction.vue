<template>
  <div class="variable-extraction">
    <div class="config-header">
      <div class="header-left">
        <span class="header-title">变量提取配置</span>
        <div class="statistics" v-if="extractions.length > 0">
          <el-tag size="small" type="info">总计: {{ extractions.length }}</el-tag>
          <el-tag size="small" type="success">启用: {{ enabledCount }}</el-tag>
          <el-tag size="small" type="warning">禁用: {{ disabledCount }}</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-input
          v-if="extractions.length > 3"
          v-model="searchText"
          placeholder="搜索变量..."
          prefix-icon="Search"
          size="small"
          style="width: 200px; margin-right: 8px"
          clearable
        />
        <el-dropdown v-if="!disabled" trigger="click" @command="addTemplateExtraction">
          <el-button type="success" size="small">
            <el-icon><DocumentAdd /></el-icon>
            模板
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item divided>
                <span style="color: #909399; font-size: 12px;">常用提取</span>
              </el-dropdown-item>
              <el-dropdown-item command="jsonToken">JSON Token提取</el-dropdown-item>
              <el-dropdown-item command="jsonId">JSON ID提取</el-dropdown-item>
              <el-dropdown-item command="jsonUserId">JSON用户ID提取</el-dropdown-item>
              <el-dropdown-item command="authToken">Authorization Token</el-dropdown-item>
              <el-dropdown-item command="sessionId">Session ID</el-dropdown-item>
              <el-dropdown-item command="csrfToken">CSRF Token</el-dropdown-item>
              <el-dropdown-item divided />
              <el-dropdown-item command="jsonCode">响应码提取</el-dropdown-item>
              <el-dropdown-item command="jsonMessage">消息提取</el-dropdown-item>
              <el-dropdown-item command="jsonData">数据对象提取</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown v-if="!disabled && extractions.length > 0" trigger="click" @command="handleBatchCommand">
          <el-button type="warning" size="small">
            <el-icon><Operation /></el-icon>
            批量
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="enableAll">全部启用</el-dropdown-item>
              <el-dropdown-item command="disableAll">全部禁用</el-dropdown-item>
              <el-dropdown-item command="deleteDisabled" divided>删除已禁用</el-dropdown-item>
              <el-dropdown-item command="deleteAll">删除全部</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button
          v-if="!disabled"
          type="primary"
          size="small"
          @click="addExtraction"
        >
          <el-icon><Plus /></el-icon>
          添加变量
        </el-button>
      </div>
    </div>

    <div v-if="extractions.length === 0" class="empty-state">
      <el-empty description="暂无变量提取配置，点击上方按钮添加">
        <template #image>
          <el-icon :size="60" color="#dcdfe6"><Collection /></el-icon>
        </template>
      </el-empty>
    </div>

    <draggable
      v-else
      v-model="extractions"
      item-key="id"
      :disabled="disabled"
      @end="handleDragEnd"
      class="extraction-list"
      :class="{ 'has-selection': hasSelection }"
    >
      <template #item="{ element: extraction, index }">
        <el-card
          v-show="shouldShow(extraction)"
          class="extraction-item"
          :class="{
            'is-disabled': !extraction.is_enabled,
            'is-selected': selectedIndices.includes(index)
          }"
        >
          <template #header>
            <div class="extraction-header">
              <div class="header-left-info">
                <el-checkbox
                  v-if="!disabled"
                  v-model="selectionMap[extraction.id || index]"
                  @change="handleSelectionChange"
                />
                <el-icon v-if="!disabled" class="drag-handle"><Rank /></el-icon>
                <el-tag type="success" size="small">
                  ${{ extraction.variable_name || 'variable' }}
                </el-tag>
                <el-tag :type="getExtractionTypeColor(extraction.extract_type)" size="small">
                  {{ getExtractionTypeName(extraction.extract_type) }}
                </el-tag>
                <el-tag size="small" :type="getScopeColor(extraction.extract_scope || extraction.scope)">
                  {{ getScopeName(extraction.extract_scope || extraction.scope) }}
                </el-tag>
                <el-switch
                  v-model="extraction.is_enabled"
                  :disabled="disabled"
                  size="small"
                  @change="updateExtraction(index, extraction)"
                />
              </div>
              <div class="extraction-actions" v-if="!disabled">
                <el-button
                  size="small"
                  text
                  title="折叠/展开"
                  @click="toggleCollapse(index)"
                >
                  <el-icon>
                    <component :is="collapsedMap[extraction.id || index] ? ArrowDown : ArrowUp" />
                  </el-icon>
                </el-button>
                <el-button
                  size="small"
                  text
                  title="测试表达式"
                  @click="testExpression(extraction)"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  text
                  title="复制"
                  @click="duplicateExtraction(index)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  text
                  title="删除"
                  @click="removeExtraction(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>

          <div v-show="!collapsedMap[extraction.id || index]" class="extraction-body">
            <el-form :model="extraction" label-width="100px" size="small">
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="变量名">
                    <el-input
                      v-model="extraction.variable_name"
                      :disabled="disabled"
                      placeholder="例: user_id, token"
                      @blur="updateExtraction(index, extraction)"
                    >
                      <template #prepend>${</template>
                      <template #append>}</template>
                    </el-input>
                  </el-form-item>
                </el-col>

                <el-col :span="8">
                  <el-form-item label="提取类型">
                    <el-select
                      v-model="extraction.extract_type"
                      :disabled="disabled"
                      placeholder="选择提取类型"
                      @change="handleTypeChange(index)"
                    >
                      <el-option
                        v-for="type in extractionTypes"
                        :key="type.value"
                        :label="type.label"
                        :value="type.value"
                      >
                        <span>{{ type.label }}</span>
                        <span class="option-desc">{{ type.desc }}</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="8">
                  <el-form-item label="提取范围">
                    <el-select
                      v-model="extraction.extract_scope"
                      :disabled="disabled"
                      placeholder="选择范围"
                      @change="updateExtraction(index, extraction)"
                    >
                      <el-option label="响应体" value="body">
                        <span>响应体</span>
                        <span class="option-desc">body</span>
                      </el-option>
                      <el-option label="响应头" value="headers">
                        <span>响应头</span>
                        <span class="option-desc">headers</span>
                      </el-option>
                      <el-option label="URL" value="url">
                        <span>URL</span>
                        <span class="option-desc">url</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="提取表达式">
                <el-input
                  v-model="extraction.extract_expression"
                  :disabled="disabled"
                  :placeholder="getPlaceholderForType(extraction.extract_type)"
                  @blur="updateExtraction(index, extraction)"
                />
                <div class="expression-help" v-if="extraction.extract_type">
                  <el-icon><InfoFilled /></el-icon>
                  {{ getExpressionHelp(extraction.extract_type) }}
                </div>
              </el-form-item>

              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="默认值">
                    <el-input
                      v-model="extraction.default_value"
                      :disabled="disabled"
                      placeholder="提取失败时的默认值（可选）"
                      @blur="updateExtraction(index, extraction)"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="变量作用域">
                    <el-select
                      v-model="extraction.variable_scope"
                      :disabled="disabled"
                      placeholder="选择作用域"
                      @change="updateExtraction(index, extraction)"
                    >
                      <el-option label="局部变量" value="local" />
                      <el-option label="全局变量" value="global" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </el-card>
      </template>
    </draggable>

    <div v-if="hasSelection && !disabled" class="batch-actions-bar">
      <span class="selection-info">已选择 {{ selectedIndices.length }} 项</span>
      <div class="batch-actions">
        <el-button size="small" @click="batchEnable">启用</el-button>
        <el-button size="small" @click="batchDisable">禁用</el-button>
        <el-button size="small" type="danger" @click="batchDelete">删除</el-button>
        <el-button size="small" @click="clearSelection">取消选择</el-button>
      </div>
    </div>

    <!-- 变量使用说明 -->
    <el-collapse v-model="activeCollapse" class="help-section">
      <el-collapse-item title="变量使用说明 & 表达式示例" name="help">
        <div class="help-content">
          <div class="help-section-content">
            <h4>提取的变量可以在以下地方使用：</h4>
            <ul class="usage-list">
              <li><code>${variable_name}</code> - URL路径</li>
              <li><code>${variable_name}</code> - 请求参数 (Query/Body)</li>
              <li><code>${variable_name}</code> - 请求头 (Headers)</li>
              <li><code>${variable_name}</code> - 请求体 (JSON/Form)</li>
            </ul>
          </div>

          <div class="help-section-content">
            <h4>表达式示例</h4>
            <el-table :data="expressionExamples" size="small" max-height="300">
              <el-table-column prop="type" label="提取类型" width="120" />
              <el-table-column prop="expression" label="表达式" width="200" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="example" label="示例数据" show-overflow-tooltip />
            </el-table>
          </div>

          <div class="help-section-content">
            <h4>快速模板参考</h4>
            <div class="template-ref">
              <div class="template-item">
                <strong>JSON Token:</strong> <code>"token":"([^"]+)"</code>
              </div>
              <div class="template-item">
                <strong>JSON ID:</strong> <code>$.data.id</code>
              </div>
              <div class="template-item">
                <strong>Auth Header:</strong> <code>Authorization</code> (类型: Header)
              </div>
              <div class="template-item">
                <strong>Session ID:</strong> <code>session_id</code> (类型: Cookie)
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 表达式测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试提取表达式"
      width="700px"
    >
      <el-form label-width="100px" size="small">
        <el-form-item label="提取类型">
          <el-tag>{{ getExtractionTypeName(testForm.extract_type) }}</el-tag>
        </el-form-item>
        <el-form-item label="提取表达式">
          <el-input v-model="testForm.extract_expression" />
        </el-form-item>
        <el-form-item label="测试数据">
          <el-input
            v-model="testForm.testData"
            type="textarea"
            :rows="6"
            placeholder="输入要测试的响应数据（JSON或文本）"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runExpressionTest">运行测试</el-button>
          <el-button @click="testDialogVisible = false">关闭</el-button>
        </el-form-item>
        <el-form-item v-if="testResult" label="测试结果">
          <el-alert
            :type="testResult.success ? 'success' : 'error'"
            :closable="false"
          >
            <template v-if="testResult.success">
              <div>提取成功!</div>
              <div class="test-result-value">
                <strong>提取值:</strong> <code>{{ testResult.value }}</code>
              </div>
            </template>
            <template v-else>
              <div>提取失败: {{ testResult.message }}</div>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Delete,
  CopyDocument,
  DocumentAdd,
  ArrowDown,
  ArrowUp,
  Rank,
  Collection,
  Operation,
  Search,
  InfoFilled,
  VideoPlay
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import type { TestCaseExtraction } from '../types/testCase'

interface Props {
  modelValue: TestCaseExtraction[]
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: TestCaseExtraction[]): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<Emits>()

// 提取类型配置
const extractionTypes = [
  { label: '正则表达式', value: 'regex', desc: '使用正则从文本中提取' },
  { label: 'JSON路径', value: 'json_path', desc: '从JSON中提取值' },
  { label: 'XPath', value: 'xpath', desc: '从HTML/XML中提取' },
  { label: 'CSS选择器', value: 'css_selector', desc: '使用CSS选择器提取' },
  { label: 'Header解析', value: 'header', desc: '从响应头中提取' },
  { label: 'Cookie解析', value: 'cookie', desc: '从Cookie中提取' }
]

// 表达式示例
const expressionExamples = [
  {
    type: '正则表达式',
    expression: '"token":"([^"]+)"',
    description: '提取JSON中的token字段',
    example: '{"token":"abc123","user":"test"}'
  },
  {
    type: '正则表达式',
    expression: 'href="([^"]+)"',
    description: '提取HTML中的链接',
    example: '<a href="https://example.com">Link</a>'
  },
  {
    type: 'JSON路径',
    expression: '$.data.id',
    description: '提取JSON中的data.id值',
    example: '{"data":{"id":123,"name":"test"}}'
  },
  {
    type: 'JSON路径',
    expression: '$.users[0].name',
    description: '提取数组第一项',
    example: '{"users":[{"name":"John"},{"name":"Jane"}]}'
  },
  {
    type: 'Header解析',
    expression: 'Authorization',
    description: '提取Authorization头',
    example: 'Authorization: Bearer token123'
  },
  {
    type: 'Cookie解析',
    expression: 'session_id',
    description: '提取session_id cookie',
    example: 'Set-Cookie: session_id=abc123; Path=/'
  },
  {
    type: 'CSS选择器',
    expression: '.user-name',
    description: '提取class为user-name的元素',
    example: '<div class="user-name">John Doe</div>'
  },
  {
    type: 'XPath',
    expression: '//div[@class="content"]/text()',
    description: '提取div的文本内容',
    example: '<div class="content">Hello World</div>'
  }
]

// 数据
const extractions = ref<TestCaseExtraction[]>([])
const searchText = ref('')
const selectionMap = ref<Record<number, boolean>>({})
const collapsedMap = ref<Record<number, boolean>>({})
const activeCollapse = ref<string[]>([])

// 测试相关
const testDialogVisible = ref(false)
const testForm = ref({
  extract_type: 'json_path',
  extract_expression: '',
  testData: ''
})
const testResult = ref<any>(null)

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  extractions.value = Array.isArray(newValue) ? [...newValue] : []
}, { immediate: true })

// 计算属性
const enabledCount = computed(() =>
  extractions.value.filter(e => e.is_enabled).length
)

const disabledCount = computed(() =>
  extractions.value.filter(e => !e.is_enabled).length
)

const selectedIndices = computed(() => {
  return extractions.value
    .map((e, i) => ({ id: e.id || i, index: i }))
    .filter(({ id }) => selectionMap.value[id])
    .map(({ index }) => index)
})

const hasSelection = computed(() => selectedIndices.value.length > 0)

// 生成唯一ID
const generateId = (): number => {
  return Date.now() + Math.random()
}

// 搜索过滤
const shouldShow = (extraction: TestCaseExtraction): boolean => {
  if (!searchText.value) return true
  const search = searchText.value.toLowerCase()
  const nameMatch = extraction.variable_name?.toLowerCase().includes(search)
  const typeMatch = extraction.extract_type?.toLowerCase().includes(search)
  const exprMatch = extraction.extract_expression?.toLowerCase().includes(search)
  return nameMatch || typeMatch || exprMatch
}

// 选择相关
const handleSelectionChange = () => {
  // 响应式自动更新
}

const clearSelection = () => {
  selectionMap.value = {}
}

// 批量操作
const handleBatchCommand = async (command: string) => {
  switch (command) {
    case 'enableAll':
      extractions.value.forEach(e => e.is_enabled = true)
      emit('update:modelValue', extractions.value)
      ElMessage.success('已全部启用')
      break
    case 'disableAll':
      extractions.value.forEach(e => e.is_enabled = false)
      emit('update:modelValue', extractions.value)
      ElMessage.success('已全部禁用')
      break
    case 'deleteDisabled':
      try {
        await ElMessageBox.confirm(
          `确定要删除 ${disabledCount.value} 个已禁用的提取配置吗？`,
          '确认删除',
          { type: 'warning' }
        )
        extractions.value = extractions.value.filter(e => e.is_enabled)
        updateOrder()
        ElMessage.success('已删除已禁用的配置')
      } catch {
        // 取消删除
      }
      break
    case 'deleteAll':
      try {
        await ElMessageBox.confirm(
          `确定要删除全部 ${extractions.value.length} 个提取配置吗？此操作不可恢复！`,
          '确认删除',
          { type: 'error', confirmButtonText: '确定删除', cancelButtonText: '取消' }
        )
        extractions.value = []
        emit('update:modelValue', [])
        ElMessage.success('已删除全部配置')
      } catch {
        // 取消删除
      }
      break
  }
}

const batchEnable = () => {
  selectedIndices.value.forEach(i => {
    extractions.value[i].is_enabled = true
  })
  emit('update:modelValue', extractions.value)
  ElMessage.success(`已启用 ${selectedIndices.value.length} 个配置`)
}

const batchDisable = () => {
  selectedIndices.value.forEach(i => {
    extractions.value[i].is_enabled = false
  })
  emit('update:modelValue', extractions.value)
  ElMessage.success(`已禁用 ${selectedIndices.value.length} 个配置`)
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIndices.value.length} 个配置吗？`,
      '确认删除',
      { type: 'warning' }
    )
    const indices = [...selectedIndices.value].sort((a, b) => b - a)
    indices.forEach(i => extractions.value.splice(i, 1))
    updateOrder()
    clearSelection()
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}

// 折叠相关
const toggleCollapse = (index: number) => {
  const id = extractions.value[index].id || index
  collapsedMap.value[id] = !collapsedMap.value[id]
}

// 添加提取配置
const addExtraction = () => {
  const newExtraction: TestCaseExtraction = {
    id: generateId(),
    test_case: 0,
    variable_name: '',
    extract_type: 'json_path',
    extract_expression: '$.data',
    default_value: null,
    is_enabled: true,
    scope: 'body',
    extract_scope: 'body',
    variable_scope: 'local'
  }

  extractions.value.push(newExtraction)
  emit('update:modelValue', extractions.value)
}

// 从模板添加
const addTemplateExtraction = (command: string) => {
  let newExtraction: TestCaseExtraction

  switch (command) {
    case 'jsonToken':
      newExtraction = createTemplateExtraction('token', 'regex', '"token":"([^"]+)"', 'body')
      break
    case 'jsonId':
      newExtraction = createTemplateExtraction('id', 'json_path', '$.data.id', 'body')
      break
    case 'jsonUserId':
      newExtraction = createTemplateExtraction('user_id', 'json_path', '$.data.user.id', 'body')
      break
    case 'authToken':
      newExtraction = createTemplateExtraction('auth_token', 'header', 'Authorization', 'headers')
      break
    case 'sessionId':
      newExtraction = createTemplateExtraction('session_id', 'cookie', 'session_id', 'headers')
      break
    case 'csrfToken':
      newExtraction = createTemplateExtraction('csrf_token', 'regex', '"csrf_token":"([^"]+)"', 'body')
      break
    case 'jsonCode':
      newExtraction = createTemplateExtraction('code', 'json_path', '$.code', 'body')
      break
    case 'jsonMessage':
      newExtraction = createTemplateExtraction('message', 'json_path', '$.message', 'body')
      break
    case 'jsonData':
      newExtraction = createTemplateExtraction('data', 'json_path', '$.data', 'body')
      break
    default:
      return
  }

  extractions.value.push(newExtraction)
  emit('update:modelValue', extractions.value)
  ElMessage.success('已添加模板配置')
}

const createTemplateExtraction = (
  varName: string,
  extractType: string,
  expression: string,
  scope: string
): TestCaseExtraction => {
  return {
    id: generateId(),
    test_case: 0,
    variable_name: varName,
    extract_type: extractType,
    extract_expression: expression,
    default_value: null,
    is_enabled: true,
    scope: scope,
    extract_scope: scope,
    variable_scope: 'local'
  }
}

// 复制
const duplicateExtraction = (index: number) => {
  const original = extractions.value[index]
  const duplicated: TestCaseExtraction = {
    ...original,
    id: generateId(),
    variable_name: `${original.variable_name}_copy`
  }
  extractions.value.splice(index + 1, 0, duplicated)
  updateOrder()
  ElMessage.success('配置已复制')
}

// 移除
const removeExtraction = (index: number) => {
  extractions.value.splice(index, 1)
  updateOrder()
  emit('update:modelValue', extractions.value)
}

// 更新
const updateExtraction = (index: number, extraction: TestCaseExtraction) => {
  extractions.value[index] = { ...extraction }
  emit('update:modelValue', extractions.value)
}

// 更新顺序
const updateOrder = () => {
  extractions.value.forEach((item, idx) => {
    item.order = idx
  })
  emit('update:modelValue', extractions.value)
}

// 处理类型变化
const handleTypeChange = (index: number) => {
  const extraction = extractions.value[index]

  switch (extraction.extract_type) {
    case 'regex':
      extraction.extract_expression = '"token":"([^"]+)"'
      break
    case 'json_path':
      extraction.extract_expression = '$.data.id'
      break
    case 'xpath':
      extraction.extract_expression = '//div[@class="content"]/text()'
      break
    case 'css_selector':
      extraction.extract_expression = '.content'
      break
    case 'header':
      extraction.extract_expression = 'Authorization'
      extraction.extract_scope = 'headers'
      break
    case 'cookie':
      extraction.extract_expression = 'session_id'
      extraction.extract_scope = 'headers'
      break
  }

  updateExtraction(index, extraction)
}

// 拖拽结束
const handleDragEnd = () => {
  updateOrder()
}

// 测试表达式
const testExpression = (extraction: TestCaseExtraction) => {
  testForm.value = {
    extract_type: extraction.extract_type,
    extract_expression: extraction.extract_expression,
    testData: ''
  }
  testResult.value = null
  testDialogVisible.value = true
}

const runExpressionTest = () => {
  try {
    const { extract_type, extract_expression, testData } = testForm.value

    if (!testData) {
      ElMessage.warning('请输入测试数据')
      return
    }

    let result: any = null
    let success = false
    let message = ''

    switch (extract_type) {
      case 'regex':
        const regex = new RegExp(extract_expression, 'i')
        const match = testData.match(regex)
        if (match && match[1]) {
          result = match[1]
          success = true
          message = '正则匹配成功'
        } else if (match && match[0]) {
          result = match[0]
          success = true
          message = '正则匹配成功（无捕获组）'
        } else {
          message = '未匹配到结果'
        }
        break

      case 'json_path':
        try {
          const jsonData = JSON.parse(testData)
          const path = extract_expression.startsWith('$.') ? extract_expression.slice(2) : extract_expression
          result = navigateJsonPath(jsonData, path)
          success = result !== undefined && result !== null
          message = success ? 'JSON路径提取成功' : '路径未找到值'
        } catch (e: any) {
          message = `JSON解析失败: ${e.message}`
        }
        break

      case 'header':
      case 'cookie':
        // 模拟header/cookie提取
        const lines = testData.split('\n')
        for (const line of lines) {
          if (line.toLowerCase().includes(extract_expression.toLowerCase())) {
            const parts = line.split(':')
            if (parts.length >= 2) {
              result = parts.slice(1).join(':').trim()
              success = true
              message = '提取成功'
              break
            }
          }
        }
        if (!success) message = '未找到匹配的header/cookie'
        break

      default:
        message = '该提取类型暂不支持测试'
    }

    testResult.value = { success, value: result, message }
  } catch (e: any) {
    testResult.value = {
      success: false,
      value: null,
      message: `测试出错: ${e.message}`
    }
  }
}

const navigateJsonPath = (data: any, path: string): any => {
  const parts = path.split('.')
  let current = data
  for (const part of parts) {
    // 处理数组索引 users[0]
    const arrayMatch = part.match(/(\w+)\[(\d+)\]/)
    if (arrayMatch) {
      const [, key, index] = arrayMatch
      current = current?.[key]?.[parseInt(index)]
    } else {
      current = current?.[part]
    }
    if (current === undefined) return undefined
  }
  return current
}

// 获取方法
const getExtractionTypeName = (type: string): string => {
  const found = extractionTypes.find(item => item.value === type)
  return found ? found.label : type
}

const getExtractionTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    regex: 'primary',
    json_path: 'success',
    xpath: 'warning',
    css_selector: 'info',
    header: 'danger',
    cookie: 'warning'
  }
  return colors[type] || 'default'
}

const getScopeName = (scope: string): string => {
  const names: Record<string, string> = {
    body: '响应体',
    headers: '响应头',
    url: 'URL'
  }
  return names[scope] || scope
}

const getScopeColor = (scope: string): string => {
  const colors: Record<string, string> = {
    body: 'success',
    headers: 'warning',
    url: 'info'
  }
  return colors[scope] || 'default'
}

const getPlaceholderForType = (type: string): string => {
  const placeholders: Record<string, string> = {
    regex: '正则表达式，例: "token":"([^"]+)"',
    json_path: 'JSON路径，例: $.data.id',
    xpath: 'XPath表达式，例: //div[@id="content"]',
    css_selector: 'CSS选择器，例: .content',
    header: 'Header名称，例: Authorization',
    cookie: 'Cookie名称，例: session_id'
  }
  return placeholders[type] || '请输入提取表达式'
}

const getExpressionHelp = (type: string): string => {
  const helps: Record<string, string> = {
    regex: '使用正则表达式提取文本，括号()中的内容将被作为变量值',
    json_path: '使用JSONPath表达式提取JSON数据，支持点号和索引访问，如: $.data.users[0].id',
    xpath: '使用XPath表达式提取XML/HTML数据',
    css_selector: '使用CSS选择器提取HTML元素内容或属性',
    header: '从响应头中提取指定header的值',
    cookie: '从Set-Cookie头中提取指定cookie的值'
  }
  return helps[type] || ''
}
</script>

<style scoped>
.variable-extraction {
  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    font-size: 14px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .header-title {
        font-weight: 600;
      }

      .statistics {
        display: flex;
        gap: 6px;
      }
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .empty-state {
    padding: 60px 0;
    text-align: center;
  }

  .extraction-list {
    &.has-selection {
      margin-bottom: 60px;
    }

    .extraction-item {
      margin-bottom: 12px;
      border-radius: 8px;
      transition: all 0.3s;

      &.is-disabled {
        opacity: 0.6;
      }

      &.is-selected {
        border-color: #67c23a;
        box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2);
      }

      &:hover {
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }

      .extraction-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-left-info {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          min-width: 0;

          .drag-handle {
            cursor: move;
            color: #909399;
            font-size: 16px;
          }
        }

        .extraction-actions {
          display: flex;
          gap: 4px;
        }
      }

      .extraction-body {
        animation: slideDown 0.2s ease-out;
      }
    }
  }

  .batch-actions-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    border-top: 1px solid #ebeef5;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
    z-index: 100;

    .selection-info {
      font-size: 14px;
      color: #606266;
      font-weight: 500;
    }

    .batch-actions {
      display: flex;
      gap: 8px;
    }
  }

  .expression-help {
    margin-top: 6px;
    padding: 8px 12px;
    background-color: #f4f4f5;
    border-radius: 4px;
    font-size: 12px;
    color: #606266;
    line-height: 1.5;
    display: flex;
    align-items: center;
    gap: 6px;

    .el-icon {
      color: #909399;
    }
  }

  :deep(.el-select-dropdown__item) {
    .option-desc {
      float: right;
      color: #909399;
      font-size: 12px;
    }
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.help-section {
  margin-top: 24px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;

  .help-content {
    h4 {
      margin: 16px 0 12px 0;
      color: #303133;
      font-size: 14px;
      font-weight: 600;
    }

    .help-section-content {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .usage-list {
      margin: 8px 0;
      padding-left: 20px;

      li {
        margin: 6px 0;
        color: #606266;
        font-size: 13px;

        code {
          background-color: #f4f4f5;
          padding: 2px 6px;
          border-radius: 3px;
          color: #e83e8c;
          font-family: 'Consolas', 'Monaco', monospace;
        }
      }
    }

    .template-ref {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      .template-item {
        padding: 10px;
        background-color: #f4f4f5;
        border-radius: 6px;
        font-size: 13px;

        strong {
          color: #409eff;
          display: block;
          margin-bottom: 4px;
        }

        code {
          color: #67c23a;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 12px;
        }
      }
    }

    .test-result-value {
      margin-top: 8px;
      padding: 8px;
      background-color: #f4f4f5;
      border-radius: 4px;

      code {
        color: #67c23a;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        word-break: break-all;
      }
    }
  }
}

:deep(.el-card__header) {
  padding: 10px 14px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-card__body) {
  padding: 14px;
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-collapse-item__header) {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 拖拽时的样式 */
.sortable-ghost {
  opacity: 0.5;
  background-color: #f0f9ff;
}

.sortable-drag {
  opacity: 0.8;
}
</style>
