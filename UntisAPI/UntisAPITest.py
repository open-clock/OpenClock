import webuntis
import datetime

DAYRANGE = 7

with webuntis.Session(
    username='40146720210116',
    password='janw2007',
    server='arche.webuntis.com',
    school='litec',
    useragent='WebUntis Test'
).login() as s:
    now = datetime.datetime.now()
    sortedTimeTable = sorted(s.my_timetable(start= now,end=now+datetime.timedelta(days=DAYRANGE)), key=lambda x: x.start, reverse=False)
    i = 0
    for t in sortedTimeTable:
        if i>1:
            if t.start.day - sortedTimeTable[i-1].start.day >= 1:
                print("---")
        print(t.studentGroup + ", " + t.start.strftime("%H:%M"))
        i += 1;

