<template>
  <div class="environment-list">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon><Odometer /></el-icon>
          环境管理
        </h1>
        <p class="page-description">管理测试环境配置，包括URL、全局变量和请求头设置</p>
      </div>
      <div class="header-actions">
        <el-dropdown trigger="click" @command="handleBatchCommand">
          <el-button type="warning" :disabled="selectedIds.length === 0">
            <el-icon><Operation /></el-icon>
            批量操作
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="enableAll">全部启用</el-dropdown-item>
              <el-dropdown-item command="disableAll">全部禁用</el-dropdown-item>
              <el-dropdown-item command="exportSelected" divided :disabled="selectedIds.length === 0">
                导出选中
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown trigger="click" @command="handleImport">
          <el-button type="success">
            <el-icon><Upload /></el-icon>
            导入
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="file">从文件导入</el-dropdown-item>
              <el-dropdown-item command="template">导入模板环境</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建环境
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <el-card class="stat-card" @click="handleShowStatisticsData('all')">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: #ecf5ff;">
            <el-icon :size="24" color="#409eff"><Files /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-label">总环境数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" @click="handleShowStatisticsData('active')">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: #f0f9ff;">
            <el-icon :size="24" color="#67c23a"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.active }}</div>
            <div class="stat-label">已启用</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" @click="handleShowStatisticsData('inactive')">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: #fef0f0;">
            <el-icon :size="24" color="#f56c6c"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.inactive }}</div>
            <div class="stat-label">已禁用</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" @click="handleShowStatisticsData('default')">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: #fdf6ec;">
            <el-icon :size="24" color="#e6a23c"><Trophy /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.defaultCount }}</div>
            <div class="stat-label">默认环境</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" @click="handleShowStatisticsData('favorite')">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: #fef0f0;">
            <el-icon :size="24" color="#f56c6c"><StarFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.favoriteCount }}</div>
            <div class="stat-label">收藏环境</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="环境名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入环境名称"
            clearable
            @keyup.enter="handleSearch"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="searchForm.project" placeholder="请选择项目" clearable style="width: 180px">
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="请选择状态" clearable style="width: 120px">
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <div class="table-header">
        <div class="table-title">
          <el-checkbox
            v-model="selectAll"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          />
          <span class="selected-info" v-if="selectedIds.length > 0">
            已选择 {{ selectedIds.length }} 项
            <el-button type="primary" text @click="clearSelection" style="margin-left: 8px">
              取消选择
            </el-button>
          </span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="environments"
        style="width: 100%"
        stripe
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        ref="tableRef"
      >
        <el-table-column type="selection" width="50" />

        <el-table-column prop="name" label="环境名称" min-width="160">
          <template #default="{ row }">
            <div class="env-name-cell">
              <el-icon
                v-if="row.is_favorite"
                class="favorite-icon favorited"
                color="#f56c6c"
                @click="handleToggleFavorite(row)"
              >
                <StarFilled />
              </el-icon>
              <el-icon
                v-else
                class="favorite-icon"
                color="#c0c4cc"
                @click="handleToggleFavorite(row)"
              >
                <StarFilled />
              </el-icon>
              <el-icon v-if="row.is_default" class="default-icon" color="#e6a23c"><Trophy /></el-icon>
              <span class="env-name">{{ row.name }}</span>
              <el-tag v-if="row.is_default" type="warning" size="small" style="margin-left: 8px;">默认</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />

        <el-table-column prop="project_name" label="所属项目" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ row.project_name }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="base_url" label="Base URL" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="url-cell">
              <el-link :href="row.base_url" target="_blank" type="primary" :underline="false">
                <el-icon><Link /></el-icon>
                {{ truncateUrl(row.base_url) }}
              </el-link>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="配置统计" width="120" align="center">
          <template #default="{ row }">
            <div class="config-stats">
              <el-tooltip content="点击查看全局请求头">
                <el-tag
                  size="small"
                  type="info"
                  class="config-tag clickable"
                  @click="handleShowConfig(row, 'headers')"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  {{ Object.keys(row.global_headers || {}).length }}
                </el-tag>
              </el-tooltip>
              <el-tooltip content="点击查看全局变量">
                <el-tag
                  size="small"
                  type="success"
                  class="config-tag clickable"
                  @click="handleShowConfig(row, 'variables')"
                >
                  <el-icon><Collection /></el-icon>
                  {{ Object.keys(row.global_variables || {}).length }}
                </el-tag>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :loading="switchLoading[row.id]"
              @change="handleStatusChange(row)"
              active-color="#67c23a"
              inactive-color="#dcdfe6"
            />
          </template>
        </el-table-column>

        <el-table-column prop="updated_time" label="更新时间" width="170" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_time) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" text @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button type="primary" size="small" text @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button type="success" size="small" text @click="handleTestConnection(row)">
                <el-icon><Connection /></el-icon>
                测试
              </el-button>
              <el-dropdown trigger="click" @command="(cmd) => handleMoreCommand(cmd, row)">
                <el-button type="info" size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="copy">
                      <el-icon><CopyDocument /></el-icon>
                      复制环境
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      导出配置
                    </el-dropdown-item>
                    <el-dropdown-item command="setDefault" :disabled="row.is_default">
                      <el-icon><Star /></el-icon>
                      设为默认
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除环境
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑环境对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingEnvironment ? '编辑环境' : '新建环境'"
      width="900px"
      :before-close="handleDialogClose"
      destroy-on-close
    >
      <EnvironmentForm
        :environment="editingEnvironment"
        :projects="projects"
        @submit="handleSubmitEnvironment"
        @cancel="handleDialogClose"
      />
    </el-dialog>

    <!-- 环境详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="环境详情"
      width="1000px"
      destroy-on-close
    >
      <EnvironmentDetail
        v-if="viewingEnvironment"
        :environment="viewingEnvironment"
      />
    </el-dialog>

    <!-- 连接测试结果对话框 -->
    <el-dialog
      v-model="showTestResultDialog"
      title="连接测试结果"
      width="900px"
    >
      <div v-if="testResult" class="test-result-content">
        <!-- 结果状态提示 -->
        <el-alert
          :type="testResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <template #title>
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </template>
        </el-alert>

        <!-- 基本信息 -->
        <el-descriptions :column="2" border style="margin-top: 20px" size="small">
          <el-descriptions-item label="目标URL" :span="2">
            <el-link :href="testResult.url" target="_blank" type="primary">
              {{ testResult.url }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="HTTP状态码">
            <el-tag v-if="testResult.status_code" :type="getStatusCodeColor(testResult.status_code)">
              {{ testResult.status_code }}
              <span v-if="testResult.response?.reason" style="margin-left: 4px">
                {{ testResult.response.reason }}
              </span>
            </el-tag>
            <el-tag v-else type="danger">无响应</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            <el-tag :type="getResponseTimeColor(testResult.response_time)">
              {{ testResult.response_time }}ms
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="消息" :span="2" v-if="testResult.message">
            {{ testResult.message }}
          </el-descriptions-item>
          <el-descriptions-item label="响应大小" v-if="testResult.response?.size">
            {{ formatBytes(testResult.response.size) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 请求信息 -->
        <el-divider content-position="left">
          <el-icon><Upload /></el-icon>
          请求信息
        </el-divider>
        <div class="request-info" v-if="testResult.request">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="请求方法">
              <el-tag type="primary">{{ testResult.request.method }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="请求URL">
              <code>{{ testResult.request.url }}</code>
            </el-descriptions-item>
          </el-descriptions>

          <div class="headers-section" style="margin-top: 12px">
            <div class="section-header">
              <span>请求头 (Request Headers)</span>
              <el-button size="small" text @click="copyToClipboard(JSON.stringify(testResult.request.headers, null, 2))">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatHeaders(testResult.request.headers) }}</pre>
            </div>
          </div>
        </div>

        <!-- 响应信息 -->
        <template v-if="testResult.response">
          <el-divider content-position="left">
            <el-icon><Download /></el-icon>
            响应信息
          </el-divider>

          <!-- 响应头 -->
          <div class="response-headers">
            <div class="section-header">
              <span>响应头 (Response Headers)</span>
              <el-button size="small" text @click="copyToClipboard(JSON.stringify(testResult.response.headers, null, 2))">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatHeaders(testResult.response.headers) }}</pre>
            </div>
          </div>

          <!-- 响应体 -->
          <div class="response-body" style="margin-top: 16px" v-if="testResult.response.body !== null">
            <div class="section-header">
              <span>响应体 (Response Body)</span>
              <el-button size="small" text @click="copyToClipboard(typeof testResult.response.body === 'object' ? JSON.stringify(testResult.response.body, null, 2) : testResult.response.body)">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
            <div class="code-block">
              <pre>{{ formatResponseBody(testResult.response.body) }}</pre>
            </div>
          </div>
        </template>

        <!-- 错误信息 -->
        <template v-if="testResult.error">
          <el-divider content-position="left">
            <el-icon><Warning /></el-icon>
            错误详情
          </el-divider>
          <div class="error-info">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="错误类型">
                <el-tag type="danger">{{ testResult.error.type }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="错误消息">
                {{ testResult.error.message }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="error-details" style="margin-top: 12px" v-if="testResult.error.details">
              <div class="section-header">
                <span>详细错误日志</span>
                <el-button size="small" text @click="copyToClipboard(testResult.error.details)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
              <div class="code-block error-code">
                <pre>{{ testResult.error.details }}</pre>
              </div>
            </div>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入环境配置"
      width="600px"
    >
      <el-upload
        class="import-upload"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".json"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .json 格式的环境配置文件
          </div>
        </template>
      </el-upload>

      <div class="import-actions" style="margin-top: 20px; text-align: right;">
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleImportFile" :loading="importing">导入</el-button>
      </div>
    </el-dialog>

    <!-- 配置预览/编辑对话框 -->
    <ConfigPreviewDialog
      v-model="showConfigDialog"
      :environment="configEnvironment"
      :config-type="configType"
      @saved="handleConfigSaved"
    />

    <!-- 统计数据弹窗 -->
    <el-dialog
      v-model="showStatisticsDialog"
      :title="statisticsDialogTitle"
      width="1200px"
      destroy-on-close
    >
      <div class="statistics-dialog-content">
        <!-- 操作按钮区 -->
        <div class="dialog-actions-bar">
          <el-space>
            <el-button v-if="statisticsType === 'all'" type="primary" :icon="Plus" @click="handleCreateEnvironment">
              新建环境
            </el-button>
            <el-button v-if="statisticsType === 'all'" type="danger" :disabled="selectedStatisticsEnvironments.length === 0" @click="handleBatchDeleteStatistics">
              删除选中 ({{ selectedStatisticsEnvironments.length }})
            </el-button>
            <el-button v-if="statisticsType === 'active' || statisticsType === 'inactive'" type="warning" @click="handleBatchToggleStatistics">
              {{ statisticsType === 'active' ? '批量禁用' : '批量启用' }}
            </el-button>
          </el-space>
          <el-button @click="handleRefreshStatistics">刷新</el-button>
        </div>

        <!-- 数据表格 -->
        <el-table
          :data="filteredStatisticsEnvironments"
          v-loading="statisticsLoading"
          @selection-change="handleStatisticsSelectionChange"
          style="width: 100%; margin-top: 16px"
          stripe
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="环境名称" min-width="140">
            <template #default="{ row }">
              <div class="env-name-cell">
                <el-icon
                  v-if="row.is_favorite"
                  class="favorite-icon favorited"
                  color="#f56c6c"
                  @click="handleToggleFavoriteInDialog(row)"
                >
                  <StarFilled />
                </el-icon>
                <el-icon
                  v-else
                  class="favorite-icon"
                  color="#c0c4cc"
                  @click="handleToggleFavoriteInDialog(row)"
                >
                  <StarFilled />
                </el-icon>
                <el-icon v-if="row.is_default" class="default-icon" color="#e6a23c"><Trophy /></el-icon>
                <span class="env-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="project_name" label="所属项目" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.project_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip />
          <el-table-column prop="is_active" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="handleStatusChangeInDialog(row)"
                active-color="#67c23a"
                inactive-color="#dcdfe6"
              />
            </template>
          </el-table-column>
          <el-table-column prop="updated_time" label="更新时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button type="primary" size="small" text @click="handleEditInDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button type="success" size="small" text @click="handleTestConnectionInDialog(row)">
                  <el-icon><Connection /></el-icon>
                  测试
                </el-button>
                <el-button type="danger" size="small" text @click="handleDeleteInDialog(row)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination" v-if="statisticsEnvironments.length > 10">
          <el-pagination
            v-model:current-page="statisticsPagination.page"
            v-model:page-size="statisticsPagination.size"
            :page-sizes="[10, 20, 50]"
            :total="statisticsEnvironments.length"
            layout="total, sizes, prev, pager, next"
            @size-change="statisticsPagination.size = $event"
            @current-change="statisticsPagination.page = $event"
          />
        </div>

        <!-- 空状态 -->
        <el-empty v-if="statisticsEnvironments.length === 0" description="暂无数据" :image-size="100" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Refresh, View, Edit, Connection, Star, StarFilled, Trophy, Delete,
  Operation, ArrowDown, Odometer, Files, CircleCheck, CircleClose,
  Link, DocumentCopy, Collection, MoreFilled, CopyDocument, Download,
  Upload, UploadFilled, VideoPlay, Warning
} from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'

import { environmentApi } from '../../api/environment'
import { projectApi } from '../../api/project'
import EnvironmentForm from '../../components/EnvironmentForm.vue'
import EnvironmentDetail from '../../components/EnvironmentDetail.vue'
import ConfigPreviewDialog from '../../components/ConfigPreviewDialog.vue'

import type { ApiTestEnvironment, EnvironmentCreate } from '../../types/environment'

const router = useRouter()

// 数据状态
const loading = ref(false)
const environments = ref<ApiTestEnvironment[]>([])
const projects = ref([])
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showTestResultDialog = ref(false)
const showImportDialog = ref(false)
const showConfigDialog = ref(false)
const configEnvironment = ref<ApiTestEnvironment | null>(null)
const configType = ref<'headers' | 'variables'>('headers')
const editingEnvironment = ref<ApiTestEnvironment | null>(null)
const viewingEnvironment = ref<ApiTestEnvironment | null>(null)
const switchLoading = ref<Record<number, boolean>>({})
const testResult = ref<any>(null)
const importing = ref(false)
const importFile = ref<File | null>(null)
const tableRef = ref()
const selectedIds = ref<number[]>([])

// 统计数据弹窗相关
const showStatisticsDialog = ref(false)
const statisticsType = ref<'all' | 'active' | 'inactive' | 'default' | 'favorite'>('all')
const statisticsDialogTitle = ref('')
const statisticsEnvironments = ref<ApiTestEnvironment[]>([])
const statisticsLoading = ref(false)
const selectedStatisticsEnvironments = ref<ApiTestEnvironment[]>([])
const statisticsPagination = reactive({ page: 1, size: 10 })

// 统计数据
const statistics = ref({
  total: 0,
  active: 0,
  inactive: 0,
  defaultCount: 0,
  favoriteCount: 0
})

// 搜索表单
const searchForm = reactive({
  name: '',
  project: null as number | null,
  is_active: null as boolean | null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 排序
const sortConfig = reactive({
  prop: '',
  order: ''
})

// 全选状态
const selectAll = ref(false)
const isIndeterminate = computed(() => {
  const selectedCount = selectedIds.value.length
  return selectedCount > 0 && selectedCount < environments.value.length
})

// 计算属性
const currentProject = computed(() => {
  return null
})

// 生命周期
onMounted(() => {
  loadEnvironments()
  loadProjects()
})

// 方法
const loadEnvironments = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.size,
      ...searchForm,
      project: currentProject.value || searchForm.project
    }

    const response = await environmentApi.getEnvironments(params)
    environments.value = response.results
    pagination.total = response.count

    // 更新统计
    updateStatistics(response.results)

  } catch (error) {
    ElMessage.error('加载环境列表失败')
    console.error('Load environments error:', error)
  } finally {
    loading.value = false
  }
}

const updateStatistics = (data: ApiTestEnvironment[]) => {
  statistics.value = {
    total: data.length,
    active: data.filter(e => e.is_active).length,
    inactive: data.filter(e => !e.is_active).length,
    defaultCount: data.filter(e => e.is_default).length,
    favoriteCount: data.filter(e => e.is_favorite).length
  }
}

const loadProjects = async () => {
  try {
    const response = await projectApi.getProjects()
    projects.value = response.results
  } catch (error) {
    console.error('Load projects error:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadEnvironments()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.project = null
  searchForm.is_active = null
  pagination.page = 1
  loadEnvironments()
}

const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  loadEnvironments()
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadEnvironments()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadEnvironments()
}

// 选择相关
const handleSelectionChange = (selection: ApiTestEnvironment[]) => {
  selectedIds.value = selection.map(item => item.id)
  selectAll.value = selection.length === environments.value.length
}

const handleSelectAll = (val: boolean) => {
  selectedIds.value = val ? environments.value.map(e => e.id) : []
}

const clearSelection = () => {
  selectedIds.value = []
  selectAll.value = false
  tableRef.value?.clearSelection()
}

const handleView = (environment: ApiTestEnvironment) => {
  viewingEnvironment.value = environment
  showDetailDialog.value = true
}

const handleEdit = (environment: ApiTestEnvironment) => {
  editingEnvironment.value = { ...environment }
  showCreateDialog.value = true
}

const handleDelete = async (environment: ApiTestEnvironment) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除环境"${environment.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await environmentApi.deleteEnvironment(environment.id)
    ElMessage.success('删除成功')
    loadEnvironments()

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete environment error:', error)
    }
  }
}

const handleTestConnection = async (environment: ApiTestEnvironment) => {
  try {
    ElMessage.info('正在测试连接...')
    const response = await environmentApi.testConnection(environment.id)

    testResult.value = response
    showTestResultDialog.value = true

    if (response.success) {
      ElMessage.success(`连接测试成功，响应时间: ${response.response_time}ms`)
    } else {
      ElMessage.warning(`连接测试完成: ${response.message || '请查看详情'}`)
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
    console.error('Test connection error:', error)
  }
}

const handleSetDefault = async (environment: ApiTestEnvironment) => {
  if (environment.is_default) {
    return
  }

  try {
    await environmentApi.setDefault(environment.id)
    ElMessage.success('设置默认环境成功')
    loadEnvironments()
  } catch (error) {
    ElMessage.error('设置默认环境失败')
    console.error('Set default environment error:', error)
  }
}

const handleStatusChange = async (environment: ApiTestEnvironment) => {
  switchLoading.value[environment.id] = true

  try {
    await environmentApi.updateEnvironment(environment.id, {
      is_active: environment.is_active
    })

    ElMessage.success(environment.is_active ? '环境已启用' : '环境已禁用')
    loadEnvironments()
  } catch (error) {
    // 恢复原状态
    environment.is_active = !environment.is_active
    ElMessage.error('状态更新失败')
    console.error('Update environment status error:', error)
  } finally {
    switchLoading.value[environment.id] = false
  }
}

const handleMoreCommand = async (command: string, environment: ApiTestEnvironment) => {
  switch (command) {
    case 'copy':
      await handleCopy(environment)
      break
    case 'export':
      await handleExport(environment)
      break
    case 'setDefault':
      await handleSetDefault(environment)
      break
    case 'delete':
      await handleDelete(environment)
      break
  }
}

const handleCopy = async (environment: ApiTestEnvironment) => {
  try {
    const copyData: EnvironmentCreate = {
      name: `${environment.name} (副本)`,
      description: environment.description,
      project: environment.project,
      base_url: environment.base_url,
      global_headers: { ...environment.global_headers },
      global_variables: { ...environment.global_variables },
      is_default: false,
      is_active: true
    }

    await environmentApi.createEnvironment(copyData)
    ElMessage.success('环境复制成功')
    loadEnvironments()
  } catch (error) {
    ElMessage.error('环境复制失败')
    console.error('Copy environment error:', error)
  }
}

const handleExport = async (environment: ApiTestEnvironment) => {
  try {
    const exportData = {
      name: environment.name,
      description: environment.description,
      base_url: environment.base_url,
      global_headers: environment.global_headers,
      global_variables: environment.global_variables
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    saveAs(blob, `environment_${environment.name}_${Date.now()}.json`)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export environment error:', error)
  }
}

const handleBatchCommand = async (command: string) => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要操作的环境')
    return
  }

  switch (command) {
    case 'enableAll':
      await batchUpdateStatus(true)
      break
    case 'disableAll':
      await batchUpdateStatus(false)
      break
    case 'exportSelected':
      await handleExportSelected()
      break
  }
}

const batchUpdateStatus = async (status: boolean) => {
  try {
    await ElMessageBox.confirm(
      `确定要${status ? '启用' : '禁用'}选中的 ${selectedIds.value.length} 个环境吗？`,
      '批量操作确认',
      { type: 'warning' }
    )

    for (const id of selectedIds.value) {
      await environmentApi.updateEnvironment(id, { is_active: status })
    }

    ElMessage.success(`已${status ? '启用' : '禁用'} ${selectedIds.value.length} 个环境`)
    clearSelection()
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量操作失败')
    }
  }
}

const handleExportSelected = async () => {
  try {
    const selectedEnvironments = environments.value.filter(e => selectedIds.value.includes(e.id))
    const exportData = selectedEnvironments.map(env => ({
      name: env.name,
      description: env.description,
      base_url: env.base_url,
      global_headers: env.global_headers,
      global_variables: env.global_variables
    }))

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    saveAs(blob, `environments_${Date.now()}.json`)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export environments error:', error)
  }
}

const handleImport = (command: string) => {
  if (command === 'file') {
    showImportDialog.value = true
  } else if (command === 'template') {
    // 导入模板环境
    const templateEnv: EnvironmentCreate = {
      name: '开发环境',
      description: '开发测试环境模板',
      project: projects.value[0]?.id,
      base_url: 'https://dev-api.example.com',
      global_headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      global_variables: {
        'env': 'dev',
        'timeout': '5000'
      },
      is_default: false,
      is_active: true
    }

    createEnvironmentFromData(templateEnv)
  }
}

const handleFileChange = (file: any) => {
  importFile.value = file.raw
}

const handleImportFile = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  importing.value = true
  try {
    const text = await importFile.value.text()
    const data = JSON.parse(text)

    if (Array.isArray(data)) {
      for (const env of data) {
        await createEnvironmentFromData(env)
      }
      ElMessage.success(`成功导入 ${data.length} 个环境`)
    } else {
      await createEnvironmentFromData(data)
      ElMessage.success('环境导入成功')
    }

    showImportDialog.value = false
    loadEnvironments()
  } catch (error: any) {
    ElMessage.error(`导入失败: ${error.message}`)
    console.error('Import environment error:', error)
  } finally {
    importing.value = false
    importFile.value = null
  }
}

const createEnvironmentFromData = async (data: any) => {
  const envData: EnvironmentCreate = {
    name: data.name,
    description: data.description,
    project: data.project || projects.value[0]?.id,
    base_url: data.base_url,
    global_headers: data.global_headers || {},
    global_variables: data.global_variables || {},
    is_default: data.is_default || false,
    is_active: data.is_active !== false
  }

  await environmentApi.createEnvironment(envData)
}

const handleSubmitEnvironment = async (data: EnvironmentCreate) => {
  try {
    if (editingEnvironment.value) {
      await environmentApi.updateEnvironment(editingEnvironment.value.id, data)
      ElMessage.success('环境更新成功')
    } else {
      await environmentApi.createEnvironment(data)
      ElMessage.success('环境创建成功')
    }

    handleDialogClose()
    loadEnvironments()

  } catch (error) {
    ElMessage.error(editingEnvironment.value ? '环境更新失败' : '环境创建失败')
    console.error('Submit environment error:', error)
  }
}

const handleDialogClose = () => {
  showCreateDialog.value = false
  showDetailDialog.value = false
  showTestResultDialog.value = false
  editingEnvironment.value = null
  viewingEnvironment.value = null
  testResult.value = null
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const truncateUrl = (url: string) => {
  if (!url) return ''
  try {
    const urlObj = new URL(url)
    return urlObj.hostname + (urlObj.pathname.length > 1 ? urlObj.pathname : '') + '...'
  } catch {
    return url.length > 30 ? url.substring(0, 30) + '...' : url
  }
}

// 配置预览相关方法
const handleShowConfig = (environment: ApiTestEnvironment, type: 'headers' | 'variables') => {
  configEnvironment.value = environment
  configType.value = type
  showConfigDialog.value = true
}

const handleConfigSaved = () => {
  // 刷新环境列表
  loadEnvironments()
}

// 统计数据弹窗相关方法
const filteredStatisticsEnvironments = computed(() => {
  const start = (statisticsPagination.page - 1) * statisticsPagination.size
  const end = start + statisticsPagination.size
  return statisticsEnvironments.value.slice(start, end)
})

const handleShowStatisticsData = (type: 'all' | 'active' | 'inactive' | 'default' | 'favorite') => {
  statisticsType.value = type
  const titles = {
    all: '所有环境',
    active: '已启用的环境',
    inactive: '已禁用的环境',
    default: '默认环境列表',
    favorite: '收藏的环境列表'
  }
  statisticsDialogTitle.value = titles[type]
  showStatisticsDialog.value = true
  loadStatisticsEnvironments()
}

const loadStatisticsEnvironments = async () => {
  statisticsLoading.value = true
  try {
    const response = await environmentApi.getEnvironments({ page_size: 1000 })
    let filtered = response.results

    // 根据类型过滤
    switch (statisticsType.value) {
      case 'active':
        filtered = filtered.filter(e => e.is_active)
        break
      case 'inactive':
        filtered = filtered.filter(e => !e.is_active)
        break
      case 'default':
        filtered = filtered.filter(e => e.is_default)
        break
      case 'favorite':
        filtered = filtered.filter(e => e.is_favorite)
        break
    }

    statisticsEnvironments.value = filtered
    statisticsPagination.page = 1
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    statisticsLoading.value = false
  }
}

const handleRefreshStatistics = () => {
  loadStatisticsEnvironments()
}

const handleStatisticsSelectionChange = (selection: ApiTestEnvironment[]) => {
  selectedStatisticsEnvironments.value = selection
}

const handleCreateEnvironment = () => {
  showStatisticsDialog.value = false
  showCreateDialog.value = true
}

const handleBatchDeleteStatistics = async () => {
  if (selectedStatisticsEnvironments.value.length === 0) {
    ElMessage.warning('请先选择要删除的环境')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedStatisticsEnvironments.value.length} 个环境吗？`,
      '批量删除确认',
      { type: 'warning' }
    )

    for (const env of selectedStatisticsEnvironments.value) {
      await environmentApi.deleteEnvironment(env.id)
    }

    ElMessage.success('删除成功')
    selectedStatisticsEnvironments.value = []
    loadStatisticsEnvironments()
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchToggleStatistics = async () => {
  if (selectedStatisticsEnvironments.value.length === 0) {
    ElMessage.warning('请先选择要操作的环境')
    return
  }

  const newStatus = statisticsType.value === 'inactive' // 如果在禁用列表，则批量启用

  try {
    await ElMessageBox.confirm(
      `确定要${newStatus ? '启用' : '禁用'}选中的 ${selectedStatisticsEnvironments.value.length} 个环境吗？`,
      '批量操作确认',
      { type: 'warning' }
    )

    for (const env of selectedStatisticsEnvironments.value) {
      await environmentApi.updateEnvironment(env.id, { is_active: newStatus })
    }

    ElMessage.success('操作成功')
    selectedStatisticsEnvironments.value = []
    loadStatisticsEnvironments()
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleToggleFavoriteInDialog = async (environment: ApiTestEnvironment) => {
  try {
    const response = await environmentApi.toggleFavorite(environment.id)
    environment.is_favorite = response.is_favorite
    ElMessage.success(response.message)
    // 刷新列表和统计数据
    loadEnvironments()
    loadStatisticsEnvironments()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleStatusChangeInDialog = async (environment: ApiTestEnvironment) => {
  try {
    await environmentApi.updateEnvironment(environment.id, {
      is_active: environment.is_active
    })
    ElMessage.success(environment.is_active ? '环境已启用' : '环境已禁用')
    loadEnvironments()
  } catch (error) {
    environment.is_active = !environment.is_active
    ElMessage.error('状态更新失败')
  }
}

const handleEditInDialog = (environment: ApiTestEnvironment) => {
  showStatisticsDialog.value = false
  editingEnvironment.value = { ...environment }
  showCreateDialog.value = true
}

const handleDeleteInDialog = async (environment: ApiTestEnvironment) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除环境"${environment.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await environmentApi.deleteEnvironment(environment.id)
    ElMessage.success('删除成功')
    loadStatisticsEnvironments()
    loadEnvironments()

    if (statisticsEnvironments.value.length === 0) {
      showStatisticsDialog.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTestConnectionInDialog = async (environment: ApiTestEnvironment) => {
  try {
    ElMessage.info('正在测试连接...')
    const response = await environmentApi.testConnection(environment.id)
    testResult.value = response
    showTestResultDialog.value = true

    if (response.success) {
      ElMessage.success(`连接测试成功，响应时间: ${response.response_time}ms`)
    } else {
      ElMessage.warning(`连接测试完成: ${response.message || '请查看详情'}`)
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
  }
}

// 收藏相关方法
const handleToggleFavorite = async (environment: ApiTestEnvironment) => {
  try {
    const response = await environmentApi.toggleFavorite(environment.id)
    environment.is_favorite = response.is_favorite
    ElMessage.success(response.message)
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('Toggle favorite error:', error)
  }
}

// 连接测试相关辅助方法
const getStatusCodeColor = (code: number | null) => {
  if (!code) return 'danger'
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  return 'danger'
}

const getResponseTimeColor = (time: number) => {
  if (time < 200) return 'success'
  if (time < 500) return 'warning'
  return 'danger'
}

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatHeaders = (headers: Record<string, string> | null) => {
  if (!headers) return ''
  return Object.entries(headers)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n')
}

const formatResponseBody = (body: any) => {
  if (body === null || body === undefined) return ''
  if (typeof body === 'object') {
    return JSON.stringify(body, null, 2)
  }
  return String(body)
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.environment-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.statistics-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 搜索和表格 */
.search-card {
  margin-bottom: 20px;
}

.table-card {
  min-height: 400px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-info {
  font-size: 13px;
  color: #606266;
}

.env-name-cell {
  display: flex;
  align-items: center;
}

.favorite-icon {
  margin-right: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.favorite-icon:hover {
  transform: scale(1.2);
}

.favorite-icon.favorited {
  animation: favoriteBounce 0.3s ease;
}

@keyframes favoriteBounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.default-icon {
  margin-right: 4px;
}

.env-name {
  font-weight: 500;
}

.url-cell {
  display: flex;
  align-items: center;
}

.config-stats {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.config-tag {
  cursor: default;
  transition: all 0.2s;
}

.config-tag.clickable {
  cursor: pointer;
}

.config-tag.clickable:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 测试结果 */
.test-result-content {
  padding: 10px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px 4px 0 0;
  border: 1px solid #dcdfe6;
  border-bottom: none;
  font-weight: 500;
  font-size: 13px;
  color: #303133;
}

.code-block {
  background-color: #fafafa;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.code-block pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-code {
  background-color: #fef0f0;
  border-color: #fbc4c4;
}

.error-code pre {
  color: #f56c6c;
}

.request-info,
.error-info {
  margin-top: 12px;
}

.response-headers,
.response-body {
  margin-top: 12px;
}

.response-headers .code-block,
.response-body .code-block {
  max-height: 250px;
}

.headers-section {
  margin-top: 12px;
}

/* 导入 */
.import-upload {
  width: 100%;
}

:deep(.el-table) {
  .el-table__header-wrapper {
    background-color: #f5f7fa;
  }
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-upload-dragger) {
  padding: 40px;
}

:deep(.el-button-group .el-button + .el-button) {
  margin-left: 0;
}

/* 统计数据弹窗 */
.statistics-dialog-content {
  min-height: 400px;
}

.dialog-actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

:deep(.el-table) {
  .el-table__header-wrapper {
    background-color: #f5f7fa;
  }
}
</style>
