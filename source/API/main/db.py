from dataClasses import *
import msal
import webuntis
import os

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

DB = {
    # Microsoft API runtime data
    "ms_result": None,
    "ms_accounts": None,
    "ms_flow": None,
    "ms_app": None,
    "token_cache": msal.SerializableTokenCache(),
    
    # Untis API runtime data
    "untis_session": None,
    "untis_state": "disconnected",
    "timeTable": [],
    "currentPeriod": webuntis.objects.PeriodObject,
    "nextPeriod": webuntis.objects.PeriodObject,
    "holidays": [],
    
    # DBus runtime data
    "bus": None,
    "wifi_device": None,
    
    # configs
    "config": ConfigModel(
        model=ClockType.Mini,
        setup=False,
        wallmounted=False
    )
}

SECURE_DB = {
    # Microsoft API credentials
    "token_cache": msal.SerializableTokenCache(),
    "client_id": "cda7262c-6d80-4c31-adb6-5d9027364fa7",
    "scopes": ["User.Read", "Mail.Read"],
    "graph_endpoint": "https://graph.microsoft.com/v1.0",
    "cache_path": os.path.join(".", "cache.bin"),  
    "authority": "https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",
    
    # Untis API credentials
    "untis_creds": None,
}