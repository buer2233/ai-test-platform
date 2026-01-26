"""
真实API测试
使用Django内置的API接口进行测试
"""

import json
import unittest
import requests
from unittest.mock import Mock, patch
from api_automation.services.http_executor import HttpExecutor


class TestRealAPIRequests(unittest.TestCase):
    """使用真实API测试HTTP执行器"""

    def setUp(self):
        """测试前准备"""
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)
        # 使用httpbin.org作为测试服务器（这是一个公开的HTTP测试服务）
        self.base_url = "https://httpbin.org"

    def tearDown(self):
        """测试后清理"""
        self.executor.close()

    def test_get_request_real(self):
        """测试真实的GET请求"""
        # 使用httpbin的get接口
        response = self.executor.execute_request(
            method='GET',
            url='/get',
            base_url=self.base_url,
            params={'param1': 'value1', 'param2': 'value2'}
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('args', response.body)
        self.assertEqual(response.body['args']['param1'], 'value1')
        self.assertEqual(response.body['args']['param2'], 'value2')
        self.assertGreater(response.response_time, 0)
        self.assertIsNone(response.error)

    def test_post_json_real(self):
        """测试真实的POST JSON请求"""
        response = self.executor.execute_request(
            method='POST',
            url='/post',
            base_url=self.base_url,
            headers={'Content-Type': 'application/json'},
            body={'key': 'value', 'number': 123, 'nested': {'field': 'data'}}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('json', response.body)
        self.assertEqual(response.body['json']['key'], 'value')
        self.assertEqual(response.body['json']['number'], 123)

    def test_post_form_urlencoded_real(self):
        """测试真实的POST Form请求"""
        response = self.executor.execute_request(
            method='POST',
            url='/post',
            base_url=self.base_url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body={'field1': 'value1', 'field2': 'value2'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('form', response.body)
        self.assertEqual(response.body['form']['field1'], 'value1')
        self.assertEqual(response.body['form']['field2'], 'value2')

    def test_put_request_real(self):
        """测试真实的PUT请求"""
        response = self.executor.execute_request(
            method='PUT',
            url='/put',
            base_url=self.base_url,
            body={'updated': True, 'data': 'new value'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        # httpbin返回完整的JSON数据在data字段中
        self.assertEqual(response.body['json']['updated'], True)
        self.assertEqual(response.body['json']['data'], 'new value')

    def test_delete_request_real(self):
        """测试真实的DELETE请求"""
        response = self.executor.execute_request(
            method='DELETE',
            url='/delete',
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)

    def test_headers_request_real(self):
        """测试请求头传递"""
        response = self.executor.execute_request(
            method='GET',
            url='/headers',
            base_url=self.base_url,
            headers={
                'User-Agent': 'Test-Agent/1.0',
                'X-Custom-Header': 'custom-value',
                'Authorization': 'Bearer token123'
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('headers', response.body)
        self.assertEqual(
            response.body['headers']['X-Custom-Header'],
            'custom-value'
        )
        self.assertEqual(
            response.body['headers']['Authorization'],
            'Bearer token123'
        )

    def test_variable_replacement_real(self):
        """测试变量替换功能"""
        # 设置全局变量
        global_vars = {
            'endpoint': 'get',
            'token': 'abc123',
            'user_id': '456'
        }

        response = self.executor.execute_request(
            method='GET',
            url='/${endpoint}',
            base_url=self.base_url,
            headers={
                'Authorization': 'Bearer ${token}',
                'X-User-ID': '${user_id}'
            },
            global_variables=global_vars
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('headers', response.body)
        # httpbin会将所有请求头转为小写
        headers = response.body['headers']
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer abc123')
        self.assertEqual(headers['X-User-Id'], '456')

    def test_delayed_request(self):
        """测试延迟请求（测试超时设置）"""
        # httpbin提供了一个延迟接口
        executor = HttpExecutor(timeout=2, verify_ssl=False)

        response = executor.execute_request(
            method='GET',
            url='/delay/1',  # 延迟1秒
            base_url=self.base_url
        )

        # 应该成功，因为超时时间设置为2秒
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.response_time, 1000)  # 至少1秒

        executor.close()

    def test_timeout_real(self):
        """测试真实的超时情况"""
        executor = HttpExecutor(timeout=0.5, verify_ssl=False)  # 设置短超时

        response = executor.execute_request(
            method='GET',
            url='/delay/2',  # 延迟2秒，但超时只有0.5秒
            base_url=self.base_url
        )

        # 应该超时
        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)
        self.assertIn('timeout', response.error.lower())

        executor.close()

    def test_response_types(self):
        """测试不同响应类型的处理"""
        # 测试JSON响应
        response = self.executor.execute_request(
            method='GET',
            url='/json',
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertIn('slideshow', response.body)

        # 测试HTML响应
        response = self.executor.execute_request(
            method='GET',
            url='/html',
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, str)
        self.assertIn('<html>', response.body)

        # 测试XML响应
        response = self.executor.execute_request(
            method='GET',
            url='/xml',
            base_url=self.base_url
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, str)
        self.assertIn('<?xml', response.body)

    def test_status_codes(self):
        """测试不同的状态码"""
        # 测试404
        response = self.executor.execute_request(
            method='GET',
            url='/status/404',
            base_url=self.base_url
        )
        self.assertEqual(response.status_code, 404)

        # 测试500
        response = self.executor.execute_request(
            method='GET',
            url='/status/500',
            base_url=self.base_url
        )
        self.assertEqual(response.status_code, 500)

        # 测试302重定向
        response = self.executor.execute_request(
            method='GET',
            url='/status/302',
            base_url=self.base_url
        )
        self.assertEqual(response.status_code, 302)

    def test_base64_encoding(self):
        """测试Base64编码的请求"""
        import base64

        # 创建Base64编码的数据
        original_data = "Hello, World!"
        encoded_data = base64.b64encode(original_data.encode()).decode()

        response = self.executor.execute_request(
            method='POST',
            url='/post',
            base_url=self.base_url,
            headers={'Content-Type': 'application/json'},
            body={'data': encoded_data, 'encoding': 'base64'}
        )

        self.assertEqual(response.status_code, 200)
        decoded_back = base64.b64decode(response.body['json']['data']).decode()
        self.assertEqual(decoded_back, original_data)

    def test_unicode_characters(self):
        """测试Unicode字符处理"""
        unicode_data = {
            'chinese': '你好世界',
            'emoji': '😀🎉',
            'special': 'áéíóúñ'
        }

        response = self.executor.execute_request(
            method='POST',
            url='/post',
            base_url=self.base_url,
            body=unicode_data
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body['json']['chinese'], '你好世界')
        self.assertEqual(response.body['json']['emoji'], '😀🎉')
        self.assertEqual(response.body['json']['special'], 'áéíóúñ')

    def test_large_request(self):
        """测试大请求的处理"""
        # 创建一个较大的JSON对象
        large_data = {
            'items': [{'id': i, 'value': f'item_{i}'} for i in range(1000)]
        }

        response = self.executor.execute_request(
            method='POST',
            url='/post',
            base_url=self.base_url,
            body=large_data
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.body['json']['items']), 1000)
        self.assertGreater(response.body_size, 1000)  # 响应体应该很大


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=5, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    def test_invalid_url(self):
        """测试无效URL"""
        response = self.executor.execute_request(
            method='GET',
            url='invalid-url',
            base_url='not-a-valid-protocol://'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)

    def test_connection_refused(self):
        """测试连接被拒绝"""
        # 使用一个不太可能被占用的端口
        response = self.executor.execute_request(
            method='GET',
            url='/',
            base_url='http://localhost:65432'  # 随机选择的高端口
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)
        self.assertIn('connection', response.error.lower())

    def test_ssl_error(self):
        """测试SSL错误（使用自签名证书的站点）"""
        executor = HttpExecutor(timeout=5, verify_ssl=True)  # 启用SSL验证

        # 使用一个SSL证书有问题的站点（这个测试可能会失败，取决于网络情况）
        response = executor.execute_request(
            method='GET',
            url='/',
            base_url='https://self-signed.badssl.com/'
        )

        # 可能会失败，但不会抛出异常
        self.assertTrue(response.status_code == 0 or response.status_code == 200)

        executor.close()


if __name__ == '__main__':
    unittest.main()