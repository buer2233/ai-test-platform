<template>
  <div class="recycle-bin-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon class="title-icon"><Delete /></el-icon>
          回收站
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>回收站</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="16">
        <el-col :span="6" v-for="(stat, key) in stats.stats" :key="key">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon" :class="`stat-icon-${getIconClass(key)}`">
                <component :is="getIconComponent(key)" :size="24" />
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stat.count }}</div>
                <div class="stat-label">{{ stat.display_name }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 操作栏 -->
    <el-card class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="filterType" placeholder="全部类型" clearable @change="handleFilterChange">
            <el-option label="全部类型" value="" />
            <el-option
              v-for="(stat, key) in stats.stats"
              :key="key"
              :label="stat.display_name"
              :value="key"
            />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索已删除的数据"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="8" class="action-col">
          <el-button
            type="success"
            :disabled="!hasSelection"
            @click="handleBatchRestore"
          >
            <el-icon><RefreshLeft /></el-icon>
            批量恢复
          </el-button>
          <el-button
            type="danger"
            :disabled="!hasSelection"
            @click="handleBatchPermanentDelete"
          >
            <el-icon><Delete /></el-icon>
            批量彻底删除
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="display_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ row.display_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="updated_time" label="删除时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              link
              @click="handleRestore(row)"
            >
              <el-icon><RefreshLeft /></el-icon>
              恢复
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handlePermanentDelete(row)"
            >
              <el-icon><Delete /></el-icon>
              彻底删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 彻底删除确认对话框 -->
    <el-dialog
      v-model="permanentDeleteDialog"
      title="彻底删除确认"
      width="450px"
    >
      <div class="permanent-delete-content">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <p class="warning-message">
          此操作将<strong>彻底删除</strong>选中的数据，删除后<strong>无法恢复</strong>。
        </p>
        <p class="confirm-text">确认要继续吗？</p>
      </div>
      <template #footer>
        <el-button @click="permanentDeleteDialog = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmPermanentDelete">
          确认彻底删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete, Search, RefreshLeft, WarningFilled,
  Folder, Document, Tickets, Setting
} from '@element-plus/icons-vue'
import { recycleBinApi } from '../../api/recycleBin'
import type { RecycleBinItem, RecycleBinStats } from '../../api/recycleBin'

const tableRef = ref()
const loading = ref(false)
const deleting = ref(false)
const tableData = ref<RecycleBinItem[]>([])
const selectedRows = ref<RecycleBinItem[]>([])
const permanentDeleteDialog = ref(false)
const pendingDeleteItems = ref<RecycleBinItem[]>([])

const stats = reactive<RecycleBinStats>({
  stats: {},
  total_count: 0
})

const filterType = ref('')
const searchKeyword = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const hasSelection = computed(() => selectedRows.value.length > 0)

onMounted(() => {
  loadStats()
  loadData()
})

const loadStats = async () => {
  try {
    const response = await recycleBinApi.getStats()
    Object.assign(stats, response)
  } catch (error) {
    console.error('加载回收站统计失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await recycleBinApi.getDeletedItems({
      type: filterType.value || undefined,
      search: searchKeyword.value || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })

    tableData.value = response.results
    pagination.total = response.count
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadData()
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadData()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadData()
}

const handleSelectionChange = (selection: RecycleBinItem[]) => {
  selectedRows.value = selection
}

const handleRestore = async (item: RecycleBinItem) => {
  try {
    await recycleBinApi.restoreItem(item.type, item.id)
    ElMessage.success('恢复成功')
    loadData()
    loadStats()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.error || '恢复失败')
  }
}

const handleBatchRestore = async () => {
  if (selectedRows.value.length === 0) return

  // 检查是否是同一类型
  const types = [...new Set(selectedRows.value.map(item => item.type))]
  if (types.length > 1) {
    ElMessage.warning('批量恢复只支持相同类型的数据')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认恢复选中的 ${selectedRows.value.length} 项数据吗？`,
      '批量恢复确认',
      { type: 'warning' }
    )

    const type = types[0]
    const ids = selectedRows.value.map(item => item.id)
    await recycleBinApi.batchRestore(type, ids)

    ElMessage.success(`成功恢复 ${selectedRows.value.length} 项数据`)
    tableRef.value?.clearSelection()
    loadData()
    loadStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.error || '批量恢复失败')
    }
  }
}

const handlePermanentDelete = (item: RecycleBinItem) => {
  pendingDeleteItems.value = [item]
  permanentDeleteDialog.value = true
}

const handleBatchPermanentDelete = () => {
  if (selectedRows.value.length === 0) return
  pendingDeleteItems.value = [...selectedRows.value]
  permanentDeleteDialog.value = true
}

const confirmPermanentDelete = async () => {
  deleting.value = true
  try {
    const items = pendingDeleteItems.value
    const types = [...new Set(items.map(item => item.type))]

    if (types.length > 1) {
      ElMessage.warning('批量删除只支持相同类型的数据')
      return
    }

    const type = types[0]
    const ids = items.map(item => item.id)

    if (ids.length === 1) {
      await recycleBinApi.permanentDeleteItem(type, ids[0])
    } else {
      await recycleBinApi.batchPermanentDelete(type, ids)
    }

    ElMessage.success(`成功删除 ${items.length} 项数据`)
    permanentDeleteDialog.value = false
    tableRef.value?.clearSelection()
    loadData()
    loadStats()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.error || '删除失败')
  } finally {
    deleting.value = false
  }
}

const getTypeTagType = (type: string) => {
  const typeMap: Record<string, any> = {
    'apiproject': 'danger',
    'apicollection': 'primary',
    'apitestcase': 'success',
    'apitestenvironment': 'warning',
    'apidatadriver': 'info'
  }
  return typeMap[type] || 'default'
}

const getIconComponent = (type: string) => {
  const iconMap: Record<string, any> = {
    'apiproject': Folder,
    'apicollection': Tickets,
    'apitestcase': Document,
    'apitestenvironment': Setting,
    'apidatadriver': Document
  }
  return iconMap[type] || Document
}

const getIconClass = (type: string) => {
  const classMap: Record<string, string> = {
    'apiproject': 'primary',
    'apicollection': 'success',
    'apitestcase': 'warning',
    'apitestenvironment': 'danger',
    'apidatadriver': 'info'
  }
  return classMap[type] || 'default'
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped lang="scss">
.recycle-bin-page {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-size: 20px;
      font-weight: 500;
      color: #303133;

      .title-icon {
        font-size: 24px;
        color: #409EFF;
      }
    }
  }

  .stats-section {
    margin-bottom: 20px;

    .stat-card {
      cursor: pointer;
      transition: transform 0.2s;

      &:hover {
        transform: translateY(-2px);
      }

      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 56px;
          height: 56px;
          border-radius: 8px;

          &.stat-icon-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
          }

          &.stat-icon-success {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #333;
          }

          &.stat-icon-warning {
            background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);
            color: white;
          }

          &.stat-icon-danger {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            color: #333;
          }

          &.stat-icon-info {
            background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
            color: #333;
          }
        }

        .stat-info {
          .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
          }

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }
    }
  }

  .filter-card {
    margin-bottom: 20px;

    .action-col {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
  }

  .table-card {
    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 20px;
    }
  }
}

.permanent-delete-content {
  text-align: center;
  padding: 20px 0;

  .warning-icon {
    font-size: 48px;
    color: #F56C6C;
    margin-bottom: 16px;
  }

  .warning-message {
    font-size: 16px;
    color: #303133;
    margin-bottom: 8px;
  }

  .confirm-text {
    font-size: 14px;
    color: #909399;
  }
}
</style>
