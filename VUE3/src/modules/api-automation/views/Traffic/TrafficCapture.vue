<template>
  <div class="traffic-capture-page">
    <div class="page-header">
      <div class="header-left">
        <el-button type="primary" link @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回项目
        </el-button>
        <h1>流量录制生成用例</h1>
      </div>
    </div>

    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>1. 上传录制文件</span>
        </div>
      </template>
      <div class="upload-body">
        <input
          ref="fileInput"
          data-testid="traffic-upload-input"
          type="file"
          accept=".json,.har"
          @change="handleFileChange"
        />
        <el-button
          data-testid="traffic-upload-button"
          type="primary"
          :loading="uploading"
          @click="handleUpload"
        >
          上传并创建录制
        </el-button>
        <span class="upload-hint">支持 JSON / HAR 文件</span>
      </div>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>2. 录制列表</span>
        </div>
      </template>
      <el-table
        data-testid="traffic-capture-table"
        :data="captures"
        v-loading="capturesLoading"
        row-key="id"
      >
        <el-table-column prop="name" label="录制名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="total_entries" label="原始条目" width="120" />
        <el-table-column prop="filtered_entries" label="有效条目" width="120" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button
              data-testid="traffic-parse-button"
              type="primary"
              link
              @click="handleParse(row)"
            >
              解析
            </el-button>
            <el-button type="primary" link @click="selectCapture(row)">查看会话</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>3. 会话列表</span>
        </div>
      </template>
      <el-table
        data-testid="traffic-session-table"
        :data="sessions"
        v-loading="sessionsLoading"
        row-key="id"
      >
        <el-table-column prop="session_key" label="会话标识" min-width="220" />
        <el-table-column prop="entry_count" label="条目数量" width="120" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              data-testid="traffic-generate-button"
              type="primary"
              link
              @click="handleGenerate(row)"
            >
              生成用例
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>4. 生成结果</span>
        </div>
      </template>
      <el-table
        data-testid="traffic-artifact-table"
        :data="artifacts"
        v-loading="artifactsLoading"
        row-key="id"
      >
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="320">
          <template #default="{ row }">
            <el-button
              data-testid="traffic-preview-button"
              type="primary"
              link
              @click="openPreview(row)"
            >
              预览编辑
            </el-button>
            <el-button
              data-testid="traffic-trial-button"
              type="success"
              link
              @click="handleTrialRun(row, true)"
            >
              试运行通过
            </el-button>
            <el-button
              data-testid="traffic-trial-fail-button"
              type="danger"
              link
              @click="handleTrialRun(row, false)"
            >
              试运行失败
            </el-button>
            <el-button
              data-testid="traffic-commit-button"
              type="warning"
              link
              :disabled="row.status !== 'READY'"
              @click="handleCommit(row)"
            >
              提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="previewVisible" title="用例预览" width="70%">
      <el-input
        data-testid="traffic-preview-textarea"
        v-model="previewContent"
        type="textarea"
        :rows="18"
      />
      <template #footer>
        <el-button
          data-testid="traffic-preview-save-button"
          type="primary"
          :loading="savingPreview"
          @click="handleSavePreview"
        >
          保存草稿
        </el-button>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { trafficApi } from '../../api/traffic'
import type { GeneratedArtifact, TrafficCapture, TrafficSession } from '../../types/traffic'

const MAX_UPLOAD_SIZE = 5 * 1024 * 1024

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

const captures = ref<TrafficCapture[]>([])
const sessions = ref<TrafficSession[]>([])
const artifacts = ref<GeneratedArtifact[]>([])

const capturesLoading = ref(false)
const sessionsLoading = ref(false)
const artifactsLoading = ref(false)
const uploading = ref(false)

const previewVisible = ref(false)
const previewContent = ref('')
const currentArtifactId = ref<number | null>(null)
const savingPreview = ref(false)

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedFile.value = target.files?.[0] || null
}

const loadCaptures = async () => {
  capturesLoading.value = true
  try {
    const response = await trafficApi.getCaptures({ project_id: projectId.value })
    captures.value = response.results
  } catch (error) {
    ElMessage.error('加载录制列表失败')
  } finally {
    capturesLoading.value = false
  }
}

const loadSessions = async (captureId?: number) => {
  sessionsLoading.value = true
  try {
    const params: Record<string, any> = { project: projectId.value }
    if (captureId) {
      params.capture = captureId
    }
    const response = await trafficApi.getSessions(params)
    sessions.value = response.results
  } catch (error) {
    ElMessage.error('加载会话失败')
  } finally {
    sessionsLoading.value = false
  }
}

const loadArtifacts = async () => {
  artifactsLoading.value = true
  try {
    const response = await trafficApi.getArtifacts({ project: projectId.value })
    artifacts.value = response.results
  } catch (error) {
    ElMessage.error('加载生成结果失败')
  } finally {
    artifactsLoading.value = false
  }
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  if (selectedFile.value.size > MAX_UPLOAD_SIZE) {
    ElMessage.error('文件大小超过限制（5MB）')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('project', String(projectId.value))
    formData.append('name', `录制-${selectedFile.value.name}`)
    await trafficApi.createCapture(formData)
    ElMessage.success('上传成功')
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    await loadCaptures()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const handleParse = async (capture: TrafficCapture) => {
  try {
    const response = await trafficApi.parseCapture(capture.id)
    ElMessage.success(response.message || '解析完成')
    await loadCaptures()
    await loadSessions(capture.id)
  } catch (error) {
    ElMessage.error('解析失败')
  }
}

const selectCapture = async (capture: TrafficCapture) => {
  await loadSessions(capture.id)
}

const handleGenerate = async (session: TrafficSession) => {
  try {
    await trafficApi.generateArtifact(session.id)
    ElMessage.success('生成成功')
    await loadArtifacts()
  } catch (error) {
    ElMessage.error('生成失败')
  }
}

const openPreview = async (artifact: GeneratedArtifact) => {
  try {
    const response = await trafficApi.previewArtifact(artifact.id)
    currentArtifactId.value = artifact.id
    previewContent.value = JSON.stringify(response.payload, null, 2)
    previewVisible.value = true
  } catch (error) {
    ElMessage.error('预览加载失败')
  }
}

const handleSavePreview = async () => {
  if (!currentArtifactId.value) {
    ElMessage.error('未找到可保存的草稿')
    return
  }
  let parsedPayload: Record<string, any>
  try {
    parsedPayload = JSON.parse(previewContent.value || '{}')
  } catch (error) {
    ElMessage.error('预览内容不是合法 JSON')
    return
  }

  savingPreview.value = true
  try {
    await trafficApi.updateArtifact(currentArtifactId.value, { payload: parsedPayload })
    ElMessage.success('保存草稿成功')
    await loadArtifacts()
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    savingPreview.value = false
  }
}

const handleTrialRun = async (artifact: GeneratedArtifact, passed: boolean) => {
  try {
    await trafficApi.trialRunArtifact(artifact.id, passed, passed ? undefined : '试运行失败')
    ElMessage.success(passed ? '试运行通过' : '试运行失败')
    await loadArtifacts()
  } catch (error) {
    ElMessage.error('试运行失败')
  }
}

const handleCommit = async (artifact: GeneratedArtifact) => {
  try {
    await trafficApi.commitArtifact(artifact.id)
    ElMessage.success('提交成功')
    await loadArtifacts()
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

onMounted(async () => {
  await loadCaptures()
  await loadSessions()
  await loadArtifacts()
})
</script>

<style scoped>
.traffic-capture-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-card .upload-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.upload-hint {
  color: #909399;
  font-size: 12px;
}

.table-card {
  margin-top: 0;
}
</style>
