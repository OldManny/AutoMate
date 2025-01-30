import os

from dotenv import load_dotenv
import requests

# Load environment variables from a .env file
load_dotenv()


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
    api_key = os.environ.get("MAILGUN_API_KEY")
    domain_name = os.environ.get("MAILGUN_DOMAIN")

    if not api_key or not domain_name:
        # Raise an error if credentials are missing
        raise ValueError("Mailgun credentials not set in environment variables.")

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

        # Handle non-200 status codes
        if response.status_code != 200:
            raise Exception(f"Mailgun send failed: {response.status_code} {response.text}")

        return response.json()

    except Exception as e:
        # Make sure files are closed even if an error occurs
        for _, file in files:
            file.close()
        raise e
