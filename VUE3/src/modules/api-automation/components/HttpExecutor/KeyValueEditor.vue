<!--
  KeyValueEditor.vue - 键值对编辑器组件

  通用的键值对编辑组件，用于编辑请求头、查询参数、表单字段等。
  功能特性：
  - 支持启用/禁用单行数据
  - 支持变量引用高亮（${变量名} 格式）
  - 支持搜索过滤
  - 支持常用 Header 快捷填充
  - 自动填充常见键值（如 Content-Type、Authorization）
  - 支持数组和对象两种数据格式的双向绑定
-->
<template>
  <div class="key-value-editor">
    <div class="editor-header" v-if="!disabled">
      <el-button
        size="small"
        type="primary"
        @click="addRow"
        :icon="Plus"
      >
        添加
      </el-button>
      <el-button
        size="small"
        @click="addCommonHeaders"
        v-if="commonHeaders && commonHeaders.length > 0"
      >
        常用Header
      </el-button>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索键值对"
        size="small"
        style="width: 200px; margin-left: 10px;"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="editor-content">
      <div
        v-for="(item, index) in filteredItems"
        :key="index"
        class="key-value-row"
        :class="{ 'row-disabled': item.disabled }"
      >
        <el-checkbox
          v-model="item.enabled"
          @change="onEnabledChange(index)"
          :disabled="disabled"
        />
        <el-input
          v-model="item.key"
          :placeholder="placeholderKey"
          size="small"
          class="key-input"
          :disabled="disabled"
          @blur="onKeyBlur(index)"
          @input="onKeyInput(index)"
        />
        <el-input
          v-model="item.value"
          :placeholder="placeholderValue"
          size="small"
          class="value-input"
          :disabled="disabled"
          @blur="onValueBlur(index)"
        >
          <template #suffix v-if="enableVariables && hasVariables(item.value)">
            <el-tooltip content="包含变量" placement="top">
              <el-icon style="color: #409eff;"><MagicStick /></el-icon>
            </el-tooltip>
          </template>
        </el-input>
        <el-button
          v-if="!disabled"
          size="small"
          type="danger"
          :icon="Delete"
          @click="removeRow(index)"
        />
      </div>

      <div v-if="filteredItems.length === 0" class="empty-state">
        <el-empty description="暂无数据" :image-size="60" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Plus, Delete, Search, MagicStick } from '@element-plus/icons-vue'

interface KeyValueItem {
  key: string
  value: string
  enabled?: boolean
  disabled?: boolean
}

interface Props {
  modelValue: KeyValueItem[]
  placeholderKey?: string
  placeholderValue?: string
  enableVariables?: boolean
  commonHeaders?: Array<{ key: string; value: string }>
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholderKey: '键',
  placeholderValue: '值',
  enableVariables: false,
  commonHeaders: () => [],
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: KeyValueItem[]]
}>()

// 响应式数据
const searchKeyword = ref('')
const items = ref<KeyValueItem[]>([])

// 计算属性
const filteredItems = computed(() => {
  if (!searchKeyword.value) {
    return items.value
  }

  const keyword = searchKeyword.value.toLowerCase()
  return items.value.filter(item =>
    item.key.toLowerCase().includes(keyword) ||
    item.value.toLowerCase().includes(keyword)
  )
})

// 方法
const addRow = () => {
  const newItem: KeyValueItem = {
    key: '',
    value: '',
    enabled: true
  }
  items.value.push(newItem)
  emitUpdate()
}

const removeRow = (index: number) => {
  items.value.splice(index, 1)
  emitUpdate()
}

const onEnabledChange = (index: number) => {
  items.value[index].disabled = !items.value[index].enabled
  emitUpdate()
}

const onKeyBlur = (index: number) => {
  // 自动填充常见的值
  const key = items.value[index].key.toLowerCase()
  if (key && !items.value[index].value) {
    if (key === 'content-type') {
      items.value[index].value = 'application/json'
    } else if (key === 'accept') {
      items.value[index].value = 'application/json'
    } else if (key === 'authorization') {
      items.value[index].value = 'Bearer ${token}'
    }
    emitUpdate()
  }
}

const onKeyInput = (index: number) => {
  emitUpdate()
}

const onValueBlur = (index: number) => {
  emitUpdate()
}

const addCommonHeaders = () => {
  const newItems = props.commonHeaders.map(header => ({
    key: header.key,
    value: header.value,
    enabled: true
  }))

  // 过滤已存在的
  const existingKeys = items.value.map(item => item.key.toLowerCase())
  const uniqueNewItems = newItems.filter(item =>
    !existingKeys.includes(item.key.toLowerCase())
  )

  items.value.push(...uniqueNewItems)
  emitUpdate()
}

const hasVariables = (value: string): boolean => {
  if (!value || !props.enableVariables) return false
  return /\$\{[^}]+\}/.test(value)
}

const emitUpdate = () => {
  emit('update:modelValue', items.value)
}

// 监听器 - 使用引用比较避免递归更新
watch(() => props.modelValue, (newValue) => {
  // 如果是同一个引用,说明是内部更新,跳过同步避免递归
  if (newValue === items.value) {
    return
  }

  // Handle both array and object formats
  if (Array.isArray(newValue)) {
    // 如果是不同的数组引用(外部更新),才同步数据
    items.value = newValue.map(item => ({
      ...item,
      enabled: item.enabled !== false,
      disabled: item.disabled === true
    }))
  } else if (typeof newValue === 'object' && newValue !== null) {
    // If it's an object, convert to array format
    items.value = Object.entries(newValue).map(([key, value]) => ({
      key,
      value: String(value),
      enabled: true,
      disabled: false
    }))
  } else {
    // Default to empty array
    items.value = []
  }
}, { immediate: true })

// 初始化
if (items.value.length === 0) {
  addRow()
}
</script>

<style scoped>
.key-value-editor {
  width: 100%;
}

.editor-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.editor-content {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.key-value-row {
  display: flex;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid #ebeef5;
  gap: 8px;
}

.key-value-row:last-child {
  border-bottom: none;
}

.key-value-row:hover {
  background: #f5f7fa;
}

.row-disabled {
  opacity: 0.6;
}

.key-input {
  width: 200px;
}

.value-input {
  flex: 1;
}

.empty-state {
  padding: 40px;
  text-align: center;
}
</style>