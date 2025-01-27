import os

from dotenv import load_dotenv
import requests

# Load environment variables from a .env file
load_dotenv()


def send_email_via_mailgun(
    from_address: str, to_addresses: list, subject: str, body_text: str, cc_addresses: list = None
):
    """
    Sends an email via Mailgun's API using environment variables for credentials.

    Parameters:
    - from_address: Sender's email address (must be authorized in Mailgun).
    - to_addresses: List of recipient email addresses (e.g., ['user@example.com']).
    - subject: The subject of the email.
    - body_text: The email body as plain text or HTML.
    - cc_addresses: (Optional) List of email addresses to Cc.
    """

    # Retrieve Mailgun credentials from environment variables
    api_key = os.environ.get("MAILGUN_API_KEY")
    domain_name = os.environ.get("MAILGUN_DOMAIN")

    if not api_key or not domain_name:
        # Raise an error if credentials are missing
        raise ValueError("Mailgun credentials not set in environment variables.")

    # Construct the Mailgun API endpoint URL
    url = f"https://api.mailgun.net/v3/{domain_name}/messages"

    # Prepare the data payload for the email
    data = {
        "from": from_address,
        "to": to_addresses,
        "subject": subject,
        "text": body_text,
    }
    if cc_addresses:
        # Include Cc recipients if provided
        data["cc"] = cc_addresses

    # Make the POST request to Mailgun API
    response = requests.post(
        url, auth=("api", api_key), data=data  # Basic authentication using the API key  # Email data payload
    )

    # Handle non-200 status codes (failure scenarios)
    if response.status_code != 200:
        raise Exception(f"Mailgun send failed: {response.status_code} {response.text}")

    # Return the API response as JSON for further processing or debugging
    return response.json()
