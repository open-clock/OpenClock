import webuntis.objects
import webuntis.session
from enum import Enum
from pydantic import BaseModel
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]



class ClockType(Enum):
    Mini="Mini"
    XL="XL"

class model(BaseModel):
    model : ClockType
    setup : bool 

class credentials(BaseModel):
    username : str
    password : str
    server : str
    school : str
    useragent : str


    def __init__(self):
        self.username : str
        self.password : str
        self.server : str
        self.school : str
        self.useragent : str


class cacheClass:
    creds : credentials
    session : webuntis.session
    timeTable: list
    currentPeriod : webuntis.objects.PeriodObject
    nextPeriod : webuntis.objects.PeriodObject
    holidays : list
    
    def __init__(self):
        self.creds = credentials
        self.session = webuntis.session.Session
        self.timeTable = None
        self.currentPeriod = []
        self.nextPeriod = None
        self.holidays = None