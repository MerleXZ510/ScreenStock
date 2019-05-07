# basic
import numpy as np
import pandas as pd

# get data
import pandas_datareader as pdr

# visual
import matplotlib.pyplot as plt
import mpl_finance as mpf
import seaborn as sns

#time
import datetime as datetime

#talib
import talib

#data
import crawlerStockServes_TW


def plotCandlestickChart(StockID, ShowDays):


    
    l = crawlerStockServes_TW.get_data(StockID)
    col = ["Date","Name","Open","High","Low","Close","Volume","PER"]
    df = pd.DataFrame(l,columns = col)
    df.set_index("Date", inplace=True)
    print(df[-20:])
    inputs = {
            'open': df['Open'].values,
            'high': df['High'].values,
            'low': df['Low'].values,
            'close': df['Close'].values,
            'volume': df['Volume'].values
        }
    df = df[ShowDays:]

    #df.index = df.index.format(formatter=lambda x: x.strftime('%Y-%m-%d')) 

    sma_10 = talib.SMA(inputs["close"], timeperiod=10)
    sma_20 = talib.SMA(inputs["close"], timeperiod=20)
    upper, middle, lower = talib.BBANDS(inputs["close"], 20, 2, 2)

    sma_10 = sma_10[ShowDays:]
    sma_20 = sma_20[ShowDays:]
    upper = upper[ShowDays:]
    lower = lower[ShowDays:]

    fig = plt.figure(figsize=(16, 10))

    ax = fig.add_axes([0.05,0.4,0.9,0.5])
    ax2 = fig.add_axes([0.05,0.2,0.9,0.2])
    ax.set_xticks(range(0, len(df.index), 10))
    ax.set_xticklabels(df.index[::10])
    mpf.candlestick2_ochl(ax, df['Open'], df['Close'], df['High'], df['Low'], width=0.6, colorup='r', colordown='g', alpha=0.75);

    #plt.rcParams['font.sans-serif']=['Microsoft JhengHei'] 
    ax.plot(sma_10, label='10MA')
    ax.plot(sma_20, label='20MA')
    ax.plot(upper, label='BBU')
    ax.plot(lower, label='BBL')
    ax.grid(True,which ='both')
    ax.legend()
    mpf.volume_overlay(ax2, df['Open'], df['Close'], df['Volume'], colorup='r', colordown='g', width=0.5, alpha=0.8)
    ax2.set_xticks(range(0, len(df.index), 10))
    ax2.set_xticklabels(df.index[::10])
    
    ax2.grid(True,which ='both')
    return plt


StockID = "2303"
ShowDays = -120
plt = plotCandlestickChart(StockID, ShowDays)

plt.show()