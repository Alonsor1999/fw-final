import pytest
from core import captcha_solver

def test_captcha_response_mock(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text

    def mock_post(*args, **kwargs):
        return MockResponse("OK|123456")

    def mock_get(*args, **kwargs):
        return MockResponse("OK|captcha123")

    monkeypatch.setattr(captcha_solver.requests, "post", mock_post)
    monkeypatch.setattr(captcha_solver.requests, "get", mock_get)

    result = captcha_solver.solve_with_2captcha(b"fake_image_data")
    assert result == "captcha123"
