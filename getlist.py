import sqlite3
import talib
import crawlerStockServes_TW
import pandas as pd

#連線
def __create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return None

### 1.取得當前股票列表資料
DB_name = 'StockData/taiwan_stock_data.db'
conn = __create_connection(DB_name)
c = conn.cursor()
sql = '''SELECT date  from tw_stock_data  ORDER BY DATE DESC  LIMIT 1 '''
cursor = c.execute(sql).fetchall()
lastdate = cursor[0][0]

c2 = conn.cursor()
sql2 = '''SELECT stockid  from tw_stock_data WHERE date = '{}' '''.format(lastdate)
cursor2 = c2.execute(sql2).fetchall()
stocklist = [stock[0] for stock in cursor2]

#股票列表
#print(stocklist)

### 2.計算MA20
upmalist = []
for stockid in stocklist:
    print('正在計算: ',stockid)
    l = crawlerStockServes_TW.get_data(stockid)
    col = ["Date", "Name", "Open", "High", "Low", "Close", "Volume", "PER"]
    df = pd.DataFrame(l, columns=col)
    df.set_index("Date", inplace=True)
    #print(df[-20:])
    inputs = {
        'open': df['Open'].values,
        'high': df['High'].values,
        'low': df['Low'].values,
        'close': df['Close'].values,
        'volume': df['Volume'].values
    }
    close_data = df['Close'].values
    volume_data = df['Volume'].values
    sma_20 = talib.SMA(inputs["close"], timeperiod=20)
    upma = close_data - sma_20

    if volume_data[-2] != 0:
        #突破20MA
        condition_1 = (upma[-1] > 0 and upma[-2] < 0)
        #交易量為前日兩倍以上
        condition_2 = volume_data[-1]/volume_data[-2] > 2 
        #成交金額大於1000萬
        condition_3 = volume_data[-1]*close_data[-1] > 1000000
        #print (condition_1, condition_2, condition_3)
    if condition_1 and condition_2 and condition_3:
        print('Hit')
        upmalist.append(stockid)




### 3.列出均線上方股票列表
print(upmalist)
da = pd.DataFrame(upmalist)
da.to_csv('stocklist.csv')
