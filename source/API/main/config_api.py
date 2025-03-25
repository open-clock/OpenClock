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
from util import handle_error, log

# Change config directory to be in user space instead of /etc
CONFIG_DIR = Path.home() / ".config" / "openclock"
CONFIG_FILE = CONFIG_DIR / "config.json"

router = APIRouter(prefix="/config", tags=["Config"])


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


# --- Helper Functions ---
def ensure_config_dir():
    """Ensure config directory exists with proper permissions."""
    try:
        # Create directory if it doesn't exist
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Set user read/write permissions
        CONFIG_DIR.chmod(0o755)

        # Create config file if it doesn't exist
        if not CONFIG_FILE.exists():
            CONFIG_FILE.touch()
            CONFIG_FILE.chmod(0o644)

        # Ensure current user owns the directory and file
        import os

        uid = os.getuid()
        gid = os.getgid()
        os.chown(CONFIG_DIR, uid, gid)
        os.chown(CONFIG_FILE, uid, gid)

        log(f"Config directory setup at {CONFIG_DIR}", module="config")
    except Exception as e:
        log(
            f"Failed to setup config directory: {str(e)}",
            level="error",
            module="config",
        )
        raise


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
    """Load configuration from file or create default."""
    try:
        ensure_config_dir()
        if not CONFIG_FILE.exists() or CONFIG_FILE.stat().st_size == 0:
            log("No config file found, creating default", module="config")
            default_config = ConfigModel(
                model=ClockType.Mini,
                setup=False,
                wallmounted=False,
                debug=False,
                hostname="openclock",
                timezone="UTC",
            )
            await save_config(default_config)
            return default_config

        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Make sure to preserve setup state
                if "setup" not in data and DB.get("config"):
                    data["setup"] = DB["config"].setup

                config = ConfigModel(**data)
                log(
                    f"Loaded existing configuration (setup={config.setup})",
                    module="config",
                )
                return config
        except json.JSONDecodeError:
            log("Invalid config file, loading from DB or default", module="config")
            if DB.get("config"):
                # Preserve existing config from DB
                return DB["config"]

            # Fallback to default if no DB config
            return ConfigModel(
                model=ClockType.Mini,
                setup=False,
                wallmounted=False,
                debug=False,
                hostname="openclock",
                timezone="UTC",
            )

    except Exception as e:
        log(f"Failed to load configuration: {str(e)}", level="error", module="config")
        # Try to preserve existing config from DB
        if DB.get("config"):
            return DB["config"]
        # Ultimate fallback
        return ConfigModel(
            model=ClockType.Mini,
            setup=False,
            wallmounted=False,
            debug=False,
            hostname="openclock",
            timezone="UTC",
        )


async def save_config(config: ConfigModel) -> bool:
    """Save configuration to file."""
    try:
        ensure_config_dir()  # Make sure directory exists with proper permissions
        config_dict = config.model_dump()
        config_dict["model"] = config.model.value
        config_dict["setup"] = config.setup  # Explicitly preserve setup state

        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2)
        log(f"Configuration saved successfully (setup={config.setup})", module="config")
        return True
    except Exception as e:
        log(f"Failed to save configuration: {str(e)}", level="error", module="config")
        return False


async def set_configDB(config: ConfigModel = None):
    """Load or save configuration from/to file."""
    global DB
    config_path = get_relative_path("config.json")

    try:
        if config:
            log(f"Saving new configuration", module="config")
            DB["config"] = config
            with open(config_path, "w") as outfile:
                outfile.write(config.toJSON())
            log("Configuration saved successfully", module="config")
            return

        log("Loading existing configuration", module="config")
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            # Create default config
            default_config = ConfigModel(
                model=ClockType.Mini, setup=False, wallmounted=False
            )
            DB["config"] = default_config
            await set_configDB(default_config)
            logging.info("Created default config")
            return

        # Load existing config
        with open(config_path, "r") as infile:
            data = json.load(infile)
            DB["config"] = ConfigModel(**data)
            logging.info("Config loaded successfully")

    except Exception as e:
        log(f"Configuration error: {str(e)}", level="error", module="config")
        tb = traceback.extract_tb(e.__traceback__)
        filename, line_no, func, text = tb[-1]
        error_loc = f"File: {filename}, Line: {line_no}, Function: {func}"
        logging.error(f"Failed to load/save config: {str(e)} at {error_loc}")
        # Use default config on error
        DB["config"] = ConfigModel(model=ClockType.Mini, setup=False, wallmounted=False)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load/save config: {str(e)} at {error_loc}",
        )


# --- API Endpoints ---


@router.post("/", operation_id="update_full_config")
async def update_config(config: ConfigModel):
    """Update system configuration."""
    try:
        DB["config"] = config
        if await save_config(config):
            return {"status": "success", "message": "Configuration updated"}
        raise ValueError("Failed to save configuration")
    except Exception as e:
        log(f"Config update failed: {str(e)}", level="error", module="config")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", operation_id="get_config")
@router.get(
    "/get", operation_id="get_config_legacy"
)  # Keep for backwards compatibility
async def get_config():
    """Get current configuration."""
    try:
        if not DB.get("config"):
            raise HTTPException(status_code=404, detail="No config found")
        log("Returning current configuration", module="config")
        return DB["config"]
    except Exception as e:
        log(f"Failed to get config: {str(e)}", level="error", module="config")
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
    """Update setup status."""
    try:
        log(f"Setting setup status to: {setup}", module="config")
        DB["config"].setup = setup
        if await save_config(DB["config"]):
            return {"status": "success", "setup": setup}
        raise ValueError("Failed to save setup state")
    except Exception as e:
        log(f"Failed to set setup status: {str(e)}", level="error", module="config")
        raise HTTPException(status_code=500, detail=str(e))


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
async def getHostname():
    with open("/etc/hostname", "r") as f:
        return f.read().strip()


@router.post("/setHostname")
async def set_hostname(hostname: str):
    """Update hostname."""
    try:
        log(f"Setting hostname to: {hostname}", module="config")
        DB["config"].hostname = hostname
        await set_configDB(DB["config"])

        try:
            subprocess.run(["hostnamectl", "set-hostname", hostname], check=True)
            log(f"Hostname updated successfully", module="config")
        except subprocess.CalledProcessError as e:
            log(f"Failed to set system hostname: {e}", level="error", module="config")

        return {"status": "success", "hostname": hostname}
    except Exception as e:
        log(f"Hostname update failed: {str(e)}", level="error", module="config")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setTimezone")
async def set_timezone(timezone: str):
    """Update timezone."""
    try:
        log(f"Setting timezone to: {timezone}", module="config")
        if not os.path.exists(f"/usr/share/zoneinfo/{timezone}"):
            log(
                f"Invalid timezone requested: {timezone}",
                level="error",
                module="config",
            )
            raise HTTPException(status_code=400, detail="Invalid timezone")

        DB["config"].timezone = timezone
        await set_configDB(DB["config"])

        try:
            subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
            log(f"Timezone updated successfully", module="config")
        except subprocess.CalledProcessError as e:
            log(f"Failed to set system timezone: {e}", level="error", module="config")
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "success", "timezone": timezone}
    except Exception as e:
        log(f"Timezone update failed: {str(e)}", level="error", module="config")
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


def set_config(config: ConfigModel):
    """Set system configuration."""
    try:
        DB["config"] = config
        # Save to file
        with open("config.json", "w") as f:
            f.write(config.toJSON())
        return True
    except Exception as e:
        logging.error(f"Failed to set config: {str(e)}")
        return False


@router.post("/set")
async def set_config_endpoint(config: ConfigModel):
    """Set system configuration endpoint."""
    try:
        if set_config(config):
            return {"status": "success", "message": "Configuration updated"}
        raise ValueError("Failed to update configuration")
    except Exception as e:
        raise handle_error(e, "Failed to set configuration")
