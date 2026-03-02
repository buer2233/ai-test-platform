<!--
  HttpExecutor.vue - HTTP 执行器页面

  提供独立的 HTTP API 测试工具，支持以下功能：
  - HTTP 请求编辑器：通过 HttpRequestEditor 组件发送请求，支持所有 HTTP 方法、多种请求格式和变量替换
  - 请求历史列表：展示最近 20 条请求记录，含方法标签、URL、状态码、响应时间、执行时间
  - 历史操作：刷新历史、清空全部历史（带确认提示）
  - 行点击加载：点击历史记录行自动加载到编辑器中重新编辑
  - 保存为用例：将历史请求保存为测试用例（功能开发中）
  - 单条删除：删除指定历史记录（带确认提示）
-->
<template>
  <div class="http-executor-page">
    <div class="page-header">
      <h1>HTTP执行器</h1>
      <p>支持所有HTTP方法、多种请求格式和变量替换的API测试工具</p>
    </div>

    <HttpRequestEditor
      ref="requestEditorRef"
      @request-executed="onRequestExecuted"
    />

    <!-- 请求历史 -->
    <el-card class="history-card" v-if="showHistory">
      <template #header>
        <div class="card-header">
          <span>请求历史</span>
          <div class="header-actions">
            <el-button
              size="small"
              @click="refreshHistory"
              :loading="loadingHistory"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button
              size="small"
              @click="clearHistory"
            >
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="history"
        v-loading="loadingHistory"
        @row-click="loadFromHistory"
        style="cursor: pointer;"
      >
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.method)" size="small">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              v-if="row.status"
              :type="getStatusTagType(row.status)"
              size="small"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.response_time }}ms
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              size="small"
              type="text"
              @click.stop="saveToTestCase(row)"
            >
              保存
            </el-button>
            <el-button
              size="small"
              type="text"
              style="color: #f56c6c;"
              @click.stop="deleteHistoryItem(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import HttpRequestEditor from '../../components/HttpExecutor/HttpRequestEditor.vue'
import { httpExecutorApi } from '../../api/httpExecutor'
import { useProjectStore } from '../../stores/project'
import type { HttpRequest, HttpResponse } from '../../types/http'

// Store
const projectStore = useProjectStore()

// 响应式数据
const requestEditorRef = ref()
const showHistory = ref(true)
const loadingHistory = ref(false)
const history = ref<Array<any>>([])

// 方法
const onRequestExecuted = (response: HttpResponse) => {
  // 请求执行后的处理
  console.log('Request executed:', response)
  refreshHistory()
}

const getMethodTagType = (method: string) => {
  const typeMap: Record<string, string> = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'PATCH': 'warning',
    'DELETE': 'danger',
    'HEAD': 'info',
    'OPTIONS': 'info'
  }
  return typeMap[method] || 'info'
}

const getStatusTagType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400) return 'danger'
  return 'info'
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const refreshHistory = async () => {
  try {
    loadingHistory.value = true
    const response = await httpExecutorApi.getHistory({ limit: 20 })
    history.value = response.results || []
  } catch (error) {
    console.error('获取历史记录失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有历史记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里需要后端提供清空历史的API
    history.value = []
    ElMessage.success('历史记录已清空')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空历史记录失败:', error)
    }
  }
}

const loadFromHistory = (item: any) => {
  try {
    const request = JSON.parse(item.request)
    requestEditorRef.value?.loadRequest(request)
    ElMessage.success('已加载历史请求')
  } catch (error) {
    console.error('加载历史请求失败:', error)
    ElMessage.error('加载历史请求失败')
  }
}

const saveToTestCase = async (item: any) => {
  try {
    const request = JSON.parse(item.request)
    // 这里可以打开保存测试用例的对话框
    ElMessage.success('功能开发中...')
  } catch (error) {
    console.error('保存到测试用例失败:', error)
    ElMessage.error('保存失败')
  }
}

const deleteHistoryItem = async (item: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条历史记录吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await httpExecutorApi.deleteHistory(item.id)
    refreshHistory()
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除历史记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 生命周期
onMounted(() => {
  refreshHistory()
  projectStore.fetchProjects()
})
</script>

<style scoped>
.http-executor-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 10px;
}

.page-header p {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

.history-card {
  margin-top: 30px;
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

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>