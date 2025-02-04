import sys
import json
import requests
import msal
import atexit
import logging
import os
from fastapi import FastAPI, HTTPException
from dataClasses import *
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio

global DB
DB = {  # stores the data so it can be accessed faster
    "result": None,
    "creds": None,
    "accounts": None,
    "result": None,
    "flow": None,
    "client_id": "cda7262c-6d80-4c31-adb6-5d9027364fa7",
    "scopes": ["User.Read", "Mail.Read"],
    "graph_endpoint": "https://graph.microsoft.com/v1.0",
    "cache_path": os.path.join(".", "cache.bin"),
    "token_cache": msal.SerializableTokenCache(),
    "app": None,
    "authority": "https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",
}


async def refresh_token_loop():
    while True:
        try:
            if DB["result"]:
                accounts = DB["app"].get_accounts()
                if accounts:
                    chosen = accounts[0]
                    result = DB["app"].acquire_token_silent(
                        scopes=DB["scopes"], account=chosen
                    )
                    if result:
                        DB["result"] = result
                        print("Token refreshed successfully")
        except Exception as e:
            print(f"Error refreshing token: {e}")
        await asyncio.sleep(3600)  # Refresh every hour


@asynccontextmanager
async def lifespan(app: FastAPI):  # life circle of the app
    global DB
    # Initialize token cache from file
    if os.path.exists(DB["cache_path"]):
        DB["token_cache"].deserialize(open(DB["cache_path"], "r").read())

    # Register cache persistence
    atexit.register(
        lambda: open(DB["cache_path"], "w").write(DB["token_cache"].serialize())
    )

    # Initialize MSAL app
    DB["app"] = msal.PublicClientApplication(
        DB["client_id"], authority=DB["authority"], token_cache=DB["token_cache"]
    )

    # Start token refresh task
    refresh_task = asyncio.create_task(refresh_token_loop())

    yield

    # Cleanup
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/accounts")
async def get_accounts() -> List[Dict]:
    """Get all accounts from cache"""
    global DB
    accounts = DB["app"].get_accounts()
    if accounts:
        logging.info("Account(s) exists in cache")
        return accounts
    else:
        logging.info("No accounts found in cache")
        return []


@app.post("/token/acquire")
async def acquire_token(account_id: str):
    """Acquire token for specific account"""
    global DB
    accounts = DB["app"].get_accounts()
    chosen = next((acc for acc in accounts if acc["username"] == account_id), None)

    if not chosen:
        raise HTTPException(status_code=404, detail="Account not found")

    result = DB["app"].acquire_token_silent(scopes=DB["scopes"], account=chosen)
    if result:
        return result
    else:
        return await initiate_device_flow()


@app.post("/auth/device-flow")
async def initiate_device_flow():
    """Start device flow authentication"""
    global DB
    flow = DB["app"].initiate_device_flow(scopes=DB["scopes"])

    if "user_code" not in flow:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create device flow: {json.dumps(flow, indent=4)}",
        )

    DB["flow"] = flow
    return {
        "verification_uri": flow["verification_uri"],
        "user_code": flow["user_code"],
        "message": flow["message"],
    }


@app.get("/auth/token")
async def get_token_by_flow():
    """Complete device flow authentication"""
    global DB
    if not DB["flow"]:
        raise HTTPException(status_code=400, detail="No active device flow")

    result = DB["app"].acquire_token_by_device_flow(DB["flow"])
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error_description"])

    DB["result"] = result
    return result


@app.get("/status")
async def get_status():
    """Get current authentication status"""
    global DB
    return {
        "has_accounts": len(DB["app"].get_accounts()) > 0 if DB["app"] else False,
        "has_token": DB["result"] is not None,
        "has_active_flow": DB["flow"] is not None,
    }
