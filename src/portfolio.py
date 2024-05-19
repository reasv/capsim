from .db import load_timeseries
from .strategy import annualize, process_strategy, cut_data_and_normalize

class Portfolio():
    def __init__(self, ticker="VTI", start_date: str | None = None, initial_investment=1000000, dividend_tax=0.26, capital_gains_tax=0.26, yearly_sale_percentage=0.04, name: str | None =None):
        self.ticker = ticker
        self.name = name if name is not None else ticker
        self.start_date: None | str = start_date
        self.initial_investment = initial_investment
        self.dividend_tax = dividend_tax
        self.capital_gains_tax = capital_gains_tax
        self.yearly_sale_percentage = yearly_sale_percentage
        self.src_data = None
        self.monthly = None
        self.yearly = None

    def load_data(self):
        self.src_data = load_timeseries(self.ticker)

    def process(self):
        if self.src_data is None:
            return
        # Cut data to start_date and normalize
        self.src_data = cut_data_and_normalize(self.src_data, self.start_date)
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
