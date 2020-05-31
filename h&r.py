#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 14:36:42 2020

@author: devang
"""

from kiteconnect import KiteConnect
import os
import datetime as dt
import pandas as pd
import numpy as np


cwd = os.chdir("/home/devang/coding/zerodha")

#generate trading session
access_token = open("access_token",'r').read()
key_secret = open("api_key",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)



def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data



    
def adx(ohlc):
    "function to calculate ADX"
    n=14
    df2 = ohlc.copy()
    df2['H-L']=abs(df2['high']-df2['low'])
    df2['H-PC']=abs(df2['high']-df2['close'].shift(1))
    df2['L-PC']=abs(df2['low']-df2['close'].shift(1))
    df2['TR']=df2[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df2['DMplus']=np.where((df2['high']-df2['high'].shift(1))>(df2['low'].shift(1)-df2['low']),df2['high']-df2['high'].shift(1),0)
    df2['DMplus']=np.where(df2['DMplus']<0,0,df2['DMplus'])
    df2['DMminus']=np.where((df2['low'].shift(1)-df2['low'])>(df2['high']-df2['high'].shift(1)),df2['low'].shift(1)-df2['low'],0)
    df2['DMminus']=np.where(df2['DMminus']<0,0,df2['DMminus'])
    TRn = []
    DMplusN = []
    DMminusN = []
    TR = df2['TR'].tolist()
    DMplus = df2['DMplus'].tolist()
    DMminus = df2['DMminus'].tolist()
    for i in range(len(df2)):
        if i < n:
            TRn.append(np.NaN)
            DMplusN.append(np.NaN)
            DMminusN.append(np.NaN)
        elif i == n:
            TRn.append(df2['TR'].rolling(n).sum().tolist()[n])
            DMplusN.append(df2['DMplus'].rolling(n).sum().tolist()[n])
            DMminusN.append(df2['DMminus'].rolling(n).sum().tolist()[n])
        elif i > n:
            TRn.append(TRn[i-1] - (TRn[i-1]/n) + TR[i])
            DMplusN.append(DMplusN[i-1] - (DMplusN[i-1]/n) + DMplus[i])
            DMminusN.append(DMminusN[i-1] - (DMminusN[i-1]/n) + DMminus[i])
    df2['TRn'] = np.array(TRn)
    df2['DMplusN'] = np.array(DMplusN)
    df2['DMminusN'] = np.array(DMminusN)
    df2['DIplusN']=100*(df2['DMplusN']/df2['TRn'])
    df2['DIminusN']=100*(df2['DMminusN']/df2['TRn'])
    df2['DIdiff']=abs(df2['DIplusN']-df2['DIminusN'])
    df2['DIsum']=df2['DIplusN']+df2['DIminusN']
    df2['DX']=100*(df2['DIdiff']/df2['DIsum'])
    ADX = []
    DX = df2['DX'].tolist()
    for j in range(len(df2)):
        if j < 2*n-1:
            ADX.append(np.NaN)
        elif j == 2*n-1:
            ADX.append(df2['DX'][j-n+1:j+1].mean())
        elif j > 2*n-1:
            ADX.append(((n-1)*ADX[j-1] + DX[j])/n)
    df2['ADX']=np.array(ADX)
    df3 = df2.loc[:,'DIdiff':'DX']
    return df3



def Expansion_Breakouts(ohlc_1day,ticker):
    
    if ohlc_1day["high"][-1]>=ohlc_1day["high"][-59:-1].max():
        if ohlc_1day["high"][-1]-ohlc_1day["low"][-1]>=(ohlc_1day["high"][-10:-1]-ohlc_1day["low"][-10:-1]).max():
            print("strategy 1, expansion breakout = buy:",ticker)
            return "b"
            
    if ohlc_1day["low"][-1]<=ohlc_1day["low"][-59:-1].min():
        if ohlc_1day["high"][-1]-ohlc_1day["low"][-1]>=(ohlc_1day["high"][-10:-1]-ohlc_1day["low"][-10:-1]).max():
            print("strategy 1, expansion breakout = sell:",ticker)
            return "s"
    else:
        print("strategy 1, expansion breakout = NOTHING:",ticker)
        
def OTT_Pullback(ohlc_1day,ticker):
    adx1=adx(ohlc_1day)
    if adx1['DX'][-3]>30:
        if adx1['DIsum'][-3]>adx1['DIdiff'][-3]:
            if (ohlc_1day['low'][-3]>ohlc_1day['low'][-2] and ohlc_1day['low'][-2]>ohlc_1day['low'][-1]) or (ohlc_1day['low'][-3]>ohlc_1day['low'][-2] and ohlc_1day['low'][-2]<ohlc_1day['low'][-1]):
                print("RARE strategy 2, 1-2-3 pullback = buy:",ticker)
                return "b"
            
    if adx1['DX'][-3]>30:
        if adx1['DIdiff'][-3]>adx1['DIsum'][-3]:
            if (ohlc_1day['high'][-3]<ohlc_1day['high'][-2] and ohlc_1day['high'][-2]<ohlc_1day['high'][-1]) or (ohlc_1day['high'][-3]<ohlc_1day['high'][-2] and ohlc_1day['high'][-2]>ohlc_1day['high'][-1]):
                print("RARE strategy 2, 1-2-3 pullback = sell:",ticker)
                return "s"
    else:
        print("strategy 2, OTT pullback = NOTHING:",ticker)

def Expansion_pivots(ohlc_1day,ticker):
    ma = ohlc_1day["close"].rolling(50).mean()
    if ohlc_1day["high"][-1]-ohlc_1day["low"][-1]>=(ohlc_1day["high"][-10:-1]-ohlc_1day["low"][-10:-1]).max():
        if ohlc_1day["high"][-2]<=ma[-2] and ohlc_1day["low"][-1]>ma[-1]:
            print("strategy 3, expansion pivots = buy:",ticker)
            return "b"
        
    if ohlc_1day["high"][-1]-ohlc_1day["low"][-1]>=(ohlc_1day["high"][-10:-1]-ohlc_1day["low"][-10:-1]).max():
        if ohlc_1day["low"][-2]>=ma[-2] and ohlc_1day["high"][-1]<ma[-1]:
            print("strategy 3, expansion pivots = sell:",ticker)
            return "s"
        
    else:
        print("strategy 3, expansion pivots = NOTHING:",ticker)
        
        
def One_eighty(ohlc_1day,ticker):
    
    ma_50 = ohlc_1day["close"].rolling(50).mean()
    ma_10 = ohlc_1day["close"].rolling(10).mean()
    
    if ((ohlc_1day["high"][-2]-ohlc_1day["open"][-2])/(ohlc_1day["high"][-2]-ohlc_1day["low"][-2]))>=0.7:
        if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.3:
            if(ohlc_1day["low"][-1]>ma_50[-1] and ohlc_1day["low"][-1]>ma_10[-1]):
                print("strategy 4, 180 deg = buy:",ticker)
                return "b"
                
    if ((ohlc_1day["high"][-2]-ohlc_1day["open"][-2])/(ohlc_1day["high"][-2]-ohlc_1day["low"][-2]))>=0.3:
        if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.7:
            if(ohlc_1day["high"][-1]<ma_50[-1] and ohlc_1day["high"][-1]<ma_10[-1]):
                print("strategy 4, 180 deg = sell:",ticker)
                return "s"
                
                
    if ((ohlc_1day["high"][-2]-ohlc_1day["open"][-2])/(ohlc_1day["high"][-2]-ohlc_1day["low"][-2]))>=0.7:
        if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.3:
            if(ohlc_1day["low"][-1]>ma_50[-1] and ohlc_1day["low"][-1]>ma_10[-1]):
                if ohlc_1day["high"][-1]>=ohlc_1day["high"][-59:-1].max():
                    print("strategy 4, new 60 day high add more position 180 deg = buy:",ticker)
                    return "b"
                         
    if ((ohlc_1day["high"][-2]-ohlc_1day["open"][-2])/(ohlc_1day["high"][-2]-ohlc_1day["low"][-2]))>=0.3:
        if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.7:
            if(ohlc_1day["high"][-1]<ma_50[-1] and ohlc_1day["high"][-1]<ma_10[-1]):
                if ohlc_1day["low"][-1]<=ohlc_1day["low"][-59:-1].min():
                    print("strategy 4,new 60 day low add more position  180 deg = sell:",ticker)
                    return "s"
    else:
        print("strategy 4, 180 deg = NOTHING:",ticker)
        
        
def Gilligan_Island(ohlc_1day,ticker):
    if ohlc_1day["high"][-1]<=ohlc_1day["low"][-59:-1].min():
        if ((ohlc_1day["close"][-1]-ohlc_1day["low"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.45:
             print("strategy 5, gulligan island = buy:",ticker)
             return "b"
         
    if ohlc_1day["low"][-1]>=ohlc_1day["high"][-59:-1].max():
        if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.45:
             print("strategy 5, gulligan island = sell:",ticker)
             return "s"
    else:
        print("strategy 5, gulligan island = NOTHING:",ticker)
        
        
def Boomer(ohlc_1day,ticker):
    adx2=adx(ohlc_1day)
    if adx2['DX'][-3]>30:
        if adx2['DIsum'][-3]>adx2['DIdiff'][-3]:
            if ohlc_1day["high"][-3]>ohlc_1day["high"][-2] and ohlc_1day["high"][-2]>ohlc_1day["high"][-1]:
                if ohlc_1day["low"][-3]<ohlc_1day["low"][-2] and ohlc_1day["low"][-2]<ohlc_1day["low"][-1]:
                    print("strategy 6, Boomer = buy:",ticker)
                    return "b"
                    
        if adx2['DIdiff'][-3]>adx2['DIsum'][-3]:
            if ohlc_1day["high"][-3]>ohlc_1day["high"][-2] and ohlc_1day["high"][-2]>ohlc_1day["high"][-1]:
                if ohlc_1day["low"][-3]<ohlc_1day["low"][-2] and ohlc_1day["low"][-2]<ohlc_1day["low"][-1]:
                    print("strategy 6, Boomer = sell:",ticker)
                    return "s"
        
    else:
        print("strategy 6, Boomer = NOTHING:",ticker)
        
        
def Slingshot(ohlc_1day,ticker):
    if ohlc_1day["high"][-2]>=ohlc_1day["high"][-60:-2].max():
        if ohlc_1day["high"][-1]<ohlc_1day["high"][-2]:
            print("strategy 7, Slingshot = buy:",ticker)
            return "b"
        
    if ohlc_1day["low"][-2]<=ohlc_1day["low"][-60:-2].min():
        if ohlc_1day["low"][-1]>ohlc_1day["low"][-2]:
            print("strategy 7, Slingshot = sell:",ticker)
            return "s"
    else:
        print("strategy 7, Slingshot = NOTHING:",ticker)

def Whoops(ohlc_1day,ticker):
    ma_50 = ohlc_1day["close"].rolling(50).mean()
    ma_10 = ohlc_1day["close"].rolling(10).mean()
    if ohlc_1day["high"][-1]<ma_10[-1] and ohlc_1day["high"][-1]<ma_50[-1]:
        if ohlc_1day["close"][-2]>ohlc_1day["high"][-1]:
            print("strategy 8, Whoops = sell:",ticker)
            return "s"
        
    else:
        print("strategy 8, Whoops = NOTHING:",ticker)
        
def Lizards(ohlc_1day,ticker):
    if ((ohlc_1day["close"][-1]-ohlc_1day["low"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.7:
        if ohlc_1day["low"][-1]<=ohlc_1day["low"][-11:-1].min():
             print("strategy 9, Lizards = buy:",ticker)
             return "b"
        
    if ((ohlc_1day["high"][-1]-ohlc_1day["open"][-1])/(ohlc_1day["high"][-1]-ohlc_1day["low"][-1]))>=0.7:
        if ohlc_1day["high"][-1]>=ohlc_1day["high"][-11:-1].max():
             print("strategy 9, Lizards = sell:",ticker)
             return "s"
             
    else:
        print ("strategy 9, Lizards = NOTHING:",ticker)
             
             
def Compile(ohlc_1day,ticker):
    buy=0
    sell=0
    EB=Expansion_Breakouts(ohlc_1day,ticker)
    if EB == "b":
        buy+=1
    if EB == "s":
        sell+=1
    
    OTP = OTT_Pullback(ohlc_1day,ticker)
    if OTP == "b":
        buy+=1
    if OTP == "s":
        sell+=1
    
    EP = Expansion_pivots(ohlc_1day,ticker)
    if EP == "b":
        buy+=1
    if EP == "s":
        sell+=1
    
    OE = One_eighty(ohlc_1day,ticker)
    if OE == "b":
        buy+=1
    if OE == "s":
        sell+=1
    
    GI = Gilligan_Island(ohlc_1day,ticker)
    if GI == "b":
        buy+=1
    if GI == "s":
        sell+=1
      
    BO = Boomer(ohlc_1day,ticker)
    if BO == "b":
        buy+=1
    if BO == "s":
        sell+=1
     
    SS = Slingshot(ohlc_1day,ticker) 
    if SS == "b":
        buy+=1
    if SS == "s":
        sell+=1
    
    WH =Whoops(ohlc_1day,ticker)
    if WH == "b":
        buy+=1
    if WH == "s":
        sell+=1
    
    LZ = Lizards(ohlc_1day,ticker)
    if LZ == "b":
        buy+=1
    if LZ == "s":
        sell+=1
        
    print(buy)
    print(sell)
    
   
    

def main():
    tickers = ["ZEEL","WIPRO","VEDL","ULTRACEMCO","UPL","TITAN","TECHM","TATASTEEL",
           "TATAMOTORS","TCS","SUNPHARMA","SBIN","SHREECEM","RELIANCE","POWERGRID",
           "ONGC","NESTLEIND","NTPC","MARUTI","M&M","LT","KOTAKBANK","JSWSTEEL","INFY",
           "INDUSINDBK","IOC","ITC","ICICIBANK","HDFC","HINDUNILVR","HINDALCO",
           "HEROMOTOCO","HDFCBANK","HCLTECH","GRASIM","GAIL","EICHERMOT","DRREDDY",
           "COALINDIA","CIPLA","BRITANNIA","INFRATEL","BHARTIARTL","BPCL","BAJAJFINSV",
           "BAJFINANCE","BAJAJ-AUTO","AXISBANK","ASIANPAINT","ADANIPORTS","IDEA",
           "MCDOWELL-N","UBL","NIACL","SIEMENS","SRTRANSFIN","SBILIFE","PNB",
           "PGHH","PFC","PEL","PIDILITIND","PETRONET","PAGEIND","OFSS","NMDC","NHPC",
           "MOTHERSUMI","MARICO","LUPIN","L&TFH","INDIGO","IBULHSGFIN","ICICIPRULI",
           "ICICIGI","HINDZINC","HINDPETRO","HAVELLS","HDFCLIFE","HDFCAMC","GODREJCP",
           "GICRE","DIVISLAB","DABUR","DLF","CONCOR","COLPAL","CADILAHC","BOSCHLTD",
           "BIOCON","BERGEPAINT","BANKBARODA","BANDHANBNK","BAJAJHLDNG",
           "AUROPHARMA","ASHOKLEY","AMBUJACEM","ADANITRANS","ACC",
           "WHIRLPOOL","WABCOINDIA","VOLTAS","VINATIORGA","VBL","VARROC","VGUARD",
           "UNIONBANK","UCOBANK","TRENT","TORNTPOWER","TORNTPHARM","THERMAX","RAMCOCEM",
           "TATAPOWER","TATACONSUM","TVSMOTOR","TTKPRESTIG","SYNGENE","SYMPHONY",
           "SUPREMEIND","SUNDRMFAST","SUNDARMFIN","SUNTV","STRTECH","SAIL","SOLARINDS",
           "SHRIRAMCIT","SCHAEFFLER","SANOFI","SRF","SKFINDIA","SJVN","RELAXO",
           "RAJESHEXPO","RECLTD","RBLBANK","QUESS","PRESTIGE","POLYCAB","PHOENIXLTD",
           "PFIZER","PNBHOUSING","PIIND","OIL","OBEROIRLTY","NAM-INDIA","NATIONALUM",
           "NLCINDIA","NBCC","NATCOPHARM","MUTHOOTFIN","MPHASIS","MOTILALOFS","MINDTREE",
           "MFSL","MRPL","MANAPPURAM","MAHINDCIE","M&MFIN","MGL","MRF","LTI","LICHSGFIN",
           "LTTS","KANSAINER","KRBL","JUBILANT","JUBLFOOD","JINDALSTEL","JSWENERGY",
           "IPCALAB","NAUKRI","IGL","IOB","INDHOTEL","INDIANB","IBVENTURES","IDFCFIRSTB",
           "IDBI","ISEC","HUDCO","HONAUT","HAL","HEXAWARE","HATSUN","HEG","GSPL",
           "GUJGASLTD","GRAPHITE","GODREJPROP","GODREJIND","GODREJAGRO","GLENMARK",
           "GLAXO","GILLETTE","GMRINFRA","FRETAIL","FCONSUMER","FORTIS","FEDERALBNK",
           "EXIDEIND","ESCORTS","ERIS","ENGINERSIN","ENDURANCE","EMAMILTD","EDELWEISS",
           "EIHOTEL","LALPATHLAB","DALBHARAT","CUMMINSIND","CROMPTON","COROMANDEL","CUB",
           "CHOLAFIN","CHOLAHLDNG","CENTRALBK","CASTROLIND","CANBK","CRISIL","CESC",
           "BBTC","BLUEDART","BHEL","BHARATFORG","BEL","BAYERCROP","BATAINDIA",
           "BANKINDIA","BALKRISIND","ATUL","ASTRAL","APOLLOTYRE","APOLLOHOSP",
           "AMARAJABAT","ALKEM","APLLTD","AJANTPHARM","ABFRL","ABCAPITAL","ADANIPOWER",
           "ADANIGREEN","ADANIGAS","ABBOTINDIA","AAVAS","AARTIIND","AUBANK","AIAENG","3MINDIA"]
    for ticker in tickers:
        ohlc_1day = fetchOHLC(ticker,'day',100) 
        Compile(ohlc_1day,ticker)  
   
        

main()

  
