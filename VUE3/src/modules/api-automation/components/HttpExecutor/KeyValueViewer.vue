<!--
  KeyValueViewer.vue - 键值对只读查看器组件

  用于展示 HTTP 响应头、Cookie 等只读键值对数据：
  - 搜索过滤功能
  - 一键复制单个值或全部内容
  - JSON 值自动识别和格式化展示
  - URL 值自动识别并提供链接跳转
  - 值详情弹窗（长文本、JSON 格式化）
  - 数据导出为 JSON 文件
-->
<template>
  <div class="key-value-viewer">
    <div class="viewer-header">
      <div class="header-left">
        <span class="title">{{ title }}</span>
        <el-tag v-if="data.length" size="small" type="info">
          共 {{ data.length }} 项
        </el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索"
          size="small"
          style="width: 200px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button
          size="small"
          @click="copyAll"
          :disabled="filteredData.length === 0"
        >
          <el-icon><CopyDocument /></el-icon>
          复制全部
        </el-button>
        <el-button
          size="small"
          @click="downloadAsJson"
          :disabled="filteredData.length === 0"
        >
          <el-icon><Download /></el-icon>
          下载
        </el-button>
      </div>
    </div>

    <div class="viewer-content">
      <div v-if="filteredData.length === 0" class="empty-state">
        <el-empty
          :description="searchKeyword ? '没有找到匹配的数据' : '暂无数据'"
          :image-size="80"
        />
      </div>

      <div v-else class="key-value-list">
        <div
          v-for="(item, index) in filteredData"
          :key="getKey(item, index)"
          class="key-value-row"
        >
          <div class="row-index">{{ index + 1 }}</div>
          <div class="row-key">
            <span class="key-text" :title="item.key">{{ item.key }}</span>
          </div>
          <div class="row-value">
            <span
              class="value-text"
              :class="{ 'is-json': isJsonValue(item.value), 'is-url': isUrl(item.value) }"
              :title="item.value"
              @click="handleValueClick(item)"
            >
              {{ formatValue(item.value) }}
            </span>
            <el-button
              v-if="isJsonValue(item.value)"
              size="small"
              type="text"
              @click="formatJsonValue(item)"
              class="format-btn"
            >
              <el-icon><MagicStick /></el-icon>
            </el-button>
            <el-button
              size="small"
              type="text"
              @click="copyValue(item.value)"
              class="copy-btn"
            >
              <el-icon><DocumentCopy /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- JSON格式化对话框 -->
    <el-dialog
      title="JSON格式化"
      v-model="jsonDialogVisible"
      width="60%"
      top="5vh"
    >
      <div class="json-formatter">
        <div class="formatter-actions">
          <el-button size="small" @click="copyFormattedJson">
            <el-icon><DocumentCopy /></el-icon>
            复制
          </el-button>
        </div>
        <pre class="json-content">{{ formattedJson }}</pre>
      </div>
    </el-dialog>

    <!-- 值详情对话框 -->
    <el-dialog
      title="值详情"
      v-model="valueDialogVisible"
      width="60%"
      top="5vh"
    >
      <div class="value-detail">
        <div class="detail-header">
          <strong>键：</strong>{{ currentValue.key }}
        </div>
        <div class="detail-content">
          <strong>值：</strong>
          <div class="value-content">
            <pre v-if="isJsonValue(currentValue.value)">{{ formatJsonValue(currentValue.value) }}</pre>
            <div v-else class="plain-value">{{ currentValue.value }}</div>
          </div>
        </div>
        <div class="detail-meta">
          <p><strong>长度：</strong>{{ currentValue.value?.length || 0 }} 字符</p>
          <p><strong>类型：</strong>{{ getValueType(currentValue.value) }}</p>
          <p v-if="isUrl(currentValue.value)">
            <strong>URL：</strong>
            <el-link :href="currentValue.value" target="_blank" type="primary">
              {{ currentValue.value }}
              <el-icon><Link /></el-icon>
            </el-link>
          </p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  CopyDocument,
  Download,
  MagicStick,
  DocumentCopy,
  Link
} from '@element-plus/icons-vue'

interface KeyValueItem {
  key: string
  value: string
  [key: string]: any
}

interface Props {
  data: KeyValueItem[]
  title?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '键值对',
  readonly: true
})

// 响应式数据
const searchKeyword = ref('')
const jsonDialogVisible = ref(false)
const valueDialogVisible = ref(false)
const formattedJson = ref('')
const currentValue = ref<KeyValueItem>({ key: '', value: '' })

// 计算属性
const filteredData = computed(() => {
  if (!searchKeyword.value) {
    return props.data
  }

  const keyword = searchKeyword.value.toLowerCase()
  return props.data.filter(item =>
    item.key.toLowerCase().includes(keyword) ||
    item.value.toLowerCase().includes(keyword)
  )
})

// 方法
const getKey = (item: KeyValueItem, index: number) => {
  return item.key || index
}

const isJsonValue = (value: string): boolean => {
  if (!value || typeof value !== 'string') return false
  return (value.startsWith('{') && value.endsWith('}')) ||
         (value.startsWith('[') && value.endsWith(']'))
}

const isUrl = (value: string): boolean => {
  if (!value) return false
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

const formatValue = (value: string): string => {
  if (!value) return ''

  // 如果是JSON，显示简化的表示
  if (isJsonValue(value)) {
    try {
      const parsed = JSON.parse(value)
      if (Array.isArray(parsed)) {
        return `Array(${parsed.length})`
      } else if (typeof parsed === 'object') {
        return `Object(${Object.keys(parsed).length} keys)`
      }
    } catch {
      // 忽略解析错误
    }
  }

  // 限制显示长度
  const maxLength = 100
  if (value.length > maxLength) {
    return value.substring(0, maxLength) + '...'
  }

  return value
}

const getValueType = (value: string): string => {
  if (!value) return '空'

  if (isJsonValue(value)) {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? 'Array' : 'Object'
    } catch {
      return 'String'
    }
  }

  if (isUrl(value)) return 'URL'

  return 'String'
}

const handleValueClick = (item: KeyValueItem) => {
  if (isJsonValue(item.value)) {
    formatJsonValue(item)
  } else if (item.value?.length > 100 || isUrl(item.value)) {
    currentValue.value = item
    valueDialogVisible.value = true
  }
}

const formatJsonValue = (item?: KeyValueItem) => {
  const targetItem = item || currentValue.value

  if (!isJsonValue(targetItem.value)) {
    ElMessage.warning('不是有效的JSON格式')
    return
  }

  try {
    const parsed = JSON.parse(targetItem.value)
    formattedJson.value = JSON.stringify(parsed, null, 2)
    jsonDialogVisible.value = true
  } catch (error) {
    ElMessage.error('JSON格式化失败')
  }
}

const copyValue = async (value: string) => {
  try {
    await navigator.clipboard.writeText(value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const copyAll = async () => {
  try {
    const text = filteredData.value.map(item => `${item.key}: ${item.value}`).join('\n')
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制全部内容到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const copyFormattedJson = async () => {
  try {
    await navigator.clipboard.writeText(formattedJson.value)
    ElMessage.success('格式化JSON已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const downloadAsJson = () => {
  const data = filteredData.value.reduce((acc, item) => {
    acc[item.key] = isJsonValue(item.value) ? JSON.parse(item.value) : item.value
    return acc
  }, {} as Record<string, any>)

  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `key-value-data_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success('数据已下载')
}
</script>

<style scoped>
.key-value-viewer {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-weight: 500;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.viewer-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.key-value-list {
  background: #fff;
}

.key-value-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #ebeef5;
  transition: background-color 0.2s;
}

.key-value-row:hover {
  background: #f5f7fa;
}

.key-value-row:last-child {
  border-bottom: none;
}

.row-index {
  width: 40px;
  text-align: center;
  color: #909399;
  font-size: 12px;
  font-family: monospace;
}

.row-key {
  width: 200px;
  padding-right: 16px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-value {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.value-text {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.value-text:hover {
  color: #409eff;
}

.value-text.is-json {
  color: #67c23a;
}

.value-text.is-url {
  color: #409eff;
  text-decoration: underline;
}

.format-btn,
.copy-btn {
  padding: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.key-value-row:hover .format-btn,
.key-value-row:hover .copy-btn {
  opacity: 1;
}

.json-formatter {
  position: relative;
}

.formatter-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
}

.json-content {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 60vh;
  overflow-y: auto;
  margin: 0;
}

.value-detail {
  padding: 10px 0;
}

.detail-header,
.detail-content,
.detail-meta {
  margin-bottom: 20px;
}

.detail-content .value-content {
  margin-top: 10px;
}

.value-content pre {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}

.plain-value {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

.detail-meta p {
  margin: 8px 0;
  color: #606266;
}
</style>