from fastapi import APIRouter, HTTPException
import webuntis
import logging
import asyncio
import json
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
            useragent=creds.useragent
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

async def set_timetable(dayRange: int = 10) -> bool:
    """Update timetable data."""
    if DB["untis_session"] is None:
        logging.error("No active Untis session")
        return False

    try:
        now = datetime.datetime.now()
        timetable = DB["untis_session"].timetable(
            start=now,
            end=now + datetime.timedelta(days=dayRange),
            teacher=SECURE_DB["untis_creds"].username
        )
        DB["timeTable"] = sorted(timetable, key=lambda x: x.start)
        logging.info(f"Successfully fetched {len(DB['timeTable'])} entries")
        return True
    except Exception as e:
        logging.error(f"Failed to set timetable: {e}")
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

# --- API Endpoints ---
@router.post("/set-cred")
async def set_untis_creds(cred: credentials):
    """Set Untis credentials."""
    SECURE_DB["untis_creds"] = cred
    with open("creds.json", "w") as f:
        json.dump(cred.dict(), f, indent=2)
    return {"status": "success"}

@router.get("/timetable")
async def get_timetable(dayRange: int = 1):
    """Get timetable entries."""
    output = {}
    sorted_timetable = sorted(DB["timeTable"], key=lambda t: t.start)
    for i, t in enumerate(sorted_timetable):
        if i > 1:
            output[t.studentGroup] = (t.start.strftime("%H:%M"), t.end.strftime("%H:%M"))
    return output

@router.get("/status")
async def get_untis_status():
    """Get Untis connection status."""
    return {
        "session": DB["untis_state"],
        "timetable_entries": len(DB["timeTable"]),
        "holidays": len(DB["holidays"])
    }