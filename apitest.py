from SPARQLWrapper import SPARQLWrapper, CSV
from PIL import Image, ImageFont, ImageDraw
from io import StringIO
import pandas as pd
from datetime import datetime, timedelta
import random



# get web page content
web_success = False
parse_success = False

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

    _csv = StringIO(sparql_results.decode('utf-8'))
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
    # then fix the index
    cases_data.reset_index(drop=True, inplace=True)
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
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(cases_data)

    cases_number = cases_data.at[cases_data.last_valid_index(),'cumulative_count']
    new_cases = cases_data.at[cases_data.last_valid_index(),'daily_count']
    cases_date = cases_data.at[cases_data.last_valid_index(),'sample_day']
    d30_max = cases_data.at[cases_data.last_valid_index(),'d30_max']
    print(cases_number,"cases of Coronavirus in Lothian up to", cases_date.strftime("%A, %d %B %Y"))
    print(new_cases,"new cases since the previous day")

# Set up the display image
inky_RED = 2
inky_WHITE = 0
inky_BLACK = 1
inky_WIDTH = 212
inky_HEIGHT = 104
img = Image.open("background.png")
virus_bg_source = img.copy()
virus_bg = virus_bg_source.crop((inky_WIDTH-153,inky_HEIGHT-74,inky_WIDTH,inky_HEIGHT))
vdraw = ImageDraw.Draw(virus_bg)
virus_img = Image.open("coronavirus.png")
virus_mask = Image.open("coronavirus-mask.png")

if web_success:  
    # Add viruses to the image
    for virus in range(new_cases):
        x = random.randint(0, 152)
        y = random.randint(0, 73)
        virus_bg.paste(virus_img,(x-10,y-10),virus_mask)
    # Draw trend line
    # if d30_max < 10:
    #     v_max = 10
    # else:
    #     v_max = d30_max
    v_max = 10
    v_line = []
    for v_day in range(30):
        x = 3 + ((30-v_day) * 5)
        y = 72 - (cases_data.at[cases_data.last_valid_index()-v_day,'d7_mean'] / v_max) * 70
        v_line.append((x,y))
        # print(v_day, x, y, cases_data.at[cases_data.last_valid_index()-v_day,'d7_mean'])
        # v_line.append((3 + ((30-v_day) * 5), 72 - (cases_data.at[cases_data.last_valid_index()-v_day,'d7_mean'] / v_max) * 70))
        # v_line.append((3 + (v_day * 5), 2 + (v_day / v_max) * 70))
    vdraw.line(v_line,fill=inky_WHITE,width=7)
    vdraw.line(v_line,fill=inky_RED,width=3)
    virus_bg.save("virus-test.png")

