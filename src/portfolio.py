from .prepare_data import download_price_data, load_source_data
from .strategy import annualize, process_strategy

class Portfolio():
    def __init__(self, ticker="VTI", start_date="2001-01-01", initial_investment=1000000, dividend_tax=0.26, capital_gains_tax=0.26, yearly_sale_percentage=0.04, name=None):
        self.ticker = ticker
        self.name = name if name is not None else ticker
        self.start_date = start_date
        self.initial_investment = initial_investment
        self.dividend_tax = dividend_tax
        self.capital_gains_tax = capital_gains_tax
        self.yearly_sale_percentage = yearly_sale_percentage
        self.bigmac_file = "bigmac2.csv"
        self.src_data = None
        self.monthly = None
        self.yearly = None

    def load_data(self):
        download_price_data(self.ticker)
        self.src_data = load_source_data(f"monthly_adjusted_{self.ticker}.csv", self.bigmac_file, self.start_date)

    def process(self):
        if self.src_data is None:
            return
        self.monthly = self.src_data.copy()
        self.monthly['perc. sold'] = self.yearly_sale_percentage / 12
        self.monthly = process_strategy(self.monthly, self.initial_investment, self.dividend_tax, self.capital_gains_tax)
        self.yearly = annualize(self.monthly)

    def run(self):
        self.load_data()
        self.process()

    # Generates a new portfolio with the same parameters except for the ones passed as arguments
    def generate_new(self, **kwargs):
        new_portfolio = Portfolio(self.ticker, self.start_date, self.initial_investment, self.dividend_tax, self.capital_gains_tax)
        # Use the passed arguments to replace the attributes of the new portfolio
        for key, value in kwargs.items():
            setattr(new_portfolio, key, value)
        return new_portfolio
