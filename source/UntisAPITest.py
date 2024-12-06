import webuntis
import datetime


DAYRANGE = 1

with webuntis.Session( # Loging into a Session as a Student
    username='40146720210116',
    password='janw2007',
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
        i += 1;