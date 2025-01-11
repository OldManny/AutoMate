import json
import os
from typing import Optional
import uuid

import bcrypt

# File where user data is stored
USER_DATA_FILE = "user_data.json"


def load_user_data():
    """
    Loads and returns the JSON content from USER_DATA_FILE.
    If the file does not exist, returns an empty dictionary.
    """
    if not os.path.exists(USER_DATA_FILE):
        return {"users": []}

    with open(USER_DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"users": []}
    return data


def save_user_data(data):
    """
    Saves the given dictionary to USER_DATA_FILE as JSON.
    """
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


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

    new_user = {"email": email, "hashed_password": hashed_pw_str, "remember_me_token": ""}  # default empty

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
