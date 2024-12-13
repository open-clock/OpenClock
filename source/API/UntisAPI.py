from pydantic import BaseModel
from fastApi import FastAPI
import webuntis.session
import webuntis
import json
import datetime
from contextlib import asynccontextmanager
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClockType(Enum):
    Mini="Mini"
    XL="XL"

class dummy(BaseModel):
    model : ClockType = ClockType.Mini
    setup : bool = True


{
 "username": "40146720210116",
  "password": "187",
  "server": "arche.webuntis.com",
  "school": "litec",
  "useragent": "WebUntis"
}
class credentials(BaseModel):
    username : str
    password : str
    server : str
    school : str
    useragent : str
class cacheClass:
    creds : credentials
    session : webuntis.session
    timeTable: list
    holidays : list

global cache
cache = cacheClass()


async def setSession()->bool:
    try:
        global session
        session = webuntis.Session( 
            username=cache.creds.username,
            password=cache.creds.password,
            server=cache.creds.server,
            school=cache.creds.school,
            useragent=cache.creds.useragent
        ).login()
        return True
    except webuntis.errors.BadCredentialsError or webuntis.errors.NotLoggedInError:
        return False
async def setTimeTable(dayRange: int = 1)->bool:
    global cache
    now: datetime.date = datetime.datetime.now()
    cache.timeTable = sorted(cache.session.my_timetable(start= now,end=now+datetime.timedelta(days=dayRange)), key=lambda x: x.start, reverse=False)
    return True
async def setNextHoliday()->bool:
    global cache
    cache.holidays = cache.session.holidays()
    return True
async def setNextEvent(maxDeph = 14)->bool:
    pass

@app.post("/set-cred")
async def setCreds(cred: credentials):
    json_object = json.dumps(credentials, indent=2)
    global creds 
    creds = cred
    with open("creds", "w") as outfile:
        outfile.write(json_object,outfile)
    return creds

@app.get("/get-Timtable")
async def getTimeTable(dayRange: int = 1)-> None:
    global cache
    return cache.timeTable
    

def hasSession()->bool:
    global cache
    if cache.session is not None:
        return True
    return False

    
@app.get("/status")
async def status()->dummy:
    return dummy()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache
    if not hasSession():
        setSession()
    setTimeTable()

