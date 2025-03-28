from fastapi import APIRouter, HTTPException
import webuntis
import logging
import asyncio
import json
import traceback
import datetime
import time
from typing import Optional
from util import log
from pathlib import Path
import webuntis.errors
from db import DB, SECURE_DB
from dataClasses import credentials

router = APIRouter(prefix="/untis", tags=["Untis"])

# Add new constant for session timeout
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
LAST_SESSION_REFRESH = time.time()


# --- Error Types ---
class UntisSessionError(Exception):
    """Raised when Untis session operations fail."""

    pass


class UntisCredentialsError(Exception):
    """Raised when Untis credentials are invalid or missing."""

    pass


# --- Session Management ---
async def refresh_session_if_needed():
    """Check and refresh session if timeout exceeded."""
    global LAST_SESSION_REFRESH

    current_time = time.time()
    if current_time - LAST_SESSION_REFRESH > SESSION_TIMEOUT:
        try:
            if DB.get("untis_session"):
                DB["untis_session"].logout()
            DB["untis_session"] = None
            DB["untis_state"] = False
            success = await set_untis_session()
            if success:
                LAST_SESSION_REFRESH = current_time
                return True
            return False
        except Exception as e:
            log(f"Session refresh failed: {str(e)}", level="error", module="untis")
            return False
    return True


async def set_untis_session():
    """Initialize Untis session with context manager."""
    try:
        if not SECURE_DB.get("untis_creds"):
            raise UntisCredentialsError("No credentials configured")

        creds = SECURE_DB["untis_creds"]
        retry_count = 3
        delay = 1

        while retry_count > 0:
            try:
                # Force new session
                if DB.get("untis_session"):
                    try:
                        DB["untis_session"].logout()
                    except:
                        pass

                session = webuntis.Session(
                    username=creds.username,
                    password=creds.password,
                    server=creds.server,
                    school=creds.school,
                    useragent="OpenClock",
                ).login()

                DB["untis_session"] = session
                DB["untis_state"] = True
                global LAST_SESSION_REFRESH
                LAST_SESSION_REFRESH = time.time()
                log("Untis session established", module="untis")
                return True

            except webuntis.errors.RemoteError as e:
                retry_count -= 1
                if retry_count == 0:
                    raise e
                log(
                    f"Connection error, retrying... ({3-retry_count}/3)",
                    level="warning",
                    module="untis",
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff

    except Exception as e:
        DB["untis_state"] = False
        log(f"Failed to create Untis session: {str(e)}", level="error", module="untis")
        return False


async def set_timetable(dayRange: int) -> bool:
    """Get and store timetable data."""
    try:
        if not await refresh_session_if_needed():
            log("Failed to refresh session", level="error", module="untis")
            return False

        if not SECURE_DB.get("untis_creds"):
            log("No Untis credentials configured", level="error", module="untis")
            return False

        if not DB.get("untis_session"):
            log("No active Untis session", level="error", module="untis")
            if not await set_untis_session():
                return False

        # Calculate date range
        start_date = datetime.datetime.now().date()
        end_date = start_date + datetime.timedelta(days=dayRange)

        # Get timetable for current student
        timetable = DB["untis_session"].my_timetable(
            start=start_date,
            end=end_date,
        )

        if timetable:
            DB["timeTable"] = sorted(timetable, key=lambda x: x.start, reverse=False)
            log(f"Fetched {len(DB['timeTable'])} timetable entries", module="untis")
            return True

        log("No timetable entries found", level="warning", module="untis")
        return False

    except webuntis.errors.RemoteError as e:
        log(f"Untis remote error: {str(e)}", level="error", module="untis")
        return False
    except Exception as e:
        log(f"Failed to fetch timetable: {str(e)}", level="error", module="untis")
        return False


async def set_next_holiday() -> bool:
    """Update holiday data."""
    try:
        if not DB["untis_session"]:
            return False
        DB["holidays"] = DB["untis_session"].holidays()
        return True
    except Exception as e:
        logging.error(f"Failed to fetch holidays: {e}")
        return False


# --- Utility Functions ---
def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")


async def save_credentials(creds: dict):
    """Save Untis credentials to file."""
    try:
        json_object = json.dumps(creds, indent=4)
        with open("creds.json", "w") as outfile:
            outfile.write(json_object)
        return SECURE_DB["untis_creds"]
    except Exception as e:
        raise handle_error(e, "Failed to save credentials")


def validate_server_url(server: str) -> str:
    """Validate and format server URL."""
    try:
        if not server or server == "string":
            return ""

        # Remove protocol and clean URL
        server = server.strip().rstrip("/")
        if "://" in server:
            server = server.split("://")[1]

        # Get base domain and ensure no trailing /WebUntis
        server = server.split("/")[0].replace("/WebUntis", "")

        if not server:
            return ""

        return server  # WebUntis lib will add https:// and /WebUntis

    except Exception as e:
        logging.error(f"URL validation error: {str(e)}")
        return ""


# --- API Endpoints ---
@router.post("/set-creds")
async def setCreds(cred: credentials):
    """Set Untis credentials and initialize session."""
    try:
        # Format and validate server URL first
        cred.server = validate_server_url(cred.server)
        logging.info(f"Attempting to connect to Untis server: {cred.server}")

        # Save credentials first
        SECURE_DB["untis_creds"] = cred
        json_object = json.dumps(cred.model_dump(), indent=2)
        with open("creds.json", "w") as outfile:
            outfile.write(json_object)

        # Test connection before returning
        session = await set_untis_session()
        if not session:
            raise ValueError("Failed to establish Untis session")

        return {
            "status": "success",
            "message": "Credentials saved and connection established",
        }

    except Exception as e:
        raise handle_error(e, "Failed to set credentials")


@router.get("/timetable")
async def get_timetable(dayRange: int = 10):
    """Get timetable for specified day range."""
    try:
        if not await set_timetable(dayRange):
            raise ValueError("Failed to fetch timetable")

        timetable = DB.get("timeTable", [])

        # Format response
        formatted_timetable = []
        for entry in timetable:
            formatted_timetable.append(
                {
                    "subject": entry.subjects[0].name if entry.subjects else "Unknown",
                    "start": entry.start.strftime("%Y-%m-%d %H:%M"),
                    "end": entry.end.strftime("%Y-%m-%d %H:%M"),
                    "room": entry.rooms[0].name if entry.rooms else "Unknown",
                    "teachers": (
                        [t.name for t in entry.teachers] if entry.teachers else []
                    ),
                    "classes": [c.name for c in entry.klassen] if entry.klassen else [],
                }
            )

        return formatted_timetable

    except Exception as e:
        raise handle_error(e, "Failed to get timetable")


@router.get("/status")
async def get_untis_status():
    """Get Untis connection status."""
    try:
        return {
            "session": DB["untis_state"],
            "timetable_entries": len(DB["timeTable"]),
            "holidays": len(DB["holidays"]),
        }
    except Exception as e:
        raise handle_error(e, "Failed to get Untis status")


# --- Update Loop ---
async def untis_update_loop():
    """Background task for Untis updates."""
    while True:
        try:
            await refresh_session_if_needed()

            if DB["untis_state"] and DB.get("untis_session"):
                if await set_timetable(10):
                    log("Timetable updated successfully", module="untis")
                else:
                    log("Failed to update timetable", level="warning", module="untis")
            else:
                if not SECURE_DB["untis_creds"]:
                    try:
                        with open("creds.json", "r") as f:
                            creds = json.load(f)
                            SECURE_DB["untis_creds"] = credentials(**creds)
                    except Exception as e:
                        log(
                            f"Credential loading error: {e}",
                            level="error",
                            module="untis",
                        )
                        await asyncio.sleep(300)
                        continue
                await set_untis_session()

        except Exception as e:
            log(f"Untis update error: {e}", level="error", module="untis")
            DB["untis_state"] = False

        await asyncio.sleep(60)  # Check more frequently


@router.post("/logout")
async def logout_untis():
    """Logout from Untis and clear session data."""
    try:
        log("Starting Untis logout process", module="untis")

        # Close existing session if present
        if DB.get("untis_session"):
            try:
                DB["untis_session"].logout()
                log("Closed Untis session", module="untis")
            except Exception as e:
                log(f"Error closing session: {str(e)}", level="warning", module="untis")

        # Clear all session and credential data
        DB["untis_session"] = None
        DB["untis_state"] = False
        DB["timeTable"] = []
        DB["holidays"] = []
        SECURE_DB["untis_creds"] = None

        # Remove credentials file if it exists
        try:
            if Path("creds.json").exists():
                Path("creds.json").unlink()
                log("Removed credentials file", module="untis")
        except Exception as e:
            log(
                f"Failed to remove credentials file: {str(e)}",
                level="warning",
                module="untis",
            )

        log("Untis logout completed", module="untis")
        return {"status": "success", "message": "Logged out successfully"}

    except Exception as e:
        log(f"Logout failed: {str(e)}", level="error", module="untis")
        return {"status": "error", "message": f"Logout failed: {str(e)}"}


@router.get("/login-name")
async def get_untis_login_name():
    """Get current Untis login name from session."""
    try:
        if not await refresh_session_if_needed():
            log("Failed to refresh session", level="error", module="untis")

        if not SECURE_DB.get("untis_creds"):
            log("No Untis credentials configured", level="error", module="untis")
            return {"username": ""}

        login_name = SECURE_DB["untis_creds"].username
        return {"username": login_name}

    except Exception as e:
        raise handle_error(e, "Failed to get login name")
