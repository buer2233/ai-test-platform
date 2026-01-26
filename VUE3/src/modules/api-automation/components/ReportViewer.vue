<template>
  <div class="report-viewer">
    <div class="header">
      <h2>测试报告</h2>
      <div class="header-actions">
        <el-button @click="fetchReports">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reportStore.statistics.totalExecutions }}</div>
              <div class="stat-label">总报告数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reportStore.statistics.avgPassRate }}%</div>
              <div class="stat-label">平均通过率</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reportStore.statistics.avgDuration }}s</div>
              <div class="stat-label">平均耗时</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ reportStore.recentReports.length }}</div>
              <div class="stat-label">最近报告</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 报告列表 -->
    <el-table :data="reportStore.reports" v-loading="reportStore.loading" stripe>
      <el-table-column prop="name" label="报告名称" />
      <el-table-column prop="project_name" label="所属项目" />
      <el-table-column prop="execution_name" label="执行名称" />
      <el-table-column label="执行结果" width="200">
        <template #default="{ row }">
          <div class="result-summary">
            <span class="passed">{{ row.summary.passed }}</span>/
            <span class="total">{{ row.summary.total }}</span>
            <span class="failed">-{{ row.summary.failed }}</span>
          </div>
          <div class="pass-rate">
            通过率: {{ row.summary.pass_rate }}%
          </div>
        </template>
      </el-table-column>
      <el-table-column label="耗时" width="100">
        <template #default="{ row }">
          {{ row.summary.duration }}s
        </template>
      </el-table-column>
      <el-table-column label="执行时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.summary.start_time) }} -
          {{ formatDateTime(row.summary.end_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="生成时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewReportDetail(row)">详情</el-button>
          <el-dropdown @command="handleExport">
            <el-button size="small">
              导出<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="{ action: 'pdf', id: row.id }">PDF格式</el-dropdown-item>
                <el-dropdown-item :command="{ action: 'excel', id: row.id }">Excel格式</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="reportStore.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 报告详情对话框 -->
    <el-dialog
      title="测试报告详情"
      v-model="detailDialogVisible"
      width="90%"
      top="5vh"
    >
      <div v-if="currentReport">
        <el-tabs v-model="activeTab">
          <!-- 基本信息 -->
          <el-tab-pane label="基本概览" name="overview">
            <div class="report-overview">
              <!-- 概览统计 -->
              <el-row :gutter="20" class="overview-stats">
                <el-col :span="8">
                  <el-card>
                    <div class="stat-item">
                      <div class="stat-number">{{ currentReport.summary.total }}</div>
                      <div class="stat-title">总用例数</div>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card>
                    <div class="stat-item">
                      <div class="stat-number passed">{{ currentReport.summary.passed }}</div>
                      <div class="stat-title">通过用例</div>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card>
                    <div class="stat-item">
                      <div class="stat-number failed">{{ currentReport.summary.failed }}</div>
                      <div class="stat-title">失败用例</div>
                    </div>
                  </el-card>
                </el-col>
              </el-row>

              <!-- 详细信息 -->
              <el-descriptions :column="2" border class="mt-20">
                <el-descriptions-item label="报告名称">{{ currentReport.name }}</el-descriptions-item>
                <el-descriptions-item label="项目">{{ currentReport.project_name }}</el-descriptions-item>
                <el-descriptions-item label="执行名称">{{ currentReport.execution_name }}</el-descriptions-item>
                <el-descriptions-item label="通过率">
                  <el-progress
                    :percentage="currentReport.summary.pass_rate"
                    :color="currentReport.summary.pass_rate >= 80 ? 'success' : 'warning'"
                  />
                </el-descriptions-item>
                <el-descriptions-item label="跳过用例">{{ currentReport.summary.skipped }}</el-descriptions-item>
                <el-descriptions-item label="执行时长">{{ currentReport.summary.duration }}秒</el-descriptions-item>
                <el-descriptions-item label="开始时间">{{ formatDateTime(currentReport.summary.start_time) }}</el-descriptions-item>
                <el-descriptions-item label="结束时间">{{ formatDateTime(currentReport.summary.end_time) }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>

          <!-- 图表分析 -->
          <el-tab-pane label="图表分析" name="charts">
            <div class="charts-container">
              <el-row :gutter="20">
                <!-- 测试结果分布图 -->
                <el-col :span="12">
                  <el-card title="测试结果分布">
                    <div class="chart-wrapper" ref="pieChartRef"></div>
                  </el-card>
                </el-col>
                <!-- 响应时间分析 -->
                <el-col :span="12">
                  <el-card title="响应时间分析">
                    <div class="chart-wrapper" ref="barChartRef"></div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

          <!-- 测试结果详情 -->
          <el-tab-pane label="测试结果" name="results">
            <el-table :data="currentReport.test_results" stripe>
              <el-table-column prop="test_case_name" label="测试用例" />
              <el-table-column prop="test_case_method" label="请求方法" width="100" />
              <el-table-column prop="test_case_url" label="请求URL" show-overflow-tooltip />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.status)" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="response_status" label="状态码" width="100" />
              <el-table-column prop="response_time" label="响应时间" width="120">
                <template #default="{ row }">
                  <span :class="getResponseTimeClass(row.response_time)">
                    {{ row.response_time }}ms
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="response_size" label="响应大小" width="120">
                <template #default="{ row }">
                  {{ formatFileSize(row.response_size) }}
                </template>
              </el-table-column>
              <el-table-column prop="start_time" label="执行时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.start_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="耗时" width="100">
                <template #default="{ row }">
                  {{ row.duration }}ms
                </template>
              </el-table-column>
              <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-popover v-if="row.error_message" placement="top" width="300">
                    <template #reference>
                      <span class="error-text">查看详情</span>
                    </template>
                    <div>{{ row.error_message }}</div>
                  </el-popover>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowDown } from '@element-plus/icons-vue'
import { useReportStore } from '../stores/report'
import * as echarts from 'echarts'

// Store
const reportStore = useReportStore()

// 响应式数据
const currentPage = ref(1)
const pageSize = ref(20)
const detailDialogVisible = ref(false)
const activeTab = ref('overview')
const currentReport = ref<any>(null)

// 图表引用
const pieChartRef = ref()
const barChartRef = ref()

// 图表实例
let pieChartInstance: echarts.ECharts | null = null
let barChartInstance: echarts.ECharts | null = null

// 方法
const fetchReports = () => {
  reportStore.fetchReports({
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchReports()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchReports()
}

const viewReportDetail = async (report: any) => {
  try {
    currentReport.value = await reportStore.fetchReport(report.id)
    detailDialogVisible.value = true
    nextTick(() => {
      initCharts()
    })
  } catch (error) {
    console.error('获取报告详情失败:', error)
  }
}

const handleExport = async ({ action, id }: { action: string; id: number }) => {
  try {
    await reportStore.exportReport(id, action as 'pdf' | 'excel')
  } catch (error) {
    console.error('导出报告失败:', error)
  }
}

const initCharts = () => {
  if (!currentReport.value) return

  // 初始化饼图
  if (pieChartRef.value) {
    pieChartInstance = echarts.init(pieChartRef.value)
    const pieOption = {
      title: {
        text: '测试结果分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [{
        name: '测试结果',
        type: 'pie',
        radius: '50%',
        data: [
          { value: currentReport.value.summary.passed, name: '通过' },
          { value: currentReport.value.summary.failed, name: '失败' },
          { value: currentReport.value.summary.skipped, name: '跳过' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    pieChartInstance.setOption(pieOption)
  }

  // 初始化柱状图
  if (barChartRef.value) {
    barChartInstance = echarts.init(barChartRef.value)
    const barOption = {
      title: {
        text: '响应时间分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: currentReport.value.charts_data.response_time?.labels || []
      },
      yAxis: {
        type: 'value',
        name: '响应时间(ms)'
      },
      series: [{
        name: '响应时间',
        type: 'bar',
        data: currentReport.value.charts_data.response_time?.data || [],
        itemStyle: {
          color: '#409eff'
        }
      }]
    }
    barChartInstance.setOption(barOption)
  }
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
  if (time < 500) return 'normal'
  if (time < 1000) return 'slow'
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

// 生命周期
onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.report-viewer {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.stat-value.passed {
  color: #67c23a;
}

.stat-value.failed {
  color: #f56c6c;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.result-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-summary .passed {
  color: #67c23a;
  font-weight: bold;
}

.result-summary .total {
  color: #666;
}

.result-summary .failed {
  color: #f56c6c;
}

.pass-rate {
  font-size: 12px;
  color: #999;
}

.report-overview {
  padding: 20px 0;
}

.overview-stats {
  margin-bottom: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-title {
  font-size: 14px;
  color: #666;
}

.mt-20 {
  margin-top: 20px;
}

.charts-container {
  padding: 20px 0;
}

.chart-wrapper {
  height: 400px;
  width: 100%;
}

.error-text {
  color: #f56c6c;
  cursor: pointer;
  text-decoration: underline;
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
</style>