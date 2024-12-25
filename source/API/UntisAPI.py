from fastapi import FastAPI
from dataClasses import *
import webuntis.session
import webuntis
import json
import datetime
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

global cache
cache = cacheClass()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache

    file = json.load(open("creds.json","r"))    

    cache.creds.username =  file["username"]
    cache.creds.password =  file["password"]
    cache.creds.server =  file["server"]
    cache.creds.school =  file["school"]
    cache.creds.useragent =  file["useragent"]
    yield
    if not await hasSession():
        await setSession()
    
        await setTimeTable()
    yield



app = FastAPI(lifespan= lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def setSession()->bool:
    try:
        global cache
        cache.session = webuntis.Session( 
            username=cache.creds.username,
            password=cache.creds.password,
            server=cache.creds.server,
            school=cache.creds.school,
            useragent=cache.creds.useragent
        ).login()
        return True
    except webuntis.errors.BadCredentialsError or webuntis.errors.NotLoggedInError:
        return False

@app.post("/set-tt")
async def setTimeTable(dayRange: int = 1)->bool:
    global cache

    now: datetime.date = datetime.datetime.now()

    cache.timeTable = sorted(cache.session.my_timetable(cache.session, start= now,end=now+datetime.timedelta(days=dayRange)), key=lambda x: x.start, reverse=False)

    return True

async def setNextHoliday()->bool:
    global cache
    cache.holidays = cache.session.holidays()
    return True
async def setNextEvent(maxDeph = 14)->bool:
    pass

@app.post("/set-cred")
async def setCreds(cred: credentials):
    global cache 
    cache.creds = cred
    json_object = json.dumps(cache.creds.__dict__, indent=2)
    with open("creds.json", "w") as outfile:
        outfile.write(json_object)
    return cache.creds

@app.get("/get-Timtable")
async def getTimeTable(dayRange: int = 1)-> None:
    global cache
    return cache.timeTable
    
@app.get("/hasSessio")
async def hasSession()->bool:
    global cache
    try:
        if cache.session is not None:
            return True
        return False
    except AttributeError:
        return False
    
@app.get("/status")
async def status()->model:
    return model()

