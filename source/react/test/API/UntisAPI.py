from pydantic import BaseModel
from fastApi import FastAPI
import webuntis.session
import webuntis
import datetime

from fastapi_cache.decorator import cache

app = FastAPI()

class credentials(BaseModel):
    username : str
    password : str
    server : str
    school : str
    useragent : str

cred: credentials

@app.get("/foo")
@cache(expire=60)
async def get_cache():
    return 1
# 127.0.0.1:8000/login-Untis/40146720210116/janw2007/arche.webuntis.com/litec/WebUntis Test
{
 "username": "40146720210116",
  "password": "janw2007",
  "server": "arche.webuntis.com",
  "school": "litec",
  "useragent": "WebUntis"
}
async def login():
    """
    #### Logging into a WebUntis session with the given credentials 

    >>> login('40146720210116', '187', 'arche.webuntis.com', 'litec', 'WebUntis Test')
    YourWebUntisSession
    """
    try:
        return webuntis.Session( 
            username=creds.username,
            password=creds.password,
            server=creds.server,
            school=creds.school,
            useragent=creds.useragent
        ).login()
    except webuntis.errors.BadCredentialsError or webuntis.errors.NotLoggedInError:
        return "Not valide credentials"

@app.get("/canloginAs-Untis/{username}/{password}/{server}/{school}/{useragent}s")
def canLoginAs(username: str, password: str, server: str, school: str, useragent: str)->bool:
    """
    #### Trys to login into a WebUnti session with the given credentials
    #### returns False if the credentials are not valide 

    >>> canlogin('40146720210116', '187', 'arche.webuntis.com', 'litec', 'WebUntis Test')
    True
    """
    try:   
        webuntis.Session( 
            username=username,
            password=password,
            server=server,
            school=school,
            useragent=useragent
        ).login().logout()
    except webuntis.errors.BadCredentialsError or webuntis.errors.NotLoggedInError:
        return False
    return True


@app.post("/set-cred")
@cache(namespace="creds", expire=1)
async def setCreds(creds: credentials):
    global cred 
    cred = creds
    return cred

@app.get("/get-Timtable")
async def getTimeTable(dayRange: int = 1):
    s = await login()
    now: datetime.date = datetime.datetime.now()
    sortedTimeTable : list = sorted(s.my_timetable(start= now,end=now+datetime.timedelta(days=dayRange)), key=lambda x: x.start, reverse=False)
    i = 0
    retStr : str =""
    for t in sortedTimeTable:
        if i>1:
            if t.start.day - sortedTimeTable[i-1].start.day >= 1:
                retStr = retStr.__add__("---\n")
        retStr = retStr.__add__(t.studentGroup)
        retStr = retStr.__add__("\n")
        i += 1;
    return retStr

@app.get("/get-creds")
@cache(namespace="test", expire=10)
async def getCreds():
    return