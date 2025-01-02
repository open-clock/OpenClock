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
    username: str
    password: str
    server: str
    school: str
    useragent: str
