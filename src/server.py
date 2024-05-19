import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from .portfolio import Portfolio  # Assuming Portfolio is defined in Portfolio.py
from .db import list_tickers, erase_ticker, fetch_and_save_timeseries, load_environment_variables

app = Flask(__name__)
CORS(app)

@app.route('/tickers', methods=['GET'])
def get_tickers():
    tickers = list_tickers('asset')
    # Return the tickers as a JSON response
    return jsonify(tickers)

@app.route('/cpi', methods=['GET'])
def get_cpi():
    tickers = list_tickers('cpi')
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

    response = jsonify({"results": results})
    response.headers.add('Content-Type', 'application/json')
    return response


def check_authorization():
    admin_pass = os.getenv('ADMIN_PASS')
    auth_header = request.headers.get('Authorization')

    if auth_header is None or auth_header != admin_pass:
        abort(401)  # Unauthorized

@app.route('/tickers/<ticker>', methods=['DELETE'])
def delete_ticker(ticker):
    load_environment_variables()
    check_authorization()

    try:
        erase_ticker(ticker, 'asset')
        return jsonify({"message": f"Ticker {ticker} erased successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tickers/<ticker>', methods=['PUT'])
def update_ticker(ticker):
    load_environment_variables()
    check_authorization()

    try:
        fetch_and_save_timeseries(ticker, "asset")
        return jsonify({"message": f"Timeseries for ticker {ticker} fetched and saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/auth-check', methods=['GET'])
def auth_check():
    try:
        check_authorization()
        return jsonify({"authorized": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401