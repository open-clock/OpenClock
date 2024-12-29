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
DB = {                                                      #sores the data so it can be accessed faster
        "creds" : credentials,
        "session" : webuntis.session,
        "timeTable": list,
        "currentPeriod" : webuntis.objects.PeriodObject,
        "nextPeriod" : webuntis.objects.PeriodObject,
        "holidays" : list}


@asynccontextmanager
async def lifespan(app: FastAPI):                               #life circle of the app   
    global DB
    while True:
        if not await hasSession():
            try:
                DB[creds] = json.load(open("creds.json","r"))    #loads the creds from the json file
                with open("creds.json", "w") as outfile:
                    outfile.write(json_object)
            except FileNotFoundError:
                print("file not found")
        await setSession()
        await setTimeTable()
        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


                                                #the following funcs the set the data in the DB
async def setSession()->bool:
    try:
        global DB
        
        DB[session] = webuntis.Session( 
            username=DB["creds"].username,
            password=DB["creds"].password,
            server=DB["creds"].server,
            school=DB["creds"].school,
            useragent=DB["creds"].useragent
        ).login()
        return True
    except webuntis.errors.BadCredentialsError or webuntis.errors.NotLoggedInError:
        return False

@app.post("/set-tt")
async def setTimeTable(dayRange: int = 1)->bool:
    global DB

    now: datetime.date = datetime.datetime.now()

    DB.timeTable = sorted(DB.session.my_timetable(DB.session, start= now,end=now+datetime.timedelta(days=dayRange)), key=lambda x: x.start, reverse=False)

    return True

async def setNextHoliday()->bool:
    global DB
    DB.holidays = DB.session.holidays()
    return True
async def setNextEvent(maxDeph = 14)->bool:
    pass

@app.post("/set-cred")
async def setCreds(cred: credentials):
    global DB 
    DB.creds = cred
    json_object = json.dumps(DB.creds.__dict__, indent=2)
    with open("creds.json", "w") as outfile:
        outfile.write(json_object)
    return DB.creds

@app.get("/get-Timtable")
async def getTimeTable(dayRange: int = 1)-> None:
    global DB
    return DB.timeTable
    
@app.get("/hasSessio")
async def hasSession()->bool:
    global DB
    try:
        if DB.session is not None:
            return True
        return False
    except AttributeError:
        return False
    
@app.get("/status")
async def status()->model:
    return model()

