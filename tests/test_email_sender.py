import os
import sys

from PyQt5.QtCore import QCoreApplication
import pytest

from src.automation.email_sender import send_email_via_mailgun

'''
Pytest's monkeypatch is used to override the requests.post method with fake implementations
(fake_post_success and fake_post_failure). This prevents real API calls from being made during
tests and allows controlled responses for verifying different scenarios.
'''


@pytest.fixture(scope="function", autouse=True)
def ensure_qapp():
    """Ensure a QCoreApplication instance exists if needed."""
    app = QCoreApplication.instance()
    if app is None:
        QCoreApplication(sys.argv if hasattr(sys, 'argv') else [''])

    # Set Org/App names if not already set
    if not QCoreApplication.organizationName():
        QCoreApplication.setOrganizationName("AutoMateTestOrg")
    if not QCoreApplication.applicationName():
        QCoreApplication.setApplicationName("AutoMateTestApp")


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
        # Simulate Mailgun sometimes returning non-json on error
        if isinstance(self._json, dict):
            return self._json
        else:
            raise ValueError("No JSON object could be decoded")


def fake_post_success(url, auth, data, files=None):
    """
    Mock requests.post function to simulate a successful Mailgun API response.
    Closes any passed file handles.
    """
    if files:
        for _, file_tuple in files:
             # Ensure file handles passed in the tuple are closed
             if hasattr(file_tuple, 'close') and not file_tuple.closed:
                 file_tuple.close()
    return FakeResponse(
        status_code=200,
        json_data={"message": "Queued. Thank you."}
    )


def fake_post_failure(url, auth, data, files=None):
    """
    Mock requests.post function to simulate a failed Mailgun API response.
    Closes any passed file handles.
    """
    if files:
        for _, file_tuple in files:
             if hasattr(file_tuple, 'close') and not file_tuple.closed:
                 file_tuple.close()
    return FakeResponse(
        status_code=400,
        json_data={"message": "Bad Request"}, # Mailgun often provides JSON errors
        text="Simulated Error Text"
    )

def fake_post_auth_error(url, auth, data, files=None):
    """Simulate a 401 Unauthorized error."""
    if files:
        for _, file_tuple in files:
             if hasattr(file_tuple, 'close') and not file_tuple.closed:
                 file_tuple.close()
    return FakeResponse(
        status_code=401,
        json_data={"message": "Forbidden"},
        text="Unauthorized"
    )

@pytest.fixture(autouse=True)
def mailgun_env_setup_teardown():
    """Fixture to setup/teardown Mailgun env vars for all tests in this file."""
    original_key = os.environ.get("MAILGUN_API_KEY")
    original_domain = os.environ.get("MAILGUN_DOMAIN")
    os.environ["MAILGUN_API_KEY"] = "fake-key"
    os.environ["MAILGUN_DOMAIN"] = "fake-domain.com"
    yield

    # Teardown: restore original values or remove if they didn't exist
    if original_key is None:
        os.environ.pop("MAILGUN_API_KEY", None)
    else:
        os.environ["MAILGUN_API_KEY"] = original_key
    if original_domain is None:
        os.environ.pop("MAILGUN_DOMAIN", None)
    else:
        os.environ["MAILGUN_DOMAIN"] = original_domain


def test_send_email_success(monkeypatch):
    """
    Test case for a successful email send.
    Uses monkeypatch to replace requests.post with a mock success response.
    """
    monkeypatch.setattr("requests.post", fake_post_success)  # Patch requests.post

    response = send_email_via_mailgun(
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        subject="Test Subject",
        body_text="This is a test email."
    )

    assert response["message"] == "Queued. Thank you."  # Validate response


def test_missing_credentials():
    """
    Test case to check behavior when Mailgun credentials are missing.
    The function should raise a ValueError.
    """

    # Temporarily remove env vars for this specific test
    original_key = os.environ.pop("MAILGUN_API_KEY", None)
    original_domain = os.environ.pop("MAILGUN_DOMAIN", None)

    with pytest.raises(ValueError) as exc_info:
        send_email_via_mailgun(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="This is a test email."
        )

    # Restore env vars if they existed
    if original_key is not None:
        os.environ["MAILGUN_API_KEY"] = original_key
    if original_domain is not None:
        os.environ["MAILGUN_DOMAIN"] = original_domain

    assert "Mailgun credentials not set" in str(exc_info.value)


def test_send_email_failure(monkeypatch):
    """
    Test case for an email send failure (e.g., bad request).
    Uses monkeypatch to replace requests.post with a mock failure response.
    """
    monkeypatch.setattr("requests.post", fake_post_failure)  # Patch requests.post
    with pytest.raises(Exception) as exc_info:
        send_email_via_mailgun(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"], # Use valid emails here
            subject="Test Subject",
            body_text="This is a test email."
        )
    # Check for the message parsed from the fake response
    assert "Bad Request" in str(exc_info.value)


def test_send_email_auth_failure(monkeypatch):
    """Test case for authentication failure (401)."""
    monkeypatch.setattr("requests.post", fake_post_auth_error)
    with pytest.raises(Exception) as exc_info:
         send_email_via_mailgun(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="This is a test email."
        )
    # Check for the specific auth error message
    assert "Invalid or missing Mailgun credentials." in str(exc_info.value)


def test_invalid_email_format():
    """Test sending with invalid email addresses."""
    # Invalid 'From'
    with pytest.raises(ValueError) as exc_info_from:
        send_email_via_mailgun("invalid-from", ["good@to.com"], "Subj", "Body")
    assert "Invalid email: invalid-from" in str(exc_info_from.value)

    # Invalid 'To'
    with pytest.raises(ValueError) as exc_info_to:
        send_email_via_mailgun("good@from.com", ["invalid-to"], "Subj", "Body")
    assert "Invalid email: invalid-to" in str(exc_info_to.value)

    # Invalid 'Cc'
    with pytest.raises(ValueError) as exc_info_cc:
        send_email_via_mailgun("good@from.com", ["good@to.com"], "Subj", "Body", cc_addresses=["invalid-cc"])
    assert "Invalid email: invalid-cc" in str(exc_info_cc.value)


def test_send_with_attachments(monkeypatch, tmp_path):
    """Test sending an email with attachments."""
    monkeypatch.setattr("requests.post", fake_post_success)

    # Create dummy attachment files
    attach1_path = tmp_path / "attach1.txt"
    attach1_path.write_text("Attachment 1 content")
    attach2_path = tmp_path / "attach2.pdf"
    attach2_path.write_text("Attachment 2 content")

    response = send_email_via_mailgun(
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        subject="Test With Attachments",
        body_text="See attached files.",
        attachments=[str(attach1_path), str(attach2_path)]
    )

    assert response["message"] == "Queued. Thank you."
