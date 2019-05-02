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

l = crawlerStockServes_TW.get_data("2303")
col = ["Date","Name","Open","High","Low","Close","Volume","PER"]
df = pd.DataFrame(l,columns = col)
df.set_index("Date", inplace=True)
print(df[-20:])
df = df[-100:]

#df.index = df.index.format(formatter=lambda x: x.strftime('%Y-%m-%d')) 

sma_10 = talib.SMA(np.array(df['Close']), 10)
sma_30 = talib.SMA(np.array(df['Close']), 30)

fig = plt.figure(figsize=(16, 9))

ax = fig.add_subplot(1, 1, 1)
ax.set_xticks(range(0, len(df.index), 10))
ax.set_xticklabels(df.index[::10])
mpf.candlestick2_ochl(ax, df['Open'], df['Close'], df['High'], df['Low'], width=0.6, colorup='r', colordown='g', alpha=0.75);

plt.rcParams['font.sans-serif']=['Microsoft JhengHei'] 
ax.plot(sma_10, label='10日均線')
ax.plot(sma_30, label='30日均線')
ax.legend();


plt.show()