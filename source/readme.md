# Readme

## Links

### link to doc of WEBUNTIS API

- https://python-webuntis.readthedocs.io

### basic code Test for getting your timetable

```python

import webuntis
import datetime

DAYRANGE = 1

with webuntis.Session(
    username='STUDENT_NAME',
    password='PASSWORT',
    server='arche.webuntis.com',
    school='litec',
    useragent='WebUntis Test'
).login() as s:
    now = datetime.datetime.now()
    sortedTimeTable : list = sorted(s.my_timetable(start= now,end=now+datetime.timedelta(days=DAYRANGE)), key=lambda x: x.start, reverse=False)
    i = 0
    for t in sortedTimeTable:
        if i>1:
            if t.start.day - sortedTimeTable[i-1].start.day >= 1:
                print("---")
        print(t.studentGroup + ", " + t.start.strftime("%H:%M"), t.end.strftime("%H:%M"))
        i += 1



print((i*50)/60 - (i*50)/60%1, "h")

```

### get acces Token for Microsoft Graph

from [source](https://gist.githubusercontent.com/marianreha/9605c1552770ed90cde256a15c51256a/raw/573f6eed4a77adab8684ce056b42577de24bcb14/ms_graph_tutorial_1.py)#

```python
# Define imports
import msal

# Enter the details of your AAD app registration
client_id = '{YOUR CLIENT ID}'
client_secret = '{YOUR CLIENT SECRET}'
authority = 'https://login.microsoftonline.com/{YOUR TENANT ID}'
scope = ['https://graph.microsoft.com/.default']

# Create an MSAL instance providing the client_id, authority and client_credential parameters
client = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)

# First, try to lookup an access token in cache
token_result = client.acquire_token_silent(scope, account=None)

# If the token is available in cache, save it to a variable
if token_result:
  access_token = 'Bearer ' + token_result['access_token']
  print('Access token was loaded from cache')

# If the token is not available in cache, acquire a new one from Azure AD and save it to a variable
if not token_result:
  token_result = client.acquire_token_for_client(scopes=scope)
  access_token = 'Bearer ' + token_result['access_token']
  print('New access token was acquired from Azure AD')

print(access_token)
```
