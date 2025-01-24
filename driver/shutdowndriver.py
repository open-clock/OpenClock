from waveshare_epd import epd7in5_V2
from PIL import Image
import os

WALLMOUNT = False

if os.path.exists("/displaydriver/skipshutdown"):
    epd = epd7in5_V2.EPD()
    epd.init_fast()
    epd.Clear()
    epd.sleep()
    exit()

epd = epd7in5_V2.EPD()

epd.init_fast()
Limage = Image.open("/displaydriver/shutdown.png")
if not WALLMOUNT:
    Limage = Limage.transpose(Image.ROTATE_180)
epd.display(epd.getbuffer(Limage))
epd.sleep()