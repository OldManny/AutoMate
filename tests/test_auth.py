import json

import pytest

from src.utils import auth


@pytest.fixture
def tmp_user_file(tmp_path, monkeypatch):
    """
    A pytest fixture that:
    1) Creates an empty 'test_user_data.json' in a temp directory.
    2) Patches auth.USER_DATA_FILE to point to this file instead
       of the real "user_data.json".
    3) Cleans up afterwards.
    """
    file_path = tmp_path / "test_user_data.json"

    # Initialize with empty users
    file_path.write_text(json.dumps({"users": []}), encoding="utf-8")

    # Patch the USER_DATA_FILE constant in auth
    monkeypatch.setattr(auth, "USER_DATA_FILE", str(file_path))

    yield file_path  # Provide the path to the test


def test_register_user_success(tmp_user_file):
    """
    Register a new user that doesn't exist yet => should succeed (return True).
    """
    result = auth.register_user("test@example.com", "Password123")
    assert result is True, "Expected register_user to return True on success"

    # Read the temp file and verify user is stored
    data = json.loads(tmp_user_file.read_text(encoding="utf-8"))
    assert len(data["users"]) == 1
    user = data["users"][0]
    assert user["email"] == "test@example.com"
    assert user["remember_me_token"] == ""
    # Check that the password is hashed, not stored in plain text
    assert "hashed_password" in user
    assert user["hashed_password"] != "Password123"


def test_register_user_already_exists(tmp_user_file):
    """
    Register the same user twice => second time should return False.
    """
    # First time
    assert auth.register_user("test@example.com", "Password123") is True
    # Second time => user exists => fail
    assert auth.register_user("test@example.com", "AnotherPass") is False

    # Verify still only one user in the file
    data = json.loads(tmp_user_file.read_text(encoding="utf-8"))
    assert len(data["users"]) == 1


def test_verify_user_success(tmp_user_file):
    """
    If a user is registered, verify_user() should return True with correct password.
    """
    auth.register_user("valid@user.com", "MySecret")

    # Verify with correct password
    assert auth.verify_user("valid@user.com", "MySecret") is True


def test_verify_user_failure_wrong_password(tmp_user_file):
    """
    verify_user() should return False if the password is incorrect.
    """
    auth.register_user("valid@user.com", "RealPass")

    # Wrong password => False
    assert auth.verify_user("valid@user.com", "WrongPass") is False


def test_verify_user_failure_no_such_user(tmp_user_file):
    """
    verify_user() should return False if the user doesn't exist at all.
    """
    # User "ghost@user.com" is not registered, so it shouldn't verify
    assert auth.verify_user("ghost@user.com", "Anything") is False


def test_generate_remember_me_token(tmp_user_file):
    """
    generate_remember_me_token() should create and store a unique token.
    """
    auth.register_user("remember@me.com", "somepass")
    token = auth.generate_remember_me_token("remember@me.com")
    assert token is not None
    assert len(token) > 0

    # Check that the token was saved
    data = json.loads(tmp_user_file.read_text(encoding="utf-8"))
    user = next(u for u in data["users"] if u["email"].lower() == "remember@me.com")
    assert user["remember_me_token"] == token


def test_get_user_by_token(tmp_user_file):
    """
    get_user_by_token() should return the user's email if token matches,
    else None.
    """
    auth.register_user("user@token.com", "abc123")
    token = auth.generate_remember_me_token("user@token.com")

    found_email = auth.get_user_by_token(token)
    assert found_email == "user@token.com"

    # Non-existent token => None
    assert auth.get_user_by_token("random-junk") is None


def test_clear_remember_me_token(tmp_user_file):
    """
    clear_remember_me_token() should remove any existing token for that user.
    """
    auth.register_user("bye@token.com", "pass")
    token = auth.generate_remember_me_token("bye@token.com")
    assert auth.get_user_by_token(token) == "bye@token.com"

    # Clear the token
    auth.clear_remember_me_token("bye@token.com")
    assert auth.get_user_by_token(token) is None
