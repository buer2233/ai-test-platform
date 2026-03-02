"""
HTTP请求执行引擎

负责构建、发送HTTP请求并封装响应结果。
支持多种Content-Type（JSON、表单、multipart文件上传），
以及请求URL/请求头/请求体中的变量占位符替换。
"""

import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import unquote, urljoin

import requests

logger = logging.getLogger(__name__)


class HttpResponse:
    """
    HTTP响应数据封装对象

    将 requests 库的原始响应统一封装为标准化的响应结构，
    便于断言引擎和提取引擎统一处理。
    """

    def __init__(self):
        self.status_code: int = 0               # HTTP状态码
        self.headers: Dict[str, str] = {}       # 响应头字典
        self.body: Any = None                   # 解析后的响应体（JSON对象或纯文本）
        self.body_size: int = 0                 # 响应体大小（字节）
        self.response_time: float = 0.0         # 响应耗时（毫秒）
        self.error: Optional[str] = None        # 请求错误信息（成功时为None）
        self.raw_response: Optional[requests.Response] = None  # requests原始响应对象


class HttpExecutor:
    """
    HTTP请求执行器

    通过 requests.Session 管理连接复用，支持：
    - 自动URL拼接（base_url + path）
    - 变量占位符替换（${variable_name} 格式）
    - 多种Content-Type自动处理
    - 超时控制和SSL验证配置
    """

    # 支持携带请求体的HTTP方法集合
    BODY_METHODS = {'POST', 'PUT', 'PATCH'}

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        """
        初始化HTTP执行器

        Args:
            timeout: 请求超时时间（秒），默认30秒
            verify_ssl: 是否验证SSL证书，默认True
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
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
        执行HTTP请求的主入口方法

        处理流程：
        1. 拼接完整URL（base_url + path）
        2. 替换所有参数中的变量占位符
        3. 根据Content-Type准备请求体
        4. 发送请求并封装响应

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE 等)
            url: 请求路径或完整URL
            base_url: 基础URL，与url拼接得到完整地址
            headers: 自定义请求头
            params: URL查询参数
            body: 请求体数据
            global_variables: 全局变量字典，用于替换 ${key} 占位符

        Returns:
            HttpResponse: 统一封装的响应对象
        """
        response = HttpResponse()

        try:
            # 步骤1：拼接完整URL
            full_url = self._build_full_url(base_url, url)

            # 步骤2：替换所有参数中的变量占位符
            if global_variables:
                full_url = self._replace_variables(full_url, global_variables)
                headers = self._replace_variables_dict(headers, global_variables)
                params = self._replace_variables_dict(params, global_variables)
                body = self._replace_variables_dict(body, global_variables)

            # 步骤3：准备请求头和参数
            request_headers = dict(headers) if headers else {}
            request_params = params or {}

            start_time = time.time()

            # 步骤4：处理multipart文件上传（需要特殊的请求发送方式）
            if method.upper() in self.BODY_METHODS and body is not None:
                content_type = request_headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    multipart_response = self._handle_multipart_request(
                        method, full_url, request_headers, request_params,
                        body, start_time, response
                    )
                    if multipart_response is not None:
                        return multipart_response

            # 步骤5：准备非multipart的请求体
            request_body = self._prepare_request_body(
                method, body, request_headers
            )

            # 步骤6：发送请求
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

            # 步骤7：封装响应数据
            response.response_time = round((time.time() - start_time) * 1000)
            response.status_code = raw_response.status_code
            response.headers = dict(raw_response.headers)
            response.raw_response = raw_response
            response.body = self._parse_response_body(raw_response)
            response.body_size = len(raw_response.content)

            logger.info(
                f"Response received: {response.status_code} "
                f"in {response.response_time}ms"
            )

        except requests.exceptions.Timeout:
            response.error = f"Request timeout after {self.timeout} seconds"
            logger.error(f"Request timeout: {url}")

        except requests.exceptions.ConnectionError as e:
            response.error = f"Connection error: {str(e)}"
            logger.error(f"Connection error: {url} - {str(e)}")

        except requests.exceptions.RequestException as e:
            response.error = f"Request error: {str(e)}"
            logger.error(f"Request error: {url} - {str(e)}")

        except Exception as e:
            response.error = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error: {url} - {str(e)}")

        return response

    def _build_full_url(self, base_url: str, url: str) -> str:
        """
        拼接完整URL

        当 base_url 存在时，将 base_url 和 url 拼接为完整地址；
        否则直接使用 url 作为完整地址。

        Args:
            base_url: 基础URL（如 https://api.example.com）
            url: 请求路径（如 /users/list）

        Returns:
            str: 拼接后的完整URL
        """
        if base_url:
            return urljoin(base_url.rstrip('/') + '/', url.lstrip('/'))
        return url

    def _prepare_request_body(
        self,
        method: str,
        body: Optional[Any],
        request_headers: Dict[str, str]
    ) -> Optional[Any]:
        """
        根据Content-Type和请求方法准备请求体

        处理逻辑：
        - GET/DELETE等方法不携带请求体
        - application/json: 序列化为JSON字符串
        - application/x-www-form-urlencoded: 解析为字典或保留原字符串
        - 无Content-Type时：字典默认按JSON处理，含&和=的字符串按表单处理

        Args:
            method: HTTP方法
            body: 原始请求体数据
            request_headers: 请求头字典（可能会被修改以补充Content-Type）

        Returns:
            处理后的请求体，可能为None、字符串或字典
        """
        if method.upper() not in self.BODY_METHODS or body is None:
            return None

        content_type = request_headers.get('Content-Type', '')

        # JSON格式
        if 'application/json' in content_type:
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/json'
            return json.dumps(body)

        # URL编码表单格式
        if 'application/x-www-form-urlencoded' in content_type:
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            return self._parse_form_body(body)

        # multipart在此之前已由 _handle_multipart_request 处理
        if 'multipart/form-data' in content_type:
            return body

        # 未指定Content-Type时，按数据类型自动推断
        return self._infer_body_format(body, request_headers)

    def _parse_form_body(self, body: Any) -> Any:
        """
        解析URL编码表单格式的请求体

        如果body已是字典则直接返回；如果是 "key1=val1&key2=val2" 格式
        的字符串，则解析为字典（同时进行URL解码，如 %40 -> @）。

        Args:
            body: 原始请求体

        Returns:
            解析后的字典或原始数据
        """
        if isinstance(body, dict):
            return body
        try:
            parsed_body = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed_body[unquote(key)] = unquote(value)
            return parsed_body
        except Exception:
            return {}

    def _infer_body_format(
        self,
        body: Any,
        request_headers: Dict[str, str]
    ) -> Any:
        """
        未指定Content-Type时，根据请求体数据类型自动推断格式

        - 字典类型：默认按JSON处理
        - 含 & 和 = 的字符串：按表单数据处理
        - 其他：原样返回

        Args:
            body: 原始请求体
            request_headers: 请求头字典（可能会被修改以补充Content-Type）

        Returns:
            格式化后的请求体
        """
        if isinstance(body, dict):
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/json'
            return json.dumps(body)

        if isinstance(body, str) and '=' in body and '&' in body:
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            return body

        return body

    def _handle_multipart_request(
        self,
        method: str,
        full_url: str,
        request_headers: Dict[str, str],
        request_params: Dict[str, Any],
        body: Any,
        start_time: float,
        response: HttpResponse
    ) -> Optional[HttpResponse]:
        """
        处理multipart/form-data文件上传请求

        将body中的字段分离为普通字段和文件字段，使用requests的files参数
        发送请求。注意：需要移除手动设置的Content-Type，让requests库自动
        生成包含boundary的Content-Type。

        Args:
            method: HTTP方法
            full_url: 完整URL
            request_headers: 请求头
            request_params: URL查询参数
            body: 请求体（包含普通字段和文件字段）
            start_time: 请求开始时间戳
            response: 待填充的响应对象

        Returns:
            填充后的HttpResponse（有文件时），或None（无文件时走通用流程）
        """
        if not isinstance(body, dict):
            return None

        # 分离文件字段和普通字段
        files = {}
        data = {}
        for key, value in body.items():
            if hasattr(value, 'read') or isinstance(value, tuple):
                files[key] = value
            else:
                data[key] = value

        if not files:
            return None

        # 移除手动设置的Content-Type，让requests自动生成含boundary的头
        headers_without_ct = {
            k: v for k, v in request_headers.items()
            if k.lower() != 'content-type'
        }

        raw_response = self.session.request(
            method=method.upper(),
            url=full_url,
            headers=headers_without_ct,
            params=request_params,
            files=files,
            data=data,
            timeout=self.timeout,
            verify=self.verify_ssl
        )

        # 填充响应对象
        response.response_time = round((time.time() - start_time) * 1000)
        response.status_code = raw_response.status_code
        response.headers = dict(raw_response.headers)
        response.raw_response = raw_response
        response.body = self._parse_response_body(raw_response)
        response.body_size = len(raw_response.content)

        logger.info(
            f"Response received: {response.status_code} "
            f"in {response.response_time}ms"
        )
        return response

    def _parse_response_body(self, raw_response: requests.Response) -> Any:
        """
        解析HTTP响应体

        根据响应头的Content-Type判断解析方式：
        - application/json: 解析为Python对象（dict/list）
        - 其他类型: 返回纯文本

        使用宽泛的异常捕获确保任何解析错误都不会导致请求失败。

        Args:
            raw_response: requests库的原始响应对象

        Returns:
            解析后的响应体（dict/list/str）
        """
        try:
            content_type = raw_response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return raw_response.json()
            return raw_response.text
        except Exception:
            return raw_response.text

    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        替换文本中的 ${key} 格式变量占位符

        遍历变量字典，将文本中所有匹配的占位符替换为对应值的字符串形式。

        Args:
            text: 包含占位符的原始文本
            variables: 变量名到值的映射字典

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
        递归替换字典中所有字符串值的变量占位符

        支持嵌套字典和列表中字符串元素的替换。

        Args:
            data: 包含占位符的原始字典
            variables: 变量名到值的映射字典

        Returns:
            替换后的新字典，原字典不被修改
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
                    self._replace_variables(item, variables)
                    if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def close(self):
        """关闭HTTP会话，释放连接池资源"""
        if self.session:
            self.session.close()