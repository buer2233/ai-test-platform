"""流量录制生成 - API 集成测试（按 13A 测试文档实现）。"""

import json
import os
import unittest

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api_automation.models import (
    ApiGeneratedArtifact,
    ApiProject,
    ApiTestCase,
    ApiTestScenario,
    ApiTrafficCapture,
    ApiTrafficSession,
    ApiTrafficVariableRule,
)


if os.environ.get('RUN_DJANGO_TESTS') != '1':
    raise unittest.SkipTest('未开启 Django 集成测试开关')


class TestTrafficApi(TestCase):
    """流量录制生成 API 集成测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.client.force_authenticate(user=self.user)
        self.project = ApiProject.objects.create(name='流量项目', owner=self.user)
        self.sample_content = json.dumps([
            {
                "request_method": "POST",
                "request_url": "https://example.com/api/login",
                "request_body": {"username": "admin", "password": "secret"},
                "response_status": 200,
                "response_body": {"token": "token-abc", "userId": 1},
            },
            {
                "request_method": "GET",
                "request_url": "https://example.com/api/profile?userId=1",
                "request_params": {"userId": 1},
                "response_status": 200,
                "response_body": {"name": "admin"},
            },
        ])
        self.filtered_only_content = json.dumps([
            {
                "request_method": "GET",
                "request_url": "https://example.com/static/app.js",
                "response_status": 200,
                "response_body": {},
            },
            {
                "request_method": "GET",
                "request_url": "https://example.com/health",
                "response_status": 200,
                "response_body": {},
            },
        ])

    def _upload_capture(self, content=None, **extra):
        payload = {
            'project': self.project.id,
            'file_content': content or self.sample_content,
            'name': '录制-测试',
            **extra,
        }
        return self.client.post('/api/v1/api-automation/traffic-captures/', payload, format='json')

    def _parse_capture(self, capture_id):
        return self.client.post(f'/api/v1/api-automation/traffic-captures/{capture_id}/parse/')

    def _create_session_chain(self):
        upload = self._upload_capture()
        self.assertEqual(upload.status_code, 201)
        capture_id = upload.data['id']

        parse = self._parse_capture(capture_id)
        self.assertEqual(parse.status_code, 200)

        session = ApiTrafficSession.objects.filter(capture_id=capture_id).first()
        self.assertIsNotNone(session)
        return capture_id, session

    def _generate_artifact(self):
        _, session = self._create_session_chain()
        response = self.client.post(f'/api/v1/api-automation/traffic-sessions/{session.id}/generate/')
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def test_it_traffic_001_upload_requires_project_id(self):
        response = self.client.post('/api/v1/api-automation/traffic-captures/', {
            'file_content': self.sample_content,
            'name': '录制-缺少项目',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_it_traffic_002_parse_success(self):
        upload = self._upload_capture()
        self.assertEqual(upload.status_code, 201)
        capture_id = upload.data['id']

        parse = self._parse_capture(capture_id)
        self.assertEqual(parse.status_code, 200)
        self.assertGreater(parse.data['sessions_count'], 0)

        capture = ApiTrafficCapture.objects.get(id=capture_id)
        self.assertEqual(capture.status, 'PARSED')

    def test_it_traffic_003_parse_failed(self):
        upload = self._upload_capture(content='not-json')
        self.assertEqual(upload.status_code, 201)

        parse = self._parse_capture(upload.data['id'])
        self.assertEqual(parse.status_code, 400)

        capture = ApiTrafficCapture.objects.get(id=upload.data['id'])
        self.assertEqual(capture.status, 'FAILED')
        self.assertIn('message', capture.error_info)

    def test_it_traffic_004_duplicate_content_hash(self):
        first = self._upload_capture()
        self.assertEqual(first.status_code, 201)

        second = self._upload_capture()
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data.get('duplicated'))
        self.assertEqual(second.data['capture']['id'], first.data['id'])

    def test_it_traffic_005_processing_config_traceable(self):
        upload = self._upload_capture()
        capture_id = upload.data['id']

        parse = self._parse_capture(capture_id)
        self.assertEqual(parse.status_code, 200)

        capture = ApiTrafficCapture.objects.get(id=capture_id)
        self.assertIn('file_format', capture.processing_config)
        self.assertIn('filter_stats', capture.processing_config)

    def test_it_traffic_006_session_scope_by_owner(self):
        _, session = self._create_session_chain()
        other_user = User.objects.create_user(username='other', password='pass1234')
        other_project = ApiProject.objects.create(name='他人项目', owner=other_user)
        other_capture = ApiTrafficCapture.objects.create(
            project=other_project,
            name='他人录制',
            file_format='JSON',
            content_hash='hash-other',
        )
        ApiTrafficSession.objects.create(
            project=other_project,
            capture=other_capture,
            session_key='other-session',
            start_time=timezone.now(),
            end_time=timezone.now(),
            duration_ms=1,
            entry_count=1,
            status='READY',
            tags=[],
        )

        response = self.client.get('/api/v1/api-automation/traffic-sessions/')
        self.assertEqual(response.status_code, 200)
        session_ids = [item['id'] for item in response.data['results']]
        self.assertIn(session.id, session_ids)
        self.assertEqual(len(session_ids), 1)

    def test_it_traffic_007_generate_artifact_draft(self):
        _, session = self._create_session_chain()
        response = self.client.post(f'/api/v1/api-automation/traffic-sessions/{session.id}/generate/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'DRAFT')

    def test_it_traffic_008_preview_payload_editable(self):
        artifact_id = self._generate_artifact()
        response = self.client.get(f'/api/v1/api-automation/generated-artifacts/{artifact_id}/preview/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('steps', response.data['payload'])
        self.assertIn('variables', response.data['payload'])

    def test_it_traffic_009_auto_variable_rules_saved(self):
        self._generate_artifact()
        self.assertTrue(ApiTrafficVariableRule.objects.filter(variable_name__icontains='token').exists())

    def test_it_traffic_010_manual_edit_variable_rule_affects_preview(self):
        artifact_id = self._generate_artifact()
        rule = ApiTrafficVariableRule.objects.first()
        self.assertIsNotNone(rule)

        update_resp = self.client.patch(
            f'/api/v1/api-automation/traffic-variable-rules/{rule.id}/',
            {'variable_name': 'auth_token'},
            format='json'
        )
        self.assertEqual(update_resp.status_code, 200)

        preview_resp = self.client.get(f'/api/v1/api-automation/generated-artifacts/{artifact_id}/preview/')
        self.assertEqual(preview_resp.status_code, 200)
        names = [item.get('variable_name') for item in preview_resp.data['payload'].get('variables', [])]
        self.assertIn('auth_token', names)

    def test_it_traffic_011_gate_ready_on_success(self):
        artifact_id = self._generate_artifact()
        trial = self.client.post(
            f'/api/v1/api-automation/generated-artifacts/{artifact_id}/trial_run/',
            {'passed': True},
            format='json'
        )
        self.assertEqual(trial.status_code, 200)
        self.assertEqual(trial.data['status'], 'READY')

    def test_it_traffic_012_gate_stays_draft_on_fail(self):
        artifact_id = self._generate_artifact()
        trial = self.client.post(
            f'/api/v1/api-automation/generated-artifacts/{artifact_id}/trial_run/',
            {'passed': False, 'error_info': 'mock fail'},
            format='json'
        )
        self.assertEqual(trial.status_code, 200)
        self.assertEqual(trial.data['status'], 'DRAFT')
        self.assertEqual(trial.data['preview_diff']['error_info'], 'mock fail')

    def test_it_traffic_013_commit_success(self):
        artifact_id = self._generate_artifact()
        self.client.post(
            f'/api/v1/api-automation/generated-artifacts/{artifact_id}/trial_run/',
            {'passed': True},
            format='json'
        )

        commit = self.client.post(f'/api/v1/api-automation/generated-artifacts/{artifact_id}/commit/')
        self.assertEqual(commit.status_code, 201)
        self.assertTrue(ApiTestScenario.objects.filter(project=self.project).exists())
        self.assertTrue(ApiTestCase.objects.filter(project=self.project).exists())
        artifact = ApiGeneratedArtifact.objects.get(id=artifact_id)
        self.assertEqual(artifact.status, 'COMMITTED')

    def test_edge_traffic_001_large_file_rejected(self):
        large_content = 'x' * (6 * 1024 * 1024)
        response = self._upload_capture(content=large_content)
        self.assertEqual(response.status_code, 400)

    def test_edge_traffic_005_no_available_session(self):
        upload = self._upload_capture(content=self.filtered_only_content)
        self.assertEqual(upload.status_code, 201)
        capture_id = upload.data['id']

        parse = self._parse_capture(capture_id)
        self.assertEqual(parse.status_code, 200)
        self.assertEqual(parse.data['sessions_count'], 0)
        self.assertEqual(parse.data.get('message'), '无可用会话')
