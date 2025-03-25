from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import traceback
import json
import logging
from enum import Enum
from pathlib import Path
from dataClasses import *

from microsoft_api import router as ms_router, ms_refresh_token_loop
from untis_api import router as untis_router, untis_update_loop
from network_api import router as network_router
from config_api import router as config_router, load_config, save_config
from system_api import router as system_router
from db import DB, SECURE_DB, origins
from util import handle_error, log


# --- Helper Functions ---
def get_relative_path(filename: str) -> str:
    """Get path relative to this file's directory."""
    return Path(__file__).parent / filename


class EnumEncoder(json.JSONEncoder):
    """JSON encoder with enum support."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


async def save_state():
    """Save application state to file."""
    try:
        state = {"microsoft": DB.get("microsoft", {}), "untis": DB.get("untis", {})}
        with open(get_relative_path("state.json"), "w") as f:
            json.dump(state, f, cls=EnumEncoder, indent=4)
        log("State saved successfully", module="main")
    except Exception as e:
        log(f"Failed to save state: {str(e)}", level="error", module="main")
        raise RuntimeError(f"Failed to save state: {str(e)}")


async def load_state():
    """Load application state from file."""
    try:
        with open(get_relative_path("state.json"), "r") as f:
            state = json.load(f)
            DB["microsoft"] = state.get("microsoft", {})
            DB["untis"] = state.get("untis", {})
        logging.info("State loaded successfully")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to load state: {str(e)} at {error_loc}")


# --- Lifespan and App Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    try:
        log("Starting application", module="main")

        # Load configuration at startup
        try:
            config = await load_config()
            DB["config"] = config
            log("Configuration loaded successfully", module="main")
        except Exception as e:
            log(f"Failed to load configuration: {str(e)}", level="error", module="main")
            # Continue with default config in DB

        # Start background tasks
        ms_task = asyncio.create_task(ms_refresh_token_loop())
        untis_task = asyncio.create_task(untis_update_loop())

        yield

        log("Shutting down application", module="main")
        # Save final state
        try:
            if DB.get("config"):
                await save_config(DB["config"])
            await save_state()
            log("Application state saved", module="main")
        except Exception as e:
            log(
                f"Failed to save application state: {str(e)}",
                level="error",
                module="main",
            )

        # Cleanup tasks
        for task in [ms_task, untis_task]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                log(f"Task cleanup error: {str(e)}", level="error", module="main")

    except Exception as e:
        log(f"Lifespan error: {str(e)}", level="error", module="main")
        raise RuntimeError(f"Lifespan error: {str(e)}")


app = FastAPI(lifespan=lifespan)

try:
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    routers = [
        (ms_router, "Microsoft API"),
        (untis_router, "Untis API"),
        (network_router, "Network API"),
        (config_router, "Config API"),
        (system_router, "System API"),
    ]

    for router, name in routers:
        try:
            app.include_router(router)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            filename, line_no, func, text = tb[-1]
            error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
            logging.error(f"Failed to include {name}: {str(e)} at {error_loc}")
            raise RuntimeError(f"Router inclusion error: {str(e)} at {error_loc}")

except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    filename, line_no, func, text = tb[-1]
    error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
    logging.error(f"App initialization error: {str(e)} at {error_loc}")
    raise RuntimeError(f"App initialization error: {str(e)} at {error_loc}")


@app.get("/status", tags=["System"])
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
