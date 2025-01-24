from PIL import Image,ImageDraw,ImageFont
import datetime
import math
from waveshare_epd import epd7in5_V2
import signal
import time

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

WALLMOUNT = False

#GRAY1  = 0xff #white
#GRAY2  = 0xC0
#GRAY3  = 0x80 #gray
GRAY1 = GRAY2 = GRAY3 = GRAY4  = 0x00 #Blackest

CENTER_X = EPD_HEIGHT - 128 - 24

clockFont = ImageFont.truetype('./GeistMono-Regular.ttf', 32)
infoFont = ImageFont.truetype('./GeistMono-Regular.ttf', 12)
timeTableHeaderFont = ImageFont.truetype('./Geist-Regular.ttf', 20)
timeTableLessonFont = ImageFont.truetype('./GeistMono-Regular.ttf', 20)
timeTableNextEventFont = ImageFont.truetype('./Geist-Regular.ttf', 14)

def handle_exit(sig, frame):
    raise(SystemExit)
signal.signal(signal.SIGTERM, handle_exit)

def drawScreen():
    image = Image.new('1', (EPD_HEIGHT, EPD_WIDTH), 255)  # 255: clear the frame    L -> Greyscale  1 -> B/W
    draw = ImageDraw.Draw(image)

    # info
    draw.text((0,2), "OpenClock Mini", font=infoFont, fill=GRAY4, anchor="lt", align="left")
    draw.text((EPD_HEIGHT,2), "192.168.1.100", font=infoFont, fill=GRAY4, anchor="rt", align="right")

    # notifications
    for i in range(1, 13):
        start = 20 + (i - 1) * 63
        end = start + 60
        draw.rounded_rectangle(((2, start), (2 + 175, end)), 8, fill=None, outline=GRAY4, width=1)

        draw.text((2 + 4, start + 2), "#klasse", font=infoFont, fill=GRAY4, anchor="lt", align="left")
        draw.text((175 - 2, start + 2), "13:10", font=infoFont, fill=GRAY4, anchor="rt", align="right")
        draw.line(((2 + 1, start + 12), (175 - 100, start + 12)), fill=GRAY2, width=1)
        draw.text((2 + 4, start + 2 + 12), "Minichberger Jakob", font=infoFont, fill=GRAY4, anchor="lt", align="left")
        draw.line(((2 + 1, start + 12 + 2 + 12), (175 + 1, start + 12 + 2 + 12)), fill=GRAY2, width=1)
        draw.text((2 + 4, start + 12 + 2 + 12), "Kann mir wer SYT\nerklärn?", font=infoFont, fill=GRAY4, align="left")

    # timetable
    draw.rectangle(((180, 275), (EPD_HEIGHT, EPD_WIDTH)), fill=None, outline=GRAY4, width=1)
    draw.line(((180, 309), (EPD_HEIGHT, 309)), fill=GRAY4, width=1)
    draw.line(((280, 275), (280, EPD_WIDTH)), fill=GRAY4, width=1) # vertical lines
    draw.line(((380, 275), (380, EPD_WIDTH)), fill=GRAY4, width=1)

    draw.text((200, 285), "Heute", font=timeTableHeaderFont, fill=GRAY4, anchor="lt", align="left")
    draw.text((295, 285), "Morgen", font=timeTableHeaderFont, fill=GRAY4, anchor="lt", align="left")
    draw.text((388, 272), "Nächster Tag\nmit Ereignis", font=timeTableNextEventFont, fill=GRAY4, align="left")

    # lessons
    for i in range(1,11):
        start = 314 + (i - 1) * 48
        end = start + 46
        draw.rounded_rectangle(((185, start), (185 + 90, end)), 8, fill=None, outline=GRAY4, width=1)
        draw.text((185 + 41, start - 3), "MEDT\nSIDE", font=timeTableLessonFont, fill=GRAY4, align="right")
        draw.text((185 + 4, start + 2), "01:00", font=infoFont, fill=GRAY4, anchor="lt", align="left")
        draw.text((185 + 4, end - 1), "02:00", font=infoFont, fill=GRAY4, anchor="lb", align="left")
        draw.text((185 + 4, start + (end - start) / 2), "9-01", font=infoFont, fill=GRAY4, anchor="lm", align="left")

    for i in range(1,11):
        start = 314 + (i - 1) * 48
        end = start + 46
        draw.rounded_rectangle(((285, start), (285 + 90, end)), 8, fill=None, outline=GRAY4, width=1)
        draw.text((285 + 41, start - 3), "MEDT\nSIDE", font=timeTableLessonFont, fill=GRAY4, align="right")
        draw.text((285 + 4, start + 2), "01:00", font=infoFont, fill=GRAY4, anchor="lt", align="left")
        draw.text((285 + 4, end - 1), "02:00", font=infoFont, fill=GRAY4, anchor="lb", align="left")
        draw.text((285 + 4, start + (end - start) / 2), "9-01", font=infoFont, fill=GRAY4, anchor="lm", align="left")

    for i in range(1,11):
        start = 314 + (i - 1) * 48
        end = start + 46
        if i == 3:
            draw.rounded_rectangle(((385, start), (385 + 90, end)), 8, fill=GRAY3, outline=GRAY4, width=1)
        else:
            draw.rounded_rectangle(((385, start), (385 + 90, end)), 8, fill=None, outline=GRAY4, width=1)

        if i == 4:
            draw.line(((385 + 3, start + 3), (385 + 90 - 3, end - 3)), fill=GRAY4, width=3)
            draw.line(((385 + 3, end - 3), (385 + 90 - 3, start + 3)), fill=GRAY4, width=3)

        draw.text((385 + 41, start - 3), "MEDT\nSIDE", font=timeTableLessonFont, fill=GRAY4, align="right")
        draw.text((385 + 4, start + 2), "01:00", font=infoFont, fill=GRAY4, anchor="lt", align="left")
        draw.text((385 + 4, end - 1), "02:00", font=infoFont, fill=GRAY4, anchor="lb", align="left")
        draw.text((385 + 4, start + (end - start) / 2), "9-01", font=infoFont, fill=GRAY4, anchor="lm", align="left")

    # Clock stuff
    draw.circle((CENTER_X, 128 + 14), 128, fill=None, outline=GRAY4, width=1) # Clock face
    draw.circle((CENTER_X, 128 + 14), 3, fill=GRAY4) # Clock face center nub
    draw.rectangle(((CENTER_X - 4, 14), (CENTER_X + 8 - 4, 14 + 8)), fill=GRAY4, width=9) #12 o'clock marker
    draw.rectangle(((CENTER_X - 4, 14 + (128 *2) - 8), (CENTER_X + 8 - 4, 14 + (128*2) + 8 - 8)), fill=GRAY4, width=9) #6 o'clock marker
    draw.rectangle(((EPD_HEIGHT - 24 - 8, 14 + 128 - 4), (EPD_HEIGHT - 24 + 8 - 8, 14 + 8 + 128 - 4)), fill=GRAY4, width=9) #3 o'clock marker
    draw.rectangle(((EPD_HEIGHT - 24 - (128 *2), 14 + 128 - 4), (EPD_HEIGHT - 24 + 8 - (128 *2), 14 + 8 + 128 - 4)), fill=GRAY4, width=9) #9 o'clock marker
    draw.text((CENTER_X, 128 + 32), datetime.datetime.now().strftime("%H:%M"), font=clockFont, fill=GRAY4, align="center", anchor="mm")

    now = datetime.datetime.now()
    hour = now.hour % 12
    if hour == 12:
        hour = 0

    minutes_decimal = now.minute / 60.0
    currentHour = hour + minutes_decimal
    currentMinute = now.minute + (now.second / 60.0)
    currentSecond = now.second

    a = (currentHour * 30) - 90
    a_rad = math.radians(-a)
    hxdiff = 90 * math.cos(a_rad)
    hydiff = 90 * math.sin(a_rad)

    a = (currentMinute * 6) - 90
    a_rad = math.radians(-a)
    mxdiff = 125 * math.cos(a_rad)
    mydiff = 125 * math.sin(a_rad)

    a = (currentSecond * 6) - 90
    a_rad = math.radians(-a)
    sxdiff = 135 * math.cos(a_rad)
    sydiff = 135 * math.sin(a_rad)

    draw.line((CENTER_X, 128 + 14, CENTER_X + hxdiff, 128 + 14 - hydiff), fill=GRAY4, width=2) # Hour hand
    draw.line((CENTER_X, 128 + 14, CENTER_X + mxdiff, 128 + 14 - mydiff), fill=GRAY4, width=2) # Minute hand
    draw.line((CENTER_X, 128 + 14, CENTER_X + sxdiff, 128 + 14 - sydiff), fill=GRAY4, width=2) # Second hand

    if not WALLMOUNT:
        image = image.transpose(Image.ROTATE_180)

    return image

try:
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(drawScreen()))
    lastMinute = datetime.datetime.now().minute

    try:
        while True:
            if datetime.datetime.now().minute != lastMinute:
                epd.init_fast()
                epd.display(epd.getbuffer(drawScreen()))
                epd.sleep()
                lastMinute = datetime.datetime.now().minute
            else:
                epd.init_part()
                epd.display_Partial(epd.getbuffer(drawScreen()),0, 0, epd.width, epd.height)
                epd.sleep()
                time.sleep(0.01)
    except (KeyboardInterrupt, SystemExit):
        epd.sleep()
        print("Exiting...")
        #raise KeyboardInterrupt

except IOError as e:
    print(e)

except KeyboardInterrupt:
    epd7in5_V2.epdconfig.module_exit(cleanup=True)
    exit()