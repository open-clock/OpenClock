from fastapi import APIRouter, HTTPException
import msal
import logging
import asyncio
import aiohttp
import traceback
from typing import List, Dict
from db import DB, SECURE_DB
from dataClasses import EmailMessage

router = APIRouter(prefix="/microsoft", tags=["Microsoft"])


def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")


@router.get("/login")
async def initiate_ms_login():
    """Start Microsoft login flow."""
    try:
        flow = DB["ms_app"].initiate_device_flow(scopes=SECURE_DB["scopes"])
        if "user_code" not in flow:
            raise HTTPException(status_code=500, detail="Failed to create device flow")
        DB["ms_flow"] = flow
        return {
            "verification_uri": flow["verification_uri"],
            "user_code": flow["user_code"],
            "message": flow["message"],
        }
    except Exception as e:
        raise handle_error(e, "Microsoft login failed")


@router.get("/accounts")
async def get_ms_accounts() -> List[Dict]:
    """Get all Microsoft accounts from cache."""
    try:
        accounts = DB["ms_app"].get_accounts()
        return accounts if accounts else []
    except Exception as e:
        raise handle_error(e, "Failed to fetch accounts")


@router.get("/messages")
async def get_ms_messages():
    """Get messages from Microsoft Graph."""
    try:
        if not DB["ms_result"]:
            raise HTTPException(status_code=401, detail="Not authenticated")

        headers = {"Authorization": f'Bearer {DB["ms_result"]["access_token"]}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{SECURE_DB["graph_endpoint"]}/me/messages', headers=headers
            ) as response:
                data = await response.json()

                if "value" not in data:
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
        logging.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout_ms_account():
    """Logout from Microsoft account."""
    try:
        DB["ms_app"].remove_account(DB["account"])
        DB["account"] = None
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        raise handle_error(e, "Logout failed")


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
            logging.error(f"MS token refresh error: {e}")
        await asyncio.sleep(3600)
