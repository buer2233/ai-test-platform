/**
 * 测试用例 Store
 *
 * 管理测试用例的状态：用例列表、当前选中用例、统计数据等。
 * 提供用例的增删改查、克隆、统计查询，以及按项目/集合筛选等操作。
 */

import { defineStore } from 'pinia'
import { testCaseApi } from '../api/testCase'
import type { ApiTestCase, ApiTestCaseCreate, ApiTestCaseList } from '../types/testCase'

/** 测试用例状态接口 */
interface TestCaseState {
  testCases: ApiTestCaseList[]
  currentTestCase: ApiTestCase | null
  loading: boolean
  total: number
  statistics: any
}

export const useTestCaseStore = defineStore('testCase', {
  state: (): TestCaseState => ({
    testCases: [],
    currentTestCase: null,
    loading: false,
    total: 0,
    statistics: null
  }),

  getters: {
    /** 转换为下拉选项格式（用于表单选择器） */
    testCaseOptions: (state) => {
      return state.testCases.map(testCase => ({
        label: testCase.name,
        value: testCase.id
      }))
    }
  },

  actions: {
    /** 获取测试用例列表 */
    async fetchTestCases(params?: any) {
      this.loading = true
      try {
        const response = await testCaseApi.getTestCases(params)
        this.testCases = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch test cases:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个测试用例详情 */
    async fetchTestCase(id: number) {
      this.loading = true
      try {
        const testCase = await testCaseApi.getTestCase(id)
        this.currentTestCase = testCase
        return testCase
      } catch (error) {
        console.error('Failed to fetch test case:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建测试用例，将新用例转换为列表格式并插入顶部 */
    async createTestCase(data: ApiTestCaseCreate) {
      try {
        const testCase = await testCaseApi.createTestCase(data)
        // 将完整的用例数据转换为列表展示的精简格式
        const listItem: ApiTestCaseList = {
          id: testCase.id,
          name: testCase.name,
          project: testCase.project,
          project_name: testCase.project_name,
          collection: testCase.collection,
          collection_name: testCase.collection_name,
          method: testCase.method,
          url: testCase.url,
          created_time: testCase.created_time
        }
        this.testCases.unshift(listItem)
        this.total += 1
        return testCase
      } catch (error) {
        console.error('Failed to create test case:', error)
        throw error
      }
    },

    /** 更新测试用例，同步更新列表和当前选中项 */
    async updateTestCase(id: number, data: Partial<ApiTestCaseCreate>) {
      try {
        const updatedTestCase = await testCaseApi.updateTestCase(id, data)
        // 仅更新列表中显示的关键字段
        const index = this.testCases.findIndex(tc => tc.id === id)
        if (index !== -1) {
          this.testCases[index] = {
            ...this.testCases[index],
            name: updatedTestCase.name,
            method: updatedTestCase.method,
            url: updatedTestCase.url
          }
        }
        if (this.currentTestCase?.id === id) {
          this.currentTestCase = updatedTestCase
        }
        return updatedTestCase
      } catch (error) {
        console.error('Failed to update test case:', error)
        throw error
      }
    },

    /** 删除测试用例，同步从列表中移除 */
    async deleteTestCase(id: number) {
      try {
        await testCaseApi.deleteTestCase(id)
        this.testCases = this.testCases.filter(tc => tc.id !== id)
        this.total -= 1
        if (this.currentTestCase?.id === id) {
          this.currentTestCase = null
        }
      } catch (error) {
        console.error('Failed to delete test case:', error)
        throw error
      }
    },

    /** 克隆测试用例，将克隆的副本插入列表顶部 */
    async cloneTestCase(id: number, name: string) {
      try {
        const clonedTestCase = await testCaseApi.cloneTestCase(id, { name })
        // 将克隆的用例转换为列表展示的精简格式
        const listItem: ApiTestCaseList = {
          id: clonedTestCase.id,
          name: clonedTestCase.name,
          project: clonedTestCase.project,
          project_name: clonedTestCase.project_name,
          collection: clonedTestCase.collection,
          collection_name: clonedTestCase.collection_name,
          method: clonedTestCase.method,
          url: clonedTestCase.url,
          created_time: clonedTestCase.created_time
        }
        this.testCases.unshift(listItem)
        this.total += 1
        return clonedTestCase
      } catch (error) {
        console.error('Failed to clone test case:', error)
        throw error
      }
    },

    /** 获取测试用例全局统计数据 */
    async fetchStatistics() {
      try {
        const statistics = await testCaseApi.getTestCaseStatistics()
        this.statistics = statistics
        return statistics
      } catch (error) {
        console.error('Failed to fetch test case statistics:', error)
        throw error
      }
    },

    /** 清除当前选中的测试用例 */
    clearCurrentTestCase() {
      this.currentTestCase = null
    },

    /** 按项目 ID 筛选测试用例 */
    getTestCasesByProject(projectId: number) {
      return this.testCases.filter(tc => tc.project === projectId)
    },

    /** 按集合 ID 筛选测试用例 */
    getTestCasesByCollection(collectionId: number) {
      return this.testCases.filter(tc => tc.collection === collectionId)
    }
  }
})