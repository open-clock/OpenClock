from fastapi import APIRouter, Query
import os
import subprocess
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model
from util import handle_error
from util import log
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
import json


router = APIRouter(prefix="/system", tags=["System"])


class LogSource(str, Enum):
    JOURNAL = "journal"
    SYSLOG = "syslog"
    ALL = "all"


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
            if since:
                if since.endswith("m"):
                    delta = timedelta(minutes=int(since[:-1]))
                elif since.endswith("h"):
                    delta = timedelta(hours=int(since[:-1]))
                elif since.endswith("d"):
                    delta = timedelta(days=int(since[:-1]))
                cmd += f" --since '{delta}'"

            if until:
                cmd += f" --until '{until}'"

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
