# -*- coding: utf-8 -*-
"""
RAG 文档解析方案 - 测试脚本骨架（TDD）
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

def test_it_doc_upload_requires_project_id():
    """IT-RAG-001: 文档上传必须带 project_id"""
    raise NotImplementedError("TODO: implement upload test")


def test_it_doc_ingest_success():
    """IT-RAG-002: 入库成功"""
    raise NotImplementedError("TODO: implement ingest success test")


def test_it_doc_ingest_failed():
    """IT-RAG-003: 入库失败"""
    raise NotImplementedError("TODO: implement ingest failed test")


def test_it_rag_generate_success():
    """IT-RAG-004: 触发生成并完成"""
    raise NotImplementedError("TODO: implement generate test")


def test_it_rag_preview_payload():
    """IT-RAG-005: 预览返回可编辑 payload"""
    raise NotImplementedError("TODO: implement preview test")


def test_it_rag_retrieve_empty():
    """IT-RAG-006: 检索为空"""
    raise NotImplementedError("TODO: implement retrieve empty test")


def test_it_gate_ready_on_success():
    """IT-RAG-007: 试运行全通过 -> READY"""
    raise NotImplementedError("TODO: implement gate success test")


def test_it_gate_stays_draft_on_fail():
    """IT-RAG-008: 试运行失败 -> DRAFT"""
    raise NotImplementedError("TODO: implement gate fail test")


def test_it_commit_artifact():
    """IT-RAG-009: 提交生成 ApiTestCase/Scenario"""
    raise NotImplementedError("TODO: implement commit test")


# ---------- 单元测试骨架（示例） ----------

def test_ut_chunking_heading_path():
    """UT-RAG-001: Markdown 切分与 heading_path"""
    raise NotImplementedError("TODO: implement unit test with fixtures")
