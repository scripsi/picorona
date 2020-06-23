import urllib.request
import re
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

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
    cases_date_text = soup.find(string=re.compile("Scottish COVID-19 test numbers:"))
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
                print(cases_data)
                try:
                    cases_number = int(cases_data.at["Lothian",1])
                except:
                    parse_success = False
                    print("Error! Parsing of Lothian cases number failed.")
                else:
                    parse_success = True
                    # Open the time series data from a csv file
                    lothian_series = pd.read_csv("lothian.csv", header=None, index_col=0, parse_dates=True, squeeze=True)

                    # Update the time series data and save it back to the csv file
                    lothian_series[cases_date] = cases_number
                    lothian_series.to_csv("lothian.csv", header=False)

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
    
