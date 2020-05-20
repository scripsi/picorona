#!/usr/bin/env python

# This script can be run twice every day by running "crontab -e" and
# adding the following lines:
#
#   0 0 * * * /usr/bin/python3 /home/pi/picorona/picorona.py >/dev/null 2>&1
#   0 15 * * * /usr/bin/python3 /home/pi/picorona/picorona.py >/dev/null 2>&1

# import lots of necessary stuff
from PIL import Image, ImageFont, ImageDraw
from inky import InkyPHAT
from font_fredoka_one import FredokaOne
from datetime import datetime, timedelta
import urllib.request
import re
import random
import pandas as pd
from bs4 import BeautifulSoup

print("""Inky pHAT: picorona

Counting the lockdown

""")

# Set up the InkyPHAT display - I'm using the red version
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.BLACK)

# Calculate days on lockdown
# We're defining the start as 16th March, when we began isolating as much as possible
lockdown_day = datetime(2020,3,16)
time_since_lockdown = datetime.now() - lockdown_day
days_on_lockdown = time_since_lockdown.days

# Get the current day name and date to display later
day_text = datetime.now().strftime("%A")
date_text = datetime.now().strftime("%d/%m")


# Use BeautifulSoup to scrape the data we need from the appropriate web page.
# 
# We're looking at the Scottish NHS Coronavirus figures to track the Lothian
# NHS region. If you want to look at other statistics you'll have to change
# the code below - there are lots of useful web tutorials to help you.
# 
# The aim is to end up with a total number of cases in "cases_number" and
# the date of that statistic in "cases_date"

# get web page content
web_success = False
parse_success = False
req = urllib.request.Request(url="https://www.gov.scot/publications/coronavirus-covid-19-tests-and-cases-in-scotland/")
# req = urllib.request.Request(url="https://www.gov.scot/coronavirus-covid-19/")
# req = urllib.request.Request(url="https://www.gov.scot/")
try:
    f = urllib.request.urlopen(req)
except urllib.error.URLError as e:
    web_success = False
    print("Error! Web page access failed - network or remote server failure.")
else:
    web_success = True
    
    # parse the web page to find the data
    xhtml = f.read().decode("utf-8")
    soup = BeautifulSoup(xhtml, "html.parser")
    cases_date_text = soup.find(string=re.compile("Scottish numbers:"))
    if cases_date_text:
        try:
            cases_date = datetime.strptime(cases_date_text, "Scottish COVID-19 test numbers: %d %B %Y")
        except:
            parse_success = False
            print("Error! Parsing of cases date failed.")
        else:
            region_table = soup.find("table")
            if region_table:
                data_tables = pd.read_html(str(region_table), index_col=0)
                cases_data = data_tables[0]
                try:
                    cases_number = int(cases_data.at["Lothian",1])
                except:
                    parse_success = False
                    print("Error! Parsing of Lothian cases number failed.")
                else:
                    parse_success = True
                    # Open the time series data from a csv file
                    lothian_series = pd.read_csv("/home/pi/picorona/lothian.csv", header=None, index_col=0, parse_dates=True, squeeze=True)

                    # Update the time series data and save it back to the csv file
                    lothian_series[cases_date] = cases_number
                    lothian_series.to_csv("/home/pi/picorona/lothian.csv", header=False)

                    # Calculate the number of new cases from the difference between the last two days
                    last_days = lothian_series.tail(2)
                    new_cases = last_days[1] - last_days[0]

                    print(cases_number,"cases of Coronavirus in Lothian up to", cases_date.strftime("%A, %d %B %Y"))
                    print(new_cases,"new cases since the previous day")
            else:
                parse_success = False
                print("Error! Parsing of cases table failed.")
    else:
        parse_success = False
        print("Error! Parsing of cases date failed.")

# Phew! we've got all the info we need - now to show it on the display

# Set up the display image
img = Image.open("/home/pi/picorona/background.png")
draw = ImageDraw.Draw(img)
font = ImageFont.truetype(FredokaOne, 24)
virus_bg_source = img.copy()
virus_bg = virus_bg_source.crop((inky_display.WIDTH-153,inky_display.HEIGHT-74,inky_display.WIDTH,inky_display.HEIGHT))
virus_img = Image.open("/home/pi/picorona/coronavirus.png")
virus_mask = Image.open("/home/pi/picorona/coronavirus-mask.png")

if web_success:
    if parse_success:
        # Add viruses to the image
        for virus in range(new_cases):
            x = random.randint(0, 152)
            y = random.randint(0, 73)
            virus_bg.paste(virus_img,(x-10,y-10),virus_mask)
    else:
        vdraw = ImageDraw.Draw(virus_bg)
        vdraw.text((5,25), "Parse Error", inky_display.RED, font)
else:
    vdraw = ImageDraw.Draw(virus_bg)
    vdraw.text((5,25), "Netwk Error", inky_display.RED, font)

img.paste(virus_bg,(inky_display.WIDTH-153,inky_display.HEIGHT-74))

draw.text((10,57), str(days_on_lockdown), inky_display.WHITE, font)

dw, dh = font.getsize(day_text)

draw.text((5,0), day_text, inky_display.WHITE, font)
draw.text((10+dw,0), date_text, inky_display.WHITE, font)

# For some reason, I've mounted my Raspberry Pi upside-down, so rotate the image!
inky_display.set_image(img.rotate(180))

# Display the finished image
inky_display.show()
