"""
HTTP执行引擎集成测试
使用真实的HTTP请求测试各种请求格式
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from api_automation.services.http_executor import HttpExecutor


class TestHTTPRequestHandler(BaseHTTPRequestHandler):
    """测试用的HTTP请求处理器"""

    def do_GET(self):
        """处理GET请求"""
        if self.path == '/api/users':
            # 解析查询参数
            parsed = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed.query)

            response_data = {
                'users': [
                    {'id': 1, 'name': 'Alice'},
                    {'id': 2, 'name': 'Bob'}
                ],
                'page': int(query_params.get('page', [1])[0]),
                'limit': int(query_params.get('limit', [10])[0])
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        elif self.path == '/api/headers':
            # 返回请求头信息
            headers = dict(self.headers)
            response_data = {
                'headers': headers,
                'authorization': headers.get('Authorization', '')
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers.get('Content-Length', 0))

        if self.path == '/api/login':
            content_type = self.headers.get('Content-Type', '')

            if 'application/json' in content_type:
                # JSON格式
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())

                if data.get('username') == 'admin' and data.get('password') == 'secret':
                    response_data = {'token': 'abc123', 'user_id': 1}
                else:
                    response_data = {'error': 'Invalid credentials'}
                    self.send_response(401)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    return

            elif 'application/x-www-form-urlencoded' in content_type:
                # Form格式
                post_data = self.rfile.read(content_length)
                data = urllib.parse.parse_qs(post_data.decode())

                username = data.get('username', [''])[0]
                password = data.get('password', [''])[0]

                if username == 'admin' and password == 'secret':
                    response_data = {'token': 'abc123', 'user_id': 1}
                else:
                    response_data = {'error': 'Invalid credentials'}
                    self.send_response(401)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    return

            else:
                self.send_response(400)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        elif self.path == '/api/upload':
            # 模拟文件上传
            content_type = self.headers.get('Content-Type', '')

            if 'multipart/form-data' in content_type:
                # 简单处理，假设有文件上传
                response_data = {
                    'file_id': '123',
                    'filename': 'test.txt',
                    'size': content_length
                }
            else:
                self.send_response(400)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        elif self.path == '/api/data':
            # 返回接收到的数据
            post_data = self.rfile.read(content_length)

            try:
                if self.headers.get('Content-Type', '').startswith('application/json'):
                    data = json.loads(post_data.decode())
                else:
                    data = post_data.decode()

                response_data = {
                    'received': data,
                    'content_type': self.headers.get('Content-Type', ''),
                    'size': content_length
                }

                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())

            except Exception as e:
                self.send_response(400)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        """处理PUT请求"""
        if self.path.startswith('/api/users/'):
            user_id = self.path.split('/')[-1]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode())
                response_data = {
                    'id': int(user_id),
                    'updated': True,
                    'data': data
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())

            except Exception:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        """处理DELETE请求"""
        if self.path.startswith('/api/users/'):
            user_id = self.path.split('/')[-1]

            response_data = {
                'deleted': True,
                'id': int(user_id)
            }

            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass


def run_test_server(port=8999):
    """运行测试服务器"""
    server = HTTPServer(('localhost', port), TestHTTPRequestHandler)
    server.serve_forever()


class TestHttpExecutorIntegration:
    """HTTP执行器集成测试"""

    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        # 启动测试服务器
        cls.server_port = 8999
        cls.server_thread = threading.Thread(
            target=run_test_server,
            args=(cls.server_port,),
            daemon=True
        )
        cls.server_thread.start()

        # 等待服务器启动
        time.sleep(0.5)

        cls.executor = HttpExecutor(timeout=5, verify_ssl=False)
        cls.base_url = f'http://localhost:{cls.server_port}'

    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        cls.executor.close()

    def test_get_request_with_params(self):
        """测试GET请求带参数"""
        response = self.executor.execute_request(
            method='GET',
            url='/api/users',
            base_url=self.base_url,
            params={'page': 2, 'limit': 5}
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert 'users' in response.body
        assert response.body['page'] == 2
        assert response.body['limit'] == 5
        assert response.response_time > 0

    def test_get_request_with_headers(self):
        """测试GET请求带头部"""
        response = self.executor.execute_request(
            method='GET',
            url='/api/headers',
            base_url=self.base_url,
            headers={
                'Authorization': 'Bearer test-token',
                'X-Custom-Header': 'custom-value'
            }
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert response.body['authorization'] == 'Bearer test-token'

    def test_post_json_request(self):
        """测试POST JSON请求"""
        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url=self.base_url,
            headers={'Content-Type': 'application/json'},
            body={'username': 'admin', 'password': 'secret'}
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert 'token' in response.body
        assert response.body['token'] == 'abc123'

    def test_post_form_urlencoded_request(self):
        """测试POST Form请求"""
        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url=self.base_url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body={'username': 'admin', 'password': 'secret'}
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert 'token' in response.body

    def test_post_multipart_form_data(self):
        """测试POST multipart/form-data请求"""
        # 创建一个模拟文件内容
        response = self.executor.execute_request(
            method='POST',
            url='/api/upload',
            base_url=self.base_url,
            headers={'Content-Type': 'multipart/form-data'},
            body={
                'file': ('test.txt', b'This is test content', 'text/plain'),
                'description': 'Test file upload'
            }
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert 'file_id' in response.body
        assert response.body['file_id'] == '123'

    def test_put_request(self):
        """测试PUT请求"""
        response = self.executor.execute_request(
            method='PUT',
            url='/api/users/1',
            base_url=self.base_url,
            body={'name': 'Updated Name', 'email': 'updated@example.com'}
        )

        assert response.status_code == 200
        assert isinstance(response.body, dict)
        assert response.body['id'] == 1
        assert response.body['updated'] is True

    def test_delete_request(self):
        """测试DELETE请求"""
        response = self.executor.execute_request(
            method='DELETE',
            url='/api/users/1',
            base_url=self.base_url
        )

        assert response.status_code == 204

    def test_auto_content_type_detection(self):
        """测试自动Content-Type检测"""
        response = self.executor.execute_request(
            method='POST',
            url='/api/data',
            base_url=self.base_url,
            body={'message': 'Hello World', 'count': 42}
        )

        assert response.status_code == 201
        assert isinstance(response.body, dict)
        assert response.body['content_type'] == 'application/json'

    def test_variable_replacement(self):
        """测试变量替换功能"""
        response = self.executor.execute_request(
            method='GET',
            url='/api/users',
            base_url=self.base_url,
            params={'page': '${page}', 'limit': '${limit}'},
            global_variables={'page': 1, 'limit': 20}
        )

        assert response.status_code == 200
        assert response.body['page'] == 1  # 变量应该被替换

    def test_request_with_invalid_credentials(self):
        """测试错误处理"""
        response = self.executor.execute_request(
            method='POST',
            url='/api/login',
            base_url=self.base_url,
            headers={'Content-Type': 'application/json'},
            body={'username': 'invalid', 'password': 'wrong'}
        )

        assert response.status_code == 401
        assert 'error' in response.body

    def test_request_timeout(self):
        """测试超时设置（使用一个不存在的端口）"""
        executor = HttpExecutor(timeout=1, verify_ssl=False)

        response = executor.execute_request(
            method='GET',
            url='/api/slow',
            base_url='http://localhost:9999',  # 不存在的端口
        )

        assert response.status_code == 0
        assert response.error is not None
        assert 'timeout' in response.error.lower() or 'connection' in response.error.lower()

        executor.close()


if __name__ == '__main__':
    # 使用pytest运行
    import pytest
    pytest.main([__file__, '-v'])