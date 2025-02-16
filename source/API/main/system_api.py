from fastapi import APIRouter, HTTPException
import os
import subprocess
import traceback
import logging
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model

router = APIRouter(prefix="/system", tags=["System"])


# --- Endpoints ---


@router.get("/reboot", response_model=dict)
async def reboot_system():
    """Initiate system reboot."""
    try:
        os.system("sudo shutdown -r now")
        return {"status": "success", "message": "System is rebooting..."}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Reboot error: {str(e)} at {error_loc}")
        raise HTTPException(
            status_code=500, detail=f"Reboot failed: {str(e)} at {error_loc}"
        )


@router.get("/shutdown", response_model=dict)
async def shutdown_system():
    """Initiate system shutdown."""
    try:
        os.system("sudo shutdown -h now")
        return {"status": "success", "message": "System is shutting down..."}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Shutdown error: {str(e)} at {error_loc}")
        raise HTTPException(
            status_code=500, detail=f"Shutdown failed: {str(e)} at {error_loc}"
        )


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
