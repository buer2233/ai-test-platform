import json
import shutil
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ui_automation.models import UiTestCase, UiTestExecution, UiTestProject, UiTestReport


class UiScreenshotApiTestCase(TestCase):
    """截图文件服务端点测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='screenshot_tester', password='pwd12345')
        self.token = Token.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

        self.project = UiTestProject.objects.create(
            name='截图测试项目',
            description='',
            base_url='https://example.com',
            created_by=self.user,
        )
        self.test_case = UiTestCase.objects.create(
            project=self.project,
            name='截图用例',
            natural_language_task='测试截图',
        )

        # 创建截图文件目录
        self.screenshot_dir = Path(__file__).resolve().parents[1] / 'browser-use-0.11.2' / 'screenshots'
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片文件（1x1 PNG）
        self.png_file = self.screenshot_dir / 'test_step_1.png'
        # Minimal valid PNG (1x1 pixel transparent)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
            b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx'
            b'\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\xb4\x00\x00\x00\x00'
            b'IEND\xaeB`\x82'
        )
        self.png_file.write_bytes(png_bytes)

        # 创建 JPEG 测试文件
        self.jpg_file = self.screenshot_dir / 'test_step_2.jpg'
        self.jpg_file.write_bytes(b'\xff\xd8\xff\xe0dummy_jpeg')

    def tearDown(self):
        # 清理测试文件（Windows 下 FileResponse 可能持有文件锁，忽略清理失败）
        import gc
        gc.collect()
        for f in (self.png_file, self.jpg_file):
            try:
                if f.exists():
                    f.unlink()
            except PermissionError:
                pass

    def test_screenshot_valid_path_returns_image(self):
        """有效路径返回图片内容"""
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': str(self.png_file), 'token': self.token.key},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('image/', response['Content-Type'])

    def test_screenshot_jpg_returns_image(self):
        """JPEG 格式也能正常返回"""
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': str(self.jpg_file), 'token': self.token.key},
        )
        self.assertEqual(response.status_code, 200)

    def test_screenshot_path_traversal_returns_403(self):
        """路径越界返回 403"""
        # 尝试访问 browser-use-0.11.2 外的文件
        outside_path = str(Path(__file__).resolve())
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': outside_path, 'token': self.token.key},
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['error_code'], 'REPORT_PATH_FORBIDDEN')

    def test_screenshot_not_found_returns_404(self):
        """文件不存在返回 404"""
        fake_path = str(self.screenshot_dir / 'nonexistent.png')
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': fake_path, 'token': self.token.key},
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['error_code'], 'SCREENSHOT_NOT_FOUND')

    def test_screenshot_missing_path_returns_400(self):
        """缺少 path 参数返回 400"""
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'token': self.token.key},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error_code'], 'REPORT_PATH_MISSING')

    def test_screenshot_non_image_format_returns_400(self):
        """非图片格式返回 400"""
        # 创建一个 .txt 文件
        txt_file = self.screenshot_dir / 'test.txt'
        txt_file.write_text('not an image')
        try:
            response = self.client.get(
                '/api/v1/ui-automation/reports/screenshot/',
                {'path': str(txt_file), 'token': self.token.key},
            )
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data['error_code'], 'SCREENSHOT_INVALID_FORMAT')
        finally:
            txt_file.unlink()

    def test_screenshot_token_auth_success(self):
        """token 查询参数认证成功"""
        # 使用未认证的客户端，仅靠 token 参数
        client = APIClient()
        response = client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': str(self.png_file), 'token': self.token.key},
        )
        self.assertEqual(response.status_code, 200)

    def test_screenshot_token_auth_failure(self):
        """token 查询参数认证失败"""
        client = APIClient()
        response = client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': str(self.png_file), 'token': 'invalid-token'},
        )
        self.assertEqual(response.status_code, 401)

    def test_screenshot_no_auth_returns_401(self):
        """没有任何认证返回 401"""
        client = APIClient()
        response = client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'path': str(self.png_file)},
        )
        self.assertEqual(response.status_code, 401)

    def test_error_response_includes_both_error_and_message(self):
        """错误响应同时包含 error 和 message 字段"""
        response = self.client.get(
            '/api/v1/ui-automation/reports/screenshot/',
            {'token': self.token.key},
        )
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('error_code', data)
        self.assertEqual(data['error'], data['message'])
