from fastapi import FastAPI
from dataClasses import *
import webuntis.session
import webuntis
import json
import datetime
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import List

global DB
DB = {                                                      #stores the data so it can be accessed faster
        "creds" : None,  # Initialize as None
        "session" : None,  # Initialize as None
        "timeTable": [],
        "currentPeriod" : webuntis.objects.PeriodObject,
        "nextPeriod" : webuntis.objects.PeriodObject,
        "holidays" : []}

@asynccontextmanager
async def lifespan(app: FastAPI):                               #life circle of the app   
    global DB
   
    if not await hasSession():
        try:
            with open("creds.json", "r") as infile:
                creds_data = json.load(infile)
                DB["creds"] = credentials(**creds_data)    #loads the creds from the json file
            with open("creds.json", "w") as outfile:
                outfile.write(json.dumps(DB["creds"].dict(), indent=2))
        except json.JSONDecodeError:
            print("Invalid JSON format in creds.json")
        except TypeError as e:
            print(f"Missing fields in creds.json: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    await setSession()
    await setTimeTable(10)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# the following funcs the set the data in the DB
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

async def setTimeTable(dayRange: int)->bool:
    global DB

    if DB["session"] is None:
        print("Session is None, cannot set timetable")
        return False

    now: datetime.date = datetime.datetime.now()
  
    try:
        print(f"Fetching timetable from {now} to {now + datetime.timedelta(days=dayRange)}")
        timetable = DB["session"].my_timetable(start=now, end=now + datetime.timedelta(days=dayRange))
        DB["timeTable"] = sorted(timetable, key=lambda x: x.start, reverse=False)
        print(f"Timetable set successfully: {DB['timeTable']}")
        return True
    except Exception as e:
        print(f"Failed to set timetable: {e}")
        return False

async def setNextHoliday()->bool:
    global DB
    DB["holidays"] = DB["session"].holidays()
    return True

async def setNextEvent(maxDeph = 14)->bool:
    pass

@app.post("/set-cred")
async def setCreds(cred: credentials):
    global DB 
    DB["creds"] = cred
    json_object = json.dumps(DB["creds"].dict(), indent=2)
    with open("creds.json", "w") as outfile:
        outfile.write(json_object)
    return DB["creds"]

@app.get("/get-Timtable")
async def getTimeTable(dayRange: int):
    global DB
    output: dict = {}
    
    # Sort the timetable by start time
    sorted_timetable = sorted(DB["timeTable"], key=lambda t: t.start,reverse=False)
    
    for i, t in enumerate(sorted_timetable):
        if i > 1:
            output[t.studentGroup] = t.start.strftime("%H:%M"), t.end.strftime("%H:%M")
    
    return output
    
@app.get("/hasSessio")
async def hasSession()->bool:
    global DB
    try:
        if DB["session"] is not None:
            return True
        return False
    except AttributeError:
        return False
    
@app.get("/status")
async def status() -> dict:
    global DB
    return {
        "creds": DB["creds"].dict() if DB["creds"] else None,
        "session": "active" if DB["session"] else "inactive",
        "timeTable": len(DB["timeTable"]),
        "holidays": len(DB["holidays"])
    }