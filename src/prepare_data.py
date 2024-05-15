import os
import requests as req
import pandas as pd

def download_price_data(ticker):
    # Load environment variables
    # Read .env file manually and set environment variables
    with open('.env') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key] = value
    # Get API_KEY from .env file
    API_KEY = os.getenv("API_KEY")
    # Save CSV file if it doesn't exist
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={API_KEY}&datatype=csv'
    filename = f"monthly_adjusted_{ticker}.csv"
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            # Ensure the request was successful
            r = req.get(url)
            r.raise_for_status()
            f.write(r.content)

def load_source_data(prices_file, bigmac_file, start_date):
    # Stock prices
    ts = pd.read_csv(prices_file)
    ts = ts.sort_values(by="timestamp")
    ts = ts.reset_index()
    ts = ts.drop(columns="index")
    df = pd.DataFrame({
    "timestamp": ts["timestamp"],
    "price": ts["adjusted close"],
    "dividend yield": ts["dividend amount"] / ts["close"],
    })
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Big Mac index
    bigmac_pricedata = pd.read_csv(bigmac_file)
    country = "United States"
    bmprice = bigmac_pricedata[bigmac_pricedata.name == country][['date', 'dollar_price']]
    bmprice['date'] = pd.to_datetime(bmprice['date'])
    bmprice.rename(columns={"date": "timestamp", "dollar_price": "cpi"}, inplace=True)
    # Big Mac index ending date plus six months
    # The Big Mac index is published every six months, so we need to extend the last date by six months
    bmprice_end = bmprice['timestamp'].iloc[-1] + pd.DateOffset(months=6)
    # Discard data that is not in the same time range for both datasets
    bmprice = bmprice[(bmprice['timestamp'] >= df['timestamp'].iloc[0]) & (bmprice['timestamp'] <= df['timestamp'].iloc[-1])]
    df = df[(df['timestamp'] >= bmprice['timestamp'].iloc[0]) & (df['timestamp'] <= bmprice_end)]
    
    # Select data from start_date
    start_date = pd.to_datetime(start_date)
    bmprice = bmprice[bmprice['timestamp'] >= start_date]
    df = df[df['timestamp'] >= start_date]

    # Merge datasets
    df = pd.merge_asof(df, bmprice, on="timestamp")
    # Normalize CPI to 1 and stock price to 100
    df['cpi'] = df['cpi'].fillna(bmprice['cpi'].iloc[0])
    df['cpi'] = (df['cpi'] / df['cpi'].iloc[0]).round(3)
    df['price'] = (df['price'] / df['price'].iloc[0] * 100).round(3)
    return df