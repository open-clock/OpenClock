from fastapi import APIRouter, HTTPException
import traceback
import logging
from typing import Dict, Any, Union
from asyncio.subprocess import create_subprocess_shell
from db import DB
from dataClasses import command, model
import datetime


def handle_error(e: Exception, message: str) -> HTTPException:
    """Utility function for consistent error handling."""
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"{message}: {str(e)} at {error_loc}")
    return HTTPException(status_code=500, detail=f"{message}: {str(e)} at {error_loc}")


def log(message: str, level: str = "info", module: str = "unknown") -> None:
    """Enhanced logging utility that includes timestamp, module, and log level.

    Args:
        message: The message to log
        level: Log level (info, warning, error, debug)
        module: Source module name for the log entry
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{module}] [{level.upper()}] {message}"

        if level.lower() == "error":
            logging.error(formatted_message)
        elif level.lower() == "warning":
            logging.warning(formatted_message)
        elif level.lower() == "debug":
            logging.debug(formatted_message)
        else:
            logging.info(formatted_message)

    except Exception as e:
        logging.error(f"Logging failed: {str(e)}")
