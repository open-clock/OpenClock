from fastapi import APIRouter, HTTPException
import webuntis
import logging
import asyncio
import json
import traceback
import datetime
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
async def set_untis_session() -> bool:
    """Initialize Untis session with error handling."""
    try:
        if not SECURE_DB.get("untis_creds"):
            raise UntisCredentialsError("No credentials configured")

        creds = SECURE_DB["untis_creds"]
        logging.info(f"Connecting to Untis server: {creds.server}")

        session = webuntis.Session(
            username=creds.username,
            password=creds.password,
            server=creds.server,
            school=creds.school,
            useragent=creds.useragent,
        )

        session.login()
        DB["untis_session"] = session
        DB["untis_state"] = "connected"
        logging.info("Untis session created successfully")
        return True

    except Exception as e:
        DB["untis_session"] = None
        DB["untis_state"] = "error"
        logging.error(f"Failed to create Untis session: {e}")
        return False


async def set_timetable(dayRange: int) -> bool:
    global DB

    if DB["session"] is None:
        set_untis_session()

    now: datetime.date = datetime.datetime.now()

    try:
        print(
            f"Fetching timetable from {now} to {now + datetime.timedelta(days=dayRange)}"
        )
        timetable = DB["session"].my_timetable(
            start=now, end=now + datetime.timedelta(days=dayRange)
        )
        DB["timeTable"] = sorted(timetable, key=lambda x: x.start, reverse=False)
        return True
    except Exception as e:
        print(f"Failed to set timetable: {e}")
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


# --- Update Loop ---
async def untis_update_loop():
    """Background task for Untis updates."""
    while True:
        try:
            if DB["untis_state"] != "connected" or DB["untis_session"] is None:
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
            DB["untis_state"] = "error"
        await asyncio.sleep(300)


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
            logging.debug("Empty or default server URL")
            return ""

        # Clean URL - remove protocol and trailing slashes
        server = server.strip().rstrip("/")
        if "://" in server:
            server = server.split("://")[1]

        # Get base domain only (e.g., ache.webuntis.com)
        server = server.split("/")[0]

        if not server:
            logging.debug("Empty server after cleaning")
            return ""

        # Return only the base URL without jsonrpc.do
        formatted_url = f"https://{server}"
        logging.debug(f"Formatted Untis URL: {formatted_url}")
        return formatted_url

    except Exception as e:
        logging.error(f"URL validation error: {str(e)}")
        return ""


def init_untis_session():
    """Initialize Untis session with credentials check."""
    try:
        if not SECURE_DB.get("untis_creds"):
            logging.debug("No Untis credentials found")
            DB["untis_state"] = "disconnected"
            return None

        creds = SECURE_DB["untis_creds"]

        # Validate credentials before attempting connection
        if not all([creds.username, creds.password, creds.server, creds.school]):
            logging.error("Missing required credentials")
            DB["untis_state"] = "disconnected"
            return None

        # Get and validate server URL
        server = validate_server_url(creds.server)
        logging.info(f"Attempting connection to: {server}")

        # Create session with verbose logging
        try:
            DB["untis_session"] = webuntis.Session(
                username=creds.username,
                password=creds.password,
                server=server,
                school=creds.school,
                useragent="OpenClock",
            )

            # Test login explicitly
            DB["untis_session"].login()
            logging.info("Login successful")
            DB["untis_state"] = "connected"
            return DB["untis_session"]

        except webuntis.errors.BadCredentialsError as e:
            logging.error(f"Invalid credentials: {str(e)}")
            DB["untis_state"] = "disconnected"
            return None
        except webuntis.errors.RemoteError as e:
            logging.error(f"Remote error: {str(e)}")
            DB["untis_state"] = "disconnected"
            return None

    except Exception as e:
        DB["untis_state"] = "disconnected"
        logging.error(f"Session initialization failed: {str(e)}")
        return None


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
        session = init_untis_session()
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
    """Get timetable entries."""
    try:
        session = init_untis_session()
        if not session:
            raise ValueError("No active Untis session")

        output = {}
        sorted_timetable = sorted(DB["timeTable"], key=lambda t: t.start)
        for i, t in enumerate(sorted_timetable):
            if i > 1:
                output[t.studentGroup] = (
                    t.start.strftime("%H:%M"),
                    t.end.strftime("%H:%M"),
                )
        return output
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
