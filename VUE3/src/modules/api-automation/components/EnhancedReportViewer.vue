<!--
  EnhancedReportViewer.vue - 增强版测试报告查看器

  功能丰富的测试报告分析组件，提供三种视图模式：
  1. 总览模式（Overview）：
     - 统计概览卡片（总执行数、通过数、失败数、通过率）
     - 通过率仪表盘、结果分布环形图、响应时间分布柱状图
     - 通过率趋势折线图、HTTP 状态码饼图
     - 失败用例 Top10、执行时间热力图
  2. 图表模式（Charts）：
     - 按集合/模块统计、多维度雷达评估图
     - 响应时间箱线图、断言失败类型饼图
  3. 详情模式（Details）：
     - 可搜索和筛选的测试结果数据表格
     - 可展开查看请求详情、响应体、断言结果

  附加功能：
  - 过滤器面板（报告类型、项目、环境、时间范围）
  - 自动刷新（每 30 秒）
  - 多格式导出（PDF、Excel、JSON、图片）
  - 全屏模式
  - 基于 ECharts 的所有图表均支持自适应窗口大小
-->
<template>
  <div class="enhanced-report-viewer" v-loading="loading">
    <!-- 头部工具栏 -->
    <div class="report-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><DataAnalysis /></el-icon>
          测试报告分析
        </h2>
        <el-tag v-if="selectedReport" type="info" size="large">
          {{ selectedReport.name }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button
            :type="viewMode === 'overview' ? 'primary' : ''"
            @click="viewMode = 'overview'"
          >
            <el-icon><Grid /></el-icon>
            总览
          </el-button>
          <el-button
            :type="viewMode === 'charts' ? 'primary' : ''"
            @click="viewMode = 'charts'"
          >
            <el-icon><PieChart /></el-icon>
            图表
          </el-button>
          <el-button
            :type="viewMode === 'details' ? 'primary' : ''"
            @click="viewMode = 'details'"
          >
            <el-icon><List /></el-icon>
            详情
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="toggleAutoRefresh" :type="autoRefresh ? 'success' : ''">
          <el-icon v-if="!autoRefresh"><VideoPlay /></el-icon>
          <el-icon v-else><VideoPause /></el-icon>
          {{ autoRefresh ? '停止' : '自动' }}
        </el-button>
        <el-dropdown @command="handleExport" trigger="click">
          <el-button>
            导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="export-image">
                <el-icon><Picture /></el-icon>
                导出图片
              </el-dropdown-item>
              <el-dropdown-item command="export-pdf">
                <el-icon><Document /></el-icon>
                导出PDF
              </el-dropdown-item>
              <el-dropdown-item command="export-excel">
                <el-icon><Tickets /></el-icon>
                导出Excel
              </el-dropdown-item>
              <el-dropdown-item command="export-data">
                <el-icon><Download /></el-icon>
                导出数据(JSON)
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
          全屏
        </el-button>
      </div>
    </div>

    <!-- 过滤器面板 -->
    <div class="filter-panel">
      <el-card shadow="never">
        <el-form :inline="true" :model="filters" size="small">
          <el-form-item label="报告类型">
            <el-select v-model="filters.reportType" placeholder="全部" clearable style="width: 120px">
              <el-option label="执行报告" value="execution" />
              <el-option label="环境报告" value="environment" />
              <el-option label="集合报告" value="collection" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目">
            <el-select v-model="filters.projectId" placeholder="全部项目" clearable style="width: 150px">
              <el-option
                v-for="project in projectOptions"
                :key="project.value"
                :label="project.label"
                :value="project.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="环境">
            <el-select v-model="filters.environmentId" placeholder="全部环境" clearable style="width: 120px">
              <el-option
                v-for="env in environmentOptions"
                :key="env.value"
                :label="env.label"
                :value="env.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filters.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 320px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyFilters">
              <el-icon><Search /></el-icon>
              筛选
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 统计概览卡片 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :span="6" v-for="stat in statistics" :key="stat.key">
          <el-card class="stat-card" :class="`stat-${stat.type}`">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="32">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
                <div v-if="stat.trend" class="stat-trend" :class="stat.trendClass">
                  <el-icon><component :is="stat.trendIcon" /></el-icon>
                  {{ stat.trendText }}
                </div>
              </div>
            </div>
            <!-- 迷你趋势图 -->
            <div class="mini-chart" :ref="el => stat.chartRef = el"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 总览模式 -->
    <div v-show="viewMode === 'overview'" class="overview-mode">
      <el-row :gutter="16">
        <!-- 通过率仪表盘 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Odometer /></el-icon> 整体通过率</span>
                <el-tag :type="getPassRateType(overallStats.passRate)" size="small">
                  {{ overallStats.passRate }}%
                </el-tag>
              </div>
            </template>
            <div ref="gaugeChartRef" class="chart-container" style="height: 280px"></div>
          </el-card>
        </el-col>

        <!-- 测试结果分布环形图 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><PieChart /></el-icon> 结果分布</span>
                <el-button-group size="small">
                  <el-button
                    :type="resultChartType === 'doughnut' ? 'primary' : ''"
                    @click="resultChartType = 'doughnut'"
                  >环形</el-button>
                  <el-button
                    :type="resultChartType === 'pie' ? 'primary' : ''"
                    @click="resultChartType = 'pie'"
                  >饼图</el-button>
                </el-button-group>
              </div>
            </template>
            <div ref="resultPieChartRef" class="chart-container" style="height: 280px"></div>
          </el-card>
        </el-col>

        <!-- 响应时间分布 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Timer /></el-icon> 响应时间分布</span>
              </div>
            </template>
            <div ref="responseTimeDistRef" class="chart-container" style="height: 280px"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 通过率趋势图 -->
        <el-col :span="16">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><TrendCharts /></el-icon> 通过率趋势</span>
                <el-select v-model="trendPeriod" size="small" style="width: 100px">
                  <el-option label="最近7天" value="7d" />
                  <el-option label="最近30天" value="30d" />
                  <el-option label="最近90天" value="90d" />
                </el-select>
              </div>
            </template>
            <div ref="trendLineChartRef" class="chart-container" style="height: 320px"></div>
          </el-card>
        </el-col>

        <!-- 状态码分布 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Coin /></el-icon> HTTP状态码</span>
              </div>
            </template>
            <div ref="statusCodeChartRef" class="chart-container" style="height: 320px"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 失败用例分析 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Warning /></el-icon> 失败用例Top10</span>
                <el-button size="small" text @click="drillDownFailed">
                  查看全部<el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>
            <div ref="failedCasesChartRef" class="chart-container" style="height: 300px"></div>
          </el-card>
        </el-col>

        <!-- 执行时间热力图 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Calendar /></el-icon> 执行时间热力图</span>
              </div>
            </template>
            <div ref="heatmapChartRef" class="chart-container" style="height: 300px"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表模式 -->
    <div v-show="viewMode === 'charts'" class="charts-mode">
      <el-row :gutter="16">
        <!-- 按模块统计 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Grid /></el-icon> 按集合/模块统计</span>
              </div>
            </template>
            <div ref="moduleStatsChartRef" class="chart-container" style="height: 350px"></div>
          </el-card>
        </el-col>

        <!-- 多维度雷达图 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Aim /></el-icon> 多维度评估</span>
              </div>
            </template>
            <div ref="radarChartRef" class="chart-container" style="height: 350px"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 响应时间箱线图 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Histogram /></el-icon> 响应时间分布(箱线图)</span>
              </div>
            </template>
            <div ref="boxPlotChartRef" class="chart-container" style="height: 320px"></div>
          </el-card>
        </el-col>

        <!-- 断言失败类型分析 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Document /></el-icon> 断言失败类型</span>
              </div>
            </template>
            <div ref="assertionFailChartRef" class="chart-container" style="height: 320px"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详情模式 -->
    <div v-show="viewMode === 'details'" class="details-mode">
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span><el-icon><List /></el-icon> 详细数据列表</span>
            <div class="header-actions-right">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索用例名称或URL"
                size="small"
                style="width: 250px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="detailStatusFilter" size="small" style="width: 120px">
                <el-option label="全部状态" value="" />
                <el-option label="通过" value="PASSED" />
                <el-option label="失败" value="FAILED" />
                <el-option label="跳过" value="SKIPPED" />
                <el-option label="错误" value="ERROR" />
              </el-select>
            </div>
          </div>
        </template>

        <el-table
          :data="filteredTestResults"
          stripe
          size="small"
          :default-sort="{ prop: 'start_time', order: 'descending' }"
          class="details-table"
        >
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="expand-content">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="请求URL">{{ row.test_case_url }}</el-descriptions-item>
                  <el-descriptions-item label="请求方法">{{ row.test_case_method }}</el-descriptions-item>
                  <el-descriptions-item label="状态码">{{ row.response_status }}</el-descriptions-item>
                  <el-descriptions-item label="响应时间">{{ row.response_time }}ms</el-descriptions-item>
                  <el-descriptions-item label="响应大小" :span="2">{{ formatFileSize(row.response_size) }}</el-descriptions-item>
                  <el-descriptions-item label="请求头" :span="2">
                    <pre class="code-preview">{{ JSON.stringify(row.request_headers, null, 2) }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item label="响应体" :span="2">
                    <pre class="code-preview">{{ formatJson(row.response_body) }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item v-if="row.error_message" label="错误信息" :span="2">
                    <el-alert type="error" :closable="false">{{ row.error_message }}</el-alert>
                  </el-descriptions-item>
                  <el-descriptions-item v-if="row.assertion_results" label="断言结果" :span="2">
                    <div class="assertion-results">
                      <div
                        v-for="(assertion, idx) in row.assertion_results"
                        :key="idx"
                        class="assertion-item"
                        :class="{ passed: assertion.passed, failed: !assertion.passed }"
                      >
                        <el-icon><component :is="assertion.passed ? 'CircleCheck' : 'CircleClose'" /></el-icon>
                        {{ assertion.assertion_type }} - {{ assertion.expected_value }}
                      </div>
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="test_case_name" label="用例名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="test_case_method" label="方法" width="80">
            <template #default="{ row }">
              <el-tag :type="getMethodType(row.test_case_method)" size="small">
                {{ row.test_case_method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" sortable>
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_status" label="状态码" width="90" sortable />
          <el-table-column label="响应时间" width="120" sortable>
            <template #default="{ row }">
              <span :class="getResponseTimeClass(row.response_time)">
                {{ row.response_time }}ms
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="执行时间" width="160" sortable>
            <template #default="{ row }">
              {{ formatDateTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时" width="90" sortable />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-dropdown @command="handleRowAction">
                <el-button size="small">
                  操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'retry', row }">
                      <el-icon><Refresh /></el-icon>
                      重试
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'copy', row }">
                      <el-icon><DocumentCopy /></el-icon>
                      复制用例
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'export', row }">
                      <el-icon><Download /></el-icon>
                      导出结果
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-footer">
          <el-pagination
            v-model:current-page="detailsPage"
            v-model:page-size="detailsPageSize"
            :total="filteredTestResults.length"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            small
          />
        </div>
      </el-card>
    </div>

    <!-- 图片导出对话框 -->
    <el-dialog
      v-model="exportImageVisible"
      title="导出为图片"
      width="400px"
    >
      <el-form label-position="top">
        <el-form-item label="图片格式">
          <el-radio-group v-model="exportImageFormat">
            <el-radio value="png">PNG</el-radio>
            <el-radio value="jpeg">JPEG</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="图片质量">
          <el-slider v-model="exportImageQuality" :min="0.1" :max="1" :step="0.1" />
        </el-form-item>
        <el-form-item label="背景色">
          <el-radio-group v-model="exportImageBg">
            <el-radio value="white">白色</el-radio>
            <el-radio value="transparent">透明</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportImageVisible = false">取消</el-button>
        <el-button type="primary" @click="exportChartsImage">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Grid, PieChart, List, Refresh, VideoPlay, VideoPause,
  ArrowDown, Download, Picture, Document, Tickets, Search,
  RefreshLeft, Odometer, Timer, TrendCharts, Coin, Warning,
  Calendar, Aim, Histogram, FullScreen, ArrowRight, CircleCheck,
  CircleClose, DocumentCopy, Upload
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useReportStore } from '../stores/report'
import { useProjectStore } from '../stores/project'
import { useEnvironmentStore } from '../stores/environment'
import { ReportExporter, generateExportFilename, type ExportFormat } from '../utils/reportExporter'

// Props
interface Props {
  reportId?: number
}

const props = defineProps<Props>()

// Stores
const reportStore = useReportStore()
const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()

// Refs
const loading = ref(false)
const viewMode = ref<'overview' | 'charts' | 'details'>('overview')
const autoRefresh = ref(false)
const selectedReport = ref<any>(null)
const resultChartType = ref<'doughnut' | 'pie'>('doughnut')
const trendPeriod = ref('7d')

// Filters
const filters = reactive({
  reportType: '',
  projectId: null as number | null,
  environmentId: null as number | null,
  dateRange: null as [string, string] | null
})

// Detail filters
const searchKeyword = ref('')
const detailStatusFilter = ref('')
const detailsPage = ref(1)
const detailsPageSize = ref(20)

// Export settings
const exportImageVisible = ref(false)
const exportImageFormat = ref('png')
const exportImageQuality = ref(1.0)
const exportImageBg = ref('white')

// Chart refs
const gaugeChartRef = ref()
const resultPieChartRef = ref()
const responseTimeDistRef = ref()
const trendLineChartRef = ref()
const statusCodeChartRef = ref()
const failedCasesChartRef = ref()
const heatmapChartRef = ref()
const moduleStatsChartRef = ref()
const radarChartRef = ref()
const boxPlotChartRef = ref()
const assertionFailChartRef = ref()

// Chart instances
const chartInstances = ref<Map<string, echarts.ECharts>>(new Map())

// Data
const reportData = ref<any>(null)
const testResults = ref<any[]>([])

// Options
const projectOptions = computed(() => projectStore.projectOptions)
const environmentOptions = computed(() =>
  environmentStore.environments.map(e => ({ label: e.name, value: e.id }))
)

// Statistics
const statistics = ref([
  {
    key: 'total',
    label: '总执行数',
    value: 0,
    icon: 'DataAnalysis',
    type: 'primary',
    trend: '+12%',
    trendClass: 'up',
    trendIcon: 'ArrowUp',
    trendText: '较上周',
    chartRef: ref()
  },
  {
    key: 'passed',
    label: '通过数',
    value: 0,
    icon: 'CircleCheck',
    type: 'success',
    trend: '+8%',
    trendClass: 'up',
    trendIcon: 'ArrowUp',
    trendText: '较上周',
    chartRef: ref()
  },
  {
    key: 'failed',
    label: '失败数',
    value: 0,
    icon: 'CircleClose',
    type: 'danger',
    trend: '-3%',
    trendClass: 'down',
    trendIcon: 'ArrowDown',
    trendText: '较上周',
    chartRef: ref()
  },
  {
    key: 'passRate',
    label: '通过率',
    value: '0%',
    icon: 'TrendCharts',
    type: 'warning',
    trend: '+2%',
    trendClass: 'up',
    trendIcon: 'ArrowUp',
    trendText: '较上周',
    chartRef: ref()
  }
])

const overallStats = ref({
  total: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  passRate: 0
})

// Computed
const filteredTestResults = computed(() => {
  let results = testResults.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    results = results.filter(r =>
      r.test_case_name?.toLowerCase().includes(keyword) ||
      r.test_case_url?.toLowerCase().includes(keyword)
    )
  }

  if (detailStatusFilter.value) {
    results = results.filter(r => r.status === detailStatusFilter.value)
  }

  return results
})

// Methods
const refreshData = async () => {
  loading.value = true
  try {
    if (props.reportId) {
      reportData.value = await reportStore.fetchReport(props.reportId)
    } else {
      // Fetch latest report
      const reports = await reportStore.fetchReports({ page_size: 1 })
      if (reports.length > 0) {
        reportData.value = await reportStore.fetchReport(reports[0].id)
      }
    }

    if (reportData.value) {
      selectedReport.value = reportData.value
      testResults.value = reportData.value.test_results || []
      updateStatistics()
      await initCharts()
    }
  } catch (error) {
    ElMessage.error('加载报告数据失败')
  } finally {
    loading.value = false
  }
}

const updateStatistics = () => {
  const results = testResults.value
  const total = results.length
  const passed = results.filter(r => r.status === 'PASSED').length
  const failed = results.filter(r => r.status === 'FAILED').length
  const skipped = results.filter(r => r.status === 'SKIPPED').length
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0

  overallStats.value = { total, passed, failed, skipped, passRate }

  statistics.value[0].value = total
  statistics.value[1].value = passed
  statistics.value[2].value = failed
  statistics.value[3].value = passRate + '%'
}

const initCharts = async () => {
  await nextTick()

  // Dispose existing charts
  chartInstances.value.forEach(chart => chart.dispose())
  chartInstances.value.clear()

  // Initialize all charts
  initGaugeChart()
  initResultPieChart()
  initResponseTimeDistChart()
  initTrendLineChart()
  initStatusCodeChart()
  initFailedCasesChart()
  initHeatmapChart()
  initModuleStatsChart()
  initRadarChart()
  initBoxPlotChart()
  initAssertionFailChart()

  // Resize charts on window resize
  window.addEventListener('resize', handleResize)
}

const initGaugeChart = () => {
  if (!gaugeChartRef.value) return

  const chart = echarts.init(gaugeChartRef.value)
  chartInstances.value.set('gauge', chart)

  const option = {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 10,
      axisLine: {
        lineStyle: {
          width: 15,
          color: [
            [0.3, '#f56c6c'],
            [0.7, '#e6a23c'],
            [1, '#67c23a']
          ]
        }
      },
      pointer: {
        icon: 'path://M2090.3638913232,0.2094376598980285 C2090.3638913232,0.2094376598980285 2090.3638913232,472.41377903781604 2624.3638913232,472.41377903781604 2624.3638913232,0.2094376598980285 C2624.3638913232,0.2094376598980285 2090.3638913232,0.2094376598980285 2090.3638913232,0.2094376598980285 Z',
        length: '75%',
        width: 16,
        offsetCenter: [0, '8%']
      },
      axisTick: {
        length: 12,
        lineStyle: { color: '#fff', width: 2 }
      },
      splitLine: {
        length: 15,
        lineStyle: { color: '#fff', width: 2 }
      },
      axisLabel: {
        formatter: '{value}%'
      },
      title: {
        show: true
      },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: 'inherit',
        fontSize: 28,
        offsetCenter: [0, '70%']
      },
      data: [{
        value: overallStats.value.passRate,
        name: '通过率'
      }]
    }]
  }

  chart.setOption(option)
}

const initResultPieChart = () => {
  if (!resultPieChartRef.value) return

  const chart = echarts.init(resultPieChartRef.value)
  chartInstances.value.set('resultPie', chart)

  const data = [
    { value: overallStats.value.passed, name: '通过', itemStyle: { color: '#67c23a' } },
    { value: overallStats.value.failed, name: '失败', itemStyle: { color: '#f56c6c' } },
    { value: overallStats.value.skipped, name: '跳过', itemStyle: { color: '#909399' } }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [{
      name: '测试结果',
      type: resultChartType.value,
      radius: resultChartType.value === 'doughnut' ? ['40%', '70%'] : '70%',
      data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  chart.setOption(option)
}

const initResponseTimeDistChart = () => {
  if (!responseTimeDistRef.value || testResults.value.length === 0) return

  const chart = echarts.init(responseTimeDistRef.value)
  chartInstances.value.set('responseTimeDist', chart)

  // Build distribution data
  const distribution = [
    { range: '0-100ms', count: 0, color: '#67c23a' },
    { range: '100-300ms', count: 0, color: '#409eff' },
    { range: '300-500ms', count: 0, color: '#e6a23c' },
    { range: '500-1s', count: 0, color: '#f56c6c' },
    { range: '>1s', count: 0, color: '#909399' }
  ]

  testResults.value.forEach(r => {
    const time = r.response_time || 0
    if (time < 100) distribution[0].count++
    else if (time < 300) distribution[1].count++
    else if (time < 500) distribution[2].count++
    else if (time < 1000) distribution[3].count++
    else distribution[4].count++
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: distribution.map(d => d.range),
      axisLabel: { interval: 0, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series: [{
      type: 'bar',
      data: distribution.map(d => ({
        value: d.count,
        itemStyle: { color: d.color }
      })),
      barWidth: '60%',
      label: {
        show: true,
        position: 'top'
      }
    }]
  }

  chart.setOption(option)
}

const initTrendLineChart = () => {
  if (!trendLineChartRef.value) return

  const chart = echarts.init(trendLineChartRef.value)
  chartInstances.value.set('trendLine', chart)

  // Mock trend data
  const dates = []
  const passRates = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString())
    passRates.push(Math.round(70 + Math.random() * 25))
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '通过率(%)',
      min: 0,
      max: 100
    },
    series: [{
      name: '通过率',
      type: 'line',
      smooth: true,
      data: passRates,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
          { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        },
        itemStyle: { color: '#67c23a' },
        lineStyle: { width: 2 }
      },
      {
        name: '平均线',
        type: 'line',
        markLine: {
          data: [{ type: 'average', name: '平均' }]
        }
      }]
  }

  chart.setOption(option)
}

const initStatusCodeChart = () => {
  if (!statusCodeChartRef.value || testResults.value.length === 0) return

  const chart = echarts.init(statusCodeChartRef.value)
  chartInstances.value.set('statusCode', chart)

  // Count status codes
  const statusCounts: Record<number, number> = {}
  testResults.value.forEach(r => {
    const code = r.response_status || 0
    statusCounts[code] = (statusCounts[code] || 0) + 1
  })

  const sortedCodes = Object.keys(statusCounts).sort((a, b) => Number(a) - Number(b))
  const data = sortedCodes.map(code => ({
    name: `${code}`,
    value: statusCounts[Number(code)],
    itemStyle: {
      color: code.startsWith('2') ? '#67c23a' :
             code.startsWith('3') ? '#e6a23c' :
             code.startsWith('4') ? '#f56c6c' :
             code.startsWith('5') ? '#909399' : '#606266'
    }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data
    }]
  }

  chart.setOption(option)
}

const initFailedCasesChart = () => {
  if (!failedCasesChartRef.value) return

  const chart = echarts.init(failedCasesChartRef.value)
  chartInstances.value.set('failedCases', chart)

  // Get top 10 failed cases
  const failedCases = testResults.value
    .filter(r => r.status === 'FAILED')
    .sort((a, b) => (a.response_time || 0) - (b.response_time || 0))
    .slice(0, 10)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: failedCases.map(c => c.test_case_name?.substring(0, 15) + '...'),
      axisLabel: { interval: 0, rotate: 45, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: '响应时间(ms)'
    },
    series: [{
      type: 'bar',
      data: failedCases.map(c => c.response_time || 0),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#f56c6c' },
          { offset: 1, color: '#e898a2' }
        ])
      },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}ms'
      }
    }]
  }

  chart.setOption(option)
}

const initHeatmapChart = () => {
  if (!heatmapChartRef.value) return

  const chart = echarts.init(heatmapChartRef.value)
  chartInstances.value.set('heatmap', chart)

  // Generate heatmap data (hour vs day)
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const days = []
  const data = []

  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const dayStr = date.toLocaleDateString()
    days.push(dayStr)

    for (let h = 0; h < 24; h++) {
      data.push([dayStr, h, Math.floor(Math.random() * 20)])
    }
  }

  const option = {
    tooltip: {
      position: 'top'
    },
    grid: {
      height: '70%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 20,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      inRange: {
        color: ['#e0f3f8', '#abd9e9', '#67c23a', '#e6a23c', '#f56c6c']
      }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  chart.setOption(option)
}

const initModuleStatsChart = () => {
  if (!moduleStatsChartRef.value) return

  const chart = echarts.init(moduleStatsChartRef.value)
  chartInstances.value.set('moduleStats', chart)

  // Mock module data
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['通过', '失败']
    },
    xAxis: {
      type: 'category',
      data: ['用户模块', '订单模块', '支付模块', '产品模块', '库存模块']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '通过',
        type: 'bar',
        stack: 'total',
        data: [320, 302, 301, 334, 390],
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        data: [20, 32, 11, 14, 8],
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }

  chart.setOption(option)
}

const initRadarChart = () => {
  if (!radarChartRef.value) return

  const chart = echarts.init(radarChartRef.value)
  chartInstances.value.set('radar', chart)

  const option = {
    tooltip: {},
    radar: {
      indicator: [
        { name: '功能覆盖', max: 100 },
        { name: '通过率', max: 100 },
        { name: '稳定性', max: 100 },
        { name: '性能', max: 100 },
        { name: '安全性', max: 100 },
        { name: '可维护性', max: 100 }
      ]
    },
    series: [{
      name: '测试评估',
      type: 'radar',
      data: [
        {
          value: [85, 90, 78, 82, 88, 75],
          name: '当前版本',
          areaStyle: { color: 'rgba(64, 158, 255, 0.3)' }
        },
        {
          value: [75, 82, 70, 75, 80, 68],
          name: '上一版本',
          areaStyle: { color: 'rgba(103, 194, 58, 0.3)' }
        }
      ]
    }]
  }

  chart.setOption(option)
}

const initBoxPlotChart = () => {
  if (!boxPlotChartRef.value) return

  const chart = echarts.init(boxPlotChartRef.value)
  chartInstances.value.set('boxPlot', chart)

  // Mock box plot data
  const option = {
    tooltip: {
      trigger: 'item',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: ['GET', 'POST', 'PUT', 'DELETE']
    },
    yAxis: {
      type: 'value',
      name: '响应时间(ms)'
    },
    series: [
      {
        name: 'GET',
        type: 'boxplot',
        data: [[50, 80, 120, 200, 450]]
      },
      {
        name: 'POST',
        type: 'boxplot',
        data: [[80, 120, 180, 300, 600]]
      },
      {
        name: 'PUT',
        type: 'boxplot',
        data: [[70, 100, 150, 250, 500]]
      },
      {
        name: 'DELETE',
        type: 'boxplot',
        data: [[40, 60, 90, 150, 350]]
      }
    ]
  }

  chart.setOption(option)
}

const initAssertionFailChart = () => {
  if (!assertionFailChartRef.value) return

  const chart = echarts.init(assertionFailChartRef.value)
  chartInstances.value.set('assertionFail', chart)

  // Mock assertion failure data
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: '断言失败类型',
      type: 'pie',
      radius: ['30%', '70%'],
      data: [
        { value: 35, name: '状态码断言' },
        { value: 28, name: '字段断言' },
        { value: 20, name: '响应时间断言' },
        { value: 12, name: '包含断言' },
        { value: 5, name: 'JSON Schema断言' }
      ]
    }]
  }

  chart.setOption(option)
}

const handleResize = () => {
  chartInstances.value.forEach(chart => {
    chart.resize()
  })
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    // Start auto refresh every 30 seconds
    setInterval(refreshData, 30000)
  }
}

const applyFilters = () => {
  refreshData()
}

const resetFilters = () => {
  filters.reportType = ''
  filters.projectId = null
  filters.environmentId = null
  filters.dateRange = null
  refreshData()
}

const handleExport = async (command: string) => {
  try {
    const reportData = {
      report: selectedReport.value,
      statistics: overallStats.value,
      testResults: testResults.value
    }

    switch (command) {
      case 'export-image':
        exportImageVisible.value = true
        break
      case 'export-pdf':
        await exportToPDF(reportData)
        break
      case 'export-excel':
        await exportToExcel(reportData)
        break
      case 'export-data':
        await exportToJSON(reportData)
        break
    }
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

/**
 * 导出为PDF
 */
const exportToPDF = async (data: any) => {
  loading.value = true
  try {
    const element = document.querySelector('.enhanced-report-viewer') as HTMLElement
    if (!element) {
      throw new Error('找不到导出元素')
    }

    const filename = generateExportFilename('pdf', 'test_report')
    await ReportExporter.exportToPDF(element, {
      filename,
      title: selectedReport.value?.name || '测试报告',
      author: 'API自动化测试平台',
      subject: 'API测试执行报告'
    })

    ElMessage.success('PDF导出成功')
  } finally {
    loading.value = false
  }
}

/**
 * 导出为Excel
 */
const exportToExcel = async (data: any) => {
  loading.value = true
  try {
    const filename = generateExportFilename('excel', 'test_report')
    ReportExporter.exportToExcel(data, {
      filename,
      title: selectedReport.value?.name || '测试报告'
    })

    ElMessage.success('Excel导出成功')
  } finally {
    loading.value = false
  }
}

/**
 * 导出为JSON
 */
const exportToJSON = async (data: any) => {
  loading.value = true
  try {
    const filename = generateExportFilename('json', 'test_report')
    ReportExporter.exportToJSON(data, {
      filename
    })

    ElMessage.success('JSON导出成功')
  } finally {
    loading.value = false
  }
}

/**
 * 导出图表为图片
 */
const exportChartsImage = async () => {
  try {
    const format = exportImageFormat.value as 'png' | 'jpeg'
    const filename = generateExportFilename(format, 'test_report_charts')

    // 获取所有图表容器
    const chartContainers = document.querySelectorAll('.chart-container') as NodeListOf<HTMLElement>

    if (chartContainers.length > 0) {
      // 导出所有图表为PDF
      await ReportExporter.exportChartsToPDF(
        Array.from(chartContainers),
        { filename: filename.replace(/\.(png|jpg)$/, '.pdf'), title: '测试报告图表' }
      )
    } else {
      ElMessage.warning('没有找到可导出的图表')
    }

    ElMessage.success('图表导出成功')
    exportImageVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.message || '图表导出失败')
  }
}

/**
 * 导出单个图表
 */
const exportSingleChart = async (chartName: string, chartRef: any) => {
  try {
    if (!chartRef.value) {
      ElMessage.warning('图表未初始化')
      return
    }

    const chartInstance = chartInstances.value.get(chartName)
    if (!chartInstance) {
      ElMessage.warning('图表实例未找到')
      return
    }

    const filename = `${chartName}_${Date.now()}.png`
    await ReportExporter.exportChartToImage(chartInstance, { filename })
    ElMessage.success(`${chartName} 导出成功`)
  } catch (error: any) {
    ElMessage.error(`${chartName} 导出失败: ${error.message}`)
  }
}

/**
 * 导出CSV
 */
const exportToCSV = async () => {
  loading.value = true
  try {
    const data = {
      report: selectedReport.value,
      statistics: overallStats.value,
      testResults: testResults.value
    }

    const filename = generateExportFilename('csv', 'test_report')
    ReportExporter.exportToCSV(data, { filename })

    ElMessage.success('CSV导出成功')
  } finally {
    loading.value = false
  }
}

/**
 * 导出JSON (保留向后兼容)
 */
const exportJsonData = () => {
  const data = {
    report: selectedReport.value,
    statistics: overallStats.value,
    testResults: testResults.value
  }
  const filename = generateExportFilename('json', 'test_report')
  ReportExporter.exportToJSON(data, { filename })
  ElMessage.success('数据已导出')
}

const toggleFullscreen = () => {
  const element = document.querySelector('.enhanced-report-viewer') as HTMLElement
  if (!document.fullscreenElement) {
    element.requestFullscreen?.()
  } else {
    document.exitFullscreen()
  }
}

const drillDownFailed = () => {
  detailStatusFilter.value = 'FAILED'
  viewMode.value = 'details'
}

const handleRowAction = ({ action, row }: { action: string; row: any }) => {
  switch (action) {
    case 'retry':
      ElMessage.info(`重试用例: ${row.test_case_name}`)
      break
    case 'copy':
      ElMessage.success(`已复制: ${row.test_case_name}`)
      break
    case 'export':
      exportJsonData()
      break
  }
}

// Utility functions
const getPassRateType = (rate: number) => {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'warning'
  return 'danger'
}

const getMethodType = (method: string) => {
  const types: Record<string, string> = {
    'GET': '',
    'POST': 'success',
    'PUT': 'warning',
    'PATCH': 'warning',
    'DELETE': 'danger'
  }
  return types[method] || ''
}

const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'ERROR': 'danger'
  }
  return statusMap[status] || 'info'
}

const getResponseTimeClass = (time: number) => {
  if (time < 100) return 'fast'
  if (time < 300) return 'normal'
  if (time < 500) return 'slow'
  return 'very-slow'
}

const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '-'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + sizes[i]
}

const formatJson = (data: any) => {
  if (!data) return '-'
  if (typeof data === 'string') return data
  return JSON.stringify(data, null, 2)
}

// Lifecycle
onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 1000 })
  await environmentStore.fetchEnvironments({ page_size: 1000 })
  await refreshData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstances.value.forEach(chart => chart.dispose())
})

// Watch view mode to initialize charts
watch(viewMode, async () => {
  if (viewMode.value === 'overview' || viewMode.value === 'charts') {
    await nextTick()
    initCharts()
  }
})
</script>

<style scoped>
.enhanced-report-viewer {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-panel {
  margin-bottom: 16px;
}

.stats-overview {
  margin-bottom: 16px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.stat-primary .stat-icon {
  background-color: #ecf5ff;
  color: #409eff;
}

.stat-card.stat-success .stat-icon {
  background-color: #f0f9ff;
  color: #67c23a;
}

.stat-card.stat-danger .stat-icon {
  background-color: #fef0f0;
  color: #f56c6c;
}

.stat-card.stat-warning .stat-icon {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
}

.stat-trend.up {
  color: #67c23a;
}

.stat-trend.down {
  color: #f56c6c;
}

.mini-chart {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 80px;
  height: 40px;
  opacity: 0.3;
}

.chart-card {
  height: 100%;
}

.chart-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  color: #303133;
}

.chart-container {
  width: 100%;
}

.details-table {
  font-size: 13px;
}

.expand-content {
  padding: 16px;
  background-color: #fafafa;
}

.code-preview {
  background-color: #2d2d2d;
  color: #ccc;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  max-height: 300px;
  overflow-y: auto;
}

.assertion-results {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.assertion-item.passed {
  background-color: #f0f9ff;
  color: #67c23a;
}

.assertion-item.failed {
  background-color: #fef0f0;
  color: #f56c6c;
}

.table-footer {
  padding: 12px 0;
  text-align: right;
}

.fast {
  color: #67c23a;
}

.normal {
  color: #409eff;
}

.slow {
  color: #e6a23c;
}

.very-slow {
  color: #f56c6c;
}

/* 全屏样式 */
:deep(.enhanced-report-viewer.fullscreen) {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  padding: 20px;
  overflow-y: auto;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-overview .el-col {
    margin-bottom: 16px;
  }
}
</style>
