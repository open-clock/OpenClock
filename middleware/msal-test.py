import sys
import json
import requests
import msal
import atexit
import logging
import os

# App configuration
CLIENT_ID = "cda7262c-6d80-4c31-adb6-5d9027364fa7"
SCOPES = ["User.Read", "Calendars.Read", "Calendars.Read.Shared", "Calendars.ReadBasic", "EduAssignments.Read", "EduAssignments.ReadBasic", "Mail.Read", "Mail.Read.Shared", "Mail.ReadBasic", "Mail.ReadBasic.Shared", "Team.ReadBasic.All"]  # Added Mail.Read scope
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

cache_filename = os.path.join(".","cache.bin")
cache = msal.SerializableTokenCache()
if os.path.exists(cache_filename):
    cache.deserialize(open(cache_filename, "r").read())
atexit.register(lambda: open(cache_filename, "w").write(cache.serialize()) if cache.has_state_changed else None)

# Create a preferably long-lived app instance which maintains a token cache.
app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority="https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",
    token_cache= cache
)

# The pattern to acquire a token looks like this.
result = None

accounts = app.get_accounts()
if accounts:
    logging.info("Account(s) exists in cache, probably with token too. Let's try.")
    print("Pick the account you want to use to proceed:")
    for a in accounts:
        print(a["username"])
    # Assuming the end user chose this one
    chosen = accounts[0]
    # Now let's try to find a token in cache for this account
    result = app.acquire_token_silent(scopes=SCOPES, account=chosen)

if not result:
    logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError(
            "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    print(flow["message"])
    print("\nAuthentication Required!")
    print(f"\nTo sign in, use a web browser to open {flow['verification_uri']}")
    print(f"Enter the code: {flow['user_code']}")
    sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

    result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    # Calling graph using the access token
    graph_data = requests.get(  # Use token to call downstream service
        GRAPH_API_ENDPOINT + "/education/me/assignments",# ?$filter=status eq 'assigned'    # ?$top=5
        headers={'Authorization': 'Bearer ' + result['access_token']},).json()
    print("Graph API call result: %s" % json.dumps(graph_data, indent=2))
else:
    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))  # You may need this when reporting a bug