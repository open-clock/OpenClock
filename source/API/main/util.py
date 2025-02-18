from fastapi import APIRouter, HTTPException
import os
import subprocess
import traceback
import logging
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model

def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")