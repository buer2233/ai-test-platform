import { defineStore } from 'pinia'
import { testCaseApi } from '../api/testCase'
import type { ApiTestCase, ApiTestCaseCreate, ApiTestCaseList } from '../types/testCase'

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
    testCaseOptions: (state) => {
      return state.testCases.map(testCase => ({
        label: testCase.name,
        value: testCase.id
      }))
    }
  },

  actions: {
    // 获取测试用例列表
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

    // 获取单个测试用例
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

    // 创建测试用例
    async createTestCase(data: ApiTestCaseCreate) {
      try {
        const testCase = await testCaseApi.createTestCase(data)
        // 转换为列表格式
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

    // 更新测试用例
    async updateTestCase(id: number, data: Partial<ApiTestCaseCreate>) {
      try {
        const updatedTestCase = await testCaseApi.updateTestCase(id, data)
        // 更新列表中的数据
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

    // 删除测试用例
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

    // 克隆测试用例
    async cloneTestCase(id: number, name: string) {
      try {
        const clonedTestCase = await testCaseApi.cloneTestCase(id, { name })
        // 转换为列表格式
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

    // 获取测试用例统计
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

    // 清除当前测试用例
    clearCurrentTestCase() {
      this.currentTestCase = null
    },

    // 根据项目ID过滤测试用例
    getTestCasesByProject(projectId: number) {
      return this.testCases.filter(tc => tc.project === projectId)
    },

    // 根据集合ID过滤测试用例
    getTestCasesByCollection(collectionId: number) {
      return this.testCases.filter(tc => tc.collection === collectionId)
    }
  }
})