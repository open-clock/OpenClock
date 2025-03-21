from fastapi import APIRouter, HTTPException
import os
import subprocess
import traceback
import logging
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model
from util import handle_error

router = APIRouter(prefix="/system", tags=["System"])

# --- Endpoints ---


@router.get("/reboot")
async def reboot_system():
    """Initiate system reboot."""
    try:
        os.system("sudo shutdown -r now")
        return {"status": "success", "message": "System is rebooting..."}
    except Exception as e:
        raise handle_error(e, "Reboot failed")


@router.get("/shutdown")
async def shutdown_system():
    """Initiate system shutdown."""
    try:
        os.system("sudo shutdown -h now")
        return {"status": "success", "message": "System is shutting down..."}
    except Exception as e:
        raise handle_error(e, "Shutdown failed")


@router.post("/run")
async def run_terminal(command: command) -> Dict[str, Union[str, Any]]:
    """Execute terminal command."""
    try:
        process = await create_subprocess_shell(
            command.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""
        return {"status": "completed", "output": output, "error": error}
    except Exception as e:
        raise handle_error(e, "Command execution failed")


@router.get("/get_logs")
async def get_logs() -> Dict[str, Union[str, Any]]:
    """Get logs."""
    try:
        with open("/var/log/syslog", "r") as f:
            logs = f.read()
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise handle_error(e, "Failed to get logs")


@router.get("/journal")
async def get_journal(lines: int = 100):
    """Get system journal logs."""
    try:
        process = await create_subprocess_shell(
            f"journalctl -n {lines} --no-pager",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if stderr:
            logging.error(f"Journal error: {stderr.decode()}")

        journal_entries = stdout.decode() if stdout else ""

        return {"status": "success", "entries": journal_entries, "lines": lines}
    except Exception as e:
        raise handle_error(e, "Failed to get journal logs")
