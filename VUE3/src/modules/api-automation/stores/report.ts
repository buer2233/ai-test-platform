import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { reportApi } from '../api/report'
import type { ApiTestReport, ReportDetail } from '../types/report'
import { ElMessage } from 'element-plus'

export const useReportStore = defineStore('report', () => {
  // 状态
  const reports = ref<ApiTestReport[]>([])
  const currentReport = ref<ReportDetail | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // 计算属性
  const recentReports = computed(() => {
    return reports.value.slice(0, 10)
  })

  const statistics = computed(() => {
    if (!reports.value.length) {
      return {
        totalExecutions: 0,
        avgPassRate: 0,
        avgDuration: 0
      }
    }

    const totalExecutions = reports.value.length
    const avgPassRate = Math.round(
      reports.value.reduce((sum, report) => sum + report.summary.pass_rate, 0) / totalExecutions
    )
    const avgDuration = Math.round(
      reports.value.reduce((sum, report) => sum + report.summary.duration, 0) / totalExecutions
    )

    return {
      totalExecutions,
      avgPassRate,
      avgDuration
    }
  })

  // 方法
  const fetchReports = async (params?: any) => {
    loading.value = true
    try {
      const response = await reportApi.getReports(params)
      reports.value = response.results
      total.value = response.count
    } catch (error) {
      ElMessage.error('获取报告列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchReport = async (id: number) => {
    loading.value = true
    try {
      const response = await reportApi.getReport(id)
      currentReport.value = response as ReportDetail
      return response
    } catch (error) {
      ElMessage.error('获取报告详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const exportReport = async (id: number, format: 'pdf' | 'excel' = 'pdf') => {
    try {
      const response = await reportApi.exportReport(id, format)

      // 创建下载链接
      const blob = new Blob([response], {
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `test-report-${Date.now()}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('报告导出成功')
    } catch (error) {
      ElMessage.error('报告导出失败')
      throw error
    }
  }

  const resetState = () => {
    reports.value = []
    currentReport.value = null
    loading.value = false
    total.value = 0
  }

  return {
    // 状态
    reports,
    currentReport,
    loading,
    total,

    // 计算属性
    recentReports,
    statistics,

    // 方法
    fetchReports,
    fetchReport,
    exportReport,
    resetState
  }
})