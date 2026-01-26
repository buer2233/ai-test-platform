"""
HTTP请求执行引擎
负责执行HTTP请求并返回响应结果
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class HttpResponse:
    """HTTP响应对象"""

    def __init__(self):
        self.status_code: int = 0
        self.headers: Dict[str, str] = {}
        self.body: Any = None
        self.body_size: int = 0
        self.response_time: float = 0.0
        self.error: Optional[str] = None
        self.raw_response: Optional[requests.Response] = None


class HttpExecutor:
    """HTTP请求执行器"""

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'API-Automation-Platform/1.0'
        })

    def execute_request(
        self,
        method: str,
        url: str,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        global_variables: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """
        执行HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE, etc.)
            url: 请求路径
            base_url: 基础URL
            headers: 请求头
            params: URL参数
            body: 请求体
            global_variables: 全局变量，用于变量替换

        Returns:
            HttpResponse: 响应对象
        """
        response = HttpResponse()

        try:
            # 合并URL
            if base_url:
                full_url = urljoin(base_url.rstrip('/') + '/', url.lstrip('/'))
            else:
                full_url = url

            # 变量替换
            if global_variables:
                full_url = self._replace_variables(full_url, global_variables)
                headers = self._replace_variables_dict(headers, global_variables)
                params = self._replace_variables_dict(params, global_variables)
                body = self._replace_variables_dict(body, global_variables)

            # 准备请求参数
            request_headers = {}
            if headers:
                request_headers.update(headers)

            request_params = params or {}
            request_body = None

            # 记录请求开始时间
            start_time = time.time()

            # 根据方法处理请求体
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                if body is not None:
                    # 判断内容类型
                    content_type = request_headers.get('Content-Type', '')

                    if 'application/json' in content_type:
                        # JSON格式
                        request_body = json.dumps(body)
                        if 'Content-Type' not in request_headers:
                            request_headers['Content-Type'] = 'application/json'

                    elif 'application/x-www-form-urlencoded' in content_type:
                        # URL编码格式
                        if isinstance(body, dict):
                            request_body = body
                        else:
                            # 如果是字符串，尝试解析为字典
                            try:
                                parsed_body = {}
                                for pair in body.split('&'):
                                    if '=' in pair:
                                        key, value = pair.split('=', 1)
                                        parsed_body[key] = value
                                request_body = parsed_body
                            except:
                                request_body = {}
                        if 'Content-Type' not in request_headers:
                            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

                    elif 'multipart/form-data' in content_type:
                        # 表单数据格式（文件上传）
                        # 注意：requests库会自动设置Content-Type和boundary
                        if isinstance(body, dict):
                            # 检查是否有文件字段
                            files = {}
                            data = {}
                            for key, value in body.items():
                                if hasattr(value, 'read') or isinstance(value, tuple):
                                    # 文件字段
                                    files[key] = value
                                else:
                                    # 普通字段
                                    data[key] = value

                            if files:
                                # 使用files参数，让requests自动处理multipart
                                raw_response = self.session.request(
                                    method=method.upper(),
                                    url=full_url,
                                    headers={k: v for k, v in request_headers.items() if k.lower() != 'content-type'},
                                    params=request_params,
                                    files=files,
                                    data=data,
                                    timeout=self.timeout,
                                    verify=self.verify_ssl
                                )
                                # 跳过后续的通用处理，直接返回响应
                                response.response_time = round((time.time() - start_time) * 1000)
                                response.status_code = raw_response.status_code
                                response.headers = dict(raw_response.headers)
                                response.raw_response = raw_response

                                try:
                                    content_type = raw_response.headers.get('Content-Type', '')
                                    if 'application/json' in content_type:
                                        response.body = raw_response.json()
                                    else:
                                        response.body = raw_response.text
                                except (json.JSONDecodeError, ValueError):
                                    response.body = raw_response.text

                                response.body_size = len(raw_response.content)
                                logger.info(f"Response received: {response.status_code} in {response.response_time}ms")
                                return response
                            else:
                                request_body = body
                        else:
                            request_body = body
                    else:
                        # 默认处理，如果没有指定Content-Type，根据body类型自动判断
                        if isinstance(body, dict):
                            # 默认作为JSON处理
                            request_body = json.dumps(body)
                            if 'Content-Type' not in request_headers:
                                request_headers['Content-Type'] = 'application/json'
                        elif isinstance(body, str):
                            # 如果是字符串且包含=，可能是form数据
                            if '=' in body and '&' in body:
                                request_body = body
                                if 'Content-Type' not in request_headers:
                                    request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                            else:
                                request_body = body
                        else:
                            request_body = body

            # 发送请求
            logger.info(f"Executing {method} {full_url}")
            logger.debug(f"Headers: {request_headers}")
            logger.debug(f"Params: {request_params}")
            logger.debug(f"Body: {request_body}")

            raw_response = self.session.request(
                method=method.upper(),
                url=full_url,
                headers=request_headers,
                params=request_params,
                data=request_body,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # 计算响应时间
            response.response_time = round((time.time() - start_time) * 1000)  # 转换为毫秒

            # 设置响应信息
            response.status_code = raw_response.status_code
            response.headers = dict(raw_response.headers)
            response.raw_response = raw_response

            # 处理响应体
            try:
                content_type = raw_response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    response.body = raw_response.json()
                else:
                    response.body = raw_response.text
            except (json.JSONDecodeError, ValueError):
                response.body = raw_response.text

            response.body_size = len(raw_response.content)

            logger.info(f"Response received: {response.status_code} in {response.response_time}ms")

        except requests.exceptions.Timeout:
            response.error = f"Request timeout after {self.timeout} seconds"
            logger.error(f"Request timeout: {full_url}")

        except requests.exceptions.ConnectionError as e:
            response.error = f"Connection error: {str(e)}"
            logger.error(f"Connection error: {full_url} - {str(e)}")

        except requests.exceptions.RequestException as e:
            response.error = f"Request error: {str(e)}"
            logger.error(f"Request error: {full_url} - {str(e)}")

        except Exception as e:
            response.error = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error: {full_url} - {str(e)}")

        return response

    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        替换文本中的变量

        Args:
            text: 原始文本
            variables: 变量字典

        Returns:
            str: 替换后的文本
        """
        if not text or not variables:
            return text

        for key, value in variables.items():
            placeholder = f"${{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))

        return text

    def _replace_variables_dict(
        self,
        data: Optional[Dict[str, Any]],
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        递归替换字典中的变量

        Args:
            data: 原始数据
            variables: 变量字典

        Returns:
            Dict: 替换后的数据
        """
        if not data or not variables:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_variables(value, variables)
            elif isinstance(value, dict):
                result[key] = self._replace_variables_dict(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_variables(item, variables) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()