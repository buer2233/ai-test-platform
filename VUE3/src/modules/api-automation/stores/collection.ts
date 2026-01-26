import { defineStore } from 'pinia'
import { collectionApi } from '../api/collection'
import type { ApiCollection, ApiCollectionCreate } from '../types/collection'

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
    collectionOptions: (state) => {
      return state.collections.map(collection => ({
        label: collection.name,
        value: collection.id
      }))
    }
  },

  actions: {
    // 获取集合列表
    async fetchCollections(params?: any) {
      this.loading = true
      try {
        const response = await collectionApi.getCollections(params)
        this.collections = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch collections:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个集合
    async fetchCollection(id: number) {
      this.loading = true
      try {
        const collection = await collectionApi.getCollection(id)
        this.currentCollection = collection
        return collection
      } catch (error) {
        console.error('Failed to fetch collection:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建集合
    async createCollection(data: ApiCollectionCreate) {
      try {
        const collection = await collectionApi.createCollection(data)
        this.collections.unshift(collection)
        this.total += 1
        return collection
      } catch (error) {
        console.error('Failed to create collection:', error)
        throw error
      }
    },

    // 更新集合
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
        console.error('Failed to update collection:', error)
        throw error
      }
    },

    // 删除集合
    async deleteCollection(id: number) {
      try {
        await collectionApi.deleteCollection(id)
        this.collections = this.collections.filter(c => c.id !== id)
        this.total -= 1
        if (this.currentCollection?.id === id) {
          this.currentCollection = null
        }
      } catch (error) {
        console.error('Failed to delete collection:', error)
        throw error
      }
    },

    // 获取集合的测试用例
    async fetchCollectionTestCases(id: number) {
      try {
        return await collectionApi.getCollectionTestCases(id)
      } catch (error) {
        console.error('Failed to fetch collection test cases:', error)
        throw error
      }
    },

    // 清除当前集合
    clearCurrentCollection() {
      this.currentCollection = null
    },

    // 根据项目ID过滤集合
    getCollectionsByProject(projectId: number) {
      return this.collections.filter(c => c.project === projectId)
    }
  }
})