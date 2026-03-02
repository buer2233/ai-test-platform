/**
 * 测试报告状态管理（Pinia Store）
 *
 * 管理 UI 自动化测试报告的列表、当前查看的报告详情，
 * 提供按状态筛选、通过率计算等派生数据。
 */

import { defineStore } from 'pinia'

import { uiReportApi } from '../api/report'
import type { UiTestReport } from '../types/report'

/** 报告 Store 的状态类型定义 */
interface ReportState {
  /** 报告列表 */
  reports: UiTestReport[]
  /** 当前查看的报告详情 */
  currentReport: UiTestReport | null
  /** 列表加载状态 */
  loading: boolean
  /** 列表总数（用于分页） */
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
    /** 筛选出通过的报告 */
    passedReports: (state) => {
      return state.reports.filter(r => r.status === 'passed')
    },

    /** 筛选出失败的报告 */
    failedReports: (state) => {
      return state.reports.filter(r => r.status === 'failed')
    },

    /** 按项目 ID 筛选报告 */
    reportsByProject: (state) => (projectId: number) => {
      return state.reports.filter(r => r.project === projectId)
    },

    /** 按执行记录 ID 筛选报告 */
    reportsByExecution: (state) => (executionId: number) => {
      return state.reports.filter(r => r.execution === executionId)
    },

    /** 计算报告通过率（百分比，0-100） */
    passRate: (state) => {
      if (state.reports.length === 0) return 0
      const passed = state.reports.filter(r => r.status === 'passed').length
      return (passed / state.reports.length) * 100
    }
  },

  actions: {
    /** 获取报告列表（支持分页和筛选参数） */
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

    /** 获取单个报告详情并设为当前报告 */
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

    /** 删除报告并从列表中移除 */
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

    /** 导出报告为 PDF 格式 */
    async exportReport(id: number) {
      try {
        return await uiReportApi.exportReport(id)
      } catch (error) {
        console.error('Failed to export UI test report:', error)
        throw error
      }
    },

    /** 清除当前查看的报告 */
    clearCurrentReport() {
      this.currentReport = null
    }
  }
})
