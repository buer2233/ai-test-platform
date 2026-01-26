<template>
  <div class="assertion-config">
    <div class="config-header">
      <div class="header-left">
        <span class="header-title">断言配置</span>
        <div class="statistics" v-if="assertions.length > 0">
          <el-tag size="small" type="info">总计: {{ assertions.length }}</el-tag>
          <el-tag size="small" type="success">启用: {{ enabledCount }}</el-tag>
          <el-tag size="small" type="warning">禁用: {{ disabledCount }}</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-input
          v-if="assertions.length > 3"
          v-model="searchText"
          placeholder="搜索断言..."
          prefix-icon="Search"
          size="small"
          style="width: 200px; margin-right: 8px"
          clearable
        />
        <el-dropdown v-if="!disabled" trigger="click" @command="addTemplateAssertion">
          <el-button type="success" size="small">
            <el-icon><DocumentAdd /></el-icon>
            模板
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item divided>
                <span style="color: #909399; font-size: 12px;">常用模板</span>
              </el-dropdown-item>
              <el-dropdown-item command="status200">HTTP 200成功</el-dropdown-item>
              <el-dropdown-item command="status201">HTTP 201创建</el-dropdown-item>
              <el-dropdown-item command="status204">HTTP 204无内容</el-dropdown-item>
              <el-dropdown-item command="status400">HTTP 400错误</el-dropdown-item>
              <el-dropdown-item command="status401">HTTP 401未授权</el-dropdown-item>
              <el-dropdown-item command="status404">HTTP 404未找到</el-dropdown-item>
              <el-dropdown-item command="status500">HTTP 500服务器错误</el-dropdown-item>
              <el-dropdown-item divided />
              <el-dropdown-item command="responseTime">响应时间检查</el-dropdown-item>
              <el-dropdown-item command="jsonValue">JSON值检查</el-dropdown-item>
              <el-dropdown-item command="jsonNotEmpty">JSON非空检查</el-dropdown-item>
              <el-dropdown-item command="headerJson">响应头JSON检查</el-dropdown-item>
              <el-dropdown-item command="bodyContains">响应体包含检查</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown v-if="!disabled && assertions.length > 0" trigger="click" @command="handleBatchCommand">
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
          @click="addAssertion"
        >
          <el-icon><Plus /></el-icon>
          添加断言
        </el-button>
      </div>
    </div>

    <div v-if="assertions.length === 0" class="empty-state">
      <el-empty description="暂无断言配置，点击上方按钮添加">
        <template #image>
          <el-icon :size="60" color="#dcdfe6"><Document /></el-icon>
        </template>
      </el-empty>
    </div>

    <draggable
      v-else
      v-model="assertions"
      item-key="id"
      :disabled="disabled"
      @end="handleDragEnd"
      class="assertion-list"
      :class="{ 'has-selection': hasSelection }"
    >
      <template #item="{ element: assertion, index }">
        <el-card
          v-show="shouldShow(assertion)"
          class="assertion-item"
          :class="{
            'is-disabled': !assertion.is_enabled,
            'is-selected': selectedIndices.includes(index)
          }"
        >
          <template #header>
            <div class="assertion-header">
              <div class="header-left-info">
                <el-checkbox
                  v-if="!disabled"
                  v-model="selectionMap[assertion.id || index]"
                  @change="handleSelectionChange"
                />
                <el-icon v-if="!disabled" class="drag-handle"><Rank /></el-icon>
                <el-tag :type="getAssertionTypeColor(assertion.assertion_type)" size="small">
                  {{ getAssertionTypeName(assertion.assertion_type) }}
                </el-tag>
                <span class="assertion-operator">{{ getOperatorName(assertion.operator) }}</span>
                <span class="assertion-target" v-if="shouldShowTarget(assertion)">
                  {{ truncateText(assertion.target, 20) }}
                </span>
                <span class="assertion-expected" v-if="shouldShowExpected(assertion)">
                  {{ truncateText(assertion.expected_value, 25) }}
                </span>
                <el-switch
                  v-model="assertion.is_enabled"
                  :disabled="disabled"
                  size="small"
                  @change="updateAssertion(index, assertion)"
                />
              </div>
              <div class="assertion-actions" v-if="!disabled">
                <el-button
                  size="small"
                  text
                  title="折叠/展开"
                  @click="toggleCollapse(index)"
                >
                  <el-icon>
                    <component :is="collapsedMap[assertion.id || index] ? ArrowDown : ArrowUp" />
                  </el-icon>
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  text
                  title="复制"
                  @click="duplicateAssertion(index)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  text
                  title="删除"
                  @click="removeAssertion(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>

          <div v-show="!collapsedMap[assertion.id || index]" class="assertion-body">
            <el-form :model="assertion" label-width="90px" size="small">
              <el-row :gutter="12">
                <el-col :span="showJsonEditor(assertion) ? 24 : 6">
                  <el-form-item label="断言类型">
                    <el-select
                      v-model="assertion.assertion_type"
                      :disabled="disabled"
                      placeholder="选择类型"
                      @change="handleTypeChange(index)"
                    >
                      <el-option
                        v-for="type in assertionTypes"
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

                <el-col :span="6" v-if="needsTarget(assertion.assertion_type) && !showJsonEditor(assertion)">
                  <el-form-item :label="getTargetLabel(assertion.assertion_type)">
                    <el-input
                      v-model="assertion.target"
                      :disabled="disabled"
                      :placeholder="getTargetPlaceholder(assertion.assertion_type)"
                      @blur="updateAssertion(index, assertion)"
                    />
                  </el-form-item>
                </el-col>

                <el-col :span="6" v-if="!showJsonEditor(assertion)">
                  <el-form-item label="操作符">
                    <el-select
                      v-model="assertion.operator"
                      :disabled="disabled"
                      placeholder="选择操作符"
                      @change="handleOperatorChange(index)"
                    >
                      <el-option
                        v-for="operator in getOperatorsForType(assertion.assertion_type)"
                        :key="operator.value"
                        :label="operator.label"
                        :value="operator.value"
                      >
                        <span>{{ operator.label }}</span>
                        <span class="option-desc">{{ operator.desc }}</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="showJsonEditor(assertion) ? 24 : 6">
                  <el-form-item
                    :label="getExpectedLabel(assertion.assertion_type, assertion.operator)"
                  >
                    <el-input
                      v-if="!showJsonEditor(assertion)"
                      v-model="assertion.expected_value"
                      :disabled="disabled || isNoValueOperator(assertion.operator)"
                      :placeholder="getPlaceholderForType(assertion.assertion_type, assertion.operator)"
                      @blur="updateAssertion(index, assertion)"
                    />
                    <div v-else class="json-editor-container">
                      <el-input
                        v-model="assertion.expected_value"
                        type="textarea"
                        :disabled="disabled"
                        :rows="6"
                        :placeholder="getJsonEditorPlaceholder(assertion.assertion_type)"
                        @blur="formatJson(index)"
                        class="json-textarea"
                      />
                      <div class="json-actions">
                        <el-button
                          size="small"
                          text
                          @click="formatJson(index)"
                          :disabled="disabled"
                        >
                          <el-icon><Document /></el-icon>
                          格式化
                        </el-button>
                        <el-button
                          size="small"
                          text
                          type="success"
                          @click="validateJson(assertion)"
                        >
                          <el-icon><CircleCheck /></el-icon>
                          验证
                        </el-button>
                      </div>
                    </div>
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
  Document,
  CircleCheck,
  Operation,
  Search
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import type { TestCaseAssertion } from '../types/testCase'

interface Props {
  modelValue: TestCaseAssertion[]
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: TestCaseAssertion[]): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<Emits>()

// 断言类型配置
const assertionTypes = [
  { label: 'HTTP状态码', value: 'status_code', desc: '验证HTTP响应状态码' },
  { label: '响应时间', value: 'response_time', desc: '验证响应时间(ms)' },
  { label: '响应体', value: 'response_body', desc: '验证响应体内容' },
  { label: '响应头', value: 'response_headers', desc: '验证响应头字段' },
  { label: 'JSON值', value: 'json_value', desc: '验证JSON字段值' },
  { label: '文本包含', value: 'text_contains', desc: '验证响应文本包含' },
  { label: 'JSON Schema', value: 'json_schema', desc: '验证JSON Schema结构' }
]

// 操作符配置
const operators = {
  status_code: [
    { label: '等于', value: 'equals', desc: 'status == 200' },
    { label: '不等于', value: 'not_equals', desc: 'status != 200' },
    { label: '包含', value: 'contains', desc: 'status in [200, 201]' },
    { label: '不包含', value: 'not_contains', desc: 'status not in [400, 500]' },
    { label: '范围', value: 'range', desc: '200-299' }
  ],
  response_time: [
    { label: '小于', value: 'less_than', desc: 'time < 1000' },
    { label: '小于等于', value: 'less_than_equal', desc: 'time <= 1000' },
    { label: '大于', value: 'greater_than', desc: 'time > 100' },
    { label: '大于等于', value: 'greater_than_equal', desc: 'time >= 100' },
    { label: '等于', value: 'equals', desc: 'time == 500' },
    { label: '不等于', value: 'not_equals', desc: 'time != 500' }
  ],
  response_body: [
    { label: '包含', value: 'contains', desc: '包含指定文本' },
    { label: '不包含', value: 'not_contains', desc: '不包含指定文本' },
    { label: '等于', value: 'equals', desc: '完全等于' },
    { label: '不等于', value: 'not_equals', desc: '不等于' },
    { label: '正则匹配', value: 'regex', desc: '正则表达式匹配' },
    { label: '为空', value: 'is_empty', desc: '值为空' },
    { label: '不为空', value: 'is_not_empty', desc: '值不为空' }
  ],
  response_headers: [
    { label: '包含', value: 'contains', desc: '包含指定文本' },
    { label: '不包含', value: 'not_contains', desc: '不包含指定文本' },
    { label: '等于', value: 'equals', desc: '完全等于' },
    { label: '不等于', value: 'not_equals', desc: '不等于' },
    { label: '正则匹配', value: 'regex', desc: '正则表达式匹配' },
    { label: '为空', value: 'is_empty', desc: '值为空' },
    { label: '不为空', value: 'is_not_empty', desc: '值不为空' }
  ],
  json_value: [
    { label: '等于', value: 'equals', desc: '值等于' },
    { label: '不等于', value: 'not_equals', desc: '值不等于' },
    { label: '包含', value: 'contains', desc: '包含指定值' },
    { label: '不包含', value: 'not_contains', desc: '不包含指定值' },
    { label: '大于', value: 'greater_than', desc: '数值大于' },
    { label: '小于', value: 'less_than', desc: '数值小于' },
    { label: '大于等于', value: 'greater_than_equal', desc: '数值大于等于' },
    { label: '小于等于', value: 'less_than_equal', desc: '数值小于等于' },
    { label: '为空', value: 'is_empty', desc: '值为空' },
    { label: '不为空', value: 'is_not_empty', desc: '值不为空' }
  ],
  text_contains: [
    { label: '包含', value: 'contains', desc: '包含指定文本' },
    { label: '不包含', value: 'not_contains', desc: '不包含指定文本' }
  ],
  json_schema: [
    { label: '有效', value: 'valid', desc: 'Schema验证通过' },
    { label: '无效', value: 'invalid', desc: 'Schema验证失败' }
  ]
}

// 无需输入值的操作符
const noValueOperators = ['is_empty', 'is_not_empty', 'valid', 'invalid']

// 数据
const assertions = ref<TestCaseAssertion[]>([])
const searchText = ref('')
const selectionMap = ref<Record<number, boolean>>({})
const collapsedMap = ref<Record<number, boolean>>({})

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  assertions.value = Array.isArray(newValue) ? [...newValue] : []
}, { immediate: true })

// 计算属性
const enabledCount = computed(() =>
  assertions.value.filter(a => a.is_enabled).length
)

const disabledCount = computed(() =>
  assertions.value.filter(a => !a.is_enabled).length
)

const selectedIndices = computed(() => {
  return assertions.value
    .map((a, i) => ({ id: a.id || i, index: i }))
    .filter(({ id }) => selectionMap.value[id])
    .map(({ index }) => index)
})

const hasSelection = computed(() => selectedIndices.value.length > 0)

// 生成唯一ID
const generateId = (): number => {
  return Date.now() + Math.random()
}

// 搜索过滤
const shouldShow = (assertion: TestCaseAssertion): boolean => {
  if (!searchText.value) return true
  const search = searchText.value.toLowerCase()
  const typeMatch = assertion.assertion_type.toLowerCase().includes(search)
  const operatorMatch = assertion.operator.toLowerCase().includes(search)
  const targetMatch = assertion.target?.toLowerCase().includes(search)
  const valueMatch = assertion.expected_value?.toLowerCase().includes(search)
  return typeMatch || operatorMatch || targetMatch || valueMatch
}

const shouldShowTarget = (assertion: TestCaseAssertion): boolean => {
  return assertion.target &&
         assertion.assertion_type !== 'status_code' &&
         assertion.assertion_type !== 'response_time'
}

const shouldShowExpected = (assertion: TestCaseAssertion): boolean => {
  return assertion.expected_value && !showJsonEditor(assertion)
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
      assertions.value.forEach(a => a.is_enabled = true)
      emit('update:modelValue', assertions.value)
      ElMessage.success('已全部启用')
      break
    case 'disableAll':
      assertions.value.forEach(a => a.is_enabled = false)
      emit('update:modelValue', assertions.value)
      ElMessage.success('已全部禁用')
      break
    case 'deleteDisabled':
      try {
        await ElMessageBox.confirm(
          `确定要删除 ${disabledCount.value} 个已禁用的断言吗？`,
          '确认删除',
          { type: 'warning' }
        )
        assertions.value = assertions.value.filter(a => a.is_enabled)
        updateOrder()
        ElMessage.success('已删除已禁用的断言')
      } catch {
        // 取消删除
      }
      break
    case 'deleteAll':
      try {
        await ElMessageBox.confirm(
          `确定要删除全部 ${assertions.value.length} 个断言吗？此操作不可恢复！`,
          '确认删除',
          { type: 'error', confirmButtonText: '确定删除', cancelButtonText: '取消' }
        )
        assertions.value = []
        emit('update:modelValue', [])
        ElMessage.success('已删除全部断言')
      } catch {
        // 取消删除
      }
      break
  }
}

const batchEnable = () => {
  selectedIndices.value.forEach(i => {
    assertions.value[i].is_enabled = true
  })
  emit('update:modelValue', assertions.value)
  ElMessage.success(`已启用 ${selectedIndices.value.length} 个断言`)
}

const batchDisable = () => {
  selectedIndices.value.forEach(i => {
    assertions.value[i].is_enabled = false
  })
  emit('update:modelValue', assertions.value)
  ElMessage.success(`已禁用 ${selectedIndices.value.length} 个断言`)
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIndices.value.length} 个断言吗？`,
      '确认删除',
      { type: 'warning' }
    )
    // 从后往前删除，避免索引问题
    const indices = [...selectedIndices.value].sort((a, b) => b - a)
    indices.forEach(i => assertions.value.splice(i, 1))
    updateOrder()
    clearSelection()
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}

// 折叠相关
const toggleCollapse = (index: number) => {
  const id = assertions.value[index].id || index
  collapsedMap.value[id] = !collapsedMap.value[id]
}

// 添加断言
const addAssertion = () => {
  const newAssertion: TestCaseAssertion = {
    id: generateId(),
    test_case: 0,
    assertion_type: 'status_code',
    target: 'status_code',
    operator: 'equals',
    expected_value: '200',
    is_enabled: true,
    order: assertions.value.length
  }

  assertions.value.push(newAssertion)
  emit('update:modelValue', assertions.value)
}

// 从模板添加断言
const addTemplateAssertion = (command: string) => {
  let newAssertion: TestCaseAssertion

  switch (command) {
    case 'status200':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '200')
      break
    case 'status201':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '201')
      break
    case 'status204':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '204')
      break
    case 'status400':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '400')
      break
    case 'status401':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '401')
      break
    case 'status404':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '404')
      break
    case 'status500':
      newAssertion = createTemplateAssertion('status_code', 'status_code', 'equals', '500')
      break
    case 'responseTime':
      newAssertion = createTemplateAssertion('response_time', 'response_time', 'less_than_equal', '3000')
      break
    case 'jsonValue':
      newAssertion = createTemplateAssertion('json_value', '$.code', 'equals', '0')
      break
    case 'jsonNotEmpty':
      newAssertion = createTemplateAssertion('json_value', '$.data', 'is_not_empty', '')
      break
    case 'headerJson':
      newAssertion = createTemplateAssertion('response_headers', 'Content-Type', 'contains', 'application/json')
      break
    case 'bodyContains':
      newAssertion = createTemplateAssertion('response_body', '', 'contains', 'success')
      break
    default:
      return
  }

  assertions.value.push(newAssertion)
  emit('update:modelValue', assertions.value)
  ElMessage.success('已添加模板断言')
}

const createTemplateAssertion = (
  type: string,
  target: string,
  operator: string,
  expected: string
): TestCaseAssertion => {
  return {
    id: generateId(),
    test_case: 0,
    assertion_type: type,
    target: target,
    operator: operator,
    expected_value: expected,
    is_enabled: true,
    order: assertions.value.length
  }
}

// 复制断言
const duplicateAssertion = (index: number) => {
  const original = assertions.value[index]
  const duplicated: TestCaseAssertion = {
    ...original,
    id: generateId(),
    order: assertions.value.length
  }
  assertions.value.splice(index + 1, 0, duplicated)
  updateOrder()
  ElMessage.success('断言已复制')
}

// 移除断言
const removeAssertion = (index: number) => {
  assertions.value.splice(index, 1)
  updateOrder()
  emit('update:modelValue', assertions.value)
}

// 更新断言
const updateAssertion = (index: number, assertion: TestCaseAssertion) => {
  assertions.value[index] = { ...assertion }
  emit('update:modelValue', assertions.value)
}

// 更新顺序
const updateOrder = () => {
  assertions.value.forEach((item, idx) => {
    item.order = idx
  })
  emit('update:modelValue', assertions.value)
}

// 处理类型变化
const handleTypeChange = (index: number) => {
  const assertion = assertions.value[index]

  switch (assertion.assertion_type) {
    case 'status_code':
      assertion.target = 'status_code'
      assertion.operator = 'equals'
      assertion.expected_value = '200'
      break
    case 'response_time':
      assertion.target = 'response_time'
      assertion.operator = 'less_than_equal'
      assertion.expected_value = '3000'
      break
    case 'response_body':
      assertion.target = ''
      assertion.operator = 'contains'
      assertion.expected_value = ''
      break
    case 'response_headers':
      assertion.target = 'Content-Type'
      assertion.operator = 'contains'
      assertion.expected_value = 'application/json'
      break
    case 'json_value':
      assertion.target = '$.data'
      assertion.operator = 'is_not_empty'
      assertion.expected_value = ''
      break
    case 'text_contains':
      assertion.target = ''
      assertion.operator = 'contains'
      assertion.expected_value = ''
      break
    case 'json_schema':
      assertion.target = ''
      assertion.operator = 'valid'
      assertion.expected_value = JSON.stringify({
        type: 'object',
        required: ['code', 'message'],
        properties: {
          code: { type: 'number' },
          message: { type: 'string' }
        }
      }, null, 2)
      break
  }

  updateAssertion(index, assertion)
}

// 处理操作符变化
const handleOperatorChange = (index: number) => {
  const assertion = assertions.value[index]

  if (isNoValueOperator(assertion.operator)) {
    assertion.expected_value = null
  }

  updateAssertion(index, assertion)
}

// 拖拽结束
const handleDragEnd = () => {
  updateOrder()
}

// 判断是否需要目标字段
const needsTarget = (type: string): boolean => {
  return ['response_body', 'response_headers', 'json_value'].includes(type)
}

// 显示JSON编辑器
const showJsonEditor = (assertion: TestCaseAssertion): boolean => {
  return assertion.assertion_type === 'json_schema'
}

// 判断是否是无值操作符
const isNoValueOperator = (operator: string): boolean => {
  return noValueOperators.includes(operator)
}

// 获取操作符列表
const getOperatorsForType = (type: string) => {
  return operators[type] || []
}

// 获取断言类型名称
const getAssertionTypeName = (type: string): string => {
  const found = assertionTypes.find(item => item.value === type)
  return found ? found.label : type
}

// 获取操作符名称
const getOperatorName = (operator: string): string => {
  for (const type in operators) {
    const found = operators[type].find(item => item.value === operator)
    if (found) return found.label
  }
  return operator
}

// 获取断言类型颜色
const getAssertionTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    status_code: 'success',
    response_time: 'warning',
    response_body: 'primary',
    response_headers: 'info',
    json_value: 'danger',
    text_contains: 'primary',
    json_schema: 'success'
  }
  return colors[type] || 'default'
}

// 获取目标字段标签
const getTargetLabel = (type: string): string => {
  const labels: Record<string, string> = {
    response_body: 'JSON路径',
    response_headers: '响应头',
    json_value: 'JSON路径'
  }
  return labels[type] || '目标'
}

// 获取目标字段占位符
const getTargetPlaceholder = (type: string): string => {
  const placeholders: Record<string, string> = {
    response_body: '$.data.user.name 或 data.user.name',
    response_headers: 'Content-Type',
    json_value: '$.data.id 或 data.items[0].name'
  }
  return placeholders[type] || '请输入目标'
}

// 获取期望值标签
const getExpectedLabel = (type: string, operator: string): string => {
  if (isNoValueOperator(operator)) {
    return '期望值'
  }
  const labels: Record<string, string> = {
    json_schema: 'JSON Schema',
    status_code: '状态码值',
    response_time: '时间值(ms)'
  }
  return labels[type] || '期望值'
}

// 获取占位符
const getPlaceholderForType = (type: string, operator: string): string => {
  if (isNoValueOperator(operator)) {
    return '无需填写'
  }

  switch (type) {
    case 'status_code':
      if (operator === 'range') return '200-299 或 200,201,204'
      if (operator === 'contains') return '200,201,204'
      return '200'
    case 'response_time':
      return '3000 (毫秒)'
    case 'response_body':
      if (operator === 'regex') return '^success$'
      return '期望的文本内容'
    case 'response_headers':
      if (operator === 'regex') return '^application/json'
      return 'application/json'
    case 'json_value':
      if (operator === 'greater_than' || operator === 'less_than') return '100'
      return '期望的JSON值'
    case 'text_contains':
      return '要查找的文本'
    default:
      return '请输入期望值'
  }
}

// 获取JSON编辑器占位符
const getJsonEditorPlaceholder = (type: string): string => {
  if (type === 'json_schema') {
    return `请输入JSON Schema，例如：
{
  "type": "object",
  "required": ["code", "message"],
  "properties": {
    "code": { "type": "number" },
    "message": { "type": "string" },
    "data": { "type": "object" }
  }
}`
  }
  return '请输入JSON格式数据'
}

// 格式化JSON
const formatJson = (index: number) => {
  const assertion = assertions.value[index]
  if (!assertion.expected_value) return

  try {
    const parsed = JSON.parse(assertion.expected_value)
    assertion.expected_value = JSON.stringify(parsed, null, 2)
    updateAssertion(index, assertion)
  } catch {
    // ignore
  }
}

// 验证JSON
const validateJson = (assertion: TestCaseAssertion) => {
  if (!assertion.expected_value) {
    ElMessage.warning('请输入JSON内容')
    return
  }

  try {
    JSON.parse(assertion.expected_value)
    ElMessage.success('JSON格式正确')
  } catch (e: any) {
    ElMessage.error(`JSON格式错误: ${e.message}`)
  }
}

// 截断文本
const truncateText = (text: string | null, maxLength: number): string => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}
</script>

<style scoped>
.assertion-config {
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

  .assertion-list {
    &.has-selection {
      margin-bottom: 60px;
    }

    .assertion-item {
      margin-bottom: 12px;
      border-radius: 8px;
      transition: all 0.3s;

      &.is-disabled {
        opacity: 0.6;
      }

      &.is-selected {
        border-color: #409eff;
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
      }

      &:hover {
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }

      .assertion-header {
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

          .assertion-operator {
            font-size: 12px;
            color: #606266;
            background-color: #f0f2f5;
            padding: 2px 8px;
            border-radius: 4px;
          }

          .assertion-target,
          .assertion-expected {
            font-size: 12px;
            color: #606266;
            background-color: #f5f7fa;
            padding: 2px 8px;
            border-radius: 4px;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .assertion-target {
            color: #409eff;
          }

          .assertion-expected {
            color: #67c23a;
          }
        }

        .assertion-actions {
          display: flex;
          gap: 4px;
        }
      }

      .assertion-body {
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

  :deep(.el-select-dropdown__item) {
    .option-desc {
      float: right;
      color: #909399;
      font-size: 12px;
    }
  }

  .json-editor-container {
    width: 100%;

    .json-textarea {
      font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
      font-size: 12px;
    }

    .json-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
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

/* 拖拽时的样式 */
.sortable-ghost {
  opacity: 0.5;
  background-color: #f0f9ff;
}

.sortable-drag {
  opacity: 0.8;
}
</style>
