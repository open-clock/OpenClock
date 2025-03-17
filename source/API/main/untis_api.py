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
                session = webuntis.Session(
                    username=creds.username,
                    password=creds.password,
                    server=creds.server,
                    school=creds.school,
                    useragent="OpenClock",
                ).login()
                DB["untis_session"] = session
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
        start_date = datetime.datetime.now()
        end_date = start_date + datetime.timedelta(days=dayRange)

        DB["timeTable"] = sorted(
            DB["untis_session"].my_timetable(start=start_date, end=end_date),
            key=lambda x: x.start,
            reverse=False,
        )
        return True

    except webuntis.errors.RemoteError as e:
        if e.code == -8509:
            logging.error("No right for getTeachers()")
        else:
            logging.error(f"Failed to fetch timetable: {str(e)}")
        return False
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
                    "classes": [c.name for c in entry.klassen] if entry.klassen else [],
                }
            )

        return formatted_timetable

    except Exception as e:
        raise handle_error(e, "Failed to get timetable")


@router.get("/current-lesson")
async def get_current_lesson():
    """Get the current lesson."""
    try:
        now = datetime.datetime.now()
        current_lesson = next(
            (lesson for lesson in DB["timeTable"] if lesson.start <= now <= lesson.end),
            None,
        )
        if not current_lesson:
            raise ValueError("No current lesson found")
        return {
            "subject": (
                current_lesson.subjects[0].name
                if current_lesson.subjects
                else "Unknown"
            ),
            "start": current_lesson.start.strftime("%Y-%m-%d %H:%M"),
            "end": current_lesson.end.strftime("%Y-%m-%d %H:%M"),
            "room": current_lesson.rooms[0].name if current_lesson.rooms else "Unknown",
            "classes": (
                [c.name for c in current_lesson.klassen]
                if current_lesson.klassen
                else []
            ),
        }
    except Exception as e:
        raise handle_error(e, "Failed to get current lesson")


@router.get("/lessons-today")
async def get_lessons_today():
    """Get all lessons of the current day."""
    try:
        today = datetime.datetime.now().date()
        lessons_today = [
            lesson for lesson in DB["timeTable"] if lesson.start.date() == today
        ]
        formatted_lessons = [
            {
                "subject": lesson.subjects[0].name if lesson.subjects else "Unknown",
                "start": lesson.start.strftime("%Y-%m-%d %H:%M"),
                "end": lesson.end.strftime("%Y-%m-%d %H:%M"),
                "room": lesson.rooms[0].name if lesson.rooms else "Unknown",
                "classes": [c.name for c in lesson.klassen] if lesson.klassen else [],
            }
            for lesson in lessons_today
        ]
        return formatted_lessons
    except Exception as e:
        raise handle_error(e, "Failed to get lessons for today")


@router.get("/lessons-week")
async def get_lessons_week():
    """Get all lessons of the current week."""
    try:
        today = datetime.datetime.now()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        lessons_week = [
            lesson
            for lesson in DB["timeTable"]
            if start_of_week <= lesson.start <= end_of_week
        ]
        formatted_lessons = [
            {
                "subject": lesson.subjects[0].name if lesson.subjects else "Unknown",
                "start": lesson.start.strftime("%Y-%m-%d %H:%M"),
                "end": lesson.end.strftime("%Y-%m-%d %H:%M"),
                "room": lesson.rooms[0].name if lesson.rooms else "Unknown",
                "classes": [c.name for c in lesson.klassen] if lesson.klassen else [],
            }
            for lesson in lessons_week
        ]
        return formatted_lessons
    except Exception as e:
        raise handle_error(e, "Failed to get lessons for the week")


@router.get("/next-event")
async def get_next_event():
    """Get the next event (holiday)."""
    try:
        now = datetime.datetime.now()
        next_event = None

        # Check for next holiday
        if DB["holidays"]:
            next_holiday = min(
                (holiday for holiday in DB["holidays"] if holiday.start > now),
                key=lambda x: x.start,
                default=None,
            )
            if next_holiday:
                next_event = {
                    "type": "holiday",
                    "name": next_holiday.name,
                    "start": next_holiday.start.strftime("%Y-%m-%d"),
                    "end": next_holiday.end.strftime("%Y-%m-%d"),
                }

        if not next_event:
            raise ValueError("No upcoming events found")

        return next_event
    except Exception as e:
        raise handle_error(e, "Failed to get next event")


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


@router.get("/login-name")
async def get_login_name():
    """Get the current login name."""
    try:
        if not SECURE_DB.get("untis_creds"):
            raise ValueError("No Untis credentials configured")
        creds = SECURE_DB["untis_creds"]
        return {"username": creds.username}
    except Exception as e:
        raise handle_error(e, "Failed to get login name")


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
                    await asyncio.sleep(30)
                    continue

            if await set_timetable(10):
                logging.info("Timetable updated successfully")
            else:
                logging.warning("Failed to update timetable")
        except Exception as e:
            logging.error(f"Untis update error: {e}")
            DB["untis_state"] = False
        await asyncio.sleep(30)
