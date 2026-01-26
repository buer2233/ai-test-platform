import { defineStore } from 'pinia'
import { uiReportApi } from '../api/report'
import type { UiTestReport } from '../types/report'

interface ReportState {
  reports: UiTestReport[]
  currentReport: UiTestReport | null
  loading: boolean
  total: number
}

export const useUiReportStore = defineStore('uiReport', {
  state: (): ReportState => ({
    reports: [],
    currentReport: null,
    loading: false,
    total: 0
  }),

  getters: {
    passedReports: (state) => {
      return state.reports.filter(r => r.status === 'passed')
    },

    failedReports: (state) => {
      return state.reports.filter(r => r.status === 'failed')
    },

    reportsByProject: (state) => (projectId: number) => {
      return state.reports.filter(r => r.project === projectId)
    },

    reportsByExecution: (state) => (executionId: number) => {
      return state.reports.filter(r => r.execution === executionId)
    },

    passRate: (state) => {
      if (state.reports.length === 0) return 0
      const passed = state.reports.filter(r => r.status === 'passed').length
      return (passed / state.reports.length) * 100
    }
  },

  actions: {
    // 获取报告列表
    async fetchReports(params?: any) {
      this.loading = true
      try {
        const response = await uiReportApi.getReports(params)
        this.reports = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch UI test reports:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个报告
    async fetchReport(id: number) {
      this.loading = true
      try {
        const report = await uiReportApi.getReport(id)
        this.currentReport = report
        return report
      } catch (error) {
        console.error('Failed to fetch UI test report:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 删除报告
    async deleteReport(id: number) {
      try {
        await uiReportApi.deleteReport(id)
        this.reports = this.reports.filter(r => r.id !== id)
        this.total -= 1
        if (this.currentReport?.id === id) {
          this.currentReport = null
        }
      } catch (error) {
        console.error('Failed to delete UI test report:', error)
        throw error
      }
    },

    // 导出报告
    async exportReport(id: number) {
      try {
        return await uiReportApi.exportReport(id)
      } catch (error) {
        console.error('Failed to export UI test report:', error)
        throw error
      }
    },

    // 清除当前报告
    clearCurrentReport() {
      this.currentReport = null
    }
  }
})
