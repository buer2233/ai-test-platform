import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { HttpRequest, HttpResponse, KeyValueItem, Variable } from '../types/http'

export function useHttpExecutor() {
  const executing = ref(false)

  // 替换变量
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

  // 替换对象中的变量
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

  // 处理请求头
  const processHeaders = (headers: KeyValueItem[], variables: Variable[]) => {
    const processedHeaders: Record<string, string> = {}

    // 默认请求头
    processedHeaders['User-Agent'] = 'API-Automation-Platform/1.0'

    // 处理用户定义的请求头
    headers
      .filter(h => h.enabled !== false && h.key && h.value)
      .forEach(header => {
        const key = replaceVariables(header.key, variables)
        const value = replaceVariables(header.value, variables)
        processedHeaders[key] = value
      })

    return processedHeaders
  }

  // 处理查询参数
  const processParams = (params: KeyValueItem[], variables: Variable[]) => {
    const processedParams: Record<string, any> = {}

    params
      .filter(p => p.enabled !== false && p.key && p.value)
      .forEach(param => {
        const key = replaceVariables(param.key, variables)
        const value = replaceVariables(param.value, variables)

        // 尝试转换为数字
        const numValue = Number(value)
        processedParams[key] = isNaN(numValue) ? value : numValue
      })

    return processedParams
  }

  // 处理请求体
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

      case 'form':
        const formData: Record<string, any> = {}
        body.form
          .filter(f => f.enabled !== false && f.key && f.value)
          .forEach(field => {
            const key = replaceVariables(field.key, variables)
            const value = replaceVariables(field.value, variables)
            formData[key] = value
          })
        return formData

      case 'raw':
        return replaceVariables(body.raw, variables)

      case 'file':
        return body.files

      default:
        return null
    }
  }

  // 执行HTTP请求
  const executeHttpRequest = async (request: HttpRequest): Promise<HttpResponse> => {
    try {
      executing.value = true

      // 处理变量
      const processedBaseUrl = replaceVariables(request.baseUrl, request.variables)
      const processedUrl = replaceVariables(request.url, request.variables)
      const fullUrl = processBaseUrl + processedUrl

      // 构建请求选项
      const requestOptions: any = {
        method: request.method,
        url: '/api/v1/api-automation/test-execute/', // 后端执行接口
        data: {
          method: request.method,
          url: fullUrl,
          headers: processHeaders(request.headers, request.variables),
          params: processParams(request.params, request.variables),
          body: processBody(request, request.variables),
          settings: request.settings
        }
      }

      // 添加认证token（如果有）
      const token = localStorage.getItem('token')
      if (token) {
        requestOptions.headers = {
          ...requestOptions.headers,
          'Authorization': `Bearer ${token}`
        }
      }

      // 发送请求到后端执行
      const response = await fetch(requestOptions.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestOptions.data)
      })

      const responseData = await response.json()

      if (!response.ok) {
        throw new Error(responseData.message || '请求执行失败')
      }

      // 构建响应对象
      const httpResponse: HttpResponse = {
        status: responseData.status_code || 200,
        headers: responseData.headers || {},
        body: responseData.body || null,
        response_time: responseData.response_time || 0,
        body_size: responseData.body_size || 0
      }

      // 添加错误信息（如果有）
      if (responseData.error) {
        httpResponse.error = responseData.error
      }

      // 处理cookies
      if (responseData.cookies) {
        httpResponse.cookies = responseData.cookies
      }

      return httpResponse

    } catch (error) {
      console.error('HTTP请求执行失败:', error)

      // 返回错误响应
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

  // 批量执行请求
  const executeBatchRequests = async (requests: HttpRequest[]) => {
    const results: HttpResponse[] = []

    for (const request of requests) {
      const result = await executeHttpRequest(request)
      results.push(result)

      // 避免请求过于频繁
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    return results
  }

  // 取消正在执行的请求
  const cancelRequest = () => {
    // 这里可以添加取消请求的逻辑
    // 使用AbortController等API
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