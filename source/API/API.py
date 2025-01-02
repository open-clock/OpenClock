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
from typing import List, Dict

# Combined DB dictionary
global DB
DB = {
    # Microsoft API settings
    "ms_result": None,
    "ms_accounts": None,
    "ms_flow": None,
    "client_id": "cda7262c-6d80-4c31-adb6-5d9027364fa7",
    "scopes": ["User.Read", "Mail.Read"],
    "graph_endpoint": "https://graph.microsoft.com/v1.0",
    "cache_path": os.path.join(".", "cache.bin"),
    "token_cache": msal.SerializableTokenCache(),
    "ms_app": None,
    "authority": "https://login.microsoftonline.com/076218b1-9f9c-4129-bbb0-337d5a8fe3e3",
    
    # Untis API settings
    "untis_creds": None,
    "untis_session": None,
    "timeTable": [],
    "currentPeriod": webuntis.objects.PeriodObject,
    "nextPeriod": webuntis.objects.PeriodObject,
    "holidays": []
}

# Helper Functions from UntisAPI
async def set_untis_session() -> bool:
    try:
        global DB
        print(f"Attempting to connect to server: {DB['untis_creds'].server}")
        
        DB["untis_session"] = webuntis.Session(
            username=DB["untis_creds"].username,
            password=DB["untis_creds"].password,
            server=DB["untis_creds"].server,
            school=DB["untis_creds"].school,
            useragent=DB["untis_creds"].useragent
        )
        DB["untis_session"].login()
        print("Untis session created and logged in successfully")
        return True
    except Exception as e:
        print(f"Failed to create or login Untis session: {e}")
        return False

async def set_timetable(dayRange: int) -> bool:
    global DB
    if DB["untis_session"] is None:
        print("Untis session is None, cannot set timetable")
        return False

    now = datetime.datetime.now()
    try:
        print(f"Fetching timetable from {now} to {now + datetime.timedelta(days=dayRange)}")
        timetable = DB["untis_session"].timetable(start=now, end=now + datetime.timedelta(days=dayRange))
        DB["timeTable"] = sorted(timetable, key=lambda x: x.start)
        return True
    except Exception as e:
        print(f"Failed to set timetable: {e}")
        return False

async def has_untis_session() -> bool:
    global DB
    try:
        return DB["untis_session"] is not None
    except AttributeError:
        return False

# Helper Functions from MicrosoftAPI
async def initiate_device_flow():
    global DB
    flow = DB["ms_app"].initiate_device_flow(scopes=DB["scopes"])
    if "user_code" not in flow:
        raise HTTPException(status_code=500, 
            detail=f"Failed to create device flow: {json.dumps(flow, indent=2)}")
    DB["ms_flow"] = flow
    return flow

# Update Loops
async def ms_refresh_token_loop():
    while True:
        try:
            if DB["ms_result"]:
                accounts = DB["ms_app"].get_accounts()
                if accounts:
                    chosen = accounts[0]
                    result = DB["ms_app"].acquire_token_silent(
                        scopes=DB["scopes"],
                        account=chosen
                    )
                    if result:
                        DB["ms_result"] = result
                        print("MS token refreshed successfully")
        except Exception as e:
            print(f"Error refreshing MS token: {e}")
        await asyncio.sleep(3600)

async def untis_update_loop():
    while True:
        if not await has_untis_session():
            try:
                with open("creds.json", "r") as infile:
                    creds_data = json.load(infile)
                    DB["untis_creds"] = credentials(**creds_data)
                print(f"Loaded Untis credentials: {DB['untis_creds']}")
            except Exception as e:
                print(f"Untis credentials error: {e}")
        
        await set_untis_session()
        await set_timetable(10)
        await asyncio.sleep(300)

# Combined lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Microsoft API initialization
    if os.path.exists(DB["cache_path"]):
        DB["token_cache"].deserialize(open(DB["cache_path"], "r").read())
    
    atexit.register(lambda: 
        open(DB["cache_path"], "w").write(DB["token_cache"].serialize())
    )
    
    DB["ms_app"] = msal.PublicClientApplication(
        DB["client_id"],
        authority=DB["authority"],
        token_cache=DB["token_cache"]
    )
    
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
@app.get("/ms/accounts")
async def get_ms_accounts() -> List[Dict]:
    """Get all Microsoft accounts from cache"""
    global DB
    accounts = DB["ms_app"].get_accounts()
    if accounts:
        logging.info("MS Account(s) exists in cache")
        return accounts
    return []

@app.post("/ms/token/acquire")
async def acquire_token(account_id: str):
    """Acquire Microsoft token for specific account"""
    global DB
    accounts = DB["ms_app"].get_accounts()
    chosen = next((acc for acc in accounts if acc["username"] == account_id), None)
    
    if not chosen:
        raise HTTPException(status_code=404, detail="Account not found")
    
    result = DB["ms_app"].acquire_token_silent(scopes=DB["scopes"], account=chosen)
    if result:
        return result
    else:
        return await initiate_device_flow()

# Untis API endpoints
@app.post("/untis/set-cred")
async def set_untis_creds(cred: credentials):
    global DB 
    DB["untis_creds"] = cred
    json_object = json.dumps(DB["untis_creds"].dict(), indent=2)
    with open("creds.json", "w") as outfile:
        outfile.write(json_object)
    return DB["untis_creds"]

@app.get("/untis/timetable")
async def get_timetable(dayRange: int = 1):
    global DB
    output: dict = {}
    sorted_timetable = sorted(DB["timeTable"], key=lambda t: t.start, reverse=False)
    for i, t in enumerate(sorted_timetable):
        if i > 1:
            output[t.studentGroup] = (t.start.strftime("%H:%M"), t.end.strftime("%H:%M"))
    return output

# Combined status endpoint
@app.get("/status")
async def get_status() -> dict:
    global DB
    return {
        "microsoft": {
            "has_accounts": len(DB["ms_app"].get_accounts()) > 0 if DB["ms_app"] else False,
            "has_token": DB["ms_result"] is not None,
            "has_active_flow": DB["ms_flow"] is not None
        },
        "untis": {
            "creds": DB["untis_creds"].dict() if DB["untis_creds"] else None,
            "session": "active" if DB["untis_session"] else "inactive",
            "timeTable": len(DB["timeTable"]),
            "holidays": len(DB["holidays"])
        }
    }



#Untis api help funcs 
async def setSession()->bool:
    try:
        global DB
        
        print(f"Attempting to connect to server: {DB['creds'].server}")
        
        DB["session"] = webuntis.Session( 
            username=DB["creds"].username,
            password=DB["creds"].password,
            server=DB["creds"].server,
            school=DB["creds"].school,
            useragent=DB["creds"].useragent
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
