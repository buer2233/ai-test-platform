"""
流量录制回放生成用例 - 服务层单元测试

覆盖解析、过滤、参数化、场景拼接与门禁逻辑。
"""

import json
from types import SimpleNamespace

import pytest

from api_automation.services.traffic_artifact_gate_service import ArtifactGateService
from api_automation.services.traffic_filter_service import TrafficFilterService
from api_automation.services.traffic_parameterize_service import ParameterizeService
from api_automation.services.traffic_parse_service import TrafficParseError, TrafficParseService
from api_automation.services.traffic_scenario_builder import TrafficScenarioBuilder


def _build_sample_entries():
    return [
        {
            "request_method": "POST",
            "request_url": "https://example.com/api/login",
            "request_headers": {"content-type": "application/json"},
            "request_params": {},
            "request_body": {"username": "admin", "password": "secret"},
            "response_status": 200,
            "response_headers": {"content-type": "application/json"},
            "response_body": {"token": "token-abc", "userId": 99},
            "response_time_ms": 120,
        },
        {
            "request_method": "GET",
            "request_url": "https://example.com/api/profile",
            "request_headers": {},
            "request_params": {"userId": 99},
            "request_body": {},
            "response_status": 200,
            "response_headers": {},
            "response_body": {"name": "admin"},
            "response_time_ms": 80,
        },
    ]


def test_parse_json_entries():
    service = TrafficParseService(max_file_size=1024 * 1024)
    content = json.dumps(_build_sample_entries())
    result = service.parse_content(content, file_format="JSON")

    assert len(result) == 2
    assert result[0]["request_method"] == "POST"
    assert result[0]["response_status"] == 200


def test_parse_invalid_json():
    service = TrafficParseService(max_file_size=1024)
    with pytest.raises(TrafficParseError):
        service.parse_content("invalid-json", file_format="JSON")


def test_parse_empty_content():
    service = TrafficParseService(max_file_size=1024)
    result = service.parse_content("[]", file_format="JSON")
    assert result == []


def test_parse_blank_content():
    service = TrafficParseService(max_file_size=1024)
    result = service.parse_content("   ", file_format="JSON")
    assert result == []


def test_parse_large_content_rejected():
    service = TrafficParseService(max_file_size=10)
    large_content = json.dumps([{"request_method": "GET"}])
    with pytest.raises(TrafficParseError) as exc:
        service.parse_content(large_content, file_format="JSON")
    assert exc.value.code == "FILE_TOO_LARGE"


def test_parse_error_has_readable_message_and_code():
    service = TrafficParseService(max_file_size=1024)
    with pytest.raises(TrafficParseError) as exc:
        service.parse_content("{broken", file_format="JSON")
    assert exc.value.code == "PARSE_ERROR"
    assert exc.value.message == "文件格式解析失败"


def test_filter_static_resource_and_health():
    entries = [
        {
            "request_method": "GET",
            "request_url": "https://example.com/static/app.js",
            "request_params": {},
            "request_body": {},
        },
        {
            "request_method": "GET",
            "request_url": "https://example.com/health",
            "request_params": {},
            "request_body": {},
        },
    ]
    filtered, stats = TrafficFilterService().filter_entries(entries)
    assert filtered[0]["is_valuable"] is False
    assert filtered[1]["is_valuable"] is False
    assert stats["filtered_count"] == 2


def test_filter_deduplicate():
    entries = _build_sample_entries()
    entries.append(entries[0].copy())
    filtered, stats = TrafficFilterService().filter_entries(entries)
    assert stats["deduplicated_count"] == 1
    assert sum(1 for item in filtered if not item.get("is_valuable", True)) == 1


def test_parameterize_dynamic_fields():
    entries = _build_sample_entries()
    parameterized, rules, conflicts = ParameterizeService().parameterize(entries)

    assert rules
    assert any(rule["variable_name"] == "token" for rule in rules)
    assert "${userId}" in json.dumps(parameterized[1])
    assert conflicts == []


def test_parameterize_no_dynamic_fields():
    entries = [
        {
            "request_method": "GET",
            "request_url": "https://example.com/api/simple",
            "request_params": {"page": 1},
            "request_body": {},
            "response_status": 200,
            "response_body": {"ok": True},
        }
    ]
    _, rules, _ = ParameterizeService().parameterize(entries)
    assert rules == []


def test_parameterize_conflict():
    entries = [
        {
            "request_method": "POST",
            "request_url": "https://example.com/api/login",
            "request_params": {},
            "request_body": {},
            "response_status": 200,
            "response_body": {"token": "token-1"},
        },
        {
            "request_method": "POST",
            "request_url": "https://example.com/api/login",
            "request_params": {},
            "request_body": {},
            "response_status": 200,
            "response_body": {"token": "token-2"},
        },
    ]
    _, rules, conflicts = ParameterizeService().parameterize(entries)
    assert len(rules) == 2
    assert conflicts


def test_scenario_builder_order():
    entries = _build_sample_entries()
    scenario = TrafficScenarioBuilder().build(entries)
    assert scenario["steps"][0]["step_order"] == 1
    assert scenario["steps"][1]["step_order"] == 2


def test_scenario_builder_missing_precondition():
    entries = [
        {
            "request_method": "GET",
            "request_url": "https://example.com/api/profile",
            "request_params": {},
            "request_body": {},
            "response_status": None,
            "response_body": {},
            "is_valuable": True,
        }
    ]
    scenario = TrafficScenarioBuilder().build(entries)
    assert scenario["requires_manual_confirmation"] is True


def test_artifact_gate_passed():
    artifact = SimpleNamespace(status="DRAFT", preview_diff={})
    ArtifactGateService().apply_trial_result(artifact, passed=True)
    assert artifact.status == "READY"


def test_artifact_gate_failed():
    artifact = SimpleNamespace(status="DRAFT", preview_diff={})
    ArtifactGateService().apply_trial_result(artifact, passed=False, error_info="boom")
    assert artifact.status == "DRAFT"
    assert artifact.preview_diff["error_info"] == "boom"
