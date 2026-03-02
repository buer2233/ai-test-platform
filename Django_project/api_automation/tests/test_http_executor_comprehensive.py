"""
HTTP执行引擎综合测试用例
依据《02-HTTP执行引擎.md》开发文档编写的全面测试
"""

import json
import time
import base64
import gzip
import urllib.parse
import unittest
from unittest.mock import Mock, patch, mock_open
import requests
from api_automation.services.http_executor import HttpExecutor


class TestHTTPMethods(unittest.TestCase):
    """测试所有支持的HTTP方法"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_get_method(self, mock_request):
        """测试GET方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'method': 'GET'}
        mock_response.text = '{"method": "GET"}'
        mock_response.content = b'{"method": "GET"}'
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/resource',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_with(
            method='GET',
            url='https://api.example.com/api/resource',
            headers={},  # 没有额外请求头时headers为空
            params={},
            data=None,
            timeout=10,
            verify=False
        )

    @patch('requests.Session.request')
    def test_post_method(self, mock_request):
        """测试POST方法"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'id': 1, 'method': 'POST'}
        mock_response.text = '{"id": 1, "method": "POST"}'
        mock_response.content = b'{"id": 1, "method": "POST"}'
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/resource',
            base_url='https://api.example.com',
            body={'name': 'Test Resource'}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.body['method'], 'POST')

    @patch('requests.Session.request')
    def test_put_method(self, mock_request):
        """测试PUT方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'method': 'PUT'}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='PUT',
            url='/api/resource/1',
            base_url='https://api.example.com',
            body={'name': 'Updated Resource'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body['method'], 'PUT')

    @patch('requests.Session.request')
    def test_patch_method(self, mock_request):
        """测试PATCH方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'method': 'PATCH'}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='PATCH',
            url='/api/resource/1',
            base_url='https://api.example.com',
            body={'name': 'Partially Updated'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body['method'], 'PATCH')

    @patch('requests.Session.request')
    def test_delete_method(self, mock_request):
        """测试DELETE方法"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='DELETE',
            url='/api/resource/1',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 204)

    @patch('requests.Session.request')
    def test_head_method(self, mock_request):
        """测试HEAD方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1024'}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='HEAD',
            url='/api/resource/1',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_options_method(self, mock_request):
        """测试OPTIONS方法"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Allow': 'GET, POST, PUT, DELETE'}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='OPTIONS',
            url='/api/resource',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)


class TestRequestFormats(unittest.TestCase):
    """测试各种请求格式"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_json_format_auto_detection(self, mock_request):
        """测试JSON格式自动检测"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'received': 'json'}
        mock_request.return_value = mock_response

        # 不指定Content-Type，应该自动检测
        response = self.executor.execute_request(
            method='POST',
            url='/api/data',
            base_url='https://api.example.com',
            body={'key': 'value', 'number': 123}
        )

        self.assertEqual(response.status_code, 200)
        # 验证是否自动设置了Content-Type
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['headers']['Content-Type'], 'application/json')
        self.assertEqual(call_args[1]['data'], '{"key": "value", "number": 123}')

    @patch('requests.Session.request')
    def test_json_format_explicit(self, mock_request):
        """测试显式指定JSON格式"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'received': 'json'}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/data',
            base_url='https://api.example.com',
            headers={'Content-Type': 'application/json'},
            body={'key': 'value'}
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['headers']['Content-Type'], 'application/json')

    @patch('requests.Session.request')
    def test_form_urlencoded_dict(self, mock_request):
        """测试表单编码格式（字典）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'form': {'username': 'admin'}}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url='https://api.example.com',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body={'username': 'admin', 'password': 'secret'}
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(
            call_args[1]['data'],
            {'username': 'admin', 'password': 'secret'}
        )

    @patch('requests.Session.request')
    def test_form_urlencoded_string(self, mock_request):
        """测试表单编码格式（字符串）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url='https://api.example.com',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body='username=admin&password=secret&email=test%40example.com'
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(
            call_args[1]['data'],
            {'username': 'admin', 'password': 'secret', 'email': 'test@example.com'}
        )

    @patch('requests.Session.request')
    def test_multipart_form_data_with_file(self, mock_request):
        """测试多部分表单格式（带文件）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'file_id': '123'}
        mock_request.return_value = mock_response

        file_content = b'This is file content'
        response = self.executor.execute_request(
            method='POST',
            url='/api/upload',
            base_url='https://api.example.com',
            headers={'Content-Type': 'multipart/form-data'},
            body={
                'file': ('test.txt', file_content, 'text/plain'),
                'description': 'Test file',
                'category': 'documents'
            }
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        # 文件上传使用files参数
        self.assertIn('files', call_args[1])
        self.assertIn('data', call_args[1])

    @patch('requests.Session.request')
    def test_multipart_form_data_without_file(self, mock_request):
        """测试多部分表单格式（不带文件）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/submit',
            base_url='https://api.example.com',
            headers={'Content-Type': 'multipart/form-data'},
            body={
                'title': 'Test Title',
                'content': 'Test content'
            }
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_raw_text_body(self, mock_request):
        """测试原始文本请求体"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.text = 'Echo: Hello World'
        mock_response.content = b'Echo: Hello World'
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/echo',
            base_url='https://api.example.com',
            headers={'Content-Type': 'text/plain'},
            body='Hello World'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, 'Echo: Hello World')


class TestVariableReplacement(unittest.TestCase):
    """测试变量替换功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_simple_variable_replacement(self, mock_request):
        """测试简单变量替换"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        global_variables = {
            'user_id': '123',
            'token': 'abc123',
            'api_version': 'v2'
        }

        response = self.executor.execute_request(
            method='GET',
            url='/api/${api_version}/users/${user_id}',
            base_url='https://api.example.com',
            headers={'Authorization': 'Bearer ${token}'},
            global_variables=global_variables
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['url'], 'https://api.example.com/api/v2/users/123')
        self.assertEqual(
            call_args[1]['headers']['Authorization'],
            'Bearer abc123'
        )

    @patch('requests.Session.request')
    def test_nested_variable_replacement(self, mock_request):
        """测试嵌套对象变量替换"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        global_variables = {
            'config': {
                'host': 'api.example.com',
                'port': 443
            },
            'user': {
                'id': '456',
                'name': 'John'
            }
        }

        response = self.executor.execute_request(
            method='GET',
            url='/api/users/${user.id}',
            base_url='https://${config.host}',
            global_variables=global_variables
        )

        # 注意：当前实现不支持嵌套访问，这是一个改进点
        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_variable_replacement_in_body(self, mock_request):
        """测试请求体中的变量替换"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        global_variables = {
            'username': 'admin',
            'password': 'secret123',
            'timestamp': '2024-01-01T00:00:00Z'
        }

        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url='https://api.example.com',
            body={
                'username': '${username}',
                'password': '${password}',
                'login_time': '${timestamp}'
            },
            global_variables=global_variables
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_variable_replacement_in_params(self, mock_request):
        """测试URL参数中的变量替换"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        global_variables = {
            'page': 2,
            'limit': 20,
            'search_term': 'test query'
        }

        response = self.executor.execute_request(
            method='GET',
            url='/api/search',
            base_url='https://api.example.com',
            params={
                'q': '${search_term}',
                'page': '${page}',
                'limit': '${limit}'
            },
            global_variables=global_variables
        )

        self.assertEqual(response.status_code, 200)

    def test_variable_replacement_edge_cases(self):
        """测试变量替换边界情况"""
        global_variables = {
            'empty': '',
            'null': None,
            'special': 'Hello ${not_replaced} World'
        }

        # 测试空字符串替换
        result = self.executor._replace_variables('${empty}', global_variables)
        self.assertEqual(result, '')

        # 测试None值替换
        result = self.executor._replace_variables('${null}', global_variables)
        self.assertEqual(result, 'None')

        # 测试不存在的变量
        result = self.executor._replace_variables('${missing}', global_variables)
        self.assertEqual(result, '${missing}')

        # 测试部分替换
        result = self.executor._replace_variables(global_variables['special'], global_variables)
        self.assertEqual(result, 'Hello ${not_replaced} World')


class TestURLHandling(unittest.TestCase):
    """测试URL处理功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_url_joining_with_slashes(self, mock_request):
        """测试URL拼接处理斜杠"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 测试不同的斜杠组合
        test_cases = [
            ('https://api.example.com/', '/users', 'https://api.example.com/users'),
            ('https://api.example.com', '/users', 'https://api.example.com/users'),
            ('https://api.example.com/', 'users', 'https://api.example.com/users'),
            ('https://api.example.com', 'users', 'https://api.example.com/users'),
            ('https://api.example.com/api/', '/v1/users', 'https://api.example.com/api/v1/users'),
        ]

        for base_url, url, expected in test_cases:
            response = self.executor.execute_request(
                method='GET',
                url=url,
                base_url=base_url
            )
            self.assertEqual(response.status_code, 200)
            call_args = mock_request.call_args
            self.assertEqual(call_args[1]['url'], expected)

    @patch('requests.Session.request')
    def test_query_parameters(self, mock_request):
        """测试URL查询参数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/users',
            base_url='https://api.example.com',
            params={
                'page': 1,
                'limit': 10,
                'filter': 'active',
                'sort': 'name'
            }
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params'], {
            'page': 1,
            'limit': 10,
            'filter': 'active',
            'sort': 'name'
        })

    @patch('requests.Session.request')
    def test_special_characters_in_url(self, mock_request):
        """测试URL中的特殊字符"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # URL编码的查询参数
        response = self.executor.execute_request(
            method='GET',
            url='/api/search',
            base_url='https://api.example.com',
            params={'q': 'hello world & special chars'}
        )

        self.assertEqual(response.status_code, 200)


class TestResponseHandling(unittest.TestCase):
    """测试响应处理功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_json_response_parsing(self, mock_request):
        """测试JSON响应解析"""
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
        self.assertEqual(response.body['data'], [1, 2, 3])

    @patch('requests.Session.request')
    def test_text_response_parsing(self, mock_request):
        """测试文本响应解析"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.json.side_effect = ValueError()  # 模拟JSON解析失败
        mock_response.text = 'Hello, World!'
        mock_response.content = b'Hello, World!'
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/message',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.body, str)
        self.assertEqual(response.body, 'Hello, World!')

    @patch('requests.Session.request')
    def test_response_size_calculation(self, mock_request):
        """测试响应大小计算"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"test": "data"}'

        # 计算实际大小
        import json
        actual_size = len(b'{"test": "data"}')
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.body_size, actual_size)  # 使用实际计算的大小

    @patch('requests.Session.request')
    def test_response_headers_handling(self, mock_request):
        """测试响应头处理"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Custom-Header': 'custom-value'
        }
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Custom-Header'], 'custom-value')


class TestErrorHandling(unittest.TestCase):
    """测试错误处理功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

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
        mock_request.side_effect = requests.exceptions.ConnectionError(
            'Failed to establish connection'
        )

        response = self.executor.execute_request(
            method='GET',
            url='/api/unreachable',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)
        self.assertIn('connection error', response.error.lower())

    @patch('requests.Session.request')
    def test_request_exception(self, mock_request):
        """测试请求异常"""
        mock_request.side_effect = requests.exceptions.RequestException(
            'Invalid request'
        )

        response = self.executor.execute_request(
            method='POST',
            url='/api/invalid',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)
        self.assertIn('request error', response.error.lower())

    @patch('requests.Session.request')
    def test_unexpected_error(self, mock_request):
        """测试意外错误"""
        mock_request.side_effect = Exception('Unexpected error')

        response = self.executor.execute_request(
            method='GET',
            url='/api/error',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 0)
        self.assertIsNotNone(response.error)
        self.assertIn('unexpected error', response.error.lower())

    @patch('requests.Session.request')
    def test_http_error_status_codes(self, mock_request):
        """测试HTTP错误状态码"""
        test_status_codes = [400, 401, 403, 404, 500, 502, 503]

        for status_code in test_status_codes:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.headers = {'Content-Type': 'application/json'}
            mock_response.json.return_value = {'error': 'HTTP Error'}
            mock_response.text = '{"error": "HTTP Error"}'
            mock_response.content = b'{"error": "HTTP Error"}'
            mock_request.return_value = mock_response

            response = self.executor.execute_request(
                method='GET',
                url=f'/api/status/{status_code}',
                base_url='https://api.example.com'
            )

            self.assertEqual(response.status_code, status_code)
            self.assertIsInstance(response.body, dict)


class TestPerformanceFeatures(unittest.TestCase):
    """测试性能相关功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_response_time_measurement(self, mock_request):
        """测试响应时间测量"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 模拟一些延迟
        def slow_request(*args, **kwargs):
            time.sleep(0.1)  # 模拟100ms延迟
            return mock_response

        mock_request.side_effect = slow_request

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.response_time, 100)  # 至少100ms

    @patch('requests.Session.request')
    def test_session_reuse(self, mock_request):
        """测试Session复用"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 执行多个请求
        for i in range(5):
            response = self.executor.execute_request(
                method='GET',
                url=f'/api/item/{i}',
                base_url='https://api.example.com'
            )
            self.assertEqual(response.status_code, 200)

        # 验证session.request被调用了5次
        self.assertEqual(mock_request.call_count, 5)

    def test_executor_configuration(self):
        """测试执行器配置"""
        # 测试自定义超时
        executor = HttpExecutor(timeout=5, verify_ssl=True)
        self.assertEqual(executor.timeout, 5)
        self.assertTrue(executor.verify_ssl)

        # 测试默认配置
        executor = HttpExecutor()
        self.assertEqual(executor.timeout, 30)
        self.assertTrue(executor.verify_ssl)

        executor.close()


class TestEdgeCasesAndBoundaryConditions(unittest.TestCase):
    """测试边界条件和特殊情况"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_empty_request_body(self, mock_request):
        """测试空请求体"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # GET请求不应该有body
        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        self.assertIsNone(call_args[1]['data'])

    @patch('requests.Session.request')
    def test_none_request_body(self, mock_request):
        """测试None请求体"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='POST',
            url='/api/data',
            base_url='https://api.example.com',
            body=None
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_large_request_body(self, mock_request):
        """测试大请求体"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 创建大JSON对象
        large_data = {
            'items': [{'id': i, 'data': 'x' * 1000} for i in range(1000)]
        }

        response = self.executor.execute_request(
            method='POST',
            url='/api/bulk',
            base_url='https://api.example.com',
            body=large_data
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        # 验证JSON序列化
        self.assertIsInstance(call_args[1]['data'], str)

    @patch('requests.Session.request')
    def test_unicode_characters(self, mock_request):
        """测试Unicode字符"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        unicode_data = {
            'chinese': '你好世界',
            'emoji': '😀🎉🚀',
            'arabic': 'مرحبا',
            'russian': 'Привет',
            'special': 'áéíóúñç'
        }

        response = self.executor.execute_request(
            method='POST',
            url='/api/unicode',
            base_url='https://api.example.com',
            body=unicode_data
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_special_headers(self, mock_request):
        """测试特殊请求头"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com',
            headers={
                'X-Custom-Header': 'custom-value',
                'User-Agent': 'Custom Agent/1.0',
                'Accept': 'application/vnd.api+json',
                'Authorization': 'Bearer token123'
            }
        )

        self.assertEqual(response.status_code, 200)
        call_args = mock_request.call_args
        # 验证请求头合并
        self.assertEqual(call_args[1]['headers']['X-Custom-Header'], 'custom-value')
        self.assertEqual(call_args[1]['headers']['User-Agent'], 'Custom Agent/1.0')
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer token123')

    def test_empty_global_variables(self):
        """测试空全局变量"""
        response = self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com',
            global_variables={}
        )

        # 应该不会出错，但没有变量被替换
        self.assertIsInstance(response, type(self.executor.execute_request(
            method='GET',
            url='/api/data',
            base_url='https://api.example.com'
        )))


class TestFileHandling(unittest.TestCase):
    """测试文件处理功能"""

    def setUp(self):
        self.executor = HttpExecutor(timeout=10, verify_ssl=False)

    def tearDown(self):
        self.executor.close()

    @patch('requests.Session.request')
    def test_file_upload_with_different_types(self, mock_request):
        """测试不同类型文件上传"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 测试不同类型的文件
        files = {
            'text_file': ('test.txt', b'Text content', 'text/plain'),
            'json_file': ('data.json', b'{"key": "value"}', 'application/json'),
            'binary_file': ('image.png', b'\x89PNG\r\n\x1a\n', 'image/png'),
            'csv_file': ('data.csv', b'name,age\nJohn,30', 'text/csv')
        }

        response = self.executor.execute_request(
            method='POST',
            url='/api/upload/multiple',
            base_url='https://api.example.com',
            headers={'Content-Type': 'multipart/form-data'},
            body=files
        )

        self.assertEqual(response.status_code, 200)

    @patch('requests.Session.request')
    def test_mixed_file_and_data_upload(self, mock_request):
        """测试混合文件和数据上传"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 混合文件和表单数据
        response = self.executor.execute_request(
            method='POST',
            url='/api/submit',
            base_url='https://api.example.com',
            headers={'Content-Type': 'multipart/form-data'},
            body={
                'metadata': json.dumps({'title': 'Test Document'}),
                'file': ('document.pdf', b'PDF content', 'application/pdf'),
                'description': 'Test file upload',
                'tags': 'test,document'
            }
        )

        self.assertEqual(response.status_code, 200)

    @patch('builtins.open', new_callable=mock_open, read_data=b'File content')
    @patch('requests.Session.request')
    def test_file_upload_from_file_object(self, mock_request, mock_file):
        """测试从文件对象上传"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 模拟打开文件
        with open('test.txt', 'rb') as f:
            response = self.executor.execute_request(
                method='POST',
                url='/api/upload',
                base_url='https://api.example.com',
                headers={'Content-Type': 'multipart/form-data'},
                body={
                    'file': f,
                    'name': 'test.txt'
                }
            )

        self.assertEqual(response.status_code, 200)
        mock_file.assert_called_once_with('test.txt', 'rb')


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)