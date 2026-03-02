/**
 * 执行记录状态管理（Pinia Store）
 *
 * 管理 UI 自动化测试执行记录的列表、当前查看的执行记录、
 * 运行状态以及 WebSocket 实时进度推送数据。
 */

import { defineStore } from 'pinia'

import { uiExecutionApi } from '../api/execution'
import type { UiTestExecution, UiTestExecutionCreate, ExecutionStatus } from '../types/execution'

/** 执行记录 Store 的状态类型定义 */
interface ExecutionState {
  /** 执行记录列表 */
  executions: UiTestExecution[]
  /** 当前查看的执行记录详情 */
  currentExecution: UiTestExecution | null
  /** 列表加载状态 */
  loading: boolean
  /** 是否有正在运行的测试 */
  running: boolean
  /** 列表总数（用于分页） */
  total: number
  /** WebSocket 实时进度信息 */
  progress: {
    executionId: number | null
    message: string
    status: ExecutionStatus | null
  }
}

export const useUiExecutionStore = defineStore('uiExecution', {
  state: (): ExecutionState => ({
    executions: [],
    currentExecution: null,
    loading: false,
    running: false,
    total: 0,
    progress: {
      executionId: null,
      message: '',
      status: null
    }
  }),

  getters: {
    /** 筛选出正在运行的执行记录 */
    runningExecutions: (state) => {
      return state.executions.filter(e => e.status === 'running')
    },

    /** 按项目 ID 筛选执行记录 */
    executionsByProject: (state) => (projectId: number) => {
      return state.executions.filter(e => e.project === projectId)
    },

    /** 按测试用例 ID 筛选执行记录 */
    executionsByTestCase: (state) => (testCaseId: number) => {
      return state.executions.filter(e => e.test_case === testCaseId)
    },

    /** 统计各状态的执行记录数量分布 */
    statusDistribution: (state) => {
      const distribution = {
        pending: 0,
        running: 0,
        passed: 0,
        failed: 0,
        error: 0,
        cancelled: 0
      }
      state.executions.forEach(exec => {
        if (exec.status in distribution) {
          distribution[exec.status as keyof typeof distribution]++
        }
      })
      return distribution
    }
  },

  actions: {
    /** 获取执行记录列表（支持分页和筛选参数） */
    async fetchExecutions(params?: any) {
      this.loading = true
      try {
        const response = await uiExecutionApi.getExecutions(params)
        this.executions = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch UI test executions:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个执行记录详情并设为当前记录 */
    async fetchExecution(id: number) {
      this.loading = true
      try {
        const execution = await uiExecutionApi.getExecution(id)
        this.currentExecution = execution
        return execution
      } catch (error) {
        console.error('Failed to fetch UI test execution:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建执行记录并插入列表头部 */
    async createExecution(data: UiTestExecutionCreate) {
      try {
        const execution = await uiExecutionApi.createExecution(data)
        this.executions.unshift(execution)
        this.total += 1
        return execution
      } catch (error) {
        console.error('Failed to create UI test execution:', error)
        throw error
      }
    },

    /** 启动测试运行并更新列表中对应记录的状态 */
    async runExecution(id: number) {
      this.running = true
      try {
        const result = await uiExecutionApi.run(id)
        const index = this.executions.findIndex(e => e.id === id)
        if (index !== -1) {
          this.executions[index].status = 'running'
        }
        return result
      } catch (error) {
        console.error('Failed to run UI test execution:', error)
        throw error
      } finally {
        this.running = false
      }
    },

    /** 取消正在运行的测试并更新状态 */
    async cancelExecution(id: number) {
      try {
        const result = await uiExecutionApi.cancel(id)
        const index = this.executions.findIndex(e => e.id === id)
        if (index !== -1) {
          this.executions[index].status = 'cancelled'
        }
        return result
      } catch (error) {
        console.error('Failed to cancel UI test execution:', error)
        throw error
      }
    },

    /** 删除执行记录并从列表中移除 */
    async deleteExecution(id: number) {
      try {
        await uiExecutionApi.deleteExecution(id)
        this.executions = this.executions.filter(e => e.id !== id)
        this.total -= 1
        if (this.currentExecution?.id === id) {
          this.currentExecution = null
        }
      } catch (error) {
        console.error('Failed to delete UI test execution:', error)
        throw error
      }
    },

    /** 获取执行关联的 HTML 测试报告 */
    async fetchReport(id: number) {
      try {
        return await uiExecutionApi.getReport(id)
      } catch (error) {
        console.error('Failed to fetch execution report:', error)
        throw error
      }
    },

    /**
     * 更新 WebSocket 推送的实时进度
     * 同时同步更新列表中对应执行记录的状态
     */
    updateProgress(executionId: number, message: string, status: ExecutionStatus) {
      this.progress = { executionId, message, status }
      const index = this.executions.findIndex(e => e.id === executionId)
      if (index !== -1) {
        this.executions[index].status = status
      }
    },

    /** 清除当前查看的执行记录 */
    clearCurrentExecution() {
      this.currentExecution = null
    }
  }
})
