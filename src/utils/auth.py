import json
import os
import sys
from typing import Optional
import uuid

from PyQt5.QtCore import QCoreApplication, QStandardPaths
import bcrypt
import keyring
from keyring.errors import KeyringError

# Use application's name to avoid collisions
APP_NAME = "AutoMate"
MAILGUN_API_KEY_SERVICE = f"{APP_NAME}-MailgunAPIKey"
MAILGUN_DOMAIN_SERVICE = f"{APP_NAME}-MailgunDomain"

USER_DATA_FILE = None
LAST_TOKEN_FILE = None
APP_DATA_DIR = None
_paths_initialized = False  # Flag to prevent redundant checks


def _initialize_auth_paths():
    """Internal function to set auth paths if not already set."""
    global USER_DATA_FILE, LAST_TOKEN_FILE, APP_DATA_DIR, _paths_initialized
    if _paths_initialized:
        return  # Already done

    if not QCoreApplication.instance():
        print("CRITICAL ERROR: No QCoreApplication instance found when initializing auth paths.", file=sys.stderr)
        raise RuntimeError("QCoreApplication instance required for auth path initialization.")

    if not QCoreApplication.organizationName() or not QCoreApplication.applicationName():
        print("Warning: Org/App names not set before getting AppDataLocation in auth.", file=sys.stderr)

        # Set defaults
        QCoreApplication.setOrganizationName("AutoMate")
        QCoreApplication.setApplicationName("AutoMate")

    APP_DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not APP_DATA_DIR or not os.path.isdir(os.path.dirname(APP_DATA_DIR)):  # Checks the path
        print(
            f"CRITICAL ERROR: Could not determine a valid AppDataLocation. Path received: {APP_DATA_DIR}",
            file=sys.stderr,
        )
        raise RuntimeError("Could not determine a valid AppDataLocation.")

    try:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
    except OSError as e:
        print(f"CRITICAL ERROR: Could not create AppData directory '{APP_DATA_DIR}': {e}", file=sys.stderr)
        raise RuntimeError(f"Failed to create AppData directory: {e}")

    USER_DATA_FILE = os.path.join(APP_DATA_DIR, "user_data.json")
    LAST_TOKEN_FILE = os.path.join(APP_DATA_DIR, "last_token.txt")
    _paths_initialized = True


def get_app_data_dir():
    """Gets the standard application data directory."""

    if not QCoreApplication.organizationName() or not QCoreApplication.applicationName():
        print("Warning: Org/App names not set before getting AppDataLocation.")

        QCoreApplication.setOrganizationName("YourOrgName")  # Fallback
        QCoreApplication.setApplicationName("AutoMate")  # Fallback

    path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    os.makedirs(path, exist_ok=True)
    return path


# This is the location where user data will be stored on the user's system.
# Is a standard location for application data on Windows, macOS, and Linux.
APP_DATA_DIR = get_app_data_dir()
USER_DATA_FILE = os.path.join(APP_DATA_DIR, "user_data.json")
LAST_TOKEN_FILE = os.path.join(APP_DATA_DIR, "last_token.txt")

print(f"Auth using user data file: {USER_DATA_FILE}")
print(f"Auth using token file: {LAST_TOKEN_FILE}")


def load_user_data():
    """Loads user data from the standard app data location."""
    _initialize_auth_paths()  # Ensure paths are set

    if not os.path.exists(USER_DATA_FILE):
        return {"users": []}
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "users" not in data:  # Basic validation
            print(f"Warning: user_data.json at {USER_DATA_FILE} is missing 'users' key. Resetting.", file=sys.stderr)
            return {"users": []}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Failed to load/decode user data from {USER_DATA_FILE}: {e}. Resetting.", file=sys.stderr)
        data = {"users": []}  # Reset if file is corrupted or not found mid-operation
    except Exception as e:
        print(f"Error loading user data from {USER_DATA_FILE}: {e}", file=sys.stderr)
        data = {"users": []}  # Fallback on other errors
    return data


def save_user_data(data):
    """Saves user data to the standard app data location."""
    _initialize_auth_paths()

    if not USER_DATA_FILE:
        print("ERROR: USER_DATA_FILE path not set in auth module.")
        return
    try:
        # Specify encoding and use atomic write pattern (write to temp, then rename)
        os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
        temp_file = USER_DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, USER_DATA_FILE)  # Atomic rename/replace
    except Exception as e:
        print(f"Error saving user data to {USER_DATA_FILE}: {e}", file=sys.stderr)


def register_user(email: str, password: str) -> bool:
    """
    Registers a new user with the email and password.
    Returns True if registration succeeded, False if the user already exists.
    """
    data = load_user_data()

    # Check if user with this email already exists
    for user in data["users"]:
        if user["email"].lower() == email.lower():
            return False  # Already exists

    # Hash the password with bcrypt
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    hashed_pw_str = hashed_pw.decode("utf-8")

    new_user = {
        "email": email,
        "hashed_password": hashed_pw_str,
        "remember_me_token": "",
        "mailgun_api_key": "",
        "mailgun_domain": "",
    }

    data["users"].append(new_user)
    save_user_data(data)
    return True


def verify_user(email: str, password: str) -> bool:
    """
    Checks if the user with the given email and password exists and password is correct.
    """
    data = load_user_data()

    for user in data["users"]:
        if user["email"].lower() == email.lower():
            stored_hash = user["hashed_password"].encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

    return False


def generate_remember_me_token(email: str) -> str:
    """
    Generates a random token for 'Remember Me' and updates the user record in the JSON.
    Returns the new token.
    """
    data = load_user_data()
    token = str(uuid.uuid4())  # Random unique token

    for user in data["users"]:
        if user["email"].lower() == email.lower():
            user["remember_me_token"] = token
            break

    save_user_data(data)
    return token


def get_mailgun_credentials(email: str) -> Optional[tuple[str, str]]:
    """
    Retrieves the Mailgun API Key and Domain for a given user email.
    Returns (api_key, domain) or None if user not found.
    """
    data = load_user_data()
    user_exists = any(user["email"].lower() == email.lower() for user in data["users"])
    if not user_exists:
        print(f"User {email} not found in user_data.json")
        return None  # User record doesn't exist

    api_key = ""
    domain = ""
    try:
        # Retrieve from keyring, using email as the 'username' for the service
        stored_api_key = keyring.get_password(MAILGUN_API_KEY_SERVICE, email)
        stored_domain = keyring.get_password(MAILGUN_DOMAIN_SERVICE, email)

        api_key = stored_api_key if stored_api_key is not None else ""
        domain = stored_domain if stored_domain is not None else ""
    except KeyringError as e:
        # Handle potential keyring errors (e.g., backend unavailable)
        print(f"Keyring error while getting credentials for {email}: {e}", file=sys.stderr)
    except Exception as e:
        # Catch other potential errors
        print(f"Unexpected error retrieving credentials from keyring for {email}: {e}", file=sys.stderr)

    # Return the retrieved (or default empty) credentials
    return api_key, domain


def save_mailgun_credentials(email: str, api_key: str, domain: str) -> bool:
    """
    Saves Mailgun credentials for the specified user securely in the system keyring.
    We still check user_data.json to ensure the user exists.
    Returns True if successful, False otherwise.
    """
    # Check if the user exists in user_data.json first
    data = load_user_data()
    user_found = False
    for user in data["users"]:
        if user["email"].lower() == email.lower():
            user_found = True
            break

    if not user_found:
        print(f"Error: Could not find user {email} in user_data.json to save Mailgun credentials.")
        return False

    try:
        # Save to keyring
        keyring.set_password(MAILGUN_API_KEY_SERVICE, email, api_key.strip())
        keyring.set_password(MAILGUN_DOMAIN_SERVICE, email, domain.strip())
        return True
    except KeyringError as e:
        print(f"Keyring error saving credentials for {email}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error saving credentials to keyring for {email}: {e}", file=sys.stderr)
        return False


def get_user_by_token(token: str) -> Optional[str]:
    """
    Returns the email of the user with the given 'remember me' token, or None if invalid.
    """
    data = load_user_data()
    for user in data["users"]:
        if user["remember_me_token"] == token:
            return user["email"]
    return None


def clear_remember_me_token(email: str) -> None:
    """
    Clears the 'remember me' token for the given email user.
    """
    data = load_user_data()

    for user in data["users"]:
        if user["email"].lower() == email.lower():
            user["remember_me_token"] = ""
            break

    save_user_data(data)


def save_last_token(token: str):
    """Saves the remember me token to its file."""
    _initialize_auth_paths()
    if not LAST_TOKEN_FILE:
        print("ERROR: LAST_TOKEN_FILE path not set in auth module.")
        return

    try:
        with open(LAST_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
    except Exception as e:
        print(f"Error saving last token to {LAST_TOKEN_FILE}: {e}", file=sys.stderr)


def load_last_token() -> Optional[str]:
    """Loads the remember me token from its file."""
    _initialize_auth_paths()
    if not LAST_TOKEN_FILE:
        print("ERROR: LAST_TOKEN_FILE path not set in auth module.")
        return None

    try:
        with open(LAST_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading last token from {LAST_TOKEN_FILE}: {e}", file=sys.stderr)
        return None


def clear_last_token_file():
    """Removes the token file."""
    if not LAST_TOKEN_FILE:
        print("ERROR: LAST_TOKEN_FILE path not set in auth module.")
        return

    try:
        if os.path.exists(LAST_TOKEN_FILE):
            os.remove(LAST_TOKEN_FILE)
    except Exception as e:
        print(f"Error clearing last token file {LAST_TOKEN_FILE}: {e}", file=sys.stderr)
