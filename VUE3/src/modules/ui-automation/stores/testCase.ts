/**
 * 测试用例状态管理（Pinia Store）
 *
 * 管理 UI 自动化测试用例的列表、当前查看的用例详情，
 * 提供按项目、标签和启用状态筛选等派生数据。
 */

import { defineStore } from 'pinia'

import { uiTestCaseApi } from '../api/testCase'
import type { UiTestCase, UiTestCaseCreate, UiTestCaseUpdate } from '../types/testCase'

/** 测试用例 Store 的状态类型定义 */
interface TestCaseState {
  /** 用例列表 */
  testCases: UiTestCase[]
  /** 当前查看的用例详情 */
  currentTestCase: UiTestCase | null
  /** 列表加载状态 */
  loading: boolean
  /** 列表总数（用于分页） */
  total: number
}

export const useUiTestCaseStore = defineStore('uiTestCase', {
  state: (): TestCaseState => ({
    testCases: [],
    currentTestCase: null,
    loading: false,
    total: 0
  }),

  getters: {
    /** 筛选出已启用的测试用例 */
    activeTestCases: (state) => {
      return state.testCases.filter(tc => tc.is_active)
    },

    /** 按项目 ID 筛选测试用例 */
    testCasesByProject: (state) => (projectId: number) => {
      return state.testCases.filter(tc => tc.project === projectId)
    },

    /** 按标签筛选测试用例 */
    testCasesByTag: (state) => (tag: string) => {
      return state.testCases.filter(tc => tc.tags.includes(tag))
    }
  },

  actions: {
    /** 获取测试用例列表（支持分页和筛选参数） */
    async fetchTestCases(params?: any) {
      this.loading = true
      try {
        const response = await uiTestCaseApi.getTestCases(params)
        this.testCases = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch UI test cases:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个测试用例详情并设为当前用例 */
    async fetchTestCase(id: number) {
      this.loading = true
      try {
        const testCase = await uiTestCaseApi.getTestCase(id)
        this.currentTestCase = testCase
        return testCase
      } catch (error) {
        console.error('Failed to fetch UI test case:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建测试用例并插入列表头部 */
    async createTestCase(data: UiTestCaseCreate) {
      try {
        const testCase = await uiTestCaseApi.createTestCase(data)
        this.testCases.unshift(testCase)
        this.total += 1
        return testCase
      } catch (error) {
        console.error('Failed to create UI test case:', error)
        throw error
      }
    },

    /** 更新测试用例信息并同步列表和当前用例 */
    async updateTestCase(id: number, data: UiTestCaseUpdate) {
      try {
        const updatedTestCase = await uiTestCaseApi.updateTestCase(id, data)
        const index = this.testCases.findIndex(tc => tc.id === id)
        if (index !== -1) {
          this.testCases[index] = updatedTestCase
        }
        if (this.currentTestCase?.id === id) {
          this.currentTestCase = updatedTestCase
        }
        return updatedTestCase
      } catch (error) {
        console.error('Failed to update UI test case:', error)
        throw error
      }
    },

    /** 删除测试用例并从列表中移除 */
    async deleteTestCase(id: number) {
      try {
        await uiTestCaseApi.deleteTestCase(id)
        this.testCases = this.testCases.filter(tc => tc.id !== id)
        this.total -= 1
        if (this.currentTestCase?.id === id) {
          this.currentTestCase = null
        }
      } catch (error) {
        console.error('Failed to delete UI test case:', error)
        throw error
      }
    },

    /** 复制测试用例（后端生成副本）并插入列表头部 */
    async copyTestCase(id: number) {
      try {
        const newTestCase = await uiTestCaseApi.copyTestCase(id)
        this.testCases.unshift(newTestCase)
        this.total += 1
        return newTestCase
      } catch (error) {
        console.error('Failed to copy UI test case:', error)
        throw error
      }
    },

    /** 清除当前查看的测试用例 */
    clearCurrentTestCase() {
      this.currentTestCase = null
    }
  }
})
