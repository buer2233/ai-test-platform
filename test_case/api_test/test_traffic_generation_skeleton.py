# -*- coding: utf-8 -*-
"""
流量录制回放方案 - 测试脚本骨架（TDD）
说明：先补齐并运行测试，再实现功能。
"""
import os
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1/api-automation")
AUTH_URL = os.getenv("AUTH_URL", "http://127.0.0.1:8000")
USERNAME = os.getenv("API_USER", "admin")
PASSWORD = os.getenv("API_PASS", "admin123")


def get_token():
    resp = requests.post(
        f"{AUTH_URL}/api-token-auth/",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("token")


def get_headers():
    token = get_token()
    return {"Authorization": f"Token {token}", "Content-Type": "application/json"}


# ---------- 集成测试骨架 ----------

def test_it_traffic_upload_requires_project_id():
    """IT-TRAFFIC-001: 录制上传必须带 project_id"""
    raise NotImplementedError("TODO: implement upload test")


def test_it_traffic_parse_success():
    """IT-TRAFFIC-002: 解析录制成功"""
    raise NotImplementedError("TODO: implement parse success test")


def test_it_traffic_parse_failed():
    """IT-TRAFFIC-003: 解析录制失败"""
    raise NotImplementedError("TODO: implement parse failed test")


def test_it_traffic_duplicate_content_hash():
    """IT-TRAFFIC-004: 重复文件 content_hash 处理"""
    raise NotImplementedError("TODO: implement duplicate handling test")


def test_it_session_project_scope():
    """IT-TRAFFIC-005: 会话仅返回当前项目"""
    raise NotImplementedError("TODO: implement project scope test")


def test_it_generate_artifact_draft():
    """IT-TRAFFIC-006: 生成用例草稿"""
    raise NotImplementedError("TODO: implement generate draft test")


def test_it_preview_payload_editable():
    """IT-TRAFFIC-007: 预览返回可编辑 payload"""
    raise NotImplementedError("TODO: implement preview test")


def test_it_variable_rules_created():
    """IT-TRAFFIC-008: 自动生成变量规则"""
    raise NotImplementedError("TODO: implement variable rule test")


def test_it_variable_rules_editable():
    """IT-TRAFFIC-009: 变量规则可编辑"""
    raise NotImplementedError("TODO: implement variable rule edit test")


def test_it_gate_ready_on_success():
    """IT-TRAFFIC-010: 试运行全通过 -> READY"""
    raise NotImplementedError("TODO: implement gate success test")


def test_it_gate_stays_draft_on_fail():
    """IT-TRAFFIC-011: 试运行失败 -> DRAFT"""
    raise NotImplementedError("TODO: implement gate fail test")


def test_it_commit_artifact():
    """IT-TRAFFIC-012: 提交生成 ApiTestCase/Scenario"""
    raise NotImplementedError("TODO: implement commit test")


# ---------- 单元测试骨架（示例） ----------

def test_ut_parameterize_conflict():
    """UT-TRAFFIC-009: 变量命名冲突处理"""
    raise NotImplementedError("TODO: implement unit test with mocks")
