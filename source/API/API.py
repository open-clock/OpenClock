"""OpenClock API Server.

Provides endpoints and background tasks for:
- Microsoft account integration
- Untis calendar synchronization  
- WiFi network management
- System status and control
"""

from fastapi import FastAPI, HTTPException
from dataClasses import *
import webuntis.session
import webuntis
import msal
import json
import datetime
import asyncio
import os
import atexit
import logging
import requests
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import subprocess
from asyncio import create_subprocess_shell, subprocess
from asyncio.exceptions import TimeoutError
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import time

global DB, SECURE_DB

# Non-sensitive data
DB = {
    # Microsoft API runtime data
    "ms_result": None,
    "ms_accounts": None,
    "ms_flow": None,
    "ms_app": None,
    "token_cache": msal.SerializableTokenCache(),
    
    # Untis API runtime data
    "untis_session": None,
    "timeTable": [],
    "currentPeriod": webuntis.objects.PeriodObject,
    "nextPeriod": webuntis.objects.PeriodObject,
    "holidays": [],
    
    # DBus runtime data
    "bus": None,
    "wifi_device": None
}

# Sensitive data
SECURE_DB = {
    # Microsoft API credentials
    "token_cache": msal.SerializableTokenCache(),
    "client_id": "cda7262c-6d80-4c31-adb6-5d9027364fa7",
    "scopes": ["User.Read", "Mail.Read"],
    "graph_endpoint": "https://graph.microsoft.com/v1.0",
    "cache_path": os.path.join(".", "cache.bin"),
    "authority": "https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",  # Changed to common
    
    # Untis API credentials
    "untis_creds": None,
}

# Helper Functions from UntisAPI
async def set_untis_session() -> bool:
    """Initialize and authenticate Untis calendar session.
    
    Uses credentials from SECURE_DB to establish WebUntis connection.
    Updates DB["untis_session"] with active session.
    
    Returns:
        bool: True if session created successfully, False otherwise
    
    Raises:
        Exception: If connection or authentication fails
    """
    try:
        global DB, SECURE_DB
        print(f"Attempting to connect to server: {SECURE_DB['untis_creds'].server}")
        
        DB["untis_session"] = webuntis.Session(
            username=SECURE_DB["untis_creds"].username,
            password=SECURE_DB["untis_creds"].password,
            server=SECURE_DB["untis_creds"].server,
            school=SECURE_DB["untis_creds"].school,
            useragent=SECURE_DB["untis_creds"].useragent
        )
        DB["untis_session"].login()
        print("Untis session created and logged in successfully")
        return True
    except Exception as e:
        print(f"Failed to create or login Untis session: {e}")
        return False
        

async def set_timetable(dayRange: int)->bool:
    global DB

    if DB["session"] is None:
        print("Session is None, cannot set timetable")
        return False

    now: datetime.date = datetime.now()
  
    try:
        print(f"Fetching timetable from {now} to {now + datetime.timedelta(days=dayRange)}")
        timetable = DB["session"].my_timetable(start=now, end=now + datetime.timedelta(days=dayRange))
        DB["timeTable"] = sorted(timetable, key=lambda x: x.start, reverse=False)
        return True
    except Exception as e:
        print(f"Failed to set timetable: {e}")
        return False
    
async def has_untis_session() -> bool:
    try:
        return DB["untis_session"] is not None
    except AttributeError:
        return False

# Helper Functions from MicrosoftAPI
async def initiate_device_flow():
    """Start Microsoft authentication device flow."""
    flow = DB["ms_app"].initiate_device_flow(scopes=SECURE_DB["scopes"])
    if "user_code" not in flow:
        raise HTTPException(status_code=500, 
            detail=f"Failed to create device flow: {json.dumps(flow, indent=2)}")
    DB["ms_flow"] = flow
    return flow

# Update Loops
import logging
from datetime import datetime
from typing import Optional

# Add configuration constants
UPDATE_INTERVALS = {
    "ms_token": 3600,  # 1 hour
    "untis": 300,      # 5 minutes
    "retry": 60        # 1 minute
}

async def ms_refresh_token_loop():
    """Background task that maintains Microsoft authentication.
    
    Features:
    - Hourly token refresh
    - Automatic retry on failure
    - Status logging
    """
    while True:
        try:
            if DB["ms_result"]:
                accounts = DB["ms_app"].get_accounts()
                if accounts:
                    chosen = accounts[0]
                    result = DB["ms_app"].acquire_token_silent(
                        scopes=SECURE_DB["scopes"],
                        account=chosen
                    )
                    if result:
                        DB["ms_result"] = result
                        DB["last_token_refresh"] = datetime.now()
                        logging.info("MS token refreshed successfully")
                    else:
                        logging.warning("Failed to refresh token silently")
                        await asyncio.sleep(UPDATE_INTERVALS["retry"])
                        continue
        except Exception as e:
            logging.error(f"Error refreshing MS token: {e}")
            await asyncio.sleep(UPDATE_INTERVALS["retry"])
            continue
            
        await asyncio.sleep(UPDATE_INTERVALS["ms_token"])

async def untis_update_loop():
    """Background task that maintains Untis calendar data.
    
    Features:
    - Periodic session verification
    - Automatic credential reload
    - Timetable updates
    - Error recovery
    """
    while True:
        try:
            if not await has_untis_session():
                try:
                    with open("creds.json", "r") as infile:
                        creds_data = json.load(infile)
                        SECURE_DB["untis_creds"] = credentials(**creds_data)
                    logging.info(f"Loaded Untis credentials")
                except Exception as e:
                    logging.error(f"Failed to load Untis credentials: {e}")
                    await asyncio.sleep(UPDATE_INTERVALS["retry"])
                    continue

            if not await set_untis_session():
                logging.error("Failed to establish Untis session")
                await asyncio.sleep(UPDATE_INTERVALS["retry"])
                continue

            if await set_timetable(10):
                DB["last_timetable_update"] = datetime.now()
                logging.info("Timetable updated successfully")
            else:
                logging.warning("Failed to update timetable")
                
        except Exception as e:
            logging.error(f"Untis update error: {e}")
            await asyncio.sleep(UPDATE_INTERVALS["retry"])
            continue

        await asyncio.sleep(UPDATE_INTERVALS["untis"])

# Combined lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Microsoft API initialization
    if os.path.exists(SECURE_DB["cache_path"]):
        DB["token_cache"].deserialize(open(SECURE_DB["cache_path"], "r").read())
    
    atexit.register(lambda: 
        open(SECURE_DB["cache_path"], "w").write(DB["token_cache"].serialize())
    )
    
    DB["ms_app"] = msal.PublicClientApplication(
        SECURE_DB["client_id"],
        authority=SECURE_DB["authority"],
        token_cache=DB["token_cache"]
    )
    
    # Initialize DBus for WiFi
    try:
        DBusGMainLoop(set_as_default=True)
        DB["bus"] = dbus.SystemBus()
    except Exception as e:
        print(f"Failed to initialize DBus: {e}")
    
    # Start both update tasks
    ms_task = asyncio.create_task(ms_refresh_token_loop())
    untis_task = asyncio.create_task(untis_update_loop())
    
    yield
    
    # Cleanup both tasks
    for task in [ms_task, untis_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Microsoft API endpoints
@app.get("/ms/accounts", tags=["Microsoft"])
async def get_ms_accounts() -> List[Dict]:
    """Get all Microsoft accounts from cache"""
    global DB
    accounts = DB["ms_app"].get_accounts()
    if accounts:
        logging.info("MS Account(s) exists in cache")
        return accounts
    return []

@app.post("/ms/token/acquire", tags=["Microsoft"])
async def acquire_token(account_id: str):
    """Acquire Microsoft token for specific account"""
    global DB
    accounts = DB["ms_app"].get_accounts()
    chosen = next((acc for acc in accounts if acc["username"] == account_id), None)
    
    if not chosen:
        raise HTTPException(status_code=404, detail="Account not found")
    
    result = DB["ms_app"].acquire_token_silent(scopes=SECURE_DB["scopes"], account=chosen)
    if result:
        return result
    else:
        return await initiate_device_flow()

@app.get("/microsoft/login", tags=["Microsoft"])
async def initiate_ms_login():
    """Start Microsoft login process."""
    try:
        # Check cache first
        accounts = DB["ms_app"].get_accounts()
        if accounts:
            result = DB["ms_app"].acquire_token_silent(
                SECURE_DB["scopes"], 
                account=accounts[0]
            )
            if result:
                return {"status": "success", "cached": True}

        # Start device flow if no cached token
        flow = DB["ms_app"].initiate_device_flow(scopes=SECURE_DB["scopes"])
        if "user_code" not in flow:
            raise ValueError(f"Failed to create device flow: {json.dumps(flow, indent=4)}")

        DB["ms_flow"] = flow  # Store flow for token acquisition

        return {
            "status": "auth_required",
            "verification_uri": flow["verification_uri"],
            "user_code": flow["user_code"],
            "message": flow["message"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.get("/microsoft/messages", response_model=List[EmailMessage], tags=["Microsoft"])
async def get_messages():
    """Fetch Microsoft email messages."""
    try:
        # Check for valid token
        if not DB["ms_result"] or "access_token" not in DB["ms_result"]:
            raise HTTPException(status_code=401, detail="Not authenticated with Microsoft")

        # Get messages from Graph API
        headers = {
            'Authorization': f'Bearer {DB["ms_result"]["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{SECURE_DB['graph_endpoint']}/me/messages?$top=10&$select=subject,from,receivedDateTime,bodyPreview",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch messages")

        messages_data = response.json().get('value', [])
        
        # Format messages
        messages = [
            EmailMessage(
                subject=msg.get('subject', 'No Subject'),
                from_email=msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                received_date=msg.get('receivedDateTime', ''),
                body=msg.get('bodyPreview', '')
            )
            for msg in messages_data
        ]
        
        return messages

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Untis API endpoints
@app.post("/untis/set-cred", tags=["Untis"])
async def set_untis_creds(cred: credentials):
    """Set Untis authentication credentials."""
    global SECURE_DB 
    SECURE_DB["untis_creds"] = cred
    json_object = json.dumps(SECURE_DB["untis_creds"].dict(), indent=2)
    with open("creds.json", "w") as outfile:
        outfile.write(json_object)
    return SECURE_DB["untis_creds"]

@app.get("/untis/timetable", tags=["Untis"])
async def get_timetable(dayRange: int = 1):
    global DB
    output: dict = {}
    sorted_timetable = sorted(DB["timeTable"], key=lambda t: t.start, reverse=False)
    for i, t in enumerate(sorted_timetable):
        if i > 1:
            output[t.studentGroup] = (t.start.strftime("%H:%M"), t.end.strftime("%H:%M"))
    return output

# Combined status endpoint
@app.get("/status", tags=["System"])
async def get_status() -> model:
    """Get system status."""
    global DB
    return model(setup=True, model=ClockType.Mini)

# Terminal endpoints
@app.post("/run", tags=["System"])
async def run_terminal(command: command) -> dict:
    try:
        process = await create_subprocess_shell(
            command.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        output = stdout.decode() if stdout else ''
        error = stderr.decode() if stderr else ''

        return {
            "status": "completed",
            "output": output,
            "error": error
        }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
# System management endpoints
@app.get("/shutdown", tags=["System"], response_model=dict)
async def shutdown_system():
    """Initiate system shutdown.
    
    Returns:
        dict: Status message indicating shutdown progress
    """
    try:
        os.system("poweroff")
        return {
            "status": "success",
            "message": "System is shutting down..."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/reboot", tags=["System"], response_model=dict)
async def reboot_system():
    """Initiate system reboot.
    
    Returns:
        dict: Status message indicating reboot progress
    """
    try:
        os.system("reboot")
        return {
            "status": "success",
            "message": "System is rebooting..."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

#Untis api help funcs 
async def setSession()->bool:
    try:
        global DB, SECURE_DB
        
        print(f"Attempting to connect to server: {SECURE_DB['creds'].server}")
        
        DB["session"] = webuntis.Session( 
            username=SECURE_DB["creds"].username,
            password=SECURE_DB["creds"].password,
            server=SECURE_DB["creds"].server,
            school=SECURE_DB["creds"].school,
            useragent=SECURE_DB["creds"].useragent
        )
        DB["session"].login()
        print("Session created and logged in successfully")
        return True
    except (webuntis.errors.BadCredentialsError, webuntis.errors.NotLoggedInError, AttributeError) as e:
        print(f"Failed to create or login session: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False

def get_wifi_device():
    if not DB["bus"]:
        raise HTTPException(status_code=500, detail="DBus not initialized")
    
    nm = DB["bus"].get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
    nm_props = dbus.Interface(nm, 'org.freedesktop.DBus.Properties')
    devices = nm_props.Get('org.freedesktop.NetworkManager', 'AllDevices')
    
    for device_path in devices:
        device = DB["bus"].get_object('org.freedesktop.NetworkManager', device_path)
        device_props = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
        device_type = device_props.Get('org.freedesktop.NetworkManager.Device', 'DeviceType')
        if device_type == 2:  # WiFi device
            return device
    return None

@app.get("/network/access-points", tags=["Network"])
async def get_access_points():
    wifi_device = get_wifi_device()
    if not wifi_device:
        raise HTTPException(status_code=404, detail="No WiFi device found")

    # Request scan
    wifi_interface = dbus.Interface(wifi_device, 'org.freedesktop.NetworkManager.Device.Wireless')
    wifi_interface.RequestScan({})

    # Wait for scan to complete
    time.sleep(2)

    # Get access points
    access_points = wifi_interface.GetAllAccessPoints()

    networks = []

    for ap in access_points:
        try:
            ap_obj = DB["bus"].get_object('org.freedesktop.NetworkManager', ap)
            ap_props = dbus.Interface(ap_obj, 'org.freedesktop.DBus.Properties')
            
            ssid = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'Ssid')
            strength = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'Strength')
            
            if not bytearray(ssid).decode() == "":
                networks.append({
                    "ssid": bytearray(ssid).decode(),
                    "strength": strength
                })
        except Exception as e:
            print(f"Error processing access point: {e}")
            continue

    return networks

@app.post("/network/connect", tags=["Network"])
async def connect_to_network(credentials: NetworkCredentials):
    global DB
    try:
        # Get NetworkManager interface
        nm = DB["bus"].get_object('org.freedesktop.NetworkManager', 
                          '/org/freedesktop/NetworkManager')
        settings = DB["bus"].get_object('org.freedesktop.NetworkManager',
                                '/org/freedesktop/NetworkManager/Settings')
        settings_interface = dbus.Interface(settings,
                                         'org.freedesktop.NetworkManager.Settings')

        connection_settings = dbus.Dictionary({
            'connection': dbus.Dictionary({
                'id': dbus.String(credentials.ssid),
                'type': dbus.String('802-11-wireless'),
                'autoconnect': dbus.Boolean(True)
            }, signature='sv'),
            '802-11-wireless': dbus.Dictionary({
                'ssid': dbus.ByteArray(credentials.ssid.encode()),
                'mode': dbus.String('infrastructure'),
                'security': dbus.String('802-11-wireless-security')
            }, signature='sv'),
            '802-11-wireless-security': dbus.Dictionary({
                'key-mgmt': dbus.String('wpa-psk'),
                'psk': dbus.String(credentials.password)
            }, signature='sv'),
            'ipv4': dbus.Dictionary({
                'method': dbus.String('auto')
            }, signature='sv'),
            'ipv6': dbus.Dictionary({
                'method': dbus.String('auto')
            }, signature='sv')
        }, signature='sa{sv}')

        new_connection = settings_interface.AddConnection(connection_settings)
        
        # Activate the connection
        nm_interface = dbus.Interface(nm, 'org.freedesktop.NetworkManager')
        wifi_device = get_wifi_device()
        nm_interface.ActivateConnection(new_connection, wifi_device, "/")

        return {"status": "success", "message": f"Connected to {credentials.ssid}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_relative_path(filename: str) -> str:
    """Get path relative to this file's directory."""
    return os.path.join(os.path.dirname(__file__), filename)


print(get_relative_path("creds.json"))