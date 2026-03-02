/**
 * 集合 Store
 *
 * 管理测试集合的状态：列表数据、当前选中的集合、加载状态等。
 * 提供集合的增删改查操作，以及按项目筛选集合的便捷方法。
 */

import { defineStore } from 'pinia'
import { collectionApi } from '../api/collection'
import type { ApiCollection, ApiCollectionCreate } from '../types/collection'

/** 集合状态接口 */
interface CollectionState {
  collections: ApiCollection[]
  currentCollection: ApiCollection | null
  loading: boolean
  total: number
}

export const useCollectionStore = defineStore('collection', {
  state: (): CollectionState => ({
    collections: [],
    currentCollection: null,
    loading: false,
    total: 0
  }),

  getters: {
    /** 转换为下拉选项格式（用于表单选择器） */
    collectionOptions: (state) => {
      return state.collections.map(collection => ({
        label: collection.name,
        value: collection.id
      }))
    }
  },

  actions: {
    /** 获取集合列表 */
    async fetchCollections(params?: any) {
      this.loading = true
      try {
        const response = await collectionApi.getCollections(params)
        this.collections = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('获取集合列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个集合详情 */
    async fetchCollection(id: number) {
      this.loading = true
      try {
        const collection = await collectionApi.getCollection(id)
        this.currentCollection = collection
        return collection
      } catch (error) {
        console.error('获取集合详情失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建集合，并将新集合插入列表顶部 */
    async createCollection(data: ApiCollectionCreate) {
      try {
        const collection = await collectionApi.createCollection(data)
        this.collections.unshift(collection)
        this.total += 1
        return collection
      } catch (error) {
        console.error('创建集合失败:', error)
        throw error
      }
    },

    /** 更新集合信息，同步更新列表和当前选中项 */
    async updateCollection(id: number, data: Partial<ApiCollectionCreate>) {
      try {
        const updatedCollection = await collectionApi.updateCollection(id, data)
        const index = this.collections.findIndex(c => c.id === id)
        if (index !== -1) {
          this.collections[index] = updatedCollection
        }
        if (this.currentCollection?.id === id) {
          this.currentCollection = updatedCollection
        }
        return updatedCollection
      } catch (error) {
        console.error('更新集合失败:', error)
        throw error
      }
    },

    /** 删除集合，同步从列表中移除 */
    async deleteCollection(id: number) {
      try {
        await collectionApi.deleteCollection(id)
        this.collections = this.collections.filter(c => c.id !== id)
        this.total -= 1
        if (this.currentCollection?.id === id) {
          this.currentCollection = null
        }
      } catch (error) {
        console.error('删除集合失败:', error)
        throw error
      }
    },

    /** 获取集合下的测试用例列表 */
    async fetchCollectionTestCases(id: number) {
      try {
        return await collectionApi.getCollectionTestCases(id)
      } catch (error) {
        console.error('获取集合测试用例失败:', error)
        throw error
      }
    },

    /** 清除当前选中的集合 */
    clearCurrentCollection() {
      this.currentCollection = null
    },

    /** 按项目 ID 筛选集合 */
    getCollectionsByProject(projectId: number) {
      return this.collections.filter(c => c.project === projectId)
    }
  }
})