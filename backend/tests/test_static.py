from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_root_contains_doctype():
    response = client.get("/")
    assert b"<!DOCTYPE html" in response.content.lower() or b"<!doctype html" in response.content.lower()


def test_unknown_path_returns_404():
    response = client.get("/does-not-exist")
    assert response.status_code == 404
