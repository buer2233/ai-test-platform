import { defineStore } from 'pinia'
import { uiExecutionApi } from '../api/execution'
import type { UiTestExecution, UiTestExecutionCreate, ExecutionStatus } from '../types/execution'

interface ExecutionState {
  executions: UiTestExecution[]
  currentExecution: UiTestExecution | null
  loading: boolean
  running: boolean
  total: number
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
    runningExecutions: (state) => {
      return state.executions.filter(e => e.status === 'running')
    },

    executionsByProject: (state) => (projectId: number) => {
      return state.executions.filter(e => e.project === projectId)
    },

    executionsByTestCase: (state) => (testCaseId: number) => {
      return state.executions.filter(e => e.test_case === testCaseId)
    },

    statusDistribution: (state) => {
      const distribution = {
        pending: 0,
        running: 0,
        completed: 0,
        failed: 0,
        cancelled: 0
      }
      state.executions.forEach(exec => {
        distribution[exec.status]++
      })
      return distribution
    }
  },

  actions: {
    // 获取执行记录列表
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

    // 获取单个执行记录
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

    // 创建执行记录
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

    // 运行测试
    async runExecution(id: number) {
      this.running = true
      try {
        const result = await uiExecutionApi.run(id)
        // 更新执行记录状态
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

    // 取消执行
    async cancelExecution(id: number) {
      try {
        const result = await uiExecutionApi.cancel(id)
        // 更新执行记录状态
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

    // 删除执行记录
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

    // 获取测试报告
    async fetchReport(id: number) {
      try {
        return await uiExecutionApi.getReport(id)
      } catch (error) {
        console.error('Failed to fetch execution report:', error)
        throw error
      }
    },

    // 更新进度信息（用于WebSocket推送）
    updateProgress(executionId: number, message: string, status: ExecutionStatus) {
      this.progress = {
        executionId,
        message,
        status
      }
      // 同时更新执行记录状态
      const index = this.executions.findIndex(e => e.id === executionId)
      if (index !== -1) {
        this.executions[index].status = status
      }
    },

    // 清除当前执行记录
    clearCurrentExecution() {
      this.currentExecution = null
    }
  }
})
