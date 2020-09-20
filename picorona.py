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
from SPARQLWrapper import SPARQLWrapper, CSV
import re
import random
import pandas as pd

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


# Use the rather nice statistics.gov.scot API to get the data we need.
# 
# We're looking at the Scottish NHS Coronavirus figures to track the Lothian
# NHS region. If you want to look at other statistics you'll have to change
# the code below - there are lots of useful web tutorials to help you.
# 
# The aim is to end up with a total number of cases in "cases_number" and
# the date of that statistic in "cases_date"

# get web page content
# get web page content
web_success = False
parse_success = False
dailyurl="https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/7fad90e5-6f19-455b-bc07-694a22f8d5dc/download/total_cases_by_hb.csv"
trendurl="https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/2dd8534b-0a6f-4744-9253-9565d62f96c2/download/trend_hb.csv"
health_board="S08000024" #Lothian Health Board

try:
    daily_cases_data=pd.read_csv(dailyurl, sep=",", index_col="HB")
    trend_cases_data=pd.read_csv(trendurl, sep=",")
except:
    web_success = False
    print("Error! Web page access failed - network or remote server failure.")
else:
    web_success = True
    # parse the daily data
    new_cases = daily_cases_data.loc[health_board,'NewPositive']
    cases_number = daily_cases_data.loc[health_board,'TotalCases']
    # recast date column to date format
    daily_cases_data.loc[:,'Date'] = pd.to_datetime(daily_cases_data.Date,format="%Y%m%d")
    cases_date = daily_cases_data.loc[health_board,'Date']
    
    # parse the trend data
    # limit it to just the health board we're interested in
    trend_cases_data.drop(trend_cases_data[trend_cases_data['HB'] != health_board].index, inplace=True)
    # recast date column to date format
    trend_cases_data.loc[:,'Date'] = pd.to_datetime(trend_cases_data.Date,format="%Y%m%d")
    # sort data by date
    trend_cases_data.sort_values(by=['Date'], inplace=True)
    # then fix the index
    trend_cases_data.reset_index(drop=True, inplace=True)
    # create a rolling 7day mean
    trend_cases_data['d7_mean'] = trend_cases_data.DailyPositive.rolling(window=7,min_periods=1).mean()
    # create a rolling 30day max
    trend_cases_data['d30_max'] = trend_cases_data.DailyPositive.rolling(window=30,min_periods=1).max()
    d30_max = trend_cases_data.at[trend_cases_data.last_valid_index(),'d30_max']
    
    print(cases_number,"cases of Coronavirus in Lothian up to", cases_date.strftime("%A, %d %B %Y"))
    print(new_cases,"new cases since the previous day")

# Phew! we've got all the info we need - now to show it on the display

# Set up the display image
img = Image.open("/home/pi/picorona/background.png")
draw = ImageDraw.Draw(img)
bigfont = ImageFont.truetype(FredokaOne, 24)
littlefont = ImageFont.truetype(FredokaOne, 12)
virus_bg_source = img.copy()
virus_bg = virus_bg_source.crop((inky_display.WIDTH-153,inky_display.HEIGHT-74,inky_display.WIDTH,inky_display.HEIGHT))
vdraw = ImageDraw.Draw(virus_bg)
virus_img = Image.open("/home/pi/picorona/coronavirus.png")
virus_mask = Image.open("/home/pi/picorona/coronavirus-mask.png")

if web_success:  
    # Add viruses to the image
    for virus in range(new_cases):
        x = random.randint(0, 152)
        y = random.randint(0, 73)
        virus_bg.paste(virus_img,(x-10,y-10),virus_mask)
    # Draw trend line
    v_max = 100
    v_line = []
    for v_day in range(30):
        x = 3 + ((30-v_day) * 5)
        y = 72 - (trend_cases_data.at[trend_cases_data.last_valid_index()-v_day,'d7_mean'] / v_max) * 70
        v_line.append((x,y))
    vdraw.line(v_line,fill=inky_display.WHITE,width=7)
    vdraw.line(v_line,fill=inky_display.RED,width=3) 
else:
    vdraw.text((5,25), "Netwk Error", inky_display.RED, bigfont)

img.paste(virus_bg,(inky_display.WIDTH-153,inky_display.HEIGHT-74))

draw.text((10,35), cases_date.strftime("%d/%m"), inky_display.RED, littlefont)
draw.text((10,45), str(new_cases), inky_display.WHITE, bigfont)

dw, dh = bigfont.getsize(day_text)

draw.text((5,0), day_text, inky_display.WHITE, bigfont)
draw.text((10+dw,0), date_text, inky_display.WHITE, bigfont)

# For some reason, I've mounted my Raspberry Pi upside-down, so rotate the image!
inky_display.set_image(img.rotate(180))

# Display the finished image
inky_display.show()
