import matplotlib.pyplot as plt
from typing import List

def plot_results(monthly, yearly, ticker):
    fig, axs = plt.subplots(nrows=2, ncols=3, figsize=(20, 10))  # Adjust nrows and ncols based on the number of plots
    
    fig.suptitle(f'Portfolio performance ({ticker})')
    axs[0, 0].plot(monthly['timestamp'], monthly['price'])
    axs[0, 0].set_title('Stock Price (normalized)')
    axs[0, 1].plot(yearly['timestamp'], yearly['dividend yield'] * 100)
    axs[0, 1].set_title('Dividend yield (%)')

    axs[0, 2].plot(yearly['timestamp'], yearly['cpi'])
    axs[0, 2].set_title('Big Mac CPI')

    axs[1, 0].plot(monthly['timestamp'], monthly["infl. adj. portfolio value"])
    axs[1, 0].set_title('Inflation adjusted portfolio value')

    axs[1, 1].plot(yearly['timestamp'], yearly['infl. adj. monthly income'])
    axs[1, 1].set_title('Inflation adjusted monthly income')

    axs[1, 2].plot(yearly['timestamp'], yearly['tax/gross income ratio'])
    axs[1, 2].set_title('Tax to gross income ratio')