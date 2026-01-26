/**
 * UI自动化测试截图类型定义
 */

export interface UiScreenshot {
  id: number
  project: number
  project_name?: string
  execution: number
  execution_id?: number
  test_case_name?: string
  description: string
  image_path: string
  image_data: string
  timestamp: string
  created_at: string
}

export interface ScreenshotCreate {
  project: number
  execution: number
  description: string
  image_data: string
  timestamp: string
}
