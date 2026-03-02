/**
 * HTTP 执行器组合式函数
 *
 * 提供客户端侧的 HTTP 请求处理逻辑，包括：
 * - 变量替换（支持 ${变量名} 语法）
 * - 请求头 / 查询参数 / 请求体的预处理
 * - 通过后端代理执行 HTTP 请求
 * - 批量执行和请求取消
 *
 * 注意：实际的 HTTP 请求通过后端 test-execute 接口转发，
 * 前端不直接发送目标请求，以避免 CORS 等问题。
 */

import { ref } from 'vue'
import type { HttpRequest, HttpResponse, KeyValueItem, Variable } from '../types/http'

export function useHttpExecutor() {
  /** 是否正在执行请求 */
  const executing = ref(false)

  // ==================== 变量替换工具 ====================

  /**
   * 将字符串中的 ${变量名} 替换为实际值。
   * 仅替换已启用的变量，未匹配的占位符保持原样。
   */
  const replaceVariables = (text: string, variables: Variable[]): string => {
    if (!text || !variables.length) return text

    const variableMap = new Map()
    variables
      .filter(v => v.enabled)
      .forEach(v => {
        variableMap.set(v.name, v.value)
      })

    return text.replace(/\$\{([^}]+)\}/g, (match, varName) => {
      return variableMap.get(varName) || match
    })
  }

  /**
   * 递归替换对象中所有字符串值里的变量占位符。
   * 支持数组、嵌套对象、字符串等多种数据类型。
   */
  const replaceVariablesInObject = (obj: any, variables: Variable[]): any => {
    if (!obj || !variables.length) return obj

    if (Array.isArray(obj)) {
      return obj.map(item => replaceVariablesInObject(item, variables))
    }

    if (typeof obj === 'object' && obj !== null) {
      const result: any = {}
      for (const [key, value] of Object.entries(obj)) {
        if (typeof value === 'string') {
          result[key] = replaceVariables(value, variables)
        } else if (typeof value === 'object') {
          result[key] = replaceVariablesInObject(value, variables)
        } else {
          result[key] = value
        }
      }
      return result
    }

    if (typeof obj === 'string') {
      return replaceVariables(obj, variables)
    }

    return obj
  }

  // ==================== 请求预处理 ====================

  /**
   * 处理请求头：合并默认 User-Agent 和用户自定义的请求头。
   * 过滤掉已禁用或键值为空的项。
   */
  const processHeaders = (headers: KeyValueItem[], variables: Variable[]) => {
    const processedHeaders: Record<string, string> = {}

    // 默认请求头
    processedHeaders['User-Agent'] = 'API-Automation-Platform/1.0'

    // 处理用户自定义的请求头
    headers
      .filter(h => h.enabled !== false && h.key && h.value)
      .forEach(header => {
        const key = replaceVariables(header.key, variables)
        const value = replaceVariables(header.value, variables)
        processedHeaders[key] = value
      })

    return processedHeaders
  }

  /**
   * 处理查询参数：过滤禁用项，替换变量，并尝试将纯数字字符串转为数字类型。
   */
  const processParams = (params: KeyValueItem[], variables: Variable[]) => {
    const processedParams: Record<string, any> = {}

    params
      .filter(p => p.enabled !== false && p.key && p.value)
      .forEach(param => {
        const key = replaceVariables(param.key, variables)
        const value = replaceVariables(param.value, variables)

        const numValue = Number(value)
        processedParams[key] = isNaN(numValue) ? value : numValue
      })

    return processedParams
  }

  /**
   * 处理请求体：根据 bodyType 解析不同格式的请求体。
   * - json: 尝试解析为 JSON 对象并替换变量，解析失败则作为字符串处理
   * - form: 处理表单键值对
   * - raw: 纯文本替换变量
   * - file: 直接传递文件列表
   * - none: 或 GET 等不需要 body 的方法返回 null
   */
  const processBody = (request: HttpRequest, variables: Variable[]) => {
    const { bodyType, body } = request

    if (bodyType === 'none' || !['POST', 'PUT', 'PATCH'].includes(request.method)) {
      return null
    }

    switch (bodyType) {
      case 'json':
        if (!body.json) return null
        try {
          const parsed = JSON.parse(body.json)
          return replaceVariablesInObject(parsed, variables)
        } catch {
          return replaceVariables(body.json, variables)
        }

      case 'form': {
        const formData: Record<string, any> = {}
        body.form
          .filter(f => f.enabled !== false && f.key && f.value)
          .forEach(field => {
            const key = replaceVariables(field.key, variables)
            const value = replaceVariables(field.value, variables)
            formData[key] = value
          })
        return formData
      }

      case 'raw':
        return replaceVariables(body.raw, variables)

      case 'file':
        return body.files

      default:
        return null
    }
  }

  // ==================== 请求执行 ====================

  /**
   * 执行单个 HTTP 请求。
   * 通过后端 test-execute 接口代理发送请求，返回标准化的响应对象。
   */
  const executeHttpRequest = async (request: HttpRequest): Promise<HttpResponse> => {
    try {
      executing.value = true

      // 处理变量替换
      const processedBaseUrl = replaceVariables(request.baseUrl, request.variables)
      const processedUrl = replaceVariables(request.url, request.variables)
      const fullUrl = processedBaseUrl + processedUrl

      // 构建发送给后端的请求数据
      const requestData = {
        method: request.method,
        url: fullUrl,
        headers: processHeaders(request.headers, request.variables),
        params: processParams(request.params, request.variables),
        body: processBody(request, request.variables),
        settings: request.settings
      }

      // 从 localStorage 获取认证 Token
      const token = localStorage.getItem('token')

      // 通过后端代理发送请求
      const response = await fetch('/api/v1/api-automation/test-execute/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestData)
      })

      const responseData = await response.json()

      if (!response.ok) {
        throw new Error(responseData.message || '请求执行失败')
      }

      // 构建标准化的响应对象
      const httpResponse: HttpResponse = {
        status: responseData.status_code || 200,
        headers: responseData.headers || {},
        body: responseData.body || null,
        response_time: responseData.response_time || 0,
        body_size: responseData.body_size || 0
      }

      // 附加可选字段
      if (responseData.error) {
        httpResponse.error = responseData.error
      }
      if (responseData.cookies) {
        httpResponse.cookies = responseData.cookies
      }

      return httpResponse

    } catch (error) {
      console.error('HTTP请求执行失败:', error)

      // 返回错误响应对象
      return {
        status: 0,
        headers: {},
        body: null,
        response_time: 0,
        body_size: 0,
        error: error instanceof Error ? error.message : '未知错误'
      }
    } finally {
      executing.value = false
    }
  }

  /**
   * 批量执行多个 HTTP 请求（串行执行）。
   * 每个请求之间间隔 100ms，避免对目标服务造成过大压力。
   */
  const executeBatchRequests = async (requests: HttpRequest[]) => {
    const results: HttpResponse[] = []

    for (const request of requests) {
      const result = await executeHttpRequest(request)
      results.push(result)

      // 请求间隔，避免过于频繁
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    return results
  }

  /** 取消正在执行的请求（当前为占位实现，后续可通过 AbortController 实现） */
  const cancelRequest = () => {
    executing.value = false
  }

  return {
    executing,
    executeHttpRequest,
    executeBatchRequests,
    cancelRequest,
    replaceVariables,
    replaceVariablesInObject,
    processHeaders,
    processParams,
    processBody
  }
}