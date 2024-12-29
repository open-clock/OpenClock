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

    
    def __dict__(self):
        return {"username":self.username,
                "password":self.password,
                "server":self.server,
                "school":self.school,
                "useragent":self.useragent}


