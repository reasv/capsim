from math import e
import os
import requests
import sqlite3
import pandas as pd

def load_environment_variables():
    # Load environment variables
    # Check if .env file exists
    try:
        # Read .env file manually and set environment variables
        with open('.env') as f:
            for line in f:
                key, value = line.strip().split('=')
                # Set environment variable only if it is not already set
                if key not in os.environ:
                    os.environ[key] = value
    except:
        print("No .env file found or file could not be read. Using system environment variables.")

    # Set default for DB_FILE if not provided
    if 'DB_FILE' not in os.environ:
        os.environ['DB_FILE'] = 'sqlite.db'

    # Set default for ADMIN_PASS if not provided
    if 'ADMIN_PASS' not in os.environ:
        os.environ['ADMIN_PASS'] = 'admin'

    # Throw exception if API_KEY is not provided
    if 'API_KEY' not in os.environ:
        raise ValueError("API_KEY environment variable is not set.")

def fetch_and_save_timeseries(ticker=None, type='asset'):
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is not set.")
    
    if type == 'cpi':
        url = f"https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey={api_key}"
    elif type == 'asset' and ticker:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={api_key}"
    else:
        raise ValueError("For type 'asset', ticker must be provided.")
    
    # Cut off the api key from the URL before printing

    printURL = url.split("&apikey")[0]
    print(f"Fetching data from AlphaVantage API: {printURL}")
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data from AlphaVantage API: {response.status_code}")

    data = response.json()

    conn = sqlite3.connect(os.environ['DB_FILE'])
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeseries (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adjusted_close REAL,
            volume INTEGER,
            dividend_amount REAL,
            type TEXT,
            PRIMARY KEY (ticker, date, type)
        )
    ''')

    if type == 'cpi':
        if "data" not in data:
            raise Exception(f"Unexpected data format received: {data}")

        timeseries = data["data"]
        
        for entry in timeseries:
            date = entry["date"]
            cpi_value = float(entry["value"])
            cursor.execute('''
                INSERT OR REPLACE INTO timeseries (
                    ticker, date, open, high, low, close, adjusted_close, volume, dividend_amount, type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'CPI',
                date,
                None,  # open
                None,  # high
                None,  # low
                None,  # close
                cpi_value,  # adjusted_close
                None,  # volume
                None,  # dividend_amount
                'cpi'
            ))
    else:  # type == 'asset'
        if "Monthly Adjusted Time Series" not in data:
            raise Exception(f"Unexpected data format received: {data}")

        timeseries = data["Monthly Adjusted Time Series"]
        
        for date, values in timeseries.items():
            cursor.execute('''
                INSERT OR REPLACE INTO timeseries (
                    ticker, date, open, high, low, close, adjusted_close, volume, dividend_amount, type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker,
                date,
                float(values['1. open']),
                float(values['2. high']),
                float(values['3. low']),
                float(values['4. close']),
                float(values['5. adjusted close']),
                int(values['6. volume']),
                float(values['7. dividend amount']),
                'asset'
            ))

    conn.commit()
    conn.close()

def ensure_initialization():
    # Make sure that the database is initialized and we have CPI data, and VTI as an asset
    # If not, fetch the data from AlphaVantage and save it to the database
    load_environment_variables()
    conn = sqlite3.connect(os.environ['DB_FILE'])
    cursor = conn.cursor()
    # Check if the timeseries table exists
    cursor.execute('''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' AND name='timeseries'
    ''')
    table_exists = cursor.fetchone()

    if not table_exists:
        fetch_and_save_timeseries(type='cpi')
        fetch_and_save_timeseries(ticker='VTI', type='asset')
        return
    
    # Check if CPI data exists
    cursor.execute('''
        SELECT COUNT(*)
        FROM timeseries
        WHERE ticker = 'CPI' AND type = 'cpi'
    ''')
    cpi_count = cursor.fetchone()[0]

    # Check if VTI data exists
    cursor.execute('''
        SELECT COUNT(*)
        FROM timeseries
        WHERE ticker = 'VTI' AND type = 'asset'
    ''')
    vti_count = cursor.fetchone()[0]

    conn.close()

    # Fetch CPI data if not present
    if cpi_count == 0:
        fetch_and_save_timeseries(type='cpi')

    # Fetch VTI data if not present
    if vti_count == 0:
        fetch_and_save_timeseries(ticker='VTI', type='asset')

def load_timeseries(ticker):
    
    conn = sqlite3.connect(os.environ['DB_FILE'])
    cursor = conn.cursor()

    # Load asset data
    query = '''
        SELECT date, adjusted_close, dividend_amount, close
        FROM timeseries
        WHERE ticker = ? AND type = 'asset'
        ORDER BY date
    '''
    cursor.execute(query, (ticker,))
    asset_rows = cursor.fetchall()

    asset_df = pd.DataFrame(asset_rows, columns=['timestamp', 'raw_price', 'Dividend Amount', 'Close'])
    asset_df['timestamp'] = pd.to_datetime(asset_df['timestamp'])
    asset_df['dividend yield'] = asset_df.apply(lambda row: (row['Dividend Amount'] / row['Close']) if row['Close'] != 0 else 0, axis=1)
    asset_df.drop(columns=['Dividend Amount', 'Close'], inplace=True)
    asset_df.sort_values(by='timestamp', inplace=True)

    # Load CPI data
    query = '''
        SELECT date, adjusted_close
        FROM timeseries
        WHERE ticker = 'CPI' AND type = 'cpi'
        ORDER BY date
    '''
    cursor.execute(query)
    cpi_rows = cursor.fetchall()

    cpi_df = pd.DataFrame(cpi_rows, columns=['timestamp', 'raw_cpi'])
    cpi_df['timestamp'] = pd.to_datetime(cpi_df['timestamp'])
    cpi_df.sort_values(by='timestamp', inplace=True)

    conn.close()

    # Merge CPI data with asset data
    merged_df = pd.merge_asof(asset_df, cpi_df, on='timestamp', direction='nearest')
    merged_df["raw_cpi"] = merged_df['raw_cpi'].ffill()
    return merged_df

def erase_ticker(ticker, type):
    
    conn = sqlite3.connect(os.environ['DB_FILE'])
    cursor = conn.cursor()

    # Delete the specified ticker and type from the database
    cursor.execute('''
        DELETE FROM timeseries
        WHERE ticker = ? AND type = ?
    ''', (ticker, type))

    conn.commit()
    conn.close()

def list_tickers(type: str):
    
    conn = sqlite3.connect(os.environ['DB_FILE'])
    cursor = conn.cursor()

    # Execute the query to get distinct tickers of the specified type
    cursor.execute('''
        SELECT DISTINCT ticker
        FROM timeseries
        WHERE type = ?
    ''', (type,))
    
    tickers = cursor.fetchall()
    
    conn.close()
    
    # Extract tickers from the result and return as a list
    return [ticker[0] for ticker in tickers]
