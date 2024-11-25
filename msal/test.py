import msal
import time
import json
import requests

# App configuration
CLIENT_ID = "d743be8a-0e6b-4cde-8294-f090040fb7e6"
SCOPES = ["User.Read", "Mail.Read"]  # Added Mail.Read scope
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

def get_user_info(access_token):
    # Set up headers with access token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Get user profile
    profile_response = requests.get(
        f"{GRAPH_API_ENDPOINT}/me",
        headers=headers
    )
    
    # Get user emails
    emails_response = requests.get(
        f"{GRAPH_API_ENDPOINT}/me/messages?$top=5&$select=subject,receivedDateTime",
        headers=headers
    )

    return profile_response.json(), emails_response.json()

def get_access_token():
    # Initialize MSAL client
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority="https://login.microsoftonline.com/common"
    )

    # Initiate device flow authentication
    flow = app.initiate_device_flow(scopes=SCOPES)
    
    if "user_code" not in flow:
        print("Could not create device flow")
        return

    print("\nAuthentication Required!")
    print(f"\nTo sign in, use a web browser to open {flow['verification_uri']}")
    print(f"Enter the code: {flow['user_code']}")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        print("\nAuthentication successful!")
        return result
    else:
        print("\nAuthentication failed:", result.get("error"))
        print("Error description:", result.get("error_description"))
        return None

if __name__ == "__main__":
    token_result = get_access_token()
    if token_result:
        print("\nAccess token acquired successfully!")
        
        # Get and display user information
        profile, emails = get_user_info(token_result['access_token'])
        
        print("\nUser Profile:")
        print(f"Display Name: {profile.get('displayName')}")
        print(f"Email: {profile.get('userPrincipalName')}")
        
        print("\nRecent Emails:")
        for email in emails.get('value', []):
            print(f"\nSubject: {email.get('subject')}")
            print(f"Received: {email.get('receivedDateTime')}")