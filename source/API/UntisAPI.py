from pydantic import BaseModel
from fastApi import FastAPI
import webuntis.session
import webuntis
import datetime

app = FastAPI()

class credentials(BaseModel):
    username : str
    password : str
    server : str
    school : str
    useragent : str

    def toJSON():
        pass

class cacheClass:
    creds
    session
    timeTable: list


global cache
cache = cacheClass()
{
 "username": "40146720210116",
  "password": "187",
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
        global session
        session = webuntis.Session( 
            username=creds.username,
            password=creds.password,
            server=creds.server,
            school=creds.school,
            useragent=creds.useragent
        ).login()
        return session
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
async def setCreds(cred: credentials):
    global creds 
    creds = cred
    return creds

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

@app.get("/session")
def getSession():
    global session
    if session is not None:
        return True
    return False