import pandas as pd

def annualize(df: pd.DataFrame):
    period_months = 12
    dfs = [df[i:i+period_months] for i in range(0, df.shape[0], period_months)]
    dfs = [df for df in dfs if df.shape[0] == period_months]
    yearly = pd.DataFrame({
        "timestamp": [d["timestamp"].iloc[-1] for d in dfs],
        "price": [d["price"].iloc[-1] for d in dfs],
        "cpi": [d["cpi"].iloc[-1] for d in dfs],
        "shares": [d["shares"].iloc[-1] for d in dfs],
        "portfolio value": [d["portfolio value"].iloc[-1] for d in dfs],
        "infl. adj. portfolio value": [d["infl. adj. portfolio value"].iloc[-1] for d in dfs],
        "infl. adj. portfolio growth": [d["infl. adj. portfolio growth"].iloc[-1] for d in dfs],
        "dividend yield": [d['dividend yield'].sum() for d in dfs],
        "dividend tax": [d["dividend tax"].sum() for d in dfs],
        "net income": [d["net income"].sum() for d in dfs],
        "infl. adj. net income": [d["infl. adj. net income"].sum() for d in dfs],
        "gross income": [d["gross income"].sum() for d in dfs],
        "capital gains tax": [d["capital gains tax"].sum() for d in dfs],
        "cost basis rate": [d["cost basis rate"].iloc[-1] for d in dfs],
    })
    yearly['infl. adj. monthly income'] = yearly['infl. adj. net income'] / period_months
    yearly['infl. adj. monthly income change'] = yearly['infl. adj. monthly income'] / yearly['infl. adj. monthly income'].iloc[0]
    yearly['tax/gross income ratio'] = (yearly['dividend tax'] + yearly['capital gains tax']) / yearly['gross income']
    return yearly

def process_strategy(df: pd.DataFrame, initial_investment: float, dividend_tax: float, capital_gains_tax: float):
    # Define a function to transform a row (month) of the time series
    def transform_row(current_month: pd.Series, previous_month: pd.Series | None, first_month: pd.Series | None):
        month = current_month.copy()
        # Initialize new columns, avoid NaNs
        month['shares sold'] = 0
        month['capital gains'] = 0
        month['capital gains tax'] = 0
        month['shares purchased'] = 0

        month['shares'] = initial_investment / month['price'] if previous_month is None else previous_month['shares']
        month['cum capital losses'] = 0 if previous_month is None else previous_month['cum capital losses']
        month['cost basis rate'] = month['price'] if previous_month is None else previous_month['cost basis rate']
        month['portfolio value'] = month['shares'] * month['price']
        # Target income
        month['gross income'] = month['portfolio value'] * month['perc. sold']

        # Receive dividends
        month['gross dividend'] = month['shares'] * month['dividend yield'] * month['price']
        month['dividend tax'] = month['gross dividend'] * dividend_tax
        month['net dividend'] = month['gross dividend'] * (1 - dividend_tax)
        
        if month['gross income'] > month['net dividend']:
            # Dividends do not cover the entire target income
            # Use dividends to cover part of the target income
            remaining_target_income = month['gross income'] - month['net dividend']
            # Sell shares to cover the remaining target income
            month['shares sold'] = remaining_target_income / month['price']
            month['shares'] -= month['shares sold']
            month['capital gains'] = month['shares sold'] * (month['price'] - month['cost basis rate'])

            if month['capital gains'] < 0:
                month['cum capital losses'] -= month['capital gains']
                month['capital gains tax'] = 0
            elif month['cum capital losses'] > 0:
                net_capital_gains = month['capital gains'] - month['cum capital losses']
                if net_capital_gains < 0:
                    month['cum capital losses'] = -net_capital_gains
                    month['capital gains tax'] = 0
                else:
                    month['capital gains tax'] = net_capital_gains * capital_gains_tax
                    month['cum capital losses'] = 0
            else:
                month['capital gains tax'] = month['capital gains'] * capital_gains_tax

            month['net income'] = month['gross income'] - month['capital gains tax']
        else:
            # Dividends cover the entire target income
            remaining_dividend_income = month['net dividend'] - month['gross income']
            month['net income'] = month['gross income']
            
            # Buy shares with remaining dividends and update cost basis rate
            month['shares purchased'] = remaining_dividend_income / month['price']
            month['cost basis rate'] = (month['shares'] * month['cost basis rate'] + month['shares purchased'] * month['price']) / (month['shares'] + month['shares purchased'])
            month['shares'] += month['shares purchased']
            
        
        month['portfolio value'] = month['shares'] * month['price']
        month['infl. adj. portfolio value'] = month['portfolio value'] / month['cpi']
        month['infl. adj. net income'] = month['net income'] / month['cpi']

        first_month = first_month if first_month is not None else month
        month['infl. adj. portfolio growth'] = month['infl. adj. portfolio value'] / first_month['infl. adj. portfolio value']
        month['infl. adj. net income growth'] = month['infl. adj. net income'] / first_month['infl. adj. net income']
        return month
    
    # Initialize an empty list to store new time series values
    new_time_series = []

    # Iterate over the DataFrame
    for i in range(len(df)):
        current_row = df.iloc[i]
        if len(new_time_series) == 0:
            previous_row = None
            first_row = None
        else:
            previous_row = new_time_series[-1]
            first_row = new_time_series[0]
        # Apply the transformation function
        new_row_value = transform_row(current_row, previous_row, first_row)
        new_time_series.append(new_row_value)

    # Create a new DataFrame for the new time series
    new_df = pd.DataFrame(new_time_series, index=df.index)
    return new_df

def cut_data_and_normalize(df: pd.DataFrame, start_date: str | None):
    if start_date is not None:
        start_date_dt = pd.to_datetime(start_date)
        df = df[df['timestamp'] >= start_date_dt]
    df['price'] = (df['raw_price'] / df['raw_price'].iloc[0] * 100).round(4)
    df['cpi'] = (df['raw_cpi'] / df['raw_cpi'].iloc[0]).round(4)
    return df