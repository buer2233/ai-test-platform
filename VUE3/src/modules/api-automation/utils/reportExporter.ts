/**
 * 报告导出工具
 * 支持 PDF、Excel、JSON、图片等多种格式导出
 */

import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

/**
 * 导出配置接口
 */
export interface ExportConfig {
  filename?: string
  title?: string
  author?: string
  subject?: string
  keywords?: string
  creator?: string
}

/**
 * 报告数据接口
 */
export interface ReportData {
  report: any
  statistics: {
    total: number
    passed: number
    failed: number
    skipped: number
    passRate: number
  }
  testResults: any[]
}

/**
 * 报告导出器类
 */
export class ReportExporter {
  /**
   * 导出为PDF
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

      // 设置PDF元数据
      pdf.setProperties({
        title,
        author,
        subject,
        creator
      })

      // 添加图片
      const imgData = canvas.toDataURL('image/jpeg', 0.98)
      let position = 0

      // 第一页
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      // 如果内容超过一页，添加新页
      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      // 保存PDF
      pdf.save(filename)
    } catch (error) {
      console.error('PDF export error:', error)
      throw new Error('PDF导出失败')
    }
  }

  /**
   * 导出为Excel
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
      // 创建工作簿
      const workbook = XLSX.utils.book_new()

      // 1. 概览工作表
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

      // 2. 详细结果工作表
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

        // 3. 失败用例工作表（如果有）
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

      // 导出
      XLSX.writeFile(workbook, filename)
    } catch (error) {
      console.error('Excel export error:', error)
      throw new Error('Excel导出失败')
    }
  }

  /**
   * 导出为JSON
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
      console.error('JSON export error:', error)
      throw new Error('JSON导出失败')
    }
  }

  /**
   * 导出为图片 (PNG/JPEG)
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
      console.error('Image export error:', error)
      throw new Error('图片导出失败')
    }
  }

  /**
   * 导出为CSV (仅测试结果)
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

      // CSV头
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

      // CSV数据
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

      // 组合CSV内容
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n')

      // 添加BOM以支持中文
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
      saveAs(blob, filename)
    } catch (error) {
      console.error('CSV export error:', error)
      throw new Error('CSV导出失败')
    }
  }

  /**
   * 导出统计图表为图片
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
      const url = chartInstance.getDataURL({
        type: format,
        pixelRatio: 2,
        backgroundColor: '#fff'
      })

      // 将base64转换为blob
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
      console.error('Chart export error:', error)
      throw new Error('图表导出失败')
    }
  }

  /**
   * 导出所有图表为PDF
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
      const pageWidth = 297 // A4横向宽度
      const pageHeight = 210 // A4横向高度
      const margin = 10

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

        // 如果不是第一页，添加新页
        if (i > 0) {
          pdf.addPage()
        }

        const imgData = canvas.toDataURL('image/jpeg', 0.98)
        pdf.addImage(imgData, 'JPEG', margin, margin, imgWidth, Math.min(imgHeight, pageHeight - 2 * margin))

        position += imgHeight
      }

      pdf.save(filename)
    } catch (error) {
      console.error('Charts PDF export error:', error)
      throw new Error('图表PDF导出失败')
    }
  }
}

/**
 * 默认导出配置
 */
export const defaultExportConfig: ExportConfig = {
  filename: `report_${Date.now()}`,
  title: 'API测试报告',
  author: 'API自动化测试平台',
  subject: 'API自动化测试执行报告',
  creator: 'API自动化测试平台'
}

/**
 * 导出格式类型
 */
export type ExportFormat = 'pdf' | 'excel' | 'json' | 'png' | 'jpeg' | 'csv'

/**
 * 获取导出文件扩展名
 */
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

/**
 * 生成导出文件名
 */
export function generateExportFilename(
  format: ExportFormat,
  prefix: string = 'report'
): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  return `${prefix}_${timestamp}${getExportExtension(format)}`
}
