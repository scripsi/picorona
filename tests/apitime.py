from SPARQLWrapper import SPARQLWrapper, CSV
import pandas as pd
from io import StringIO
from PIL import Image, ImageFont, ImageDraw
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
    data_timestamp = datetime.today()
    print(data_timestamp.strftime("%y-%m-%d-%H:%M:%S"), cases_date.strftime("%y-%m-%d"), cases_number, new_cases)

