"""
基于开发文档的HTTP执行引擎核心功能测试
重点测试开发文档中提到的关键功能
"""

import json
import time
import unittest
from unittest.mock import Mock, patch
import requests
from api_automation.services.http_executor import HttpExecutor


class TestCoreHTTPMethods(unittest.TestCase):
    """测试开发文档中提到的所有HTTP方法"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_all_http_methods(self, mock_request):
        """测试文档中提到的所有HTTP方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

        for method in methods:
            response = self.executor.execute_request(
                method=method,
                url='/api/test',
                base_url='https://api.example.com'
            )

            self.assertEqual(response.status_code, 200)
            # 验证方法被正确调用
            call_args = mock_request.call_args
            self.assertEqual(call_args[1]['method'], method)


class TestRequestFormats(unittest.TestCase):
    """测试文档中的请求格式示例"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_json_format_examples(self, mock_request):
        """测试JSON格式示例"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1, 'name': 'John'}
        mock_request.return_value = mock_response

        # 测试自动Content-Type检测
        response = self.executor.execute_request(
            method='POST',
            url='/api/users',
            base_url='https://api.example.com',
            body={'name': 'John', 'email': 'john@example.com'}
        )

        self.assertEqual(response.status_code, 201)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['headers']['Content-Type'], 'application/json')

        # 测试手动指定Content-Type
        response = self.executor.execute_request(
            method='POST',
            url='/api/users',
            headers={'Content-Type': 'application/json'},
            body={'name': 'John', 'email': 'john@example.com'}
        )

        self.assertEqual(response.status_code, 201)

    @patch('requests.Session.request')
    def test_form_urlencoded_examples(self, mock_request):
        """测试表单编码格式示例"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'abc123'}
        mock_request.return_value = mock_response

        # 测试字典格式
        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body={'username': 'admin', 'password': 'secret'}
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['data'], {'username': 'admin', 'password': 'secret'})

        # 测试字符串格式
        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body='username=admin&password=secret'
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_multipart_form_data_examples(self, mock_request):
        """测试多部分表单格式示例"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'file_id': '123'}
        mock_request.return_value = mock_response

        # 测试文件上传
        file_content = b'Test file content'
        response = self.executor.execute_request(
            method='POST',
            url='/api/upload',
            headers={'Content-Type': 'multipart/form-data'},
            body={
                'file': ('document.pdf', file_content, 'application/pdf'),
                'description': 'Important document'
            }
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertIn('files', call_args[1])


class TestVariableReplacement(unittest.TestCase):
    """测试变量替换系统"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_variable_replacement_examples(self, mock_request):
        """测试文档中的变量替换示例"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        global_variables = {
            'base_url': 'https://api.example.com',
            'token': 'abc123',
            'user_id': '456'
        }

        response = self.executor.execute_request(
            method='GET',
            url='/api/users/${user_id}',
            base_url='${base_url}',
            headers={'Authorization': 'Bearer ${token}'},
            global_variables=global_variables
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['url'], 'https://api.example.com/api/users/456')
        self.assertEqual(
            call_args[1]['headers']['Authorization'],
            'Bearer abc123'
        )

    def test_variable_types(self):
        """测试不同类型的变量替换"""
        variables = {
            'env': 'production',
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'user_id': '12345'
        }

        # 测试环境变量
        result = self.executor._replace_variables('${env}', variables)
        self.assertEqual(result, 'production')

        # 测试认证令牌
        result = self.executor._replace_variables('${token}', variables)
        self.assertEqual(result, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...')

        # 测试用户ID
        result = self.executor._replace_variables('${user_id}', variables)
        self.assertEqual(result, '12345')


class TestAdvancedFeatures(unittest.TestCase):
    """测试高级功能"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_url_joining(self, mock_request):
        """测试URL拼接功能"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        test_cases = [
            ('https://api.example.com/', '/v1/users'),
            ('https://api.example.com', 'v1/users'),
            ('https://api.example.com/api/', '/users'),
        ]

        for base_url, path in test_cases:
            response = self.executor.execute_request(
                method='GET',
                url=path,
                base_url=base_url
            )

            self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_response_handling(self, mock_request):
        """测试响应处理"""
        # 测试JSON响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'status': 'success', 'data': [1, 2, 3]}
        mock_response.text = '{"status": "success", "data": [1, 2, 3]}'
        mock_response.content = b'{"status": "success", "data": [1, 2, 3]}'
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, dict)
        self.assertEqual(response.body['status'], 'success')
        # 在Mock情况下，response_time可能为0
        self.assertGreaterEqual(response.response_time, 0)
        self.assertGreater(response.body_size, 0)

    @patch('requests.Session.request')
    def test_performance_monitoring(self, mock_request):
        """测试性能监控功能"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 模拟延迟
        def slow_request(*args, **kwargs):
            time.sleep(0.05)  # 50ms延迟
            return mock_response

        mock_request.side_effect = slow_request

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.response_time, 40)  # 至少40ms


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_timeout_error(self, mock_request):
        """测试超时错误"""
        mock_request.side_effect = requests.exceptions.Timeout()

        response = self.executor.execute_request(
            method='GET',
            url='/api/slow',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNone(response.raw_response)
        self.assertIsNotNone(response.error)
        self.assertIn('timeout', response.error.lower())

    @patch('requests.Session.request')
    def test_connection_error(self, mock_request):
        """测试连接错误"""
        mock_request.side_effect = requests.exceptions.ConnectionError()

        response = self.executor.execute_request(
            method='GET',
            url='/api/unreachable',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)

    @patch('requests.Session.request')
    def test_http_status_errors(self, mock_request):
        """测试HTTP状态码错误"""
        status_codes = [400, 401, 403, 404, 500]

        for status_code in status_codes:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.json.return_value = {'error': f'HTTP {status_code}'}
            mock_request.return_value = mock_response

            response = self.executor.execute_request(
                method='GET',
                url=f'/api/error/{status_code}',
                base_url='https://api.example.com'
            )

            self.assertEqual(response.status_code, status_code)
            self.assertIsInstance(response.body, dict)


class TestConfigurationOptions(unittest.TestCase):
    """测试配置选项"""

    def test_executor_configuration(self):
        """测试执行器配置"""
        # 测试自定义配置
        executor = HttpExecutor(timeout=60, verify_ssl=False)
        self.assertEqual(executor.timeout, 60)
        self.assertFalse(executor.verify_ssl)

        # 测试默认配置
        executor = HttpExecutor()
        self.assertEqual(executor.timeout, 30)
        self.assertTrue(executor.verify_ssl)

        # 测试全局请求头
        self.assertIn('User-Agent', executor.session.headers)
        executor.close()


class TestRealWorldScenarios(unittest.TestCase):
    """测试真实世界场景"""

    def setUp(self):
        self.executor = HttpExecutor()

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_api_authentication(self, mock_request):
        """测试API认证场景"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'user': {'id': 1, 'name': 'John'}}
        mock_request.return_value = mock_response

        # Bearer Token认证
        response = self.executor.execute_request(
            method='GET',
            url='/api/profile',
            base_url='https://api.example.com',
            headers={
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
            }
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertIn('Authorization', call_args[1]['headers'])

    @patch('requests.Session.request')
    def test_api_versioning(self, mock_request):
        """测试API版本控制"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'version': 'v2'}
        mock_request.return_value = mock_response

        # URL版本控制
        response = self.executor.execute_request(
            method='GET',
            url='/v2/users',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)

        # Header版本控制
        response = self.executor.execute_request(
            method='GET',
            url='/users',
            base_url='https://api.example.com',
            headers={
                'Accept': 'application/vnd.api+json;version=2',
                'API-Version': '2'
            }
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_complex_request(self, mock_request):
        """测试复杂请求场景"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1}
        mock_request.return_value = mock_response

        # 复杂的请求头和参数
        response = self.executor.execute_request(
            method='POST',
            url='/api/resources',
            base_url='https://api.example.com',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer token123',
                'X-Request-ID': 'req-123',
                'X-Client-Version': '1.0.0'
            },
            params={
                'validate': 'true',
                'format': 'full'
            },
            body={
                'name': 'Test Resource',
                'metadata': {
                    'tags': ['test', 'api'],
                    'created_by': 'automation'
                },
                'settings': {
                    'enabled': True,
                    'timeout': 30
                }
            }
        )

        self.assertEqual(response.status_code, 201)


if __name__ == '__main__':
    unittest.main(verbosity=2)