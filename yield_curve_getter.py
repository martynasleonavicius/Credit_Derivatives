# -*- coding: utf-8 -*-

"""
Script for extracting zero-yield curves for more accurate discounting of cds payments.
A lot of this script is produced using Claude since this is my first time using panda_datareader.data.

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



# Constant maturity treasury yields
tickers = ['DGS6MO' ,'DGS1','DGS2','DGS3','DGS5','DGS7','DGS10','DGS30']
maturities = [1/2, 1, 2, 3, 5, 7, 10, 30]

def get_fred_series(ticker): #We get the constant-maturity yield curves from FRED (Federal Reserve Economic Data)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
    df = pd.read_csv(url, index_col=0, parse_dates=True)
    df.columns = [ticker]
    return df



def rates():    #Get the latest rate curve data
    rates_fred = {}
    for tick, mat in zip(tickers, maturities):
        series = get_fred_series(tick).replace('.', float('nan')).dropna()
        rates_fred[mat] = np.log(1 + float(series.iloc[-1].values[0])/100)  #Convert to continously compounding rate
    return rates_fred


plt.plot(rates().keys(), rates().values())



