import { http } from '../../../shared/utils/http'
import type { ApiDataDriver } from '../types/dataDriver'

export const dataDriverApi = {
  // 获取数据驱动列表
  getDataDrivers(params?: any) {
    return http.get<{ results: ApiDataDriver[], count: number }>('/data-drivers/', params)
  },

  // 获取单个数据驱动
  getDataDriver(id: number) {
    return http.get<ApiDataDriver>(`/data-drivers/${id}/`)
  },

  // 创建数据驱动
  createDataDriver(data: any) {
    return http.post<ApiDataDriver>('/data-drivers/', data)
  },

  // 更新数据驱动
  updateDataDriver(id: number, data: Partial<ApiDataDriver>) {
    return http.patch<ApiDataDriver>(`/data-drivers/${id}/`, data)
  },

  // 删除数据驱动
  deleteDataDriver(id: number) {
    return http.delete(`/data-drivers/${id}/`)
  },

  // 预览数据内容
  previewData(id: number) {
    return http.post(`/data-drivers/${id}/preview_data/`)
  },

  // 导入数据
  importData(formData: FormData) {
    return http.post('/data-drivers/import_data/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}