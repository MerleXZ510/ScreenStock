import datetime
import sqlite3
import time
from io import StringIO
import numpy as np
import pandas as pd
import requests
import random
import pickle

"""##建立DB連線 & 建立Table"""

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
  
def __create_table(fn):
    conn = sqlite3.connect(fn)
    #股價表
    conn.execute('''CREATE TABLE IF NOT EXISTS tw_stock_data (
        id INTEGER  PRIMARY KEY AUTOINCREMENT,
        date_stockid TEXT UNIQUE, 
        date TEXT NOT NULL,
        stockid     TEXT    NOT NULL,
        name           TEXT    NOT NULL,
        tradenum  INT NOT NULL,
        tradetimes  INT NOT NULL,
        tradeamount  INT NOT NULL,
        open  REAL NOT NULL,
        high  REAL NOT NULL,
        low  REAL NOT NULL,
        close  REAL NOT NULL,
        VWAP REAL NOT NULL,
        PER REAL NOT NULL
        );''')
    conn.close()
    
def __create_table_fail(fn):
    conn = sqlite3.connect(fn)
    #股價表
    conn.execute('''CREATE TABLE IF NOT EXISTS lost_data (
        id INTEGER  PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL
        );''')
    conn.close()

"""##查詢資料"""

def __get_lastdata(conn, stockid):
    c = conn.cursor()
    sql = '''SELECT *  from tw_stock_data WHERE STOCKID = '{}' ORDER BY DATE DESC  LIMIT 1 '''.format(
        stockid)
    cursor = c.execute(sql).fetchall()
    return cursor


""" 取得資料 """
def get_data(stockid):
    DB_name = 'StockData/taiwan_stock_data.db'
    conn = __create_connection(DB_name)
    c = conn.cursor()
    sql = '''SELECT date,name,open,high,low,close,tradenum,PER  from tw_stock_data WHERE STOCKID = '{}' ORDER BY DATE ASC '''.format(
        stockid)
    cursor = c.execute(sql).fetchall()
    return cursor

def __get_data(conn, stockid):
    c = conn.cursor()
    sql = '''SELECT *  from tw_stock_data WHERE STOCKID = '{}' ORDER BY DATE ASC '''.format(
        stockid)
    cursor = c.execute(sql).fetchall()
    return cursor

def __get_lostdata(conn):
    c = conn.cursor()
    sql = '''SELECT *  from lost_data ORDER BY DATE ASC '''
    cursor = c.execute(sql).fetchall()
    return cursor

""" 刪除資料 """
def __del_lostdata(conn, date):
    c = conn.cursor()
    sql = '''DELETE FROM lost_data WHERE date = '{}' '''.format(date)
    cursor = c.execute(sql)
    return cursor

"""## 資料寫入DB"""

def __create_lostdata(conn, purchases):
    # sql語法
    sql = '''INSERT OR IGNORE  INTO lost_data (date) VALUES (?)'''
    # 資料串列 purchases
    cur_1 = conn.cursor()
    #print(purchases)
    cur_1.execute(sql, purchases)

    return cur_1
  
def __create_stockdata(conn, purchases):
    # sql語法
    sql = '''INSERT OR IGNORE  INTO tw_stock_data (date_stockid,date,stockid,name,tradenum,tradetimes,tradeamount,open,high,low,close,VWAP,PER) \
                                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    # 資料串列 purchases
    cur = conn.cursor()
    cur.execute(sql, purchases)

    return cur

#將每日價格輸入DB(所有)
def __create_stock_date_data(conn, date, data):
    for stockid in data.index:
        new_stockid = stockid.replace('"', '').replace('=', '')
        stockdatalist = data.loc[stockid].values
        dateid = date + new_stockid
        #有成交 正常輸入
        if stockdatalist[4] != '--':
            purchases = (
                dateid,
                date,
                new_stockid,
                stockdatalist[0],
                eval(stockdatalist[1]),
                eval(stockdatalist[2]),
                eval(stockdatalist[3]),
                eval(stockdatalist[4]),
                eval(stockdatalist[5]),
                eval(stockdatalist[6]),
                eval(stockdatalist[7]),
                eval(stockdatalist[3])/eval(stockdatalist[1]),
                stockdatalist[14])
            __create_stockdata(conn, purchases)
        #未成交 以最高買價為隔日開盤參考價
        elif stockdatalist[10] != '--':
            #分母不能為0
            if eval(stockdatalist[1]) != 0:
                vwap = eval(stockdatalist[3])/eval(stockdatalist[1])
            else:
                vwap = 0
            #stockdatalist[10] 不可使用eval() 會有異常狀況
            purchases = (
                dateid,
                date,
                new_stockid,
                stockdatalist[0],
                eval(stockdatalist[1]),
                eval(stockdatalist[2]),
                eval(stockdatalist[3]),
                stockdatalist[10],
                stockdatalist[10],
                stockdatalist[10],
                stockdatalist[10],
                vwap,
                stockdatalist[14])
            __create_stockdata(conn, purchases)
    time.sleep(2)

"""## 爬取資料"""

##第一次爬
def __update_stockdata(conn, time_sleep, start_date = datetime.datetime.strptime("2004-02-11 16:00:01", "%Y-%m-%d %H:%M:%S")): 
    date = datetime.datetime.now()
    err_time = 0
    sus_time = 0
    while start_date < date:
        print('parsing', start_date)
        # 使用 __crawl_price 爬資料
        date_ = str(start_date).split(' ')[0]
        try:
            # 抓資料
            data = __crawl_price(date_)
            sus_time += 1 
            err_time = 0
            print('爬取股價       成功 ', sus_time)
            print('寫入 成功 完成', date_)
            print('----------------------------------------------------------------------------')
            __create_stock_date_data(conn, date_, data)
        except:
            # 假日爬不到   
            err_time+=1
            sus_time = 0
        if err_time>=1:
            print('爬取股價 失敗 ', err_time)
            print('寫入 失敗 完成', date_)
            print('----------------------------------------------------------------------------')
            __create_lostdata(conn,(date_,))
            time.sleep(2)
        conn.commit()    
        # 加一天 
        time.sleep(time_sleep+random.random())
        start_date += datetime.timedelta(days=1)
    return None

  
## 重新爬  
def __reCrawlLostData(conn, time_sleep):
    date = __get_lostdata(conn)
    list_date = [i[1] for i in date]
    set_date = set(list_date)
    sus_time = 0
    err_time = 0
    for date_ in sorted(set_date):
        print('parsing', date_)
        print('錯誤次數',list_date.count(date_))
        # 使用 __crawl_price 爬資料
        try:
            # 抓資料
            data = __crawl_price(date_)
            sus_time += 1 
            err_time = 0
            print('爬取股價       成功 ', sus_time)
            print('寫入 成功 ', date_)
            print('----------------------------------------------------------------------------')
            __create_stock_date_data(conn, date_, data)
            __del_lostdata(conn, date_)
        except:
            # 假日爬不到 or 爬取失敗  
            err_time+=1
            sus_time = 0
        if err_time>=1:
            print('爬取股價 失敗 ', err_time)
            print('寫入 失敗 完成', date_)
            print('----------------------------------------------------------------------------')
            __create_lostdata(conn,(date_,))
            time.sleep(2)
        # 爬取資料失敗超過10次 判讀為假日
        if list_date.count(date_) >= 5:
            #print(list_date.count(date_))
            __del_lostdata(conn, date_)
        conn.commit()
        time.sleep(time_sleep+random.random())
        # 爬取資料失敗超過10次 判讀為假日

    
    conn.close()
    return None
  
#爬取資料 輸出dataframe
def __crawl_price(date):
    #http://www.twse.com.tw/fund/T86?response=csv&date=20120502&selectType=ALLBUT0999
    #http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=20181003&type=ALLBUT0999
    url='http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + date.replace('-', '') + '&type=ALLBUT0999'
    r = requests.post(url)   
    stock_dict={ord(' '): None}
    #stock_list=[i.translate(stock_dict)   for i in r.text.split('\n')  if  len(i.split('",')) == 17 and i[0] != '=' ]
    stock_list=[i.translate(stock_dict)   for i in r.text.split('\n')  if  len(i.split('",')) == 17 and (i[0] != '=' or len(i.split('",')[0]) <= 6)]
    ret = pd.read_csv(StringIO("\n".join(stock_list)), header=0)
    ret = ret.set_index('證券代號')
    ret['成交金額'] = ret['成交金額'].str.replace(',','')
    ret['成交股數'] = ret['成交股數'].str.replace(',','')
    ret['成交筆數'] = ret['成交筆數'].str.replace(',','')
    ret['開盤價'] = ret['開盤價'].str.replace(',','')
    ret['最高價'] = ret['最高價'].str.replace(',','')
    ret['最低價'] = ret['最低價'].str.replace(',','')
    ret['收盤價'] = ret['收盤價'].str.replace(',','') 
    if type(ret['本益比'][1]) == type('str'):
        ret['本益比'] = ret['本益比'].str.replace(',', '')
    return ret

"""## 方法


*   更新股票資料
"""

def update(conn, time_sleep, start_date = None):
    if start_date == None:
        try:
            df = __get_lastdata(conn, '0050')[0][2]
            start_date = datetime.datetime.strptime(df+" 16:00:01", "%Y-%m-%d %H:%M:%S")
            start_date += datetime.timedelta(days=1)
        except :
            start_date = datetime.datetime.strptime("2004-02-11 16:00:01", "%Y-%m-%d %H:%M:%S")
    __update_stockdata(conn, time_sleep, start_date)
    conn.close()

"""##主程式 (呼叫方法)"""
if __name__ == "__main__":
    
    DB_name = 'StockData/taiwan_stock_data.db'
    #建立表格
    #成功表
    __create_table(DB_name)
    #失敗表
    __create_table_fail(DB_name)

    #建立連線
    conn = __create_connection(DB_name)

    #更新
    print("爬新資料")
    time_sleep = 5
    start_date = datetime.datetime.strptime("2004-02-11 16:00:01", "%Y-%m-%d %H:%M:%S")
    #update(conn, time_sleep, start_date)
    update(conn, time_sleep)


    print("重新爬取失敗資料")
    #重新爬取失敗資料...
    conn = __create_connection(DB_name)
    __reCrawlLostData(conn, time_sleep)


