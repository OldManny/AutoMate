import os

import pytest

from src.automation.email_sender import send_email_via_mailgun

'''
Pytest's monkeypatch is used to override the requests.post method with fake implementations
(fake_post_success and fake_post_failure). This prevents real API calls from being made during
tests and allows controlled responses for verifying different scenarios.
'''


class FakeResponse:
    """
    A mock response object that mimics requests.Response.
    Used to simulate API responses during tests.
    """
    def __init__(self, status_code, json_data, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        return self._json  # Simulate requests.Response.json()


def fake_post_success(url, auth, data, files=None):
    """
    Mock requests.post function to simulate a successful Mailgun API response.
    """
    return FakeResponse(
        status_code=200,
        json_data={"message": "Queued. Thank you."}
    )


def fake_post_failure(url, auth, data, files=None):
    """
    Mock requests.post function to simulate a failed Mailgun API response.
    """
    return FakeResponse(
        status_code=400,
        json_data={"message": "Bad Request"},
        text="Error"
    )


def setup_env():
    """Set environment variables required for Mailgun API authentication."""
    os.environ["MAILGUN_API_KEY"] = "fake-key"
    os.environ["MAILGUN_DOMAIN"] = "fake-domain.com"


def teardown_env():
    """Remove Mailgun-related environment variables."""
    os.environ.pop("MAILGUN_API_KEY", None)
    os.environ.pop("MAILGUN_DOMAIN", None)


def test_send_email_success(monkeypatch):
    """
    Test case for a successful email send.
    Uses monkeypatch to replace requests.post with a mock success response.
    """
    setup_env()
    monkeypatch.setattr("requests.post", fake_post_success)  # Patch requests.post

    response = send_email_via_mailgun(
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        subject="Test Subject",
        body_text="This is a test email."
    )

    assert response["message"] == "Queued. Thank you."  # Validate response

    teardown_env()


def test_missing_credentials():
    """
    Test case to check behavior when Mailgun credentials are missing.
    The function should raise a ValueError.
    """
    teardown_env()  # Ensure no environment variables are set

    with pytest.raises(ValueError) as exc_info:
        send_email_via_mailgun(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="This is a test email."
        )

    assert "Mailgun credentials not set" in str(exc_info.value)


def test_send_email_failure(monkeypatch):
    """
    Test case for an email send failure.
    Uses monkeypatch to replace requests.post with a mock failure response.
    """
    setup_env()
    monkeypatch.setattr("requests.post", fake_post_failure)  # Patch requests.post

    with pytest.raises(Exception) as exc_info:
        send_email_via_mailgun(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="This is a test email."
        )

    assert "Mailgun send failed" in str(exc_info.value)  # Validate error message

    teardown_env()
