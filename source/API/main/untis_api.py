from fastapi import APIRouter, HTTPException
import webuntis
import logging
import asyncio
import json
import traceback
import datetime
import time
from typing import Optional

import webuntis.errors
from db import DB, SECURE_DB
from dataClasses import credentials

router = APIRouter(prefix="/untis", tags=["Untis"])


# --- Error Types ---
class UntisSessionError(Exception):
    """Raised when Untis session operations fail."""

    pass


class UntisCredentialsError(Exception):
    """Raised when Untis credentials are invalid or missing."""

    pass


# --- Session Management ---
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
                with webuntis.Session(
                    username=creds.username,
                    password=creds.password,
                    server=creds.server,
                    school=creds.school,
                    useragent="OpenClock",
                ).login() as session:
                    # Test connection with student parameter
                    DB["untis_state"] = True
                    return True

            except Exception as e:
                retry_count -= 1
                if retry_count == 0:
                    raise e
                logging.warning(f"Connection error, retrying... ({3-retry_count}/3)")
                await asyncio.sleep(delay)

    except Exception as e:
        DB["untis_state"] = False
        logging.error(f"Failed to create Untis session: {str(e)}")
        return False


async def set_timetable(dayRange: int) -> bool:
    """Get and store timetable data."""
    try:
        if not SECURE_DB.get("untis_creds"):
            raise ValueError("No Untis credentials configured")

        creds = SECURE_DB["untis_creds"]

        # Calculate date range
        start_date = datetime.datetime.now().date()
        end_date = start_date + datetime.timedelta(days=dayRange)

        with webuntis.Session(
            username=creds.username,
            password=creds.password,
            server=creds.server,
            school=creds.school,
            useragent="OpenClock",
        ).login() as session:
            DB["timeTable"] = session.timetable(start=start_date, end=end_date)
            return True

    except Exception as e:
        logging.error(f"Failed to fetch timetable: {str(e)}")
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
            if not DB["untis_state"] or DB["untis_session"] is None:
                try:
                    if not SECURE_DB["untis_creds"]:
                        with open("creds.json", "r") as f:
                            creds = json.load(f)
                            SECURE_DB["untis_creds"] = credentials(**creds)
                    await set_untis_session()
                except Exception as e:
                    logging.error(f"Credential loading error: {e}")
                    await asyncio.sleep(300)
                    continue

            if await set_timetable(10):
                logging.info("Timetable updated successfully")
            else:
                logging.warning("Failed to update timetable")
        except Exception as e:
            logging.error(f"Untis update error: {e}")
            DB["untis_state"] = False
        await asyncio.sleep(300)
