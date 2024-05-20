# Prerequisites

## AlphaVantage
This server uses pricing data obtained from AlphaVantage's Stock API and requires a working api key in order to function. You can get one for free at https://www.alphavantage.co/support/#api-key

## Python
Python is required to run this application.

Python 3.11 or greater is recommended.
You can obtain the correct release for your platform along with installation instructions at https://www.python.org/downloads/

## Dependencies
`Capsim` depends on the following libraries: `pandas`, `Flask`, `Flask-Cors`, `requests`, `requests-toolbelt`.

Assuming you have a working python environment on your system and `pip` is in `PATH`, you can install all dependencies by using the `requirements.txt` file:

```
pip install -r requirements.txt
```

# How to run
Make a copy of the `.env.example` file and rename it to just `.env`.

Edit the file, making sure to replace `ALPHA_VANTAGE_API_KEY` with your own AlphaVantage API key obtained previously.

You can optionally set a custom admin password and a filename for the SQLite Database.

To run the server:
```
python run.py
```

The host:port the API is listening on will be printed on the terminal:
```
 * Serving Flask app 'src.server'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 979-269-837
```

Now you can proceed to set up the [client](https://github.com/reasv/capsim-client-ts)

# Notes
Uses https://www.alphavantage.co/documentation/