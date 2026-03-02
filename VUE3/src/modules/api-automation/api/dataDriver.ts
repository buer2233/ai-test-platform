/**
 * 数据驱动 API
 *
 * 管理数据驱动测试的数据源配置。
 * 支持 JSON、CSV、Excel、数据库等多种数据源类型，
 * 通过参数化驱动测试用例的多轮执行。
 */

import { http } from '../../../shared/utils/http'
import type { ApiDataDriver } from '../types/dataDriver'

export const dataDriverApi = {
  /** 获取数据驱动配置列表 */
  getDataDrivers(params?: any) {
    return http.get<{ results: ApiDataDriver[], count: number }>('/data-drivers/', params)
  },

  /** 获取单个数据驱动配置详情 */
  getDataDriver(id: number) {
    return http.get<ApiDataDriver>(`/data-drivers/${id}/`)
  },

  /** 创建数据驱动配置 */
  createDataDriver(data: any) {
    return http.post<ApiDataDriver>('/data-drivers/', data)
  },

  /** 更新数据驱动配置 */
  updateDataDriver(id: number, data: Partial<ApiDataDriver>) {
    return http.patch<ApiDataDriver>(`/data-drivers/${id}/`, data)
  },

  /** 删除数据驱动配置 */
  deleteDataDriver(id: number) {
    return http.delete(`/data-drivers/${id}/`)
  },

  /** 预览数据源的实际内容（用于配置验证） */
  previewData(id: number) {
    return http.post(`/data-drivers/${id}/preview_data/`)
  },

  /** 从文件导入数据（支持 CSV / Excel 格式） */
  importData(formData: FormData) {
    return http.post('/data-drivers/import_data/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}