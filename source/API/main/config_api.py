from fastapi import APIRouter, HTTPException
import json
import subprocess
import logging
import os
from enum import Enum
from pathlib import Path
from source.API.dataClasses import ConfigModel, ClockType
from db import DB

router = APIRouter(prefix="/config", tags=["Config"])


# --- Helper Functions ---
def get_config_path() -> Path:
    """Get path to config file."""
    return Path(__file__).parent / "config.json"


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


async def save_config(config: ConfigModel) -> bool:
    try:
        config_dict = config.dict()
        config_dict["model"] = config.model.value
        with open(get_config_path(), "w") as f:
            json.dump(config_dict, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save config: {e}")
        return False


async def load_config() -> ConfigModel:
    try:
        config_path = get_config_path()
        if not config_path.exists():
            return ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
        with open(config_path, "r") as f:
            data = json.load(f)
            return ConfigModel(**data)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return ConfigModel()


# --- API Endpoints ---
@router.get("/")
async def get_config():
    """Get current configuration."""
    try:
        return DB["config"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def update_config(config: ConfigModel):
    """Update complete configuration."""
    try:
        DB["config"] = config
        await save_config(config)
        return {"status": "success", "message": "Config updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/debug")
async def update_debug(debug: bool):
    """Update debug mode."""
    try:
        DB["config"].debug = debug
        await save_config(DB["config"])
        return {"status": "success", "debug": debug}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/hostname")
async def update_hostname(hostname: str):
    """Update system hostname."""
    try:
        DB["config"].hostname = hostname
        await save_config(DB["config"])
        try:
            subprocess.run(["hostnamectl", "set-hostname", hostname], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set hostname: {e}")
        return {"status": "success", "hostname": hostname}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/timezone")
async def update_timezone(timezone: str):
    """Update system timezone."""
    try:
        if not os.path.exists(f"/usr/share/zoneinfo/{timezone}"):
            raise HTTPException(status_code=400, detail="Invalid timezone")
        DB["config"].timezone = timezone
        await save_config(DB["config"])
        try:
            subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set timezone: {e}")
        return {"status": "success", "timezone": timezone}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reset")
async def reset_config():
    """Reset configuration to defaults."""
    try:
        DB["config"] = ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
        await save_config(DB["config"])
        return {"status": "success", "message": "Config reset to defaults"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
