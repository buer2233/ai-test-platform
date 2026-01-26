<template>
  <div class="http-execution-records">
    <el-page-header @back="$router.go(-1)" title="返回">
      <template #content>
        <span class="text-large font-600">HTTP执行记录管理</span>
      </template>
    </el-page-header>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="statistics-cards">
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card" shadow="hover" @click="filterByStatus(null)">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-label">总记录数</div>
          </div>
          <el-icon class="stat-icon total"><DataLine /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card success" shadow="hover" @click="filterByStatus('SUCCESS')">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.success }}</div>
            <div class="stat-label">成功</div>
          </div>
          <el-icon class="stat-icon"><CircleCheck /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card failed" shadow="hover" @click="filterByStatus('FAILED')">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <el-icon class="stat-icon"><CircleClose /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card timeout" shadow="hover" @click="filterByStatus('TIMEOUT')">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.timeout }}</div>
            <div class="stat-label">超时</div>
          </div>
          <el-icon class="stat-icon"><Clock /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card error" shadow="hover" @click="filterByStatus('ERROR')">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.error }}</div>
            <div class="stat-label">错误</div>
          </div>
          <el-icon class="stat-icon"><Warning /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <el-card class="stat-card favorite" shadow="hover" @click="filterByFavorite(true)">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.favorite }}</div>
            <div class="stat-label">收藏</div>
          </div>
          <el-icon class="stat-icon"><StarFilled /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable @change="loadRecords">
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAILED" />
            <el-option label="超时" value="TIMEOUT" />
            <el-option label="错误" value="ERROR" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行来源">
          <el-select v-model="filterForm.execution_source" placeholder="全部来源" clearable @change="loadRecords">
            <el-option label="手动执行" value="MANUAL" />
            <el-option label="定时执行" value="SCHEDULED" />
            <el-option label="批量执行" value="BATCH" />
            <el-option label="API调用" value="API" />
            <el-option label="直接HTTP" value="DIRECT_HTTP" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRecords" :icon="Search">搜索</el-button>
          <el-button @click="resetFilters" :icon="RefreshLeft">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>执行记录列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索URL或错误信息"
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
              style="width: 250px; margin-right: 10px"
            />
            <el-dropdown @command="handleBatchAction" style="margin-right: 10px">
              <el-button :disabled="selectedIds.length === 0">
                批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="delete" :icon="Delete">批量删除</el-dropdown-item>
                  <el-dropdown-item command="export" :icon="Download">批量导出</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="danger" plain @click="showBatchDeleteDialog = true" :icon="Delete">
              按条件删除
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        @selection-change="handleSelectionChange"
        @row-click="showDetailDialog"
        style="cursor: pointer"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="request_method" label="方法" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.request_method)" size="small">
              {{ row.request_method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="request_url" label="请求URL" min-width="250" show-overflow-tooltip />
        <el-table-column prop="response_status" label="状态码" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.response_status" :type="getStatusType(row.response_status)" size="small">
              {{ row.response_status }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="执行状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getExecutionStatusType(row.status)" size="small">
              {{ getExecutionStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="响应时间" width="120" align="center">
          <template #default="{ row }">
            <span :class="getDurationClass(row.duration)">
              {{ row.duration_formatted || `${row.duration}ms` }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="response_size_formatted" label="响应大小" width="100" align="center">
          <template #default="{ row }">
            {{ row.response_size_formatted || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="execution_source" label="来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ getExecutionSourceText(row.execution_source) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="执行时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="收藏" placement="top">
              <el-button
                type="primary"
                link
                @click.stop="toggleFavorite(row)"
              >
                <el-icon :color="row.is_favorite ? '#f59e0b' : '#999'">
                  <StarFilled v-if="row.is_favorite" />
                  <Star v-else />
                </el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button type="danger" link @click.stop="handleDelete(row)" :icon="Delete" />
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadRecords"
          @current-change="loadRecords"
        />
      </div>
    </el-card>

    <!-- 执行记录详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="执行记录详情"
      width="80%"
      destroy-on-close
    >
      <HttpExecutionRecordDetail
        v-if="detailDialogVisible && currentRecord"
        :record="currentRecord"
        @close="detailDialogVisible = false"
      />
    </el-dialog>

    <!-- 批量删除弹窗 -->
    <el-dialog v-model="showBatchDeleteDialog" title="按条件批量删除" width="500px">
      <el-form :model="batchDeleteForm" label-width="100px">
        <el-form-item label="删除条件">
          <el-checkbox-group v-model="batchDeleteForm.conditions">
            <el-checkbox label="status">状态</el-checkbox>
            <el-checkbox label="date">日期</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="batchDeleteForm.conditions.includes('status')" label="状态">
          <el-select v-model="batchDeleteForm.status" placeholder="选择状态">
            <el-option label="失败" value="FAILED" />
            <el-option label="错误" value="ERROR" />
            <el-option label="超时" value="TIMEOUT" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="batchDeleteForm.conditions.includes('date')" label="日期之前">
          <el-date-picker
            v-model="batchDeleteForm.date_before"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-alert
          title="警告：批量删除操作不可恢复，请谨慎操作！"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 15px"
        />
      </el-form>
      <template #footer>
        <el-button @click="showBatchDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="handleBatchDeleteByConditions">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  RefreshLeft,
  Delete,
  Download,
  ArrowDown,
  DataLine,
  CircleCheck,
  CircleClose,
  Clock,
  Warning,
  StarFilled,
  Star
} from '@element-plus/icons-vue'
import { httpExecutionRecordApi } from '../../api/httpExecutor'
import type {
  HttpExecutionRecord,
  HttpExecutionRecordStatistics,
  HttpExecutionRecordQuery,
  ExecutionStatus
} from '../../types/http'
import HttpExecutionRecordDetail from '../../components/HttpExecutor/HttpExecutionRecordDetail.vue'

// 统计数据
const statistics = ref<HttpExecutionRecordStatistics>({
  total: 0,
  success: 0,
  failed: 0,
  timeout: 0,
  error: 0,
  favorite: 0
})

// 表格数据
const tableData = ref<HttpExecutionRecord[]>([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 筛选表单
const filterForm = reactive<HttpExecutionRecordQuery>({
  status: undefined,
  execution_source: undefined,
  start_date: undefined,
  end_date: undefined
})

const dateRange = ref<[string, string] | null>(null)
const searchKeyword = ref('')
const selectedIds = ref<number[]>([])

// 详情弹窗
const detailDialogVisible = ref(false)
const currentRecord = ref<HttpExecutionRecord | null>(null)

// 批量删除弹窗
const showBatchDeleteDialog = ref(false)
const batchDeleteForm = reactive({
  conditions: [] as string[],
  status: undefined as ExecutionStatus | undefined,
  date_before: undefined as string | undefined
})

// 加载统计数据
const loadStatistics = async () => {
  try {
    statistics.value = await httpExecutionRecordApi.getStatistics()
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

// 加载执行记录列表
const loadRecords = async () => {
  loading.value = true
  try {
    const query: HttpExecutionRecordQuery = {
      page: pagination.page,
      page_size: pagination.page_size,
      status: filterForm.status,
      execution_source: filterForm.execution_source,
      start_date: filterForm.start_date,
      end_date: filterForm.end_date,
      search: searchKeyword.value || undefined,
      ordering: '-created_time'
    }

    const response = await httpExecutionRecordApi.getList(query)
    tableData.value = response.results
    pagination.total = response.count
  } catch (error) {
    ElMessage.error('加载执行记录失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 日期范围变化
const handleDateRangeChange = (value: [string, string] | null) => {
  if (value) {
    filterForm.start_date = value[0]
    filterForm.end_date = value[1]
  } else {
    filterForm.start_date = undefined
    filterForm.end_date = undefined
  }
  loadRecords()
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadRecords()
}

// 重置筛选
const resetFilters = () => {
  filterForm.status = undefined
  filterForm.execution_source = undefined
  filterForm.start_date = undefined
  filterForm.end_date = undefined
  dateRange.value = null
  searchKeyword.value = ''
  pagination.page = 1
  loadRecords()
}

// 按状态筛选
const filterByStatus = (status: ExecutionStatus | null) => {
  filterForm.status = status || undefined
  loadRecords()
}

// 按收藏筛选
const filterByFavorite = (isFavorite: boolean) => {
  // 注意：这个功能需要在后端API支持 is_favorite 参数
  ElMessage.info('收藏筛选功能开发中')
}

// 表格选择变化
const handleSelectionChange = (selection: HttpExecutionRecord[]) => {
  selectedIds.value = selection.map(item => item.id)
}

// 显示详情弹窗
const showDetailDialog = (row: HttpExecutionRecord) => {
  currentRecord.value = row
  detailDialogVisible.value = true
}

// 切换收藏状态
const toggleFavorite = async (row: HttpExecutionRecord) => {
  try {
    const result = await httpExecutionRecordApi.toggleFavorite(row.id)
    row.is_favorite = result.is_favorite
    ElMessage.success(result.message)
    loadStatistics()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除单条记录
const handleDelete = async (row: HttpExecutionRecord) => {
  try {
    await ElMessageBox.confirm('确定要删除这条执行记录吗？', '确认删除', {
      type: 'warning'
    })
    await httpExecutionRecordApi.delete(row.id)
    ElMessage.success('删除成功')
    loadRecords()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量操作
const handleBatchAction = async (command: string) => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要操作的记录')
    return
  }

  if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedIds.value.length} 条记录吗？`,
        '确认删除',
        { type: 'warning' }
      )
      await httpExecutionRecordApi.batchDelete({ ids: selectedIds.value })
      ElMessage.success('删除成功')
      loadRecords()
      loadStatistics()
      selectedIds.value = []
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('删除失败')
      }
    }
  } else if (command === 'export') {
    ElMessage.info('批量导出功能开发中')
  }
}

// 按条件批量删除
const handleBatchDeleteByConditions = async () => {
  try {
    const filters: any = {}
    if (batchDeleteForm.conditions.includes('status') && batchDeleteForm.status) {
      filters.status = batchDeleteForm.status
    }
    if (batchDeleteForm.conditions.includes('date') && batchDeleteForm.date_before) {
      filters.date_before = batchDeleteForm.date_before
    }

    if (Object.keys(filters).length === 0) {
      ElMessage.warning('请至少选择一个删除条件')
      return
    }

    await ElMessageBox.confirm(
      '确定要删除符合条件的所有记录吗？此操作不可恢复！',
      '确认删除',
      { type: 'warning' }
    )

    await httpExecutionRecordApi.batchDelete({ filters })
    ElMessage.success('删除成功')
    showBatchDeleteDialog.value = false
    loadRecords()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 辅助函数
const getMethodTagType = (method: string) => {
  const types: Record<string, any> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info'
  }
  return types[method] || ''
}

const getStatusType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400 && status < 500) return 'danger'
  if (status >= 500) return 'danger'
  return 'info'
}

const getExecutionStatusType = (status: ExecutionStatus) => {
  const types: Record<string, any> = {
    SUCCESS: 'success',
    FAILED: 'danger',
    TIMEOUT: 'warning',
    ERROR: 'danger',
    PENDING: 'info'
  }
  return types[status] || ''
}

const getExecutionStatusText = (status: ExecutionStatus) => {
  const texts: Record<string, string> = {
    SUCCESS: '成功',
    FAILED: '失败',
    TIMEOUT: '超时',
    ERROR: '错误',
    PENDING: '进行中'
  }
  return texts[status] || status
}

const getExecutionSourceText = (source: string) => {
  const texts: Record<string, string> = {
    MANUAL: '手动',
    SCHEDULED: '定时',
    BATCH: '批量',
    API: 'API',
    DIRECT_HTTP: '直接'
  }
  return texts[source] || source
}

const getDurationClass = (duration: number) => {
  if (duration < 200) return 'text-success'
  if (duration < 500) return 'text-warning'
  return 'text-danger'
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadStatistics()
  loadRecords()
})
</script>

<style scoped>
.http-execution-records {
  padding: 20px;
}

.statistics-cards {
  margin: 20px 0;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card.success {
  border-left: 4px solid #67c23a;
}

.stat-card.failed {
  border-left: 4px solid #f56c6c;
}

.stat-card.timeout {
  border-left: 4px solid #e6a23c;
}

.stat-card.error {
  border-left: 4px solid #f56c6c;
}

.stat-card.favorite {
  border-left: 4px solid #f59e0b;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 36px;
  opacity: 0.2;
}

.stat-card.total .stat-icon {
  color: #409eff;
}

.stat-card.success .stat-icon {
  color: #67c23a;
}

.stat-card.failed .stat-icon {
  color: #f56c6c;
}

.stat-card.timeout .stat-icon {
  color: #e6a23c;
}

.stat-card.error .stat-icon {
  color: #f56c6c;
}

.stat-card.favorite .stat-icon {
  color: #f59e0b;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}
</style>
