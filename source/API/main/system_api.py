from fastapi import APIRouter, HTTPException
import webuntis
import logging
import asyncio
import json
import datetime
from db import DB, SECURE_DB
from source.API.dataClasses import credentials

router = APIRouter(prefix="/", tags=["System"])



# --- Endpoints ---


@router.get("/reboot", response_model=dict)
async def reboot_system():
    """Initiate system reboot.

    Returns:
        dict: Status message indicating reboot progress
    """
    try:
        os.system("reboot")
        return {"status": "success", "message": "System is rebooting..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/shutdown", response_model=dict)
async def shutdown_system():
    """Initiate system shutdown.

    Returns:
        dict: Status message indicating shutdown progress
    """
    try:
        os.system("poweroff")
        return {"status": "success", "message": "System is shutting down..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    
@router.post("/run")
async def run_terminal(command: command) -> dict:
    try:
        process = await create_subprocess_shell(
            command.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""

        return {"status": "completed", "output": output, "error": error}

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/status")
async def get_status() -> model:
    """Get system status."""
    global DB
    return model(
        setup=DB["config"].setup,
        model=DB["config"].model,
        wallmounted=DB["config"].wallmounted,
    )

