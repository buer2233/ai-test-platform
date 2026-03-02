/**
 * 测试执行 Store
 *
 * 管理测试执行任务的状态和生命周期。
 * 支持创建、运行、取消、轮询刷新等操作。
 * 提供运行中任务筛选、通过率计算等计算属性。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

import { executionApi } from '../api/execution'
import type { ApiTestExecution, ExecutionCreate, ExecutionDetail } from '../types/execution'

export const useExecutionStore = defineStore('execution', () => {
  // ==================== 状态 ====================

  /** 执行任务列表 */
  const executions = ref<ApiTestExecution[]>([])
  /** 当前选中的执行任务详情 */
  const currentExecution = ref<ExecutionDetail | null>(null)
  /** 全局加载状态 */
  const loading = ref(false)
  /** 数据总条数（分页用） */
  const total = ref(0)
  /** 全局执行统计数据 */
  const statistics = ref<any>(null)

  // ==================== 计算属性 ====================

  /** 筛选出正在运行的执行任务 */
  const runningExecutions = computed(() => {
    return executions.value.filter(exec => exec.status === 'RUNNING')
  })

  /** 最近的 10 条执行任务 */
  const recentExecutions = computed(() => {
    return executions.value.slice(0, 10)
  })

  /** 计算所有执行任务的综合通过率 */
  const passRate = computed(() => {
    if (!executions.value.length) return 0
    const totalTests = executions.value.reduce((sum, exec) => sum + exec.total_count, 0)
    const passedTests = executions.value.reduce((sum, exec) => sum + exec.passed_count, 0)
    return totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
  })

  // ==================== 异步操作 ====================
  const fetchExecutions = async (params?: any) => {
    loading.value = true
    try {
      const response = await executionApi.getExecutions(params)
      executions.value = response.results
      total.value = response.count
    } catch (error) {
      ElMessage.error('获取执行列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchExecution = async (id: number) => {
    loading.value = true
    try {
      const response = await executionApi.getExecution(id)
      currentExecution.value = response as ExecutionDetail
      return response
    } catch (error) {
      ElMessage.error('获取执行详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createExecution = async (data: ExecutionCreate) => {
    loading.value = true
    try {
      const response = await executionApi.createExecution(data)
      executions.value.unshift(response)
      ElMessage.success('测试执行创建成功')
      return response
    } catch (error) {
      ElMessage.error('创建测试执行失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateExecution = async (id: number, data: Partial<ApiTestExecution>) => {
    loading.value = true
    try {
      const response = await executionApi.updateExecution(id, data)
      const index = executions.value.findIndex(exec => exec.id === id)
      if (index !== -1) {
        executions.value[index] = response
      }
      if (currentExecution.value?.id === id) {
        Object.assign(currentExecution.value, response)
      }
      ElMessage.success('测试执行更新成功')
      return response
    } catch (error) {
      ElMessage.error('更新测试执行失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteExecution = async (id: number) => {
    loading.value = true
    try {
      await executionApi.deleteExecution(id)
      const index = executions.value.findIndex(exec => exec.id === id)
      if (index !== -1) {
        executions.value.splice(index, 1)
      }
      if (currentExecution.value?.id === id) {
        currentExecution.value = null
      }
      ElMessage.success('测试执行删除成功')
    } catch (error) {
      ElMessage.error('删除测试执行失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const executeTest = async (id: number) => {
    loading.value = true
    try {
      const response = await executionApi.execute(id)
      // 更新执行状态
      const index = executions.value.findIndex(exec => exec.id === id)
      if (index !== -1) {
        executions.value[index] = { ...executions.value[index], ...response }
      }
      ElMessage.success('测试执行开始')
      return response
    } catch (error) {
      ElMessage.error('测试执行失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const cancelExecution = async (id: number) => {
    loading.value = true
    try {
      await executionApi.cancel(id)
      // 更新执行状态
      const index = executions.value.findIndex(exec => exec.id === id)
      if (index !== -1) {
        executions.value[index].status = 'CANCELLED'
      }
      if (currentExecution.value?.id === id) {
        currentExecution.value.status = 'CANCELLED'
      }
      ElMessage.success('测试执行已取消')
    } catch (error) {
      ElMessage.error('取消测试执行失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await executionApi.getStatistics()
      statistics.value = response
      return response
    } catch (error) {
      ElMessage.error('获取执行统计失败')
      throw error
    }
  }

  const updateExecutionStatus = (id: number, status: string) => {
    const index = executions.value.findIndex(exec => exec.id === id)
    if (index !== -1) {
      executions.value[index].status = status as any
    }
    if (currentExecution.value?.id === id) {
      currentExecution.value.status = status as any
    }
  }

  const refreshRunningExecutions = async () => {
    // 获取正在运行的执行并更新状态
    const running = runningExecutions.value
    for (const exec of running) {
      try {
        await fetchExecution(exec.id)
      } catch (error) {
        console.error('刷新执行状态失败:', error)
      }
    }
  }

  const resetState = () => {
    executions.value = []
    currentExecution.value = null
    loading.value = false
    total.value = 0
    statistics.value = null
  }

  return {
    // 状态
    executions,
    currentExecution,
    loading,
    total,
    statistics,

    // 计算属性
    runningExecutions,
    recentExecutions,
    passRate,

    // 方法
    fetchExecutions,
    fetchExecution,
    createExecution,
    updateExecution,
    deleteExecution,
    executeTest,
    cancelExecution,
    fetchStatistics,
    updateExecutionStatus,
    refreshRunningExecutions,
    resetState
  }
})