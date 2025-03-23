from fastapi import APIRouter, HTTPException
import msal
import logging
import time
import asyncio
import aiohttp
import traceback
from typing import List, Dict, Union, Optional
from db import DB, SECURE_DB
from dataClasses import EmailMessage
from util import log

router = APIRouter(prefix="/microsoft", tags=["Microsoft"])


def init_msal_app():
    """Initialize MSAL application."""
    try:
        if "ms_app" not in DB or not DB["ms_app"]:
            DB["ms_app"] = msal.PublicClientApplication(
                client_id=SECURE_DB["client_id"],
                authority=SECURE_DB["authority"],
                token_cache=DB["token_cache"],
            )
        return DB["ms_app"]
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        log(f"MSAL initialization failed: {str(e)} at {error_loc}")
        raise RuntimeError(f"MSAL initialization failed: {str(e)} at {error_loc}")


@router.post("/client-id")
async def set_client_id(client_id: str):
    """Set Microsoft client ID."""
    try:
        SECURE_DB["client_id"] = client_id
        return {"status": "success", "message": "Client ID set successfully"}
    except Exception as e:
        log(f"Failed to set client ID: {e}")
        return {"status": "error", "message": "Failed to set client ID"}


@router.post("/scopes")
async def set_scopes(scopes: List[str]):
    """Set Microsoft scopes."""
    try:
        SECURE_DB["scopes"] = scopes
        return {"status": "success", "message": "Scopes set successfully"}
    except Exception as e:
        log(f"Failed to set scopes: {e}")
        return {"status": "error", "message": "Failed to set scopes"}


@router.post("/graph-endpoint")
async def set_graph_endpoint(endpoint: str):
    """Set Microsoft Graph endpoint."""
    try:
        SECURE_DB["graph_endpoint"] = endpoint
        return {"status": "success", "message": "Graph endpoint set successfully"}
    except Exception as e:
        log(f"Failed to set graph endpoint: {e}")
        return {"status": "error", "message": "Failed to set graph endpoint"}


@router.post("/authority")
async def set_authority(authority: str):
    """Set Microsoft authority."""
    try:
        SECURE_DB["authority"] = authority
        return {"status": "success", "message": "Authority set successfully"}
    except Exception as e:
        log(f"Failed to set authority: {e}")
        return {"status": "error", "message": "Failed to set authority"}


@router.get("/login")
async def initiate_ms_login(force: bool = False):
    """Start Microsoft login flow or return existing token info."""
    try:
        # Check if we have a valid token and force is not requested
        if not force and DB.get("ms_result") and DB["ms_result"].get("access_token"):
            accounts = DB["ms_app"].get_accounts() if DB["ms_app"] else []
            if accounts:
                expires_on = DB["ms_result"].get("expires_on", 0)
                current_time = time.time()
                time_left = max(0, expires_on - current_time)

                return {
                    "status": "authenticated",
                    "account": accounts[0].get("username", "Unknown"),
                    "expires_on": expires_on,
                    "time_left_seconds": int(time_left),
                    "scopes": DB["ms_result"].get("scope", []),
                }

        # If no valid token or force requested, start new flow
        app = init_msal_app()
        flow = app.initiate_device_flow(scopes=SECURE_DB["scopes"])
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow")

        # Clear existing token if forcing new login
        if force:
            DB["ms_result"] = None

        DB["ms_flow"] = flow
        return {
            "status": "login_required",
            "verification_uri": flow["verification_uri"],
            "user_code": flow["user_code"],
            "message": flow["message"],
            "expires_in": flow.get("expires_in", 0),
        }

    except Exception as e:
        log(f"Microsoft login error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/accounts")
async def get_ms_accounts() -> List[Dict]:
    """Get all Microsoft accounts from cache."""
    try:
        accounts = DB["ms_app"].get_accounts()
        return accounts if accounts else []
    except Exception as e:
        log(f"Failed to get accounts: {e}")
        return []


@router.get("/messages")
async def get_ms_messages():
    """Get messages from Microsoft Graph."""
    try:
        # Check if we have an active device flow
        if "ms_flow" not in DB or not DB["ms_flow"]:
            log("No active authentication flow")
            raise HTTPException(status_code=401, detail="No active authentication flow")

        # Attempt to acquire token if not present
        if not DB.get("ms_result"):
            app = init_msal_app()
            DB["ms_result"] = app.acquire_token_by_device_flow(DB["ms_flow"])
            if not DB["ms_result"]:
                raise HTTPException(
                    status_code=401, detail="Authentication not completed"
                )

        headers = {"Authorization": f'Bearer {DB["ms_result"]["access_token"]}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{SECURE_DB["graph_endpoint"]}/me/messages', headers=headers
            ) as response:
                data = await response.json()

                if response.status == 401:
                    DB["ms_result"] = None  # Clear invalid token
                    log("Token expired")
                    raise HTTPException(status_code=401, detail="Token expired")

                if "value" not in data:
                    log("Invalid response")
                    raise HTTPException(status_code=500, detail="Invalid response")

                messages = []
                for msg in data["value"]:
                    messages.append(
                        EmailMessage(
                            subject=msg.get("subject", ""),
                            from_email=msg.get("from", {})
                            .get("emailAddress", {})
                            .get("address", ""),
                            received_date=msg.get("receivedDateTime", ""),
                            body=msg.get("body", {}).get("content", ""),
                        )
                    )
                return messages

    except Exception as e:
        log(f"Failed to get messages: {e}")
        return []


@router.get("/notifications")
async def get_ms_notifications():
    """Get notifications from Microsoft Graph."""
    try:
        # Check if we have an active device flow
        if "ms_flow" not in DB or not DB["ms_flow"]:
            log("No active authentication flow")
            raise HTTPException(status_code=401, detail="No active authentication flow")

        # Attempt to acquire token if not present
        if not DB.get("ms_result"):
            app = init_msal_app()
            DB["ms_result"] = app.acquire_token_by_device_flow(DB["ms_flow"])
            if not DB["ms_result"]:
                raise HTTPException(
                    status_code=401, detail="Authentication not completed"
                )

        headers = {"Authorization": f'Bearer {DB["ms_result"]["access_token"]}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{SECURE_DB["graph_endpoint"]}/me/notifications', headers=headers
            ) as response:
                data = await response.json()

                if response.status == 401:
                    DB["ms_result"] = None  # Clear invalid token
                    raise HTTPException(status_code=401, detail="Token expired")

                if "value" not in data:
                    raise HTTPException(status_code=500, detail="Invalid response")

                notifications = []
                for notification in data["value"]:
                    notifications.append(
                        {
                            "title": notification.get("title", ""),
                            "body": notification.get("body", ""),
                            "receivedDateTime": notification.get(
                                "receivedDateTime", ""
                            ),
                        }
                    )
                return notifications

    except Exception as e:
        log(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout_ms_account():
    """Logout from Microsoft account."""
    try:
        DB["ms_app"].remove_account(DB["account"])
        DB["account"] = None
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        log(f"Failed to logout: {e}")
        return {"status": "error", "message": "Failed to logout"}


async def ms_refresh_token_loop():
    """Background task to refresh Microsoft token."""
    while True:
        try:
            if DB["ms_result"]:
                accounts = DB["ms_app"].get_accounts()
                if accounts:
                    chosen = accounts[0]
                    result = DB["ms_app"].acquire_token_silent(
                        scopes=SECURE_DB["scopes"], account=chosen
                    )
                    if result:
                        DB["ms_result"] = result
                        logging.info("MS token refreshed")
        except Exception as e:
            log(f"MS token refresh error: {e}")
        await asyncio.sleep(3600)


@router.get("/device-flow-status")
async def get_device_flow_status() -> Dict[str, Union[bool, Optional[float]]]:
    """Check if there is an active device flow."""
    try:
        if "ms_flow" in DB and DB["ms_flow"]:
            # Check if flow has expired
            expires_at = DB["ms_flow"].get("expires_at", 0)
            current_time = time.time()
            is_active = expires_at > current_time

            return {
                "active": is_active,
                "expires_at": expires_at if is_active else None,
            }
        return {"active": False, "expires_at": None}
    except Exception as e:
        log(f"Failed to get device flow status: {e}")
        return {"active": False, "expires_at": None}
