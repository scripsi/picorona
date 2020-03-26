#!/usr/bin/env python

# This script is run every day by running "crontab -e" and
# adding the following line:
#
#   1 23 * * * /home/pi/brexit.py >/dev/null 2>&1

from PIL import Image, ImageFont, ImageDraw
from inky import InkyPHAT
from font_source_sans_pro import SourceSansPro
from font_fredoka_one import FredokaOne
from datetime import datetime, timedelta
import random

print("""Inky pHAT: picorona

Counting the lockdown

""")

inky_display = InkyPHAT("red")

inky_display.set_border(inky_display.BLACK)
# inky_display.set_rotation(180)

# Calculate days on lockdown
lockdown_time = datetime(2020,3,16)
now_time = datetime.now()
time_since_lockdown = now_time - lockdown_time
days_on_lockdown = time_since_lockdown.days

new_cases = 10
day_text = now_time.strftime("%A")
date_text = now_time.strftime("%d/%m")

# 153 x 74

img = Image.open("/home/pi/picorona/background.png")
draw = ImageDraw.Draw(img)
virus_bg_source = img.copy()
virus_bg = virus_bg_source.crop((inky_display.WIDTH-153,inky_display.HEIGHT-74,inky_display.WIDTH,inky_display.HEIGHT))
virus_img = Image.open("/home/pi/picorona/coronavirus.png")

# Add viruses to image
for virus in range(1, new_cases, 1):
    x = random.randint(0, 152)
    y = random.randint(0, 73)
    virus_bg.paste(virus_img,(x-10,y-10))

img.paste(virus_bg,(inky_display.WIDTH-153,inky_display.HEIGHT-74))

# font = ImageFont.truetype(SourceSansPro, 48)
font = ImageFont.truetype(FredokaOne, 24)
days_on_lockdown_text = str(days_on_lockdown)
draw.text((10,60), days_on_lockdown_text, inky_display.WHITE, font)

dw, dh = font.getsize(day_text)
tw, th = font.getsize(date_text)

draw.text((5,0), day_text, inky_display.WHITE, font)
draw.text((10+dw,0), date_text, inky_display.WHITE, font)


# Display the finished image

inky_display.set_image(img.rotate(180))
inky_display.show()
