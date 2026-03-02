/**
 * 报告导出工具
 *
 * 支持将测试报告导出为多种格式：
 * - PDF：通过 html2canvas 截取 DOM 元素，再嵌入 jsPDF 生成多页 PDF
 * - Excel：使用 xlsx 库生成包含概览、详细结果、失败用例三个工作表的 Excel 文件
 * - JSON：直接将报告数据序列化为 JSON 文件
 * - 图片（PNG/JPEG）：通过 html2canvas 将 DOM 元素导出为图片
 * - CSV：将测试结果导出为 CSV 文件（含 BOM 头以支持中文）
 * - 图表导出：支持将 ECharts 图表实例导出为图片或 PDF
 */

import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

// ==================== 类型定义 ====================

/** 导出配置选项，用于设置文件名、标题、作者等元数据 */
export interface ExportConfig {
  /** 导出文件名（含扩展名） */
  filename?: string
  /** 文档标题 */
  title?: string
  /** 文档作者 */
  author?: string
  /** 文档主题 */
  subject?: string
  /** 文档关键词 */
  keywords?: string
  /** 文档创建者 */
  creator?: string
}

/** 报告数据结构，包含报告基本信息、统计摘要和测试结果列表 */
export interface ReportData {
  /** 报告基本信息 */
  report: any
  /** 测试统计摘要 */
  statistics: {
    total: number
    passed: number
    failed: number
    skipped: number
    passRate: number
  }
  /** 测试结果详情列表 */
  testResults: any[]
}

// ==================== 报告导出器 ====================

/**
 * 报告导出器类
 *
 * 提供多种静态方法，支持将测试报告导出为不同格式。
 * 所有方法均为静态方法，无需实例化即可调用。
 */
export class ReportExporter {
  /**
   * 导出为 PDF 文件。
   * 将 DOM 元素通过 html2canvas 截取为图片，再按 A4 纸张尺寸分页嵌入 PDF。
   */
  static async exportToPDF(
    element: HTMLElement,
    config: ExportConfig = {}
  ): Promise<void> {
    const {
      filename = `report_${Date.now()}.pdf`,
      title = '测试报告',
      author = 'API自动化测试平台',
      subject = 'API测试执行报告'
    } = config

    try {
      // 创建canvas
      const canvas = await html2canvas(element, {
        scale: 2, // 提高清晰度
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      })

      // 计算PDF尺寸
      const imgWidth = 210 // A4宽度 (mm)
      const pageHeight = 297 // A4高度 (mm)
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      let heightLeft = imgHeight

      // 创建PDF
      const pdf = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4'
      })

      // 设置 PDF 文档元数据
      pdf.setProperties({
        title,
        author,
        subject,
        creator: config.creator
      })

      // 将 canvas 转为 JPEG 图片数据
      const imgData = canvas.toDataURL('image/jpeg', 0.98)
      let position = 0

      // 添加第一页内容
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      // 内容超过一页时，循环添加新页
      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      // 保存 PDF 文件
      pdf.save(filename)
    } catch (error) {
      console.error('PDF 导出失败:', error)
      throw new Error('PDF导出失败')
    }
  }

  /**
   * 导出为 Excel 文件。
   * 生成包含三个工作表的 Excel 文件：
   * 1. 概览：报告基本信息和统计数据
   * 2. 详细结果：所有测试用例的执行结果
   * 3. 失败用例：仅包含失败的测试用例及其断言详情
   */
  static exportToExcel(
    data: ReportData,
    config: ExportConfig = {}
  ): void {
    const {
      filename = `report_${Date.now()}.xlsx`,
      title = '测试报告'
    } = config

    try {
      // 创建 Excel 工作簿
      const workbook = XLSX.utils.book_new()

      // 工作表 1：概览信息
      const overviewData = [
        ['测试报告概览'],
        ['报告名称', data.report?.name || '未命名'],
        ['生成时间', new Date().toLocaleString()],
        ['测试环境', data.report?.environment_name || '-'],
        [''],
        ['统计信息'],
        ['总用例数', data.statistics.total],
        ['通过数', data.statistics.passed],
        ['失败数', data.statistics.failed],
        ['跳过数', data.statistics.skipped],
        ['通过率', `${data.statistics.passRate}%`]
      ]

      const overviewSheet = XLSX.utils.aoa_to_sheet(overviewData)

      // 设置列宽
      overviewSheet['!cols'] = [{ wch: 20 }, { wch: 30 }]

      XLSX.utils.book_append_sheet(workbook, overviewSheet, '概览')

      // 工作表 2：详细测试结果
      if (data.testResults && data.testResults.length > 0) {
        const resultsData = [
          [
            '用例名称',
            '请求方法',
            '请求URL',
            '状态',
            '状态码',
            '响应时间(ms)',
            '响应大小(B)',
            '执行时间',
            '错误信息'
          ]
        ]

        data.testResults.forEach(result => {
          resultsData.push([
            result.test_case_name || '-',
            result.test_case_method || '-',
            result.test_case_url || '-',
            result.status || '-',
            result.response_status || '-',
            result.response_time || '-',
            result.response_size || '-',
            result.start_time ? new Date(result.start_time).toLocaleString() : '-',
            result.error_message || '-'
          ])
        })

        const resultsSheet = XLSX.utils.aoa_to_sheet(resultsData)

        // 设置列宽
        resultsSheet['!cols'] = [
          { wch: 30 },
          { wch: 10 },
          { wch: 50 },
          { wch: 10 },
          { wch: 10 },
          { wch: 15 },
          { wch: 15 },
          { wch: 25 },
          { wch: 50 }
        ]

        XLSX.utils.book_append_sheet(workbook, resultsSheet, '详细结果')

        // 工作表 3：失败用例（仅在有失败时生成）
        const failedCases = data.testResults.filter(r => r.status === 'FAILED')
        if (failedCases.length > 0) {
          const failedData = [
            ['失败用例名称', '请求URL', '状态码', '错误信息', '断言结果']
          ]

          failedCases.forEach(result => {
            failedData.push([
              result.test_case_name || '-',
              result.test_case_url || '-',
              result.response_status || '-',
              result.error_message || '-',
              result.assertion_results
                ? result.assertion_results
                    .filter((a: any) => !a.passed)
                    .map((a: any) => `${a.assertion_type}: ${a.message}`)
                    .join('; ')
                : '-'
            ])
          })

          const failedSheet = XLSX.utils.aoa_to_sheet(failedData)
          failedSheet['!cols'] = [{ wch: 30 }, { wch: 50 }, { wch: 10 }, { wch: 30 }, { wch: 50 }]

          XLSX.utils.book_append_sheet(workbook, failedSheet, '失败用例')
        }
      }

      // 导出 Excel 文件
      XLSX.writeFile(workbook, filename)
    } catch (error) {
      console.error('Excel 导出失败:', error)
      throw new Error('Excel导出失败')
    }
  }

  /**
   * 导出为 JSON 文件。
   * 将报告数据序列化为格式化的 JSON 字符串并保存。
   */
  static exportToJSON(
    data: ReportData,
    config: ExportConfig = {}
  ): void {
    const { filename = `report_${Date.now()}.json` } = config

    try {
      const jsonStr = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' })
      saveAs(blob, filename)
    } catch (error) {
      console.error('JSON 导出失败:', error)
      throw new Error('JSON导出失败')
    }
  }

  /**
   * 导出为图片（PNG 或 JPEG）。
   * 通过 html2canvas 将指定 DOM 元素渲染为图片并下载。
   */
  static async exportToImage(
    element: HTMLElement,
    config: ExportConfig & { format?: 'png' | 'jpeg'; quality?: number } = {}
  ): Promise<void> {
    const {
      filename = `report_${Date.now()}.png`,
      format = 'png',
      quality = 1.0
    } = config

    try {
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      })

      canvas.toBlob(blob => {
        if (blob) {
          saveAs(blob, filename)
        }
      }, `image/${format}`, quality)
    } catch (error) {
      console.error('图片导出失败:', error)
      throw new Error('图片导出失败')
    }
  }

  /**
   * 导出为 CSV 文件（仅测试结果数据）。
   * 自动添加 UTF-8 BOM 头以确保 Excel 中正确显示中文。
   */
  static exportToCSV(
    data: ReportData,
    config: ExportConfig = {}
  ): void {
    const { filename = `report_${Date.now()}.csv` } = config

    try {
      if (!data.testResults || data.testResults.length === 0) {
        throw new Error('没有测试结果数据')
      }

      // CSV 表头
      const headers = [
        '用例名称',
        '请求方法',
        '请求URL',
        '状态',
        '状态码',
        '响应时间(ms)',
        '响应大小(B)',
        '执行时间',
        '错误信息'
      ]

      // CSV 数据行（双引号转义处理）
      const rows = data.testResults.map(result => [
        `"${(result.test_case_name || '').replace(/"/g, '""')}"`,
        `"${(result.test_case_method || '').replace(/"/g, '""')}"`,
        `"${(result.test_case_url || '').replace(/"/g, '""')}"`,
        `"${(result.status || '').replace(/"/g, '""')}"`,
        `"${(result.response_status || '').replace(/"/g, '""')}"`,
        `"${(result.response_time || '').replace(/"/g, '""')}"`,
        `"${(result.response_size || '').replace(/"/g, '""')}"`,
        `"${(result.start_time ? new Date(result.start_time).toLocaleString() : '').replace(/"/g, '""')}"`,
        `"${(result.error_message || '').replace(/"/g, '""')}"`
      ])

      // 组合完整的 CSV 内容
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n')

      // 添加 UTF-8 BOM 头以确保中文在 Excel 中正确显示
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
      saveAs(blob, filename)
    } catch (error) {
      console.error('CSV 导出失败:', error)
      throw new Error('CSV导出失败')
    }
  }

  /**
   * 将 ECharts 图表实例导出为图片。
   * 调用图表实例的 getDataURL 方法获取 base64 数据，再转换为 Blob 下载。
   */
  static async exportChartToImage(
    chartInstance: any,
    config: ExportConfig & { format?: 'png' | 'jpeg'; quality?: number } = {}
  ): Promise<void> {
    const {
      filename = `chart_${Date.now()}.png`,
      format = 'png',
      quality = 1.0
    } = config

    try {
      // 从图表实例获取 base64 编码的图片数据
      const url = chartInstance.getDataURL({
        type: format,
        pixelRatio: 2,
        backgroundColor: '#fff'
      })

      // 将 base64 数据转换为 Blob 对象
      const arr = url.split(',')
      const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/png'
      const bstr = atob(arr[1])
      let n = bstr.length
      const u8arr = new Uint8Array(n)

      while (n--) {
        u8arr[n] = bstr.charCodeAt(n)
      }

      const blob = new Blob([u8arr], { type: mime })
      saveAs(blob, filename)
    } catch (error) {
      console.error('图表导出失败:', error)
      throw new Error('图表导出失败')
    }
  }

  /**
   * 将多个图表容器导出为横向 A4 的 PDF 文件。
   * 每个图表容器占一页，通过 html2canvas 逐一截取并嵌入 PDF。
   */
  static async exportChartsToPDF(
    chartContainers: HTMLElement[],
    config: ExportConfig = {}
  ): Promise<void> {
    const {
      filename = `charts_${Date.now()}.pdf`,
      title = '测试报告图表'
    } = config

    try {
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4'
      })

      pdf.setProperties({ title, author: 'API自动化测试平台' })

      let position = 0
      const pageWidth = 297  // A4 横向宽度（mm）
      const pageHeight = 210 // A4 横向高度（mm）
      const margin = 10      // 页面边距（mm）

      for (let i = 0; i < chartContainers.length; i++) {
        const container = chartContainers[i]

        const canvas = await html2canvas(container, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff'
        })

        const imgWidth = pageWidth - 2 * margin
        const imgHeight = (canvas.height * imgWidth) / canvas.width

        // 非第一页时添加新页
        if (i > 0) {
          pdf.addPage()
        }

        const imgData = canvas.toDataURL('image/jpeg', 0.98)
        pdf.addImage(imgData, 'JPEG', margin, margin, imgWidth, Math.min(imgHeight, pageHeight - 2 * margin))

        position += imgHeight
      }

      pdf.save(filename)
    } catch (error) {
      console.error('图表 PDF 导出失败:', error)
      throw new Error('图表PDF导出失败')
    }
  }
}

// ==================== 导出工具函数 ====================

/** 默认导出配置 */
export const defaultExportConfig: ExportConfig = {
  filename: `report_${Date.now()}`,
  title: 'API测试报告',
  author: 'API自动化测试平台',
  subject: 'API自动化测试执行报告',
  creator: 'API自动化测试平台'
}

/** 支持的导出格式类型 */
export type ExportFormat = 'pdf' | 'excel' | 'json' | 'png' | 'jpeg' | 'csv'

/** 根据导出格式获取对应的文件扩展名 */
export function getExportExtension(format: ExportFormat): string {
  const extensions: Record<ExportFormat, string> = {
    pdf: '.pdf',
    excel: '.xlsx',
    json: '.json',
    png: '.png',
    jpeg: '.jpg',
    csv: '.csv'
  }
  return extensions[format] || '.pdf'
}

/** 根据导出格式和前缀生成带时间戳的文件名 */
export function generateExportFilename(
  format: ExportFormat,
  prefix: string = 'report'
): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  return `${prefix}_${timestamp}${getExportExtension(format)}`
}
