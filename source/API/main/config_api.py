from fastapi import APIRouter, HTTPException
import json
import subprocess
import logging
import os
import traceback
from enum import Enum
from pathlib import Path
from dataClasses import ConfigModel, ClockType
from db import DB

router = APIRouter(prefix="/config", tags=["Config"])


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


# --- Helper Functions ---
def get_config_path() -> Path:
    """Get path to config file."""
    try:
        return Path(__file__).parent / "config.json"
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to get config path: {str(e)} at {error_loc}")
        raise RuntimeError(f"Failed to get config path: {str(e)} at {error_loc}")


def get_relative_path(filename: str) -> Path:
    """Get path relative to this file's directory."""
    try:
        return Path(__file__).parent / filename
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to get relative path: {str(e)} at {error_loc}")
        raise RuntimeError(f"Failed to get relative path: {str(e)} at {error_loc}")


async def set_configFile():
    """Save config to file with enum handling."""
    global DB
    try:
        with open(get_relative_path("config.json"), "w") as f:
            config_dict = DB["config"]
            f.write(DB["config"].toJSON())
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Error saving config file: {str(e)} at {error_loc}")
        raise HTTPException(
            status_code=500, detail=f"Error saving config: {str(e)} at {error_loc}"
        )


async def load_config() -> ConfigModel:
    """Load config from file or create default."""
    try:
        config_path = get_config_path()
        if not config_path.exists():
            default_config = ConfigModel(
                model=ClockType.Mini, setup=False, wallmounted=False
            )
            await set_configDB(default_config)
            return default_config

        with open(config_path, "r") as f:
            data = json.load(f)
            return ConfigModel(**data)
    except json.JSONDecodeError:
        logging.error("Failed to decode config file")
        default_config = ConfigModel(
            model=ClockType.Mini, setup=False, wallmounted=False
        )
        await set_configDB(default_config)
        return ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)


async def set_configDB():
    """Load configuration from file."""
    global DB
    config_path = get_relative_path("config.json")

    try:
        # Check if file exists and has content
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            # Create default config
            default_config = ConfigModel(
                model=ClockType.Mini, setup=False, wallmounted=False
            )
            DB["config"] = default_config

            # Save default config
            await set_configDB(default_config)
            logging.info("Created default config")
            return

        # Load existing config
        with open(config_path, "r") as infile:
            data = json.load(infile)
            DB["config"] = ConfigModel(**data)
            logging.info("Config loaded successfully")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to load config: {str(e)} at {error_loc}")
        # Use default config on error
        DB["config"] = ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
        raise HTTPException(
            status_code=500, detail=f"Failed to load config: {str(e)} at {error_loc}"
        )


# --- API Endpoints ---


@router.post("/", operation_id="update_full_config")
async def update_config(config: ConfigModel):
    """Update system configuration."""
    try:
        # Convert to dict and handle enum serialization
        config_dict = config.model_dump()
        config_dict["model"] = config.model.value

        # Update DB
        DB["config"] = config

        # Save to file with custom encoder
        with open(get_config_path(), "w") as f:
            json.dump(config_dict, f, cls=EnumEncoder, indent=2)

        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to update config: {str(e)} at {error_loc}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update config: {str(e)} at {error_loc}"
        )


@router.get("/", operation_id="get_full_config")
async def get_config():
    """Get current configuration."""
    try:
        if not DB.get("config"):
            raise HTTPException(status_code=404, detail="No config found")
        return DB["config"]
    except Exception as e:
        logging.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reset")
async def reset_config():
    """Reset configuration to defaults."""
    try:
        DB["config"] = ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
        await set_configFile()
        return {"status": "success", "message": "Config reset to defaults"}
    except Exception as e:
        logging.error(f"Failed to reset config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setWallmount")
async def set_wallmount(wallmount: bool):
    global DB
    DB["config"].wallmounted = wallmount
    await set_configFile()
    return True


@router.post("/setSetup")
async def set_setup(setup: bool):
    global DB
    DB["config"].setup = setup
    await set_configFile()
    return True


@router.post("/setDebug")
async def set_debug(debug: bool):
    """Update debug status."""
    try:
        DB["config"].debug = debug
        await set_configDB(DB["config"])
        return {"status": "success", "debug": debug}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/getHostname", operation_id="get_system_hostname")
async def getHostname(hostname: str):
    with open("/etc/hostname", "r") as f:
        return f.read().strip()


@router.post("/setHostname")
async def set_hostname(hostname: str):
    """Update hostname."""
    try:
        DB["config"].hostname = hostname
        await set_configDB(DB["config"])
        try:
            subprocess.run(["hostnamectl", "set-hostname", hostname], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set system hostname: {e}")
        return {"status": "success", "hostname": hostname}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setTimezone")
async def set_timezone(timezone: str):
    """Update timezone."""
    try:
        if not os.path.exists(f"/usr/share/zoneinfo/{timezone}"):
            raise HTTPException(status_code=400, detail="Invalid timezone")
        DB["config"].timezone = timezone
        await set_configDB(DB["config"])
        try:
            subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set system timezone: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        return {"status": "success", "timezone": timezone}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/getTimezone", operation_id="get_current_timezone")
async def getTimezone():
    try:
        sowh = subprocess.check_output(["timedatectl", "show"])
        for line in sowh.decode().splitlines():
            if "Timezone" in line:
                return line.split("=")[1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/getTimezones", operation_id="get_timezone_list")
async def getTimezones():
    try:
        timezones = []
        base_path = "/usr/share/zoneinfo"
        for root, dirs, files in os.walk(base_path):
            # Skip posix and right directories
            if "posix" in root or "right" in root:
                continue

            for file in files:
                full_path = os.path.join(root, file)
                # Get relative path from zoneinfo directory
                rel_path = os.path.relpath(full_path, base_path)
                # Skip hidden files and non-timezone files
                if not file.startswith(".") and "." not in file:
                    timezones.append(rel_path)

        return sorted(timezones)  # Return sorted list for better readability
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setClientID")
async def set_clientID(id: str):
    try:
        DB["client_id"] = id
        await set_configDB(DB["config"])
        return {"status": "success", "client_id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setAuthority")
async def set_Authority(authority: str):
    try:
        DB["authority"] = authority
        await set_configDB(DB["authority"])
        return {"status": "success", "authority": authority}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
