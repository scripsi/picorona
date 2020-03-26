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

# 
new_cases = 10
day_text = now_time.strftime("%A")
date_text = now_time.strftime("%d/%m")

# 152 x 74

# img = Image.new(mode = "P", size = (inky_display.WIDTH,inky_display.HEIGHT), color = inky_display.WHITE))
img = Image.open("/home/pi/picorona/background.png")
draw = ImageDraw.Draw(img)
virus_bg_source = img.copy()
virus_bg = virus_bg_source.crop((inky_display.WIDTH-152,inky_display.HEIGHT-74,inky_display.WIDTH,inky_display.HEIGHT))
virus_img = Image.open("/home/pi/picorona/coronavirus.png")

# Add viruses to image
for virus in range(1, new_cases, 1):
    x = random.randint(0, 151)
    y = random.randint(0, 73)
    virus_bg.paste(virus_img,(x-10,y-10))

img.paste(virus_bg,(inky_display.WIDTH-152,inky_display.HEIGHT-74))

# font = ImageFont.truetype(SourceSansPro, 48)
font = ImageFont.truetype(FredokaOne, 24)
days_on_lockdown_text = str(days_on_lockdown)
draw.text((10,60), days_on_lockdown_text, inky_display.WHITE, font)

dw, dh = font.getsize(day_text)
tw, th = font.getsize(date_text)

draw.text((5,1), day_text, inky_display.WHITE, font)
draw.text((10+dw,1), date_text, inky_display.WHITE, font)


# qmark = "?"
# qw, qh = font.getsize(qmark)

# for q in range(1, 200, 1):
#     qx = random.randint(0, inky_display.WIDTH) - qw
#     qy = random.randint(0, inky_display.HEIGHT) - qh
#     draw.text((qx,qy), "?", random.randint(0, 2), font)

# draw.ellipse([81,27,131,77], inky_display.BLACK)

#number_text = str(days_to_brexit1)
#w, h = font.getsize(number_text)
#rx = (inky_display.WIDTH / 2) - (w / 2) - 3
#ry = (inky_display.HEIGHT / 2) - (h / 2) - 3
#rxx = (inky_display.WIDTH / 2) + (w / 2) + 3
#ryy = (inky_display.HEIGHT / 2) + (h / 2) + 3
#draw.rectangle((rx,ry,rxx,ryy), inky_display.BLACK)
#x = (inky_display.WIDTH / 2) - (w / 2)
#y = (inky_display.HEIGHT / 2) - (h / 2) - 7
# first_text = str(days_to_brexit1)
# second_text = ' or ' + str(days_to_brexit2)
# fw, fh = font.getsize(first_text)
# draw.text((x,y), first_text, inky_display.WHITE, font)
# draw.text((x+fw,y), second_text, inky_display.RED, font)
#draw.text((x,y), number_text, inky_display.WHITE, font)

# Display the logo image

inky_display.set_image(img.rotate(180))
inky_display.show()
