from fastapi import APIRouter, HTTPException
import os
import subprocess
import traceback
import logging
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model

router = APIRouter(prefix="/system", tags=["System"])


def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")


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


@router.get("/status")
async def get_status() -> Dict[str, Union[bool, str]]:
    """Get system status."""
    try:
        return {
            "setup": DB["config"].setup,
            "model": DB["config"].model,
            "wallmounted": DB["config"].wallmounted,
        }
    except Exception as e:
        raise handle_error(e, "Failed to get system status")
