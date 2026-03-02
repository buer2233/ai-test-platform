/**
 * 测试环境 Store
 *
 * 管理测试环境的状态：环境列表、当前选中环境、默认环境等。
 * 提供环境的增删改查、设为默认、连接测试等操作。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

import { environmentApi } from '../api/environment'
import type { ApiTestEnvironment, EnvironmentCreate } from '../types/environment'

export const useEnvironmentStore = defineStore('environment', () => {
  // ==================== 状态 ====================

  /** 环境列表 */
  const environments = ref<ApiTestEnvironment[]>([])
  /** 当前选中的环境 */
  const currentEnvironment = ref<ApiTestEnvironment | null>(null)
  /** 全局加载状态 */
  const loading = ref(false)
  /** 数据总条数（分页用） */
  const total = ref(0)

  // ==================== 计算属性 ====================

  /** 转换为下拉选项格式（用于表单选择器） */
  const environmentOptions = computed(() => {
    return environments.value.map(env => ({
      label: env.name,
      value: env.id,
      description: env.description
    }))
  })

  /** 获取当前项目的默认环境 */
  const defaultEnvironment = computed(() => {
    return environments.value.find(env => env.is_default) || null
  })

  // ==================== 异步操作 ====================
  const fetchEnvironments = async (params?: any) => {
    loading.value = true
    try {
      const response = await environmentApi.getEnvironments(params)
      environments.value = response.results
      total.value = response.count
    } catch (error) {
      ElMessage.error('获取环境列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchEnvironment = async (id: number) => {
    loading.value = true
    try {
      const response = await environmentApi.getEnvironment(id)
      currentEnvironment.value = response
      return response
    } catch (error) {
      ElMessage.error('获取环境详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createEnvironment = async (data: EnvironmentCreate) => {
    loading.value = true
    try {
      const response = await environmentApi.createEnvironment(data)
      environments.value.push(response)
      ElMessage.success('环境创建成功')
      return response
    } catch (error) {
      ElMessage.error('环境创建失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateEnvironment = async (id: number, data: Partial<ApiTestEnvironment>) => {
    loading.value = true
    try {
      const response = await environmentApi.updateEnvironment(id, data)
      const index = environments.value.findIndex(env => env.id === id)
      if (index !== -1) {
        environments.value[index] = response
      }
      if (currentEnvironment.value?.id === id) {
        currentEnvironment.value = response
      }
      ElMessage.success('环境更新成功')
      return response
    } catch (error) {
      ElMessage.error('环境更新失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteEnvironment = async (id: number) => {
    loading.value = true
    try {
      await environmentApi.deleteEnvironment(id)
      const index = environments.value.findIndex(env => env.id === id)
      if (index !== -1) {
        environments.value.splice(index, 1)
      }
      if (currentEnvironment.value?.id === id) {
        currentEnvironment.value = null
      }
      ElMessage.success('环境删除成功')
    } catch (error) {
      ElMessage.error('环境删除失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const setDefault = async (id: number) => {
    loading.value = true
    try {
      await environmentApi.setDefault(id)
      // 更新所有环境的默认状态
      environments.value.forEach(env => {
        env.is_default = env.id === id
      })
      ElMessage.success('默认环境设置成功')
    } catch (error) {
      ElMessage.error('设置默认环境失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const testConnection = async (id: number) => {
    loading.value = true
    try {
      const response = await environmentApi.testConnection(id)
      if (response.status === 'success') {
        ElMessage.success(`连接测试成功，响应时间: ${response.response_time}ms`)
      } else {
        ElMessage.error(`连接测试失败: ${response.message}`)
      }
      return response
    } catch (error) {
      ElMessage.error('连接测试失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const resetState = () => {
    environments.value = []
    currentEnvironment.value = null
    loading.value = false
    total.value = 0
  }

  return {
    // 状态
    environments,
    currentEnvironment,
    loading,
    total,

    // 计算属性
    environmentOptions,
    defaultEnvironment,

    // 方法
    fetchEnvironments,
    fetchEnvironment,
    createEnvironment,
    updateEnvironment,
    deleteEnvironment,
    setDefault,
    testConnection,
    resetState
  }
})