# Web scraper that looks for companies that have earnings coming up in the next week and has positive sentiment around it.
# Can search for bank analysts ratings on it and see how price has been fluctuating past couple of days.
# Give recommendation as to whether or not to buy the stock.  

# Import Modules
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time 
from bs4 import BeautifulSoup
import pandas as pd

# URL of TradingView Earnings Calender.
url = 'https://www.tradingview.com/markets/stocks-usa/earnings/'

# Initialise Chrome Webdriver & navigate to url
driver = webdriver.Chrome()
driver.get(url)

# Once page has loaded click on 'next week' button to see list of companies who are reporting earnings next week.
next_week_button = WebDriverWait(driver,15).until(EC.presence_of_element_located((By.XPATH, "//div[@class='itemContent-LeZwGiB6' and text()='Next Week']")))
# next_week_button = driver.find_element(By.CLASS_NAME, 'itemContent-LeZwGiB6')
next_week_button.click()

# Wait for earnings table to load.
WebDriverWait(driver,15).until(EC.presence_of_element_located((By.CLASS_NAME, 'tv-data-table__row')))
time.sleep(5)
# Get HTML content of page
page = driver.page_source

# Quit WebDriver
driver.quit()

# Extract HTML Data
soup = BeautifulSoup(page, 'html.parser')
table = soup.find('div', class_ = 'tv-screener__content-pane').find_all('tr')

# Create empty list to store row data
rows = []
# Extract row data and append onto rows
for i,row in enumerate(table):
    if i == 0:
        continue
    row_values = [cell.text.strip() for cell in row.find_all('td')]
    row_values.insert(0,row.find('a').text.strip())
    rows.append(row_values)

# Create DataFrame
earnings_data = pd.DataFrame(rows,columns = ['TICKER','COMPANY','MKT_CAP', 'EPS_ESTIMATE', 'REPORTED_EPS','SUPRISE','SUPRISE%', 'REVENUE_FORECAST'
                                       ,'REVENUE_ACTUAL', 'DATE', 'PERIOD_ENDING', 'TIME'])


# Drop columns since they will never be populated as the data is forward looking.
cols_to_drop = ['REPORTED_EPS','SUPRISE','SUPRISE%','REVENUE_ACTUAL', 'TIME']
earnings_data.drop(cols_to_drop, axis = 1, inplace=True)

# List of columns to strip 'USD' from
cols_to_change = ['MKT_CAP', 'EPS_ESTIMATE','REVENUE_FORECAST']
for col in cols_to_change:
    earnings_data[col] = earnings_data[col].str.replace('USD','')

# Create function to convert from string to numeric
def convert_to_numeric(row):
    if row[-1] == 'B':
        return float(row[:-1]) * 10**9
    elif row[-1] == 'M':
        return float(row[:-1]) * 10**6
    else:
        return None
    
# Apply function
earnings_data['MKT_CAP'] = earnings_data['MKT_CAP'].apply(lambda x: convert_to_numeric(x))
earnings_data['REVENUE_FORECAST'] = earnings_data['REVENUE_FORECAST'].apply(lambda x: convert_to_numeric(x))


# Convert cols to datetime
earnings_data[['DATE', 'PERIOD_ENDING']] = earnings_data[['DATE', 'PERIOD_ENDING']].apply(pd.to_datetime)

# Filter for companies with > $500M market cap
earnings_data = earnings_data[earnings_data['MKT_CAP'] > 500*10**6]



# Set API Key & Time Interval 
# API_KEY = "579515UOE0JE5VXJ"
# TIME_INTERVAL = 60 
# response = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=" + API_KEY)
# data = response.json()
# print(data)

# Create a list of tickers to extract price data for
tickers = earnings_data['TICKER']

# Create Main DataFrame to store historical price information
stock_data = pd.DataFrame(columns = ['TICKER','DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'ADJUSTED_CLOSE', 'VOLUME'])

# URL of yahoo finance and initialise web driver
yahoo_finance_url = 'https://uk.finance.yahoo.com/'
driver = webdriver.Chrome()
driver.get(yahoo_finance_url)

# Click the scroll down button, cookies will handle themselves
scroll_button = driver.find_element(By.CLASS_NAME, 'btn')
scroll_button.click()

# Wait for the search bar to load
search_ticker = WebDriverWait(driver,15).until(EC.presence_of_element_located((By.CLASS_NAME, 'finsrch-inpt')))

# Iterate over list of tickers
for ticker in tickers:
    # Search for search bar
    search_ticker = driver.find_element(By.CLASS_NAME, 'finsrch-inpt')
    search_ticker.send_keys(ticker)
    search_ticker.submit()
    time.sleep(2)

    # Click Historical Data button
    try:
        historical_data = WebDriverWait(driver,15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="quote-nav"]/ul/li[5]/a')))
        historical_data.click()
        time.sleep(2)
        page = driver.page_source
    except TimeoutException as EX:
        continue

    # Extract HTML Data
    soup = BeautifulSoup(page, 'html.parser')
    table = soup.find('div', class_ = 'W(100%)').find_all('tr')

    # Create empty list to contain table data
    rows = []

    # Iterate over every row in table
    for i, row in enumerate(table):
        # Skip Header row
        if i == 0:
            continue

        row_values = [cell.text.strip() for cell in row.find_all('td')]
        row_values.insert(0,ticker)
        rows.append(row_values)
        
        # Append data onto main dataframe
    try:
        df = pd.DataFrame(rows,columns = ['TICKER','DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'ADJUSTED_CLOSE', 'VOLUME'])
        df.drop(index=df.index[-1],axis=0,inplace=True)
        stock_data = pd.concat([stock_data,df])
    except:
        continue

# Close browser
driver.quit()

print(stock_data)


# GET LAST YEARS REVENUE FORECAST AND EPS AND STORE ONTO EARNINGS DATA.
# COMPUTE ANALYSIS OF STOCK PERFORMANCE 5D 1 WEEK AND 1 MONTH DATA. 



