<template>
  <div class="key-value-editor">
    <el-table
      :data="localData"
      border
      size="small"
      :show-header="true"
      class="key-value-table"
    >
      <el-table-column width="40" align="center">
        <template #default="{ $index }">
          <el-checkbox v-model="localData[$index].enabled" />
        </template>
      </el-table-column>

      <el-table-column label="Key" min-width="180">
        <template #default="{ row, $index }">
          <el-input
            v-model="row.key"
            placeholder="Key"
            size="small"
            :class="{ 'has-variable': hasVariable(row.key) }"
          >
            <template #suffix>
              <el-icon
                v-if="hasVariable(row.key)"
                class="variable-indicator"
                @click="handleVariableClick($index, 'key')"
              >
                <MagicStick />
              </el-icon>
            </template>
          </el-input>
        </template>
      </el-table-column>

      <el-table-column label="Value" min-width="200">
        <template #default="{ row, $index }">
          <el-input
            v-if="!showType || row.type !== 'file'"
            v-model="row.value"
            placeholder="Value"
            size="small"
            :class="{ 'has-variable': hasVariable(row.value) }"
          >
            <template #suffix>
              <el-icon
                v-if="hasVariable(row.value)"
                class="variable-indicator"
                @click="handleVariableClick($index, 'value')"
              >
                <MagicStick />
              </el-icon>
            </template>
          </el-input>
          <el-upload
            v-else
            :show-file-list="false"
            :on-change="(file) => handleFileSelect($index, file)"
            :auto-upload="false"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <span v-if="row.value" class="file-name">{{ row.value }}</span>
          </el-upload>
        </template>
      </el-table-column>

      <el-table-column v-if="showType" label="类型" width="100">
        <template #default="{ row }">
          <el-select v-model="row.type" size="small" style="width: 100%">
            <el-option label="Text" value="text" />
            <el-option label="File" value="file" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column v-if="showDescription" label="描述" width="150">
        <template #default="{ row }">
          <el-input v-model="row.description" placeholder="描述" size="small" />
        </template>
      </el-table-column>

      <el-table-column width="80" align="center">
        <template #default="{ $index }">
          <el-button
            type="danger"
            link
            size="small"
            @click="removeItem($index)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="editor-footer">
      <div class="footer-left">
        <el-dropdown trigger="click" @click.stop>
          <el-button size="small" type="primary" link>
            <el-icon><Plus /></el-icon>
            添加常用
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="item in commonItems"
                :key="item.key"
                @click="addCommonItem(item)"
              >
                {{ item.key }}: {{ item.value }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button
          v-if="showVariables"
          size="small"
          link
          @click="$emit('variable-click')"
        >
          <el-icon><MagicStick /></el-icon>
          插入变量
        </el-button>
      </div>

      <el-button size="small" type="primary" link @click="addItem">
        <el-icon><Plus /></el-icon>
        添加行
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Plus, Delete, MagicStick, ArrowDown, Upload } from '@element-plus/icons-vue'

interface KeyValueItem {
  key: string
  value: string
  enabled?: boolean
  type?: string
  description?: string
}

interface Props {
  modelValue: KeyValueItem[]
  showType?: boolean
  showDescription?: boolean
  showVariables?: boolean
  commonHeaders?: Array<{ key: string; value: string }>
  commonParams?: Array<{ key: string; value: string }>
}

const props = withDefaults(defineProps<Props>(), {
  showType: false,
  showDescription: false,
  showVariables: false,
  commonHeaders: () => [],
  commonParams: () => []
})

const emit = defineEmits(['update:modelValue', 'variable-click'])

const localData = ref<KeyValueItem[]>([])

// 用于防止循环更新的标志
const isUpdatingFromProps = ref(false)

// Computed common items based on context
const commonItems = computed(() => {
  if (props.commonHeaders.length > 0) {
    return props.commonHeaders
  }
  if (props.commonParams.length > 0) {
    return props.commonParams
  }
  return []
})

// Initialize with enabled flag
watch(() => props.modelValue, (newVal) => {
  isUpdatingFromProps.value = true
  localData.value = (newVal || []).map(item => ({
    key: item.key || '',
    value: item.value || '',
    enabled: item.enabled !== false,
    type: item.type || 'text',
    description: item.description || ''
  }))
  // 使用 nextTick 确保在 DOM 更新后再重置标志
  setTimeout(() => {
    isUpdatingFromProps.value = false
  }, 0)
}, { immediate: true, deep: true })

watch(localData, (newVal) => {
  // 防止循环更新
  if (!isUpdatingFromProps.value) {
    emit('update:modelValue', newVal)
  }
}, { deep: true })

const addItem = () => {
  localData.value.push({
    key: '',
    value: '',
    enabled: true,
    type: 'text',
    description: ''
  })
}

const removeItem = (index: number) => {
  localData.value.splice(index, 1)
}

const addCommonItem = (item: { key: string; value: string }) => {
  // Check if already exists
  const exists = localData.value.some(row => row.key === item.key)
  if (exists) {
    // Find and update
    const row = localData.value.find(r => r.key === item.key)
    if (row) {
      row.value = item.value
      row.enabled = true
    }
  } else {
    localData.value.push({
      key: item.key,
      value: item.value,
      enabled: true,
      type: 'text',
      description: ''
    })
  }
}

const hasVariable = (text: string) => {
  return text && /\$\{[^}]+\}/.test(text)
}

const handleVariableClick = (index: number, field: 'key' | 'value') => {
  emit('variable-click', { index, field })
}

const handleFileSelect = (index: number, file: any) => {
  localData.value[index].value = file.name
}
</script>

<style scoped>
.key-value-editor {
  width: 100%;
}

.key-value-table {
  font-size: 13px;
}

:deep(.key-value-table .el-input__wrapper) {
  padding: 0 8px;
}

:deep(.key-value-table .el-input__inner) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
}

.has-variable {
  border-color: #67c23a;
}

.variable-indicator {
  color: #67c23a;
  cursor: pointer;
  font-size: 14px;
}

.variable-indicator:hover {
  color: #85ce61;
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  margin-left: 8px;
  font-size: 12px;
  color: #606266;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #67c23a;
  border-color: #67c23a;
}
</style>
