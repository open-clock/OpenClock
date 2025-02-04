from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from enum import Enum
from pathlib import Path
from source.API.dataClasses import *

from microsoft_api import router as ms_router, ms_refresh_token_loop
from untis_api import router as untis_router, untis_update_loop
from network_api import router as network_router
from config_api import router as config_router
from db import DB, SECURE_DB, origins


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
    """Save runtime and secure state to disk."""
    try:
        # Save runtime state
        with open(get_relative_path("runtime_state.json"), "w") as f:
            json.dump(DB, f, indent=2, cls=EnumEncoder)

        # Save secure data
        secure_data = {
            "untis_creds": (
                SECURE_DB["untis_creds"].dict() if SECURE_DB["untis_creds"] else None
            ),
            "token_cache": DB["token_cache"].serialize() if DB["token_cache"] else None,
        }
        with open(get_relative_path("secure_state.json"), "w") as f:
            json.dump(secure_data, f, indent=2)

    except Exception as e:
        logging.error(f"Failed to save state: {e}")


async def load_state():
    """Load runtime and secure state from disk."""
    try:
        # Load runtime state
        if Path("runtime_state.json").exists():
            with open(get_relative_path("runtime_state.json"), "r") as f:
                DB.update(json.load(f))

        # Load secure state
        if Path("secure_state.json").exists():
            with open(get_relative_path("secure_state.json"), "r") as f:
                secure_data = json.load(f)
                if secure_data.get("untis_creds"):
                    SECURE_DB["untis_creds"] = credentials(**secure_data["untis_creds"])
                if secure_data.get("token_cache"):
                    DB["token_cache"].deserialize(secure_data["token_cache"])

    except Exception as e:
        logging.error(f"Failed to load state: {e}")


# --- Lifespan and App Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load saved state
    await load_state()

    # Start background tasks
    ms_task = asyncio.create_task(ms_refresh_token_loop())
    untis_task = asyncio.create_task(untis_update_loop())

    yield

    # Save state before shutdown
    await save_state()

    # Cleanup tasks
    for task in [ms_task, untis_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ms_router)
app.include_router(untis_router)
app.include_router(network_router)
app.include_router(config_router)
