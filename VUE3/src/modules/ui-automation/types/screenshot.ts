/**
 * UI自动化测试截图相关类型定义
 *
 * 包含截图记录和创建参数。
 * 截图在 browser_use 执行过程中自动生成，关联到具体的执行记录。
 */

/** 截图完整信息（对应后端 UiScreenshot 模型） */
export interface UiScreenshot {
  id: number
  project: number
  project_name?: string
  execution: number
  execution_id?: number
  test_case_name?: string
  /** 截图描述（通常为当前执行步骤的目标说明） */
  description: string
  /** 截图在服务端的文件路径 */
  image_path: string
  /** Base64 编码的图片数据 */
  image_data: string
  /** 截图时间戳 */
  timestamp: string
  created_at: string
}

/** 创建截图所需参数 */
export interface ScreenshotCreate {
  project: number
  execution: number
  description: string
  image_data: string
  timestamp: string
}
