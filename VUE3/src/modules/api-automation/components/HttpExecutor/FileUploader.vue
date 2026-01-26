<template>
  <div class="file-uploader">
    <div class="upload-area"
         :class="{ 'is-dragover': dragover }"
         @drop.prevent="handleDrop"
         @dragover.prevent="dragover = true"
         @dragleave.prevent="dragover = false">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        multiple
        :on-change="handleFileChange"
        :accept="acceptTypes"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-hint">{{ uploadHint }}</p>
          </div>
        </div>
      </el-upload>
    </div>

    <div class="file-list" v-if="files.length > 0">
      <h4>文件列表</h4>
      <div class="file-items">
        <div
          v-for="(file, index) in files"
          :key="index"
          class="file-item"
        >
          <div class="file-info">
            <el-icon class="file-icon"><Document /></el-icon>
            <div class="file-details">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                <span class="file-size">{{ formatSize(file.size) }}</span>
                <span class="file-type">{{ file.type || '未知类型' }}</span>
              </div>
            </div>
          </div>
          <div class="file-form-key">
            <el-input
              v-model="file.formKey"
              placeholder="表单字段名"
              size="small"
              style="width: 150px;"
            />
          </div>
          <div class="file-actions">
            <el-tooltip content="预览" placement="top">
              <el-button
                size="small"
                type="text"
                @click="previewFile(file)"
                :disabled="!canPreview(file)"
              >
                <el-icon><View /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button
                size="small"
                type="text"
                style="color: #f56c6c;"
                @click="removeFile(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>

    <!-- 预览对话框 -->
    <el-dialog
      title="文件预览"
      v-model="previewVisible"
      width="60%"
      top="5vh"
    >
      <div class="file-preview">
        <div v-if="previewType === 'image'">
          <img :src="previewUrl" style="max-width: 100%; max-height: 500px;" />
        </div>
        <div v-else-if="previewType === 'text'" class="text-preview">
          <pre>{{ previewContent }}</pre>
        </div>
        <div v-else-if="previewType === 'json'" class="json-preview">
          <pre>{{ formatJson(previewContent) }}</pre>
        </div>
        <div v-else class="no-preview">
          <el-empty description="该文件类型不支持预览" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  Document,
  View,
  Delete
} from '@element-plus/icons-vue'

interface FileItem {
  file: File
  name: string
  size: number
  type: string
  formKey: string
  url?: string
}

interface Props {
  modelValue: FileItem[]
  acceptTypes?: string
  maxSize?: number // MB
  maxCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  acceptTypes: '*',
  maxSize: 10,
  maxCount: 10
})

const emit = defineEmits<{
  'update:modelValue': [value: FileItem[]]
}>()

// 响应式数据
const uploadRef = ref()
const files = ref<FileItem[]>([])
const dragover = ref(false)
const previewVisible = ref(false)
const previewType = ref('')
const previewUrl = ref('')
const previewContent = ref('')

// 计算属性
const uploadHint = computed(() => {
  return `支持 ${props.acceptTypes === '*' ? '所有' : props.acceptTypes} 格式，单个文件不超过 ${props.maxSize}MB`
})

// 方法
const handleFileChange = (file: any) => {
  const rawFile = file.raw

  // 检查文件大小
  if (rawFile.size > props.maxSize * 1024 * 1024) {
    ElMessage.error(`文件 "${rawFile.name}" 大小超过 ${props.maxSize}MB 限制`)
    return
  }

  // 检查文件数量
  if (files.value.length >= props.maxCount) {
    ElMessage.error(`文件数量不能超过 ${props.maxCount} 个`)
    return
  }

  // 检查重复
  if (files.value.some(f => f.name === rawFile.name)) {
    ElMessage.warning(`文件 "${rawFile.name}" 已存在`)
    return
  }

  const fileItem: FileItem = {
    file: rawFile,
    name: rawFile.name,
    size: rawFile.size,
    type: rawFile.type || '未知类型',
    formKey: rawFile.name,
    url: URL.createObjectURL(rawFile)
  }

  files.value.push(fileItem)
  emitUpdate()

  ElMessage.success(`文件 "${rawFile.name}" 添加成功`)
}

const handleDrop = (e: DragEvent) => {
  dragover.value = false

  const droppedFiles = e.dataTransfer?.files
  if (!droppedFiles) return

  Array.from(droppedFiles).forEach(file => {
    handleFileChange({ raw: file })
  })
}

const removeFile = (index: number) => {
  const file = files.value[index]
  if (file.url) {
    URL.revokeObjectURL(file.url)
  }
  files.value.splice(index, 1)
  emitUpdate()
}

const canPreview = (file: FileItem) => {
  return file.type.startsWith('image/') ||
         file.type.startsWith('text/') ||
         file.type === 'application/json'
}

const previewFile = async (file: FileItem) => {
  previewVisible.value = true

  if (file.type.startsWith('image/')) {
    previewType.value = 'image'
    previewUrl.value = file.url || ''
  } else if (file.type.startsWith('text/') || file.type === 'application/json') {
    previewType.value = file.type === 'application/json' ? 'json' : 'text'
    try {
      const content = await readFileContent(file.file)
      previewContent.value = content
    } catch (error) {
      previewContent.value = '读取文件失败'
    }
  } else {
    previewType.value = 'unknown'
  }
}

const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatJson = (jsonString: string) => {
  try {
    const parsed = JSON.parse(jsonString)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return jsonString
  }
}

const emitUpdate = () => {
  emit('update:modelValue', files.value)
}

// 监听器
const watchProps = () => {
  // 监听外部值变化
}
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
}

.upload-area.is-dragover {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.upload-content {
  padding: 40px;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 0;
  line-height: 1.5;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px !important;
}

.file-list {
  margin-top: 20px;
}

.file-list h4 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #303133;
}

.file-items {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: #f5f7fa;
}

.file-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.file-icon {
  font-size: 20px;
  color: #909399;
  flex-shrink: 0;
}

.file-details {
  min-width: 0;
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  word-break: break-all;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}

.file-size::after {
  content: ' • ';
}

.file-form-key {
  margin: 0 20px;
}

.file-actions {
  display: flex;
  gap: 5px;
}

.file-preview {
  max-height: 70vh;
  overflow: auto;
}

.text-preview pre,
.json-preview pre {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.no-preview {
  text-align: center;
  padding: 40px;
}
</style>