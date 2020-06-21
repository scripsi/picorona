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
web_success = False

sparql_endpoint = "https://statistics.gov.scot/sparql"
sparql_query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?periodname ?value
WHERE {
	?obs <http://purl.org/linked-data/cube#dataSet> <http://statistics.gov.scot/data/coronavirus-covid-19-management-information> .
	?obs <http://purl.org/linked-data/sdmx/2009/dimension#refArea> <http://statistics.gov.scot/id/statistical-geography/S08000024> .
    ?obs <http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure> <http://statistics.gov.scot/def/concept/measure-units/testing-cumulative-people-tested-for-covid-19-positive> .
	?obs <http://purl.org/linked-data/sdmx/2009/dimension#refPeriod> ?perioduri .
	?obs <http://statistics.gov.scot/def/measure-properties/count> ?value .
	?perioduri rdfs:label ?periodname .
}
"""

sparql = SPARQLWrapper(sparql_endpoint)
sparql.setQuery(sparql_query)
sparql.setReturnFormat(CSV)

try:
    sparql_results = sparql.query().convert()
except:
    web_success = False
    print("Error! API access failed - network or remote server failure.")  
else:
    web_success = True

    _csv = pd.compat.StringIO(sparql_results.decode('utf-8'))
    cases_data=pd.read_csv(_csv, sep=",")

    # rename data columns to something more useful
    cases_data.rename(
        columns={
            'periodname' : 'sample_day',
            'value' : 'cumulative_count'
        }, inplace=True
    )
    # recast date sample_day column to date format
    cases_data.loc[:,'sample_day'] = pd.to_datetime(cases_data.sample_day)
    # sort data by date
    cases_data.sort_values(by=['sample_day'], inplace=True)
    # recast cumulative_count column safely to numeric format, replace the NaNs with zero and then recast to int
    cases_data.cumulative_count = pd.to_numeric(cases_data.cumulative_count,errors='coerce')
    cases_data.loc[:,'cumulative_count'].fillna(0, inplace=True)
    cases_data.cumulative_count = cases_data.cumulative_count.astype('Int64')

    # create a daily_count column, replace the NaNs with zero and then recast to int
    cases_data['daily_count'] = cases_data.cumulative_count.diff()
    cases_data.loc[:,'daily_count'].fillna(0, inplace=True)
    cases_data.daily_count = cases_data.daily_count.astype('Int64')

    # create a rolling 7day mean
    cases_data['d7_mean'] = cases_data.daily_count.rolling(window=7,min_periods=1).mean()

    # create a rolling 30day max
    cases_data['d30_max'] = cases_data.daily_count.rolling(window=30,min_periods=1).max()
    # print(cases_data.describe())
    # print(cases_data)

    cases_number = cases_data.at[cases_data.last_valid_index(),'cumulative_count']
    new_cases = cases_data.at[cases_data.last_valid_index(),'daily_count']
    cases_date = cases_data.at[cases_data.last_valid_index(),'sample_day']
    d30_max = cases_data.at[cases_data.last_valid_index(),'d30_max']
    print(cases_number,"cases of Coronavirus in Lothian up to", cases_date.strftime("%A, %d %B %Y"))
    print(new_cases,"new cases since the previous day")

# Phew! we've got all the info we need - now to show it on the display

# Set up the display image
img = Image.open("/home/pi/picorona/background.png")
draw = ImageDraw.Draw(img)
font = ImageFont.truetype(FredokaOne, 24)
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
    if d30_max < 10:
        v_max = 10
    else:
        v_max = d30_max
    v_line = []
    for v_day in range(30):
        v_line.append((3 + (v_day * 5), 2 + (cases_data.at[cases_data.last_valid_index()-v_day,'d7_mean'] / v_max) * 70))
    
    vdraw.line(v_line,fill=inky_display.WHITE,width=7)
    vdraw.line(v_line,fill=inky_display.RED,width=3) 
else:
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
