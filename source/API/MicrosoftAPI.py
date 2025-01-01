import sys
import json
import requests
import msal
import atexit
import logging
import os
import fastapi
from dataClasses import *
from contextlib import asynccontextmanager

global DB
DB = {                                                      #stores the data so it can be accessed faster
        "result" : None,  
        "creds" : None,
        "accounts" : None,
        "result" : None,
        "flow" : None,
        "client_id": "cda7262c-6d80-4c31-adb6-5d9027364fa7",
        "scopes": ["User.Read", "Mail.Read"],
        "graph_endpoint": "https://graph.microsoft.com/v1.0",
        "cache_path": os.path.join(".", "cache.bin"),
        "token_cache": msal.SerializableTokenCache(),
        "app": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):                               #life circle of the app   
    global DB
    # Initialize token cache from file
    if os.path.exists(DB["cache_path"]):
        DB["token_cache"].deserialize(open(DB["cache_path"], "r").read())
    
    # Register cache persistence
    atexit.register(lambda: 
        open(DB["cache_path"], "w").write(DB["token_cache"].serialize())
    )
    
    # Initialize MSAL app
    DB["app"] = msal.PublicClientApplication(
        DB["client_id"],
        authority="https://login.microsoftonline.com/common",
        token_cache=DB["token_cache"]
    )
    
    yield

def getAccounts():
    global DB
    accounts = DB["app"].get_accounts()
    if accounts:
        print("Account(s) exists in cache, probably with token too. Let's try.")
        return accounts
    else:
        print("No suitable token exists in cache. Let's get a new one from AAD.")
        return None
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# App configuration
CLIENT_ID = "cda7262c-6d80-4c31-adb6-5d9027364fa7"
SCOPES = ["User.Read", "Mail.Read"]  # Added Mail.Read scope
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

cache_filename = os.path.join(".","cache.bin")
cache = msal.SerializableTokenCache()
if os.path.exists(cache_filename):
    cache.deserialize(open(cache_filename, "r").read())
atexit.register(lambda:
    open(cache_filename, "w").write(cache.serialize())
    # Hint: The following optional line persists only when state changed
    if cache.has_state_changed else None
    )


# Create a preferably long-lived app instance which maintains a token cache.
app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority="https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",
    token_cache= cache
)

def acquire_token():
    logging.info("Account(s) exists in cache, probably with token too. Let's try.")
    print("Pick the account you want to use to proceed:")
    for a in accounts:
        print(a["username"])
    # Assuming the end user chose this one
    chosen = accounts[0]
    # Now let's try to find a token in cache for this account
    DB.result = app.acquire_token_silent(scopes=SCOPES, account=chosen)

def result():
    logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

    DB.flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError(
            "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    print(flow["message"])
    print("\nAuthentication Required!")
    print(f"\nTo sign in, use a web browser to open {flow['verification_uri']}")
    print(f"Enter the code: {flow['user_code']}")
    sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

    DB.result = app.acquire_token_by_device_flow(flow)

def eccess_token():
    if "access_token" in DB.result:
        # Calling graph using the access token
        graph_data = requests.get(  # Use token to call downstream service
            GRAPH_API_ENDPOINT + "/me",
            headers={'Authorization': 'Bearer ' + DB.result['access_token'],}).json()
        print("Graph API call result: %s" % json.dumps(graph_data, indent=2))
    else:
        print(DB.result.get("error"))
        print(DB.result.get("error_description"))
        print(DB.result.get("correlation_id"))  # You may need this when reporting a bug
