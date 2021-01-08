import urllib.request
import re
import pandas as pd
from datetime import datetime, timedelta

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
    
    print(cases_number,"cases of Coronavirus in Lothian up to", cases_date.strftime("%A, %d %B %Y"))
    print(new_cases,"new cases since the previous day")
