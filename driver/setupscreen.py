from PIL import Image,ImageDraw,ImageFont
#import ipdetect

# Display resolution
#EPD_WIDTH       = 800
#EPD_HEIGHT      = 480

#GRAY1  = 0xff #white
#GRAY2  = 0xC0
#GRAY3  = 0x80 #gray
#GRAY1 = GRAY2 = GRAY3 = GRAY4  = 0x00 #Blackest

#IPFont = ImageFont.truetype('./GeistMono-Regular.ttf', 32)
#HeadingFont = ImageFont.truetype('./Geist-Regular.ttf', 65)
#SubHeadingFont = ImageFont.truetype('./Geist-Regular.ttf', 32)

def drawSetupScreen(wallmount: bool) -> Image:
    #image = Image.new('1', (EPD_HEIGHT, EPD_WIDTH), 255)  # 255: clear the frame    L -> Greyscale  1 -> B/W
    #draw = ImageDraw.Draw(image)
    #draw.text((0,30), "Ready to set up", font=HeadingFont, fill=GRAY4, anchor="lt", align="left")
    #draw.text((0,100), "Connect to WIFI and visit", font=SubHeadingFont, fill=GRAY4, anchor="lt", align="left")
    #draw.text((0,150), "192.167.100.100", font=IPFont, fill=GRAY4, anchor="lt", align="left")
    #draw.text((200,150), "to start the wizard", font=SubHeadingFont, fill=GRAY4, anchor="lt", align="left")

    image = Image.open("/displaydriver/setup.png")

    if not wallmount:
        image = image.transpose(Image.ROTATE_180)

    return image

if __name__ == '__main__':
    drawSetupScreen(True).show()