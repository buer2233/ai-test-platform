import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dataDriverApi } from '../api/dataDriver'
import type { ApiDataDriver, DataDriverCreate } from '../types/dataDriver'
import { ElMessage } from 'element-plus'

export const useDataDriverStore = defineStore('dataDriver', () => {
  // 状态
  const dataDrivers = ref<ApiDataDriver[]>([])
  const currentDataDriver = ref<ApiDataDriver | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // 计算属性
  const activeDataDrivers = computed(() => {
    return dataDrivers.value.filter(driver => driver.is_active)
  })

  const dataTypes = computed(() => [
    { label: 'JSON数据', value: 'JSON' },
    { label: 'CSV文件', value: 'CSV' },
    { label: 'Excel文件', value: 'EXCEL' },
    { label: '数据库', value: 'DATABASE' }
  ])

  // 方法
  const fetchDataDrivers = async (params?: any) => {
    loading.value = true
    try {
      const response = await dataDriverApi.getDataDrivers(params)
      dataDrivers.value = response.results
      total.value = response.count
    } catch (error) {
      ElMessage.error('获取数据驱动列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchDataDriver = async (id: number) => {
    loading.value = true
    try {
      const response = await dataDriverApi.getDataDriver(id)
      currentDataDriver.value = response
      return response
    } catch (error) {
      ElMessage.error('获取数据驱动详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createDataDriver = async (data: DataDriverCreate) => {
    loading.value = true
    try {
      const response = await dataDriverApi.createDataDriver(data)
      dataDrivers.value.unshift(response)
      ElMessage.success('数据驱动创建成功')
      return response
    } catch (error) {
      ElMessage.error('数据驱动创建失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateDataDriver = async (id: number, data: Partial<ApiDataDriver>) => {
    loading.value = true
    try {
      const response = await dataDriverApi.updateDataDriver(id, data)
      const index = dataDrivers.value.findIndex(driver => driver.id === id)
      if (index !== -1) {
        dataDrivers.value[index] = response
      }
      if (currentDataDriver.value?.id === id) {
        currentDataDriver.value = response
      }
      ElMessage.success('数据驱动更新成功')
      return response
    } catch (error) {
      ElMessage.error('数据驱动更新失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteDataDriver = async (id: number) => {
    loading.value = true
    try {
      await dataDriverApi.deleteDataDriver(id)
      const index = dataDrivers.value.findIndex(driver => driver.id === id)
      if (index !== -1) {
        dataDrivers.value.splice(index, 1)
      }
      if (currentDataDriver.value?.id === id) {
        currentDataDriver.value = null
      }
      ElMessage.success('数据驱动删除成功')
    } catch (error) {
      ElMessage.error('数据驱动删除失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const previewData = async (id: number) => {
    loading.value = true
    try {
      const response = await dataDriverApi.previewData(id)
      return response
    } catch (error) {
      ElMessage.error('预览数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const importData = async (formData: FormData) => {
    loading.value = true
    try {
      const response = await dataDriverApi.importData(formData)
      if (response.success) {
        ElMessage.success('数据导入成功')
      } else {
        ElMessage.warning(response.message || '数据导入完成，但存在警告')
      }
      return response
    } catch (error) {
      ElMessage.error('数据导入失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const resetState = () => {
    dataDrivers.value = []
    currentDataDriver.value = null
    loading.value = false
    total.value = 0
  }

  return {
    // 状态
    dataDrivers,
    currentDataDriver,
    loading,
    total,

    // 计算属性
    activeDataDrivers,
    dataTypes,

    // 方法
    fetchDataDrivers,
    fetchDataDriver,
    createDataDriver,
    updateDataDriver,
    deleteDataDriver,
    previewData,
    importData,
    resetState
  }
})