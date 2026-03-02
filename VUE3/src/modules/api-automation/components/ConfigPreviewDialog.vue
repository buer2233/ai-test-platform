<!--
  ConfigPreviewDialog.vue - 配置编辑预览对话框

  用于编辑环境的全局请求头或全局变量配置：
  - 支持两种配置类型：headers（请求头）和 variables（变量）
  - 动态添加/删除配置行
  - 变量值中的 ${变量名} 引用自动高亮标识
  - 一键复制全部配置
  - 一键清空全部配置
  - 保存后通过 API 更新环境配置
  - 变量使用提示（${variable_name} 格式说明）
-->
<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="800px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div class="config-preview-dialog">
      <div class="dialog-header">
        <div class="env-info">
          <el-tag type="info" size="small">{{ environment?.name }}</el-tag>
          <span class="config-type-label">{{ configTypeLabel }}</span>
        </div>
        <el-alert
          :type="isHeaders ? 'info' : 'success'"
          :closable="false"
          show-icon
          style="margin-top: 12px"
        >
          <template #title>
            {{ configDescription }}
          </template>
        </el-alert>
      </div>

      <div class="editor-section">
        <div class="section-header">
          <span>{{ isHeaders ? '全局请求头配置' : '全局变量配置' }}</span>
          <div class="header-actions">
            <el-button size="small" text @click="handleCopyAll">
              <el-icon><DocumentCopy /></el-icon>
              复制全部
            </el-button>
            <el-button size="small" text @click="handleClearAll" type="danger" v-if="items.length > 0">
              <el-icon><Delete /></el-icon>
              清空全部
            </el-button>
          </div>
        </div>

        <div class="editor-content">
          <div
            v-for="(item, index) in items"
            :key="index"
            class="config-row"
          >
            <el-input
              v-model="item.key"
              :placeholder="isHeaders ? 'Header名称' : '变量名称'"
              size="small"
              class="key-input"
            >
              <template #prefix v-if="!isHeaders">
                <el-icon><Collection /></el-icon>
              </template>
              <template #prefix v-else>
                <el-icon><DocumentCopy /></el-icon>
              </template>
            </el-input>
            <el-input
              v-model="item.value"
              :placeholder="isHeaders ? 'Header值' : '变量值'"
              size="small"
              class="value-input"
            >
              <template #suffix v-if="!isHeaders && hasVariables(item.value)">
                <el-tooltip content="包含变量引用" placement="top">
                  <el-icon style="color: #409eff;"><MagicStick /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
            <el-button
              size="small"
              type="danger"
              :icon="Delete"
              @click="removeRow(index)"
              circle
            />
          </div>

          <div v-if="items.length === 0" class="empty-state">
            <el-empty description="暂无配置数据" :image-size="60" />
          </div>

          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            @click="addRow"
            style="width: 100%; margin-top: 12px"
            v-if="items.length > 0 || isHeaders"
          >
            添加{{ isHeaders ? '请求头' : '变量' }}
          </el-button>
        </div>

        <div class="usage-hint" v-if="!isHeaders && items.length > 0">
          <el-alert type="info" :closable="false">
            <template #title>
              <span style="font-size: 12px">
                <el-icon><InfoFilled /></el-icon>
                在测试用例中使用 <code>{{ variableExample }}</code> 格式引用全局变量
              </span>
            </template>
          </el-alert>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          <el-icon><Check /></el-icon>
          保存更改
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DocumentCopy, Collection, Delete, Plus, MagicStick, Check, InfoFilled
} from '@element-plus/icons-vue'
import { environmentApi } from '../api/environment'
import type { ApiTestEnvironment } from '../types/environment'

interface ConfigItem {
  key: string
  value: string
}

interface Props {
  environment: ApiTestEnvironment | null
  configType: 'headers' | 'variables'
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const items = ref<ConfigItem[]>([])
const saving = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isHeaders = computed(() => props.configType === 'headers')

const dialogTitle = computed(() => {
  return isHeaders.value ? '全局请求头配置' : '全局变量配置'
})

const configTypeLabel = computed(() => {
  return isHeaders.value ? '全局请求头' : '全局变量'
})

const configDescription = computed(() => {
  if (isHeaders.value) {
    return '全局请求头将在该环境的所有请求中自动添加'
  } else {
    return '全局变量可在请求中使用 ${variable_name} 格式引用'
  }
})

const variableExample = computed(() => {
  if (items.value.length > 0) {
    return `\${${items.value[0].key}}`
  }
  return '${variable_name}'
})

// 方法
const hasVariables = (value: string): boolean => {
  if (!value) return false
  return /\$\{[^}]+\}/.test(value)
}

const addRow = () => {
  items.value.push({ key: '', value: '' })
}

const removeRow = (index: number) => {
  items.value.splice(index, 1)
}

const handleCopyAll = async () => {
  const data = isHeaders.value
    ? props.environment?.global_headers
    : props.environment?.global_variables

  if (data) {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      ElMessage.success('已复制到剪贴板')
    } catch {
      ElMessage.error('复制失败')
    }
  }
}

const handleClearAll = () => {
  items.value = []
}

const loadConfig = () => {
  if (!props.environment) return

  const data = isHeaders.value
    ? props.environment.global_headers || {}
    : props.environment.global_variables || {}

  items.value = Object.entries(data).map(([key, value]) => ({
    key,
    value: typeof value === 'string' ? value : JSON.stringify(value)
  }))
}

const configToSubmit = (): Record<string, string> => {
  const obj: Record<string, string> = {}
  items.value.forEach(item => {
    if (item.key && item.key.trim()) {
      obj[item.key.trim()] = item.value
    }
  })
  return obj
}

const handleSave = async () => {
  if (!props.environment) return

  saving.value = true
  try {
    const updateData: any = {
      name: props.environment.name,
      description: props.environment.description,
      project: props.environment.project,
      base_url: props.environment.base_url,
      is_default: props.environment.is_default,
      is_active: props.environment.is_active
    }

    if (isHeaders.value) {
      updateData.global_headers = configToSubmit()
      updateData.global_variables = props.environment.global_variables || {}
    } else {
      updateData.global_headers = props.environment.global_headers || {}
      updateData.global_variables = configToSubmit()
    }

    await environmentApi.updateEnvironment(props.environment.id, updateData)
    ElMessage.success('保存成功')
    emit('saved')
    handleClose()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error('Save config error:', error)
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  visible.value = false
}

// 监听
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadConfig()
  }
})

watch(() => props.configType, () => {
  if (visible.value) {
    loadConfig()
  }
})
</script>

<style scoped>
.config-preview-dialog {
  padding: 0;
}

.dialog-header {
  margin-bottom: 20px;
}

.env-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-type-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.editor-section {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.editor-content {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  min-height: 120px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.config-row:last-child {
  margin-bottom: 0;
}

.key-input {
  width: 200px;
}

.value-input {
  flex: 1;
}

.empty-state {
  padding: 20px;
  text-align: center;
}

.usage-hint {
  margin-top: 16px;
}

.usage-hint code {
  background-color: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #e83e8c;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-input__prefix) {
  color: #909399;
}

:deep(.el-alert) {
  padding: 8px 12px;
}

:deep(.el-alert__title) {
  font-size: 13px;
}
</style>
