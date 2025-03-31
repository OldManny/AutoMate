import json
import sys

from PyQt5.QtCore import QCoreApplication
import pytest

from src.utils import auth

# Store the original state of auth globals
_original_paths_initialized = auth._paths_initialized
_original_user_data_file = auth.USER_DATA_FILE
_original_last_token_file = auth.LAST_TOKEN_FILE
_original_app_data_dir = auth.APP_DATA_DIR

@pytest.fixture(scope="function", autouse=True)
def manage_qapp_and_auth_state(monkeypatch):
    """
    Ensures QApp exists for potential setup, and importantly,
    resets the auth module's path state after each test.
    """
    # QApp Setup
    app = QCoreApplication.instance()
    created_app = False
    if app is None:
        app = QCoreApplication(sys.argv if hasattr(sys, 'argv') else [''])
        created_app = True

    org_name_set = False
    app_name_set = False
    if not QCoreApplication.organizationName():
        QCoreApplication.setOrganizationName("AutoMateTestOrg")
        org_name_set = True
    if not QCoreApplication.applicationName():
        QCoreApplication.setApplicationName("AutoMateTestApp")
        app_name_set = True

    yield # Test runs

    # Cleanup
    auth._paths_initialized = _original_paths_initialized
    auth.USER_DATA_FILE = _original_user_data_file
    auth.LAST_TOKEN_FILE = _original_last_token_file
    auth.APP_DATA_DIR = _original_app_data_dir


@pytest.fixture
def mock_auth_paths_direct(tmp_path, monkeypatch):
    """
    Directly patches the global path variables in the auth module
    and sets the initialized flag to True to bypass internal init logic
    during the test execution.
    """
    # Define temporary file paths
    temp_app_data_dir = tmp_path / "auth_test_data"
    temp_user_data_file = temp_app_data_dir / "user_data.json"
    temp_last_token_file = temp_app_data_dir / "last_token.txt"

    # Create the directory and initial user file
    temp_app_data_dir.mkdir(parents=True, exist_ok=True)
    if not temp_user_data_file.exists():
        temp_user_data_file.write_text(json.dumps({"users": []}), encoding="utf-8")

    # Directly patch the globals in the auth module
    monkeypatch.setattr(auth, "USER_DATA_FILE", str(temp_user_data_file))
    monkeypatch.setattr(auth, "LAST_TOKEN_FILE", str(temp_last_token_file))
    monkeypatch.setattr(auth, "APP_DATA_DIR", str(temp_app_data_dir))

    # Set the paths initialized flag to True
    monkeypatch.setattr(auth, "_paths_initialized", True)

    yield {
        "user_data": temp_user_data_file,
        "last_token": temp_last_token_file,
        "app_data": temp_app_data_dir
    }


def test_register_user_success(mock_auth_paths_direct):
    """Test user registration with valid data."""

    # Ensure the user data file is empty before the test
    result = auth.register_user("test@example.com", "Password123")
    assert result is True
    user_file = mock_auth_paths_direct["user_data"]
    assert user_file.exists()
    data = json.loads(user_file.read_text(encoding="utf-8"))
    assert len(data["users"]) == 1
    assert data["users"][0]["email"] == "test@example.com"
    assert "hashed_password" in data["users"][0]

def test_register_user_already_exists(mock_auth_paths_direct):
    """Test user registration with an already existing email."""

    # Register the user first
    assert auth.register_user("test@example.com", "Password123") is True
    assert auth.register_user("test@example.com", "AnotherPass") is False
    user_file = mock_auth_paths_direct["user_data"]
    data = json.loads(user_file.read_text(encoding="utf-8"))
    assert len(data["users"]) == 1

def test_verify_user_success(mock_auth_paths_direct):
    """Test user verification with valid credentials."""

    # Register a user first
    auth.register_user("valid@user.com", "MySecret")
    assert auth.verify_user("valid@user.com", "MySecret") is True

def test_verify_user_failure_wrong_password(mock_auth_paths_direct):
    """Test user verification with an incorrect password."""
    auth.register_user("valid@user.com", "RealPass")
    assert auth.verify_user("valid@user.com", "WrongPass") is False

def test_verify_user_failure_no_such_user(mock_auth_paths_direct):
    """Test user verification with a non-existent user."""
    assert auth.verify_user("ghost@user.com", "Anything") is False

def test_generate_remember_me_token(mock_auth_paths_direct):
    """Test generation of remember me token."""
    auth.register_user("remember@me.com", "somepass")
    token = auth.generate_remember_me_token("remember@me.com")
    assert isinstance(token, str) and len(token) > 10

    user_file = mock_auth_paths_direct["user_data"]
    data = json.loads(user_file.read_text(encoding="utf-8"))
    user = next((u for u in data["users"] if u["email"].lower() == "remember@me.com"), None)
    assert user is not None
    assert user["remember_me_token"] == token

def test_get_user_by_token(mock_auth_paths_direct):
    """Test retrieval of user by remember me token."""
    auth.register_user("user@token.com", "abc123")
    token = auth.generate_remember_me_token("user@token.com")
    assert auth.get_user_by_token(token) == "user@token.com"
    assert auth.get_user_by_token("non-existent-token") is None
    assert auth.get_user_by_token("") is None

def test_clear_remember_me_token(mock_auth_paths_direct):
    """Test clearing of remember me token."""
    auth.register_user("bye@token.com", "pass")
    token = auth.generate_remember_me_token("bye@token.com")
    assert auth.get_user_by_token(token) == "bye@token.com"

    auth.clear_remember_me_token("bye@token.com")

    user_file = mock_auth_paths_direct["user_data"]
    data = json.loads(user_file.read_text(encoding="utf-8"))
    user = next((u for u in data["users"] if u["email"].lower() == "bye@token.com"), None)
    assert user is not None
    assert user.get("remember_me_token", "") == ""
    assert auth.get_user_by_token(token) is None

def test_save_load_last_token(mock_auth_paths_direct):
    """Test saving and loading the last token."""
    token_to_save = "my-test-token-123"
    auth.save_last_token(token_to_save)

    token_file = mock_auth_paths_direct["last_token"]
    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8") == token_to_save

    loaded_token = auth.load_last_token()
    assert loaded_token == token_to_save

def test_clear_last_token_file(mock_auth_paths_direct):
    """Test clearing the last token file."""
    token_file = mock_auth_paths_direct["last_token"]
    if not token_file.exists():
        token_file.touch()
    token_file.write_text("some-token", encoding="utf-8")
    assert token_file.exists()

    auth.clear_last_token_file()
    assert not token_file.exists()

def test_load_last_token_no_file(mock_auth_paths_direct):
    """Test loading last token when the file doesn't exist."""
    token_file = mock_auth_paths_direct["last_token"]
    if token_file.exists():
        token_file.unlink()
    assert auth.load_last_token() is None

def test_load_user_data_no_file(mock_auth_paths_direct):
    """Test loading user data when the file doesn't exist."""
    user_file = mock_auth_paths_direct["user_data"]
    if user_file.exists():
        user_file.unlink()
    data = auth.load_user_data()
    assert data == {"users": []}
