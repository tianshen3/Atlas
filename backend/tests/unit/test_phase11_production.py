import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.workers.tasks import process_document_task

client = TestClient(app)


def test_security_password_hashing():
    password = "MySecretPassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_security_jwt_token():
    payload = {"sub": "user123", "tenant_id": "tenant_abc"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["tenant_id"] == "tenant_abc"
    assert "exp" in decoded


def test_auth_login_success():
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "admin", "password": "secret123", "tenant_id": "tenant_1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["tenant_id"] == "tenant_1"


def test_auth_login_invalid():
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "admin", "password": "wrong_password"},
    )
    assert response.status_code == 401


def test_task_status_polling_endpoint():
    with patch("app.api.v1.tasks.AsyncResult") as MockAsyncResult:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"total_chunks": 5}
        MockAsyncResult.return_value = mock_result

        response = client.get("/api/v1/tasks/test-task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "SUCCESS"
        assert data["result"] == {"total_chunks": 5}


def test_process_document_task_execution():
    with patch("app.workers.tasks.extract_text_from_pdf") as mock_extract, \
         patch("app.workers.tasks.chunk_document_pages") as mock_chunk:
        
        mock_extract.return_value = [{"page_number": 1, "text": "sample"}]
        mock_chunk.return_value = [{"chunk_index": 0, "text": "sample"}]

        res = process_document_task.apply(args=["doc123", "fake/path.pdf", "tenant_1"]).get()
        assert res["status"] == "SUCCESS"
        assert res["document_id"] == "doc123"
        assert res["total_chunks"] == 1
