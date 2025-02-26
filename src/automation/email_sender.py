import os
import re

from dotenv import load_dotenv
import requests

# Load environment variables from a .env file
load_dotenv()

# Regular expression for validating email addresses
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    """
    Validates an email address using a regex pattern.
    """
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_addresses(from_address, to_addresses, cc_addresses=None):
    """
    Validates sender and recipient email addresses before sending.
    """
    if not is_valid_email(from_address):
        raise ValueError(f"Invalid email: {from_address}")

    for addr in to_addresses:
        if not is_valid_email(addr):
            raise ValueError(f"Invalid email: {addr}")

    if cc_addresses:
        for addr in cc_addresses:
            if not is_valid_email(addr):
                raise ValueError(f"Invalid email: {addr}")


def parse_mailgun_error(response):
    """
    Attempts to extract a user-friendly error message
    from Mailgun's JSON response.
    """
    try:
        error_data = response.json()  # Might raise ValueError if not JSON
        if 'message' in error_data:
            mg_message = error_data['message']

        # Handle common free account restrictions
        if (
            "not allowed to send" in mg_message
            or "free accounts are for test purposes" in mg_message
            or "authorized recipients" in mg_message
        ):
            return "Your Mailgun sandbox domain only allows\n" "sending to authorized recipients."
        # Otherwise, return the original error message
        return mg_message
    except ValueError:
        pass

    return f"Mailgun error (status {response.status_code}). Check your email fields."


def send_email_via_mailgun(
    from_address: str,
    to_addresses: list,
    subject: str,
    body_text: str,
    cc_addresses: list = None,
    attachments: list = None,
):
    """
    Sends an email via Mailgun's API using environment variables for credentials.

    Parameters:
    - from_address: Sender's email address (must be authorized in Mailgun)
    - to_addresses: List of recipient email addresses (e.g., ['user@example.com'])
    - subject: The subject of the email
    - body_text: The email body as plain text
    - cc_addresses: (Optional) List of email addresses to Cc
    - attachments: (Optional) List of file paths to attach
    """

    # Retrieve Mailgun credentials from environment variables
    api_key = os.environ.get("MAILGUN_API_KEY", "").strip()
    domain_name = os.environ.get("MAILGUN_DOMAIN", "").strip()

    if not api_key.strip() or not domain_name.strip():
        # Raise an error if credentials are missing
        raise ValueError("Mailgun credentials not set\nin environment variables.")

    # Validate email addresses before sending
    validate_addresses(from_address, to_addresses, cc_addresses)

    # Construct the Mailgun API endpoint URL
    url = f"https://api.mailgun.net/v3/{domain_name}/messages"

    # Format the body text to preserve newlines
    formatted_body = body_text.replace('\n', '<br>')

    # Prepare the data payload for the email
    data = {
        "from": from_address,
        "to": to_addresses,
        "subject": subject,
        "text": body_text,  # Plain text version
        "html": f"<div style='white-space: pre-line;'>{formatted_body}</div>",  # HTML version with preserved formatting
    }

    if cc_addresses:
        # Include Cc recipients if provided
        data["cc"] = cc_addresses

    # Prepare files if there are attachments
    files = []
    if attachments:
        for path in attachments:
            if os.path.isfile(path):
                files.append(("attachment", open(path, "rb")))

    # Make the POST request to Mailgun API
    try:
        response = requests.post(url, auth=("api", api_key), data=data, files=files)

        # Close all opened files
        for _, file in files:
            file.close()

        # Handle non-200 status codes with a short message
        if response.status_code == 401:
            # Means invalid credentials
            raise Exception("Invalid or missing Mailgun credentials.")
        elif response.status_code != 200:
            # Parse a short error from the Mailgun response
            error_msg = parse_mailgun_error(response)
            raise Exception(error_msg)

        return response.json()

    except Exception as e:
        # Make sure files are closed even if an error occurs
        for _, file in files:
            file.close()
        raise e
