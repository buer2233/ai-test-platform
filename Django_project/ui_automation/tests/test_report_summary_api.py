import json
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from ui_automation.models import UiTestCase, UiTestExecution, UiTestProject, UiTestReport


class UiReportSummaryApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='ui_tester', password='pwd12345')
        self.client.force_authenticate(user=self.user)

        self.project = UiTestProject.objects.create(
            name='UI项目',
            description='',
            base_url='https://example.com',
            created_by=self.user,
        )
        self.test_case = UiTestCase.objects.create(
            project=self.project,
            name='登录用例',
            natural_language_task='打开页面并登录',
        )

    def test_report_summary_returns_metrics_from_json_report(self):
        execution = UiTestExecution.objects.create(
            project=self.project,
            test_case=self.test_case,
            status='passed',
            browser_mode='headless',
            started_at=timezone.now(),
            completed_at=timezone.now(),
            duration_seconds=12,
            executed_by=self.user,
        )

        report_dir = Path(__file__).resolve().parents[1] / 'browser-use-0.11.2' / 'report'
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f'test-report-{execution.id}.json'
        report_file.write_text(
            json.dumps(
                {
                    'history': [
                        {
                            'result': [{'success': True, 'is_done': False}],
                            'state': {'screenshot_path': str(report_dir / '1.png')},
                        },
                        {
                            'result': [{'success': False, 'error': '步骤失败'}],
                            'state': {'screenshot_path': None},
                        },
                        {
                            'result': [{'success': True, 'extracted_content': '最终结果'}],
                            'state': {'screenshot_path': str(report_dir / '2.png')},
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )

        report = UiTestReport.objects.create(
            execution=execution,
            total_steps=0,
            completed_steps=0,
            failed_steps=0,
            summary='测试完成',
            json_report_path=str(report_file),
        )

        response = self.client.get(f'/api/v1/ui-automation/reports/{report.id}/summary/')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload['status'], 'passed')
        self.assertEqual(payload['metrics']['total_steps'], 3)
        self.assertEqual(payload['metrics']['failed_steps'], 1)
        self.assertEqual(payload['metrics']['success_steps'], 2)
        self.assertEqual(payload['metrics']['screenshot_count'], 2)
        self.assertEqual(payload['final_result'], '最终结果')

    def test_report_summary_fallbacks_to_db_metrics_when_json_missing(self):
        execution = UiTestExecution.objects.create(
            project=self.project,
            test_case=self.test_case,
            status='failed',
            browser_mode='headed',
            executed_by=self.user,
        )
        report = UiTestReport.objects.create(
            execution=execution,
            total_steps=5,
            completed_steps=4,
            failed_steps=1,
            summary='执行失败',
            screenshot_paths=json.dumps(['a.png', 'b.png']),
            json_report_path='',
        )

        response = self.client.get(f'/api/v1/ui-automation/reports/{report.id}/summary/')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload['status'], 'failed')
        self.assertEqual(payload['metrics']['total_steps'], 5)
        self.assertEqual(payload['metrics']['failed_steps'], 1)
        self.assertEqual(payload['metrics']['screenshot_count'], 2)
