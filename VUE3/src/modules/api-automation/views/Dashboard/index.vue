<template>
  <div class="dashboard-container">
    <!-- API自动化测试平台内容 -->
    <div class="platform-content">
      <div class="page-header">
        <h1 class="page-title">测试报告仪表盘</h1>
        <p class="page-description">接口自动化测试报告概览</p>
      </div>

      <!-- 顶部筛选栏 -->
      <el-card class="filter-card mb-20">
        <el-form :inline="true" :model="filters">
          <el-form-item label="项目">
            <el-select v-model="filters.project_id" placeholder="全部项目" clearable style="width: 180px" @change="handleFilterChange">
              <el-option v-for="project in allProjects" :key="project.id" :label="project.name" :value="project.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="集合">
            <el-select v-model="filters.collection_id" placeholder="全部集合" clearable style="width: 180px" @change="handleFilterChange">
              <el-option v-for="collection in allCollections" :key="collection.id" :label="collection.name" :value="collection.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人">
            <el-select v-model="filters.owner_id" placeholder="全部负责人" clearable style="width: 180px" @change="handleFilterChange">
              <el-option v-for="owner in allOwners" :key="owner.id" :label="owner.username" :value="owner.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="模块">
            <el-select v-model="filters.module" placeholder="全部模块" clearable style="width: 180px" @change="handleFilterChange">
              <el-option v-for="module in allModules" :key="module" :label="module" :value="module" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 280px"
              @change="handleFilterChange"
            />
          </el-form-item>
          <el-form-item>
            <el-button @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 统计概览卡片 -->
      <el-row :gutter="20" class="mb-20">
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover" @click="showDetailDialog('all')">
            <div class="stat-content">
              <div class="stat-icon total-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ testStats.total_cases }}</div>
                <div class="stat-label">总用例数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card success" shadow="hover" @click="showDetailDialog('passed')">
            <div class="stat-content">
              <div class="stat-icon passed-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ testStats.passed_cases }}</div>
                <div class="stat-label">通过用例</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card danger" shadow="hover" @click="showDetailDialog('failed')">
            <div class="stat-content">
              <div class="stat-icon failed-icon">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ testStats.failed_cases }}</div>
                <div class="stat-label">失败用例</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover" @click="showDetailDialog('all')">
            <div class="stat-content">
              <div class="stat-icon rate-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ testStats.pass_rate }}%</div>
                <div class="stat-label">通过率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="mb-20">
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="chart-title">用例执行统计（柱状图）</span>
                <el-button text link @click="refreshChartData">刷新</el-button>
              </div>
            </template>
            <div ref="barChartRef" class="chart-container" style="height: 300px"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="chart-title">用例执行分布（饼图）</span>
                <el-button text link @click="refreshChartData">刷新</el-button>
              </div>
            </template>
            <div ref="pieChartRef" class="chart-container" style="height: 300px"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 测试结果列表 -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>测试结果列表</span>
            <div class="header-actions">
              <el-radio-group v-model="statusFilter" size="small" @change="handleStatusFilterChange">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button value="PASSED">通过</el-radio-button>
                <el-radio-button value="FAILED">失败</el-radio-button>
                <el-radio-button value="SKIPPED">跳过</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        <el-table :data="testResults" v-loading="loadingResults" stripe>
          <el-table-column prop="test_case_name" label="用例名称" min-width="200" />
          <el-table-column prop="collection_name" label="集合" width="150" />
          <el-table-column prop="project_name" label="项目" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_time" label="响应时间" width="100" align="right">
            <template #default="{ row }">
              {{ row.response_time }}ms
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="执行时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button text link type="primary" @click="viewDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadTestResults"
            @current-change="loadTestResults"
          />
        </div>
      </el-card>

      <!-- 数据详情弹窗 -->
      <DataDetailDialog
        v-model="detailDialogVisible"
        :data-type="detailDataType"
        :filters="currentFilters"
        @remove-filter="handleRemoveFilter"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  Document, CircleCheck, CircleClose, TrendCharts
} from '@element-plus/icons-vue'
import { dashboardApi } from '../../api/dashboard'
import { environmentApi } from '../../api/environment'
import { projectApi } from '../../api/project'
import { collectionApi } from '../../api/collection'
import { userApi } from '../../api/user'
import type { DashboardFilterParams } from '../../api/dashboard'
import DataDetailDialog from './components/DataDetailDialog.vue'

const router = useRouter()

// 数据状态
const loading = ref(false)
const loadingResults = ref(false)
const statusFilter = ref('')

// 详情弹窗
const detailDialogVisible = ref(false)
const detailDataType = ref<'all' | 'passed' | 'failed' | 'skipped' | 'error'>('all')
const currentFilters = ref<DashboardFilterParams>({})

// 筛选条件
const filters = reactive<DashboardFilterParams & { dateRange?: [string, string] }>({
  project_id: undefined,
  collection_id: undefined,
  owner_id: undefined,
  module: undefined,
  dateRange: undefined
})

// 选项数据
const allProjects = ref<any[]>([])
const allCollections = ref<any[]>([])
const allOwners = ref<any[]>([])
const allModules = ref<string[]>([])

// 统计数据
const testStats = ref({
  total_cases: 0,
  passed_cases: 0,
  failed_cases: 0,
  skipped_cases: 0,
  error_cases: 0,
  pass_rate: 0,
  avg_response_time: 0
})

// 测试结果
const testResults = ref<any[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 图表相关
const barChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let barChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'ERROR': 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'PASSED': '通过',
    'FAILED': '失败',
    'SKIPPED': '跳过',
    'ERROR': '错误'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (time: string | null) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 初始化图表
const initCharts = () => {
  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value)
  }
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
  }

  // 监听窗口大小变化
  window.addEventListener('resize', handleChartResize)
}

const handleChartResize = () => {
  barChart?.resize()
  pieChart?.resize()
}

// 更新图表数据
const updateCharts = () => {
  const chartData = [
    { name: '通过', value: testStats.value.passed_cases, itemStyle: { color: '#67c23a' } },
    { name: '失败', value: testStats.value.failed_cases, itemStyle: { color: '#f56c6c' } },
    { name: '跳过', value: testStats.value.skipped_cases, itemStyle: { color: '#909399' } },
    { name: '错误', value: testStats.value.error_cases, itemStyle: { color: '#e6a23c' } }
  ]

  // 更新柱状图
  if (barChart) {
    const barOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.name)
      },
      yAxis: {
        type: 'value',
        name: '用例数'
      },
      series: [{
        data: chartData.map(d => ({
          value: d.value,
          itemStyle: { color: d.itemStyle.color }
        })),
        type: 'bar',
        barWidth: '50%',
        label: {
          show: true,
          position: 'top'
        }
      }]
    }
    barChart.setOption(barOption)

    // 柱状图点击事件
    barChart.off('click')
    barChart.on('click', (params: any) => {
      const typeMap: Record<string, 'all' | 'passed' | 'failed' | 'skipped' | 'error'> = {
        '通过': 'passed',
        '失败': 'failed',
        '跳过': 'skipped',
        '错误': 'error'
      }
      showDetailDialog(typeMap[params.name] || 'all')
    })
  }

  // 更新饼图
  if (pieChart) {
    const pieOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}\n({d}%)'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: chartData
      }]
    }
    pieChart.setOption(pieOption)

    // 饼图点击事件
    pieChart.off('click')
    pieChart.on('click', (params: any) => {
      const typeMap: Record<string, 'all' | 'passed' | 'failed' | 'skipped' | 'error'> = {
        '通过': 'passed',
        '失败': 'failed',
        '跳过': 'skipped',
        '错误': 'error'
      }
      showDetailDialog(typeMap[params.name] || 'all')
    })
  }
}

// 刷新图表数据
const refreshChartData = async () => {
  await loadDashboardData()
}

// 显示详情弹窗
const showDetailDialog = (type: 'all' | 'passed' | 'failed' | 'skipped' | 'error') => {
  detailDataType.value = type
  currentFilters.value = { ...buildFilterParams() }
  detailDialogVisible.value = true
}

// 构建筛选参数
const buildFilterParams = (): DashboardFilterParams => {
  const params: DashboardFilterParams = {}
  if (filters.project_id) params.project_id = filters.project_id
  if (filters.collection_id) params.collection_id = filters.collection_id
  if (filters.owner_id) params.owner_id = filters.owner_id
  if (filters.module) params.module = filters.module
  if (filters.dateRange && filters.dateRange.length === 2) {
    params.start_date = filters.dateRange[0]
    params.end_date = filters.dateRange[1]
  }
  return params
}

// 筛选条件变更
const handleFilterChange = () => {
  pagination.page = 1
  loadDashboardData()
  loadTestResults()
}

// 状态筛选变更
const handleStatusFilterChange = () => {
  pagination.page = 1
  loadTestResults()
}

// 移除筛选条件
const handleRemoveFilter = (key: string) => {
  const keyMap: Record<string, keyof typeof filters> = {
    '项目': 'project_id',
    '集合': 'collection_id',
    '负责人': 'owner_id',
    '模块': 'module',
    '开始日期': 'dateRange',
    '结束日期': 'dateRange'
  }

  const filterKey = keyMap[key]
  if (filterKey) {
    filters[filterKey] = undefined
    handleFilterChange()
  }
}

// 重置筛选条件
const resetFilters = () => {
  filters.project_id = undefined
  filters.collection_id = undefined
  filters.owner_id = undefined
  filters.module = undefined
  filters.dateRange = undefined
  statusFilter.value = ''
  handleFilterChange()
}

// 加载仪表盘数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    const params = buildFilterParams()
    const overview = await dashboardApi.getOverview(params)
    testStats.value = overview.test_stats

    // 更新图表
    await nextTick()
    updateCharts()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

// 加载选项数据
const loadOptionsData = async () => {
  try {
    const [projectsRes, collectionsRes, ownersRes] = await Promise.all([
      projectApi.getProjects(),
      collectionApi.getCollections(),
      userApi.getUsers()
    ])

    allProjects.value = projectsRes.results || projectsRes
    allCollections.value = collectionsRes.results || collectionsRes
    allOwners.value = ownersRes.results || ownersRes

    // 收集所有模块
    const moduleSet = new Set<string>()
    allCollections.value.forEach((c: any) => {
      if (c.module) moduleSet.add(c.module)
    })
    allModules.value = Array.from(moduleSet).sort()
  } catch (error) {
    console.error('Failed to load options data:', error)
  }
}

// 加载测试结果
const loadTestResults = async () => {
  loadingResults.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size,
      sort_by: '-start_time',
      ...buildFilterParams()
    }

    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    const response = await dashboardApi.getTestResults(params)
    testResults.value = response.results
    pagination.total = response.count
  } catch (error) {
    console.error('Failed to load test results:', error)
  } finally {
    loadingResults.value = false
  }
}

// 跳转到测试结果详情
const viewDetail = (row: any) => {
  // TODO: 跳转到测试结果详情页
  ElMessage.info('测试结果详情页开发中...')
}

// 启动自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadDashboardData()
    loadTestResults()
  }, 30000)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载
onMounted(async () => {
  initCharts()
  await loadOptionsData()
  await loadDashboardData()
  await loadTestResults()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleChartResize)
  barChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.platform-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.mb-20 {
  margin-bottom: 20px;
}

.filter-card {
  border-left: 4px solid #409eff;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card.success {
  border-left: 4px solid #67c23a;
}

.stat-card.danger {
  border-left: 4px solid #f56c6c;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #fff;
}

.total-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.passed-icon {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.failed-icon {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
}

.rate-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.chart-card {
  height: 100%;
}

.chart-container {
  width: 100%;
}

.chart-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
