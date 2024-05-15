import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from .portfolio import Portfolio  # Assuming Portfolio is defined in Portfolio.py

app = Flask(__name__)
CORS(app)

@app.route('/tickers', methods=['GET'])
def get_tickers():
    # List all files in the current directory
    files = os.listdir('.')
    
    # Filter out the CSV files and extract ticker symbols
    tickers = [file.split('_')[2].replace('.csv', '') for file in files if file.startswith('monthly_adjusted_') and file.endswith('.csv')]
    
    # Return the tickers as a JSON response
    return jsonify(tickers)

@app.route('/backtest', methods=['POST'])
def backtest():
    data = request.json
    error_response = {"error": "Invalid input. Expected a JSON object with a 'portfolios' field containing an array of portfolio parameters."}
    # Ensure the request contains a 'portfolios' field with a list of portfolio parameters
    if data is None or 'portfolios' not in data or not isinstance(data['portfolios'], list):
        return jsonify(error_response), 400

    portfolios = data['portfolios']
    results = []

    for item in portfolios:
        portfolio = Portfolio(**item)
        portfolio.run()
        monthly_results = portfolio.monthly.to_dict(orient='records') if portfolio.monthly is not None else None
        yearly_results = portfolio.yearly.to_dict(orient='records') if portfolio.yearly is not None else None
        
        results.append({
            "name": portfolio.name,
            "ticker": portfolio.ticker,
            "start_date": portfolio.start_date,
            "initial_investment": portfolio.initial_investment,
            "dividend_tax": portfolio.dividend_tax,
            "capital_gains_tax": portfolio.capital_gains_tax,
            "yearly_sale_percentage": portfolio.yearly_sale_percentage,
            "monthly_results": monthly_results,
            "yearly_results": yearly_results
        })

    return jsonify({"results": results})