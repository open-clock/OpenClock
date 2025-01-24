from waveshare_epd import epd7in5_V2
from PIL import Image

WALLMOUNT = False

epd = epd7in5_V2.EPD()

epd.init()
Limage = Image.open("/displaydriver/boot.png")
if not WALLMOUNT:
    Limage = Limage.transpose(Image.ROTATE_180)
epd.display(epd.getbuffer(Limage))
epd.sleep()