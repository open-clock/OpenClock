from fastapi import APIRouter, Query
import os
import subprocess
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB, SECURE_DB
from dataClasses import command, model
from util import handle_error
from util import log
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
import json
from fastapi import HTTPException
from dataClasses import ConfigModel, ClockType
from config_api import router as config_router
import msal


router = APIRouter(prefix="/system", tags=["System"])


class LogSource(str, Enum):
    JOURNAL = "journal"
    SYSLOG = "syslog"
    ALL = "all"


def format_time_arg(time_str: Optional[str]) -> str:
    """Format time argument for journalctl."""
    if not time_str:
        return ""

    try:
        now = datetime.now()
        if time_str.endswith("m"):
            delta = timedelta(minutes=int(time_str[:-1]))
        elif time_str.endswith("h"):
            delta = timedelta(hours=int(time_str[:-1]))
        elif time_str.endswith("d"):
            delta = timedelta(days=int(time_str[:-1]))
        else:
            return ""

        target_time = now - delta
        return target_time.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        log(f"Invalid time format: {time_str}", level="warning", module="system")
        return ""


# --- Endpoints ---


@router.get("/reboot")
async def reboot_system():
    """Initiate system reboot."""
    try:
        log("Initiating system reboot", module="system")
        os.system("sudo shutdown -r now")
        return {"status": "success", "message": "System is rebooting..."}
    except Exception as e:
        log(f"Reboot failed: {str(e)}", level="error", module="system")
        return {"status": "error", "message": "Reboot failed"}


@router.get("/shutdown")
async def shutdown_system():
    """Initiate system shutdown."""
    try:
        os.system("sudo shutdown -h now")
        return {"status": "success", "message": "System is shutting down..."}
    except Exception as e:
        log(f"Shutdown failed: {e}")
        return {"status": "error", "message": "Shutdown failed"}


@router.post("/run")
async def run_terminal(command: command) -> Dict[str, Union[str, Any]]:
    """Execute terminal command."""
    try:
        log(f"Executing command: {command.command}", module="system")
        process = await create_subprocess_shell(
            command.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""

        if error:
            log(f"Command produced error: {error}", level="warning", module="system")

        return {"status": "completed", "output": output, "error": error}
    except Exception as e:
        log(f"Command execution failed: {str(e)}", level="error", module="system")
        return {"status": "error", "message": str(e)}


@router.get("/logs")
async def get_logs(
    source: LogSource = Query(default=LogSource.ALL, description="Log source to query"),
    lines: Optional[int] = Query(default=100, description="Number of lines to return"),
    since: Optional[str] = Query(
        default=None, description="Start time (format: 1h, 2d, 30m)"
    ),
    until: Optional[str] = Query(default=None, description="End time"),
    services: Optional[str] = Query(
        default=None, description="Comma-separated list of services to filter"
    ),
    priority: Optional[str] = Query(default=None, description="Log priority level"),
) -> str:
    """Get system logs as a formatted string."""
    try:
        log(f"Fetching logs from {source}", module="system")

        # Build command based on source
        if source == LogSource.JOURNAL:
            cmd = "journalctl"

            # Format time arguments
            since_time = format_time_arg(since)
            until_time = format_time_arg(until)

            if since_time:
                cmd += f" --since '{since_time}'"
            if until_time:
                cmd += f" --until '{until_time}'"

            if services:
                service_list = services.split(",")
                cmd += " " + " ".join(f"-u {service}" for service in service_list)

            if priority:
                cmd += f" -p {priority}"

            if lines:
                cmd += f" -n {lines}"

        elif source == LogSource.SYSLOG:
            cmd = f"tail -n {lines} /var/log/syslog"
            if services:
                services_grep = "|".join(services.split(","))
                cmd += f" | grep -E '({services_grep})'"

        else:  # ALL
            # Combine both logs
            journal_cmd = f"journalctl -n {lines}"
            syslog_cmd = f"tail -n {lines} /var/log/syslog"
            cmd = f"{journal_cmd}; echo '=== Syslog ==='; {syslog_cmd}"

        # Execute command
        process = await create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if stderr:
            log(f"Log error: {stderr.decode()}", level="warning", module="system")

        return stdout.decode() if stdout else "No logs found"

    except Exception as e:
        log(f"Log retrieval failed: {str(e)}", level="error", module="system")
        return f"Error retrieving logs: {str(e)}"


@router.post("/factory-reset")
async def system_factory_reset():
    """Perform system-wide factory reset."""
    try:
        # 1. Clear all runtime data
        DB.clear()
        SECURE_DB.clear()

        # 2. Reinitialize DB with defaults
        DB.update(
            {
                "ms_result": None,
                "ms_accounts": None,
                "ms_flow": None,
                "ms_app": None,
                "token_cache": msal.SerializableTokenCache(),
                "untis_session": None,
                "untis_state": "disconnected",
                "timeTable": [],
                "holidays": [],
                "bus": None,
                "wifi_device": None,
                "config": ConfigModel(
                    model=ClockType.Mini, setup=False, wallmounted=False
                ),
            }
        )

        # 3. Call config API factory reset
        await config_router.factory_reset()

        # 4. Restart background tasks
        # This will be handled by lifespan management

        return {
            "status": "success",
            "message": "System factory reset completed. Please restart the application.",
        }
    except Exception as e:
        log(f"System factory reset failed: {str(e)}", level="error", module="main")
        raise HTTPException(
            status_code=500, detail=f"System factory reset failed: {str(e)}"
        )
