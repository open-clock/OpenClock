"""Data models for the OpenClock API.

This module contains all the Pydantic models and enums used for:
- System configuration and hardware types
- Network credentials and WiFi settings
- Microsoft email message formats
- Untis calendar authentication
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional

# CORS allowed origins
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

class ClockType(Enum):
    """Available clock hardware types.
    
    Defines the physical clock models supported by the system.
    
    Attributes:
        Mini: Compact clock hardware variant
        XL: Large format clock hardware variant
    """
    Mini = "Mini"
    XL = "XL"

class model(BaseModel):
    """System model and setup information.
    
    Represents the current clock hardware configuration and setup state.
    
    Attributes:
        model (ClockType): The type of clock hardware being used
        setup (bool): Whether initial system setup has been completed
    """
    model: ClockType
    setup: bool
    wallmounted: bool

class credentials(BaseModel):
    """Untis authentication credentials.
    
    Used for authenticating with the WebUntis calendar service.
    
    Attributes:
        username (str): WebUntis account username
        password (str): WebUntis account password
        server (str): WebUntis server URL (e.g. 'demo.webuntis.com')
        school (str): School identifier in WebUntis
        useragent (str): User agent string for API requests
    """
    username: str
    password: str
    server: str
    school: str
    useragent: str = "OpenClDevtest"

class command(BaseModel):
    """System command model.
    
    Used for executing system commands through the API.
    
    Attributes:
        command (str): The command string to execute
    """
    command: str

class NetworkCredentials(BaseModel):
    """WiFi network credentials.
    
    Used for connecting to wireless networks.
    
    Attributes:
        ssid (str): Network name to connect to
        password (str): Network password/key
    """
    ssid: str
    password: str

class EmailMessage(BaseModel):
    """Microsoft email message format.
    
    Represents an email message retrieved from Microsoft Graph API.
    
    Attributes:
        subject (str): Email subject line
        from_email (str): Sender's email address
        received_date (str): Date and time message was received
        body (Optional[str]): Email body text, if available
    """
    subject: str
    from_email: str
    received_date: str
    body: Optional[str]

class ConfigModel(BaseModel):
    """System configuration settings."""
    model: ClockType
    setup: bool = False
    wallmounted: bool = False
    debug: bool = False