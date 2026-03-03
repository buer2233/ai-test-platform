"""
流量录制解析服务

负责解析代理抓包生成的 JSON/HAR 数据，转换为标准化的请求/响应结构。
"""

import json
import hashlib
from urllib.parse import urlparse, parse_qs


class TrafficParseError(Exception):
    """解析错误，携带错误码与描述。"""

    def __init__(self, message, code="PARSE_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class TrafficParseService:
    """流量解析服务。"""

    def __init__(self, max_file_size=5 * 1024 * 1024):
        self.max_file_size = max_file_size

    def parse_content(self, content, file_format="JSON"):
        """解析文本内容，返回标准化 entry 列表。"""
        if content is None:
            return []
        if isinstance(content, str) and not content.strip():
            return []

        if len(content.encode("utf-8")) > self.max_file_size:
            raise TrafficParseError("文件大小超过限制", code="FILE_TOO_LARGE")

        try:
            raw_data = json.loads(content) if isinstance(content, str) else content
        except (TypeError, json.JSONDecodeError) as exc:
            raise TrafficParseError("文件格式解析失败") from exc

        entries = []

        if isinstance(raw_data, dict):
            if "log" in raw_data and "entries" in raw_data["log"]:
                raw_entries = raw_data["log"]["entries"]
            elif "entries" in raw_data:
                raw_entries = raw_data["entries"]
            else:
                raw_entries = []
        elif isinstance(raw_data, list):
            raw_entries = raw_data
        else:
            raw_entries = []

        for item in raw_entries:
            normalized = self._normalize_entry(item)
            if normalized:
                entries.append(normalized)

        return entries

    def _normalize_entry(self, item):
        if not isinstance(item, dict):
            return None

        request = item.get("request", item)
        response = item.get("response", {})

        method = request.get("method") or request.get("request_method")
        url = request.get("url") or request.get("request_url")
        headers = request.get("headers") or request.get("request_headers") or {}
        params = request.get("params") or request.get("queryString") or request.get("request_params") or {}
        body = request.get("body") or request.get("postData") or request.get("request_body") or {}

        if isinstance(body, dict) and "text" in body and len(body) == 1:
            body = body.get("text")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except (TypeError, json.JSONDecodeError):
                body = {"raw": body}

        if isinstance(params, list):
            params = {item.get("name"): item.get("value") for item in params if item.get("name")}

        if not params and url:
            parsed = urlparse(url)
            params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}

        response_status = (
            response.get("status")
            or response.get("response_status")
            or item.get("response_status")
        )
        response_headers = (
            response.get("headers")
            or response.get("response_headers")
            or item.get("response_headers")
            or {}
        )
        response_body = (
            response.get("content")
            or response.get("body")
            or response.get("response_body")
            or item.get("response_body")
            or {}
        )
        if isinstance(response_body, dict) and "text" in response_body and len(response_body) == 1:
            response_body = response_body.get("text")
        if isinstance(response_body, str):
            try:
                response_body = json.loads(response_body)
            except (TypeError, json.JSONDecodeError):
                response_body = {"raw": response_body}

        response_time = item.get("time") or response.get("time") or response.get("response_time_ms") or 0

        return {
            "request_method": method,
            "request_url": url,
            "request_headers": headers or {},
            "request_params": params or {},
            "request_body": body or {},
            "response_status": response_status,
            "response_headers": response_headers or {},
            "response_body": response_body or {},
            "response_time_ms": int(response_time) if response_time else 0,
        }

    @staticmethod
    def compute_hash(content):
        if content is None:
            return ""
        payload = content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
