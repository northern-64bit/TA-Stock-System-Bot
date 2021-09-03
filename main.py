import discord
import os
import pandas as pd
import pandas_datareader as pdr
import datetime
import matplotlib.pyplot as plt
import pyimgur
import lxml
import requests
import json
import numpy
import yfinance as yf
from yahoo_fin import stock_info
import urllib
import urllib.request
from html_table_parser.parser import HTMLTableParser
import pandas_datareader.data as web

IMGUR_CLIENT_ID = 'ENTER ID HERE' # Get the Imgur client_id here: https://apidocs.imgur.com/#intro
ALPHA_VANTAGE_KEY = 'ENTER KEY HERE' # Get the API key here: https://www.alphavantage.co/support/#api-key
NYT_KEY = 'ENTER KEY HERE' # Get your New York Times API key here: https://developer.nytimes.com/get-started
FMP_API_KEY = 'ENTER KEY HERE' # Get the Financial Modeling Prep API key here: https://financialmodelingprep.com/developer/docs
MBOUM_KEY = 'ENTER KEY HERE' # Get your MBOUM API key here: https://mboum.com/api/welcome
DISCORD_BOT_TOKEN = 'ENTER TOKEN HERE' # Get your Discord Bot token here: https://discord.com/developers

client = discord.Client()
im = pyimgur.Imgur(IMGUR_CLIENT_ID)

USER_AGENT = {
  'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
  }
sesh = requests.Session()
sesh.headers.update(USER_AGENT)

yf_stock = 0
recent_message = 'None'

global counter_balance, counter_income, counter_cash, quarter_balance_sheet, annual_balance_sheet, quarter_cash_flow, annual_cash_flow, quarter_income_statement, annual_income_statement, ci, cc, cb, yesterday
counter_balance = False
counter_cash = False
counter_income = False
ci = 0
cc = 0
cb = 0
quarter_balance_sheet = 0
annual_balance_sheet = 0
quarter_cash_flow = 0
annual_cash_flow = 0
quarter_income_statement = 0
annual_income_statement = 0

yesterday = datetime.date.today() - datetime.timedelta(days = 1)


def date_float_to_input(float_date):
    str_date = str(float_date)
    year = int(str_date[0] + str_date[1] + str_date[2] + str_date[3])
    if str_date[5] == "0":
        month = int(str_date[6])
        if str_date[8] == "0":
            day = int(str_date[9])
        else:
            day = int(str_date[8] + str_date[9])
    else:
        month = int(str_date[5] + str_date[6])
        if str_date[8] == "0":
            day = int(str_date[9])
        else:
            day = int(str_date[8] + str_date[9])
    return year, month, day
  
def get_datastock(stock, begin_date):
  y, m, d = date_float_to_input(begin_date)
  data_stock = web.DataReader(stock, 'yahoo', start=datetime.datetime(y, m, d), end=datetime.date.today(), session=sesh)
  return data_stock

def get_balance(stock):
  url = 'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={}&apikey={}'.format(stock.upper(), ALPHA_VANTAGE_KEY)
  response = requests.get(url)
  dictr = response.json()
  recs = dictr['quarterlyReports']
  quarter_balance_sheet = pd.json_normalize(recs)
  recs = dictr['annualReports']
  annual_balance_sheet = pd.json_normalize(recs)
  return quarter_balance_sheet, annual_balance_sheet

def get_cash_flow(stock):
  url = 'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={}&apikey={}'.format(stock.upper(), ALPHA_VANTAGE_KEY)
  response = requests.get(url)
  dictr = response.json()
  recs = dictr['quarterlyReports']
  quarter_cash_flow = pd.json_normalize(recs)
  recs = dictr['annualReports']
  annual_cash_flow = pd.json_normalize(recs)
  return quarter_cash_flow, annual_cash_flow

def get_income(stock):
  url = 'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={}&apikey={}'.format(stock.upper(), ALPHA_VANTAGE_KEY)
  response = requests.get(url)
  dictr = response.json()
  recs = dictr['quarterlyReports']
  quarter_income_statement = pd.json_normalize(recs)
  recs = dictr['annualReports']
  annual_income_statement = pd.json_normalize(recs)
  return quarter_income_statement, annual_income_statement

def get_stock(inp):
  i = 0
  stock = ''
  stock_list = []
  print(inp)
  while i <= len(inp)-1:
    if inp[i] != ' ':
      stock_list.append(str(inp[i]))
      i+=1
    else:
      break
  return stock.join(stock_list)

def get_daa_or_rf(stock, daa_or_rf):
  url = 'https://api.eclect.us/symbol/'+stock+'?page=1'
  dictr = requests.get(url).json()
  headline = dictr[0]['shortname'] + '´s ' + dictr[0]['file_type']
  url = 'https://api.eclect.us/symbol/' + stock
  response = requests.get(url, params={'page': 1})
  page = response.json()
  l_daa = []
  l_rf = []
  daa_str = ''
  rf_str = ''
  if daa_or_rf == 'rf': 
    for record in page:
      for rf in record['rf_highlights']:
        l_rf.append(rf['sentence'])
        rf_str = rf_str + '- ' + rf['sentence'] + '\n'
      return l_rf, rf_str, headline
  elif daa_or_rf == 'daa':
    for record in page:
      for daa in record['daa_highlights']:
        l_daa.append(daa['sentence'])
        daa_str = daa_str + '- ' + daa['sentence'] + '\n'
      return l_daa, daa_str, headline


def get_etf(etf):
  def url_get_contents(url):
    req = urllib.request.Request(url=url)
    temp = urllib.request.urlopen(req)

    return temp.read()

  url = str('https://etfdb.com/etf/' + etf + '/#etf-ticker-profile/')
  xhtml = url_get_contents(url).decode('utf-8')
  temp = HTMLTableParser()
  temp.feed(xhtml)
  etf_holding_table = pd.DataFrame(temp.tables[2])
  etf_holding_country_table = pd.DataFrame(temp.tables[5])
  etf_holding_region_table = pd.DataFrame(temp.tables[7])
  etf_holding_sector_table = pd.DataFrame(temp.tables[4])
  return etf_holding_table, etf_holding_country_table, etf_holding_region_table, etf_holding_sector_table


def webscrape_etf_data():
  def url_get_contents(url):
    req = urllib.request.Request(url=url)
    temp = urllib.request.urlopen(req)

    return temp.read()

  xhtml = url_get_contents('https://etfdb.com/etfs/').decode('utf-8')
  temp = HTMLTableParser()
  temp.feed(xhtml)

  etf_sector_table = pd.DataFrame(temp.tables[1])
  etf_country_table = pd.DataFrame(temp.tables[4])
  return etf_sector_table, etf_country_table

def fix_amount(inp):
  i = 0
  amounts_min = ''
  amount_list = []
  print(inp)
  while i <= len(inp)-1:
    if inp[i] != ' ':
      amount_list.append(str(inp[i]))
      i+=1
    else:
      break
  return amounts_min.join(amount_list)

def make_embed(title, desc, img, foot, n_field, list_field_title, list_field_content):
  embed = discord.Embed(
    title = title,
    description = desc,
    colour = discord.Colour.green()
  )
  embed.set_footer(text=foot)
  if img != 0:
    embed.set_image(url=img)
  embed.set_author(name='TA Stock System Bot', icon_url='https://cdn.discordapp.com/avatars/817330703673851904/3708790a83cee0595f0686aed5f02d48.png')
  try:
    thumbnail = yf_stock.info['logo_url']
    print(thumbnail)
    embed.set_thumbnail(url=thumbnail)
  except:
    embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/817330703673851904/3708790a83cee0595f0686aed5f02d48.png')
  c = 1
  i = 0
  while c <= n_field:
    embed.add_field(name=list_field_title[i], value=list_field_content[i])
    i=c
    c+=1
  return embed

@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))
  await client.change_presence(activity=discord.Game(name='?help | Market Data'))

@client.event
async def on_message(message):
  
  if message.author == client.user:
    await message.add_reaction('0️⃣')
    await message.add_reaction('1️⃣')
    await message.add_reaction('2️⃣')
    await message.add_reaction('3️⃣')
    await message.add_reaction('4️⃣')
    await message.add_reaction('5️⃣')
    await message.add_reaction('6️⃣')
    await message.add_reaction('7️⃣')
    global message_id
    message_id = message.id
    return

  global title, footer
  recent_message = 'None'

  if message.content.startswith('?market'):
    recent_message = 'market'
    sp500 = pdr.get_data_yahoo('^GSPC', start=yesterday, end=datetime.date.today())
    sp_500_price = stock_info.get_live_price('^GSPC')
    sp_500_pc = (sp_500_price/sp500['Adj Close'][0]-1)*100
    ndx = pdr.get_data_yahoo('^NDX', start=yesterday, end=datetime.date.today())
    ndx_price = stock_info.get_live_price('^NDX')
    ndx_pc = (ndx_price/ndx['Adj Close'][0]-1)*100
    nsdq_c = pdr.get_data_yahoo('^IXIC', start=yesterday, end=datetime.date.today())
    nsdq_c_price = stock_info.get_live_price('^IXIC')
    nsdq_c_pc = (nsdq_c_price/nsdq_c['Adj Close'][0]-1)*100
    dji = pdr.get_data_yahoo('^DJI', start=yesterday, end=datetime.date.today())
    dji_price = stock_info.get_live_price('^DJI')
    dji_pc = (dji_price/dji['Adj Close'][0]-1)*100
    russ_2k = pdr.get_data_yahoo('^RUT', start=datetime.datetime(2021, 4, 29), end=datetime.date.today())
    russ_2k_price = stock_info.get_live_price('^RUT')
    russ_2k_pc = (russ_2k_price/russ_2k['Adj Close'][-2]-1)*100
    text = '0️⃣ Index\n1️⃣ Global Markets\n2️⃣ Commodities\n3️⃣ Bonds\n4️⃣ Currencies\n\n American Markets:\n**S&P 500:**   '+str(round(sp_500_price,2))+'; '+str(round(sp_500_pc, 2))+'%\n**Nasdaq Comp:**   '+str(round(nsdq_c_price, 2))+'; '+str(round(nsdq_c_pc,2))+'%\n**Nasdaq 100:**   '+str(round(ndx_price, 2))+'; '+str(round(ndx_pc,2))+'%\n**Dow Jones Industrial Average:**   '+str(round(dji_price, 2))+'; '+str(round(dji_pc,2))+'%\n**Russel 2000:**   '+str(round(russ_2k_price, 2))+'; '+str(round(russ_2k_pc,2))+'%'
    embed = make_embed('Market Overview', text, 0, 'For more info visit: https://www.avanza.se/marknadsoversikt.html', 0, 0, 0)
    market_overview = await message.channel.send(embed=embed)
  elif message.content.startswith('?help'):
    embed = make_embed('Help', 'Hello!\nThis is the TA Stock System Bot. It\'s developed by northern-64bit and it is open source: https://github.com/northern-64bit/TA-Stock-System-Bot \n\n***__Commands:__***\n? is the Prefix\n\n? + Ticker -> Stock Chart going back to 2010.01.10, ex. ?aapl \n\n? + Ticker + fr + date -> Stock Chart going back to the selected date, ex. ?aapl fr 2021.03.05\n\n? + Ticker + backtest + sma/ema + Number (+ +s) -> Backtest the price crossing the sma/ema (+s adds shorting), ex. ?aapl backtest sma 10 +s \n\n?market -> Shows an overview of the Global Markets\n\n? + Ticker + senator -> Transactions by senators on the stock, ex. ?aapl senator\n\n? + Ticker + insider -> Insider activity on the stock, ex. ?aapl insider\n\n?news -> Delivers news from the business section of the NYT\n\n?insider -> Shows insider trades over 1 mil USD sorted by value\n\n?insider recent -> Shows insider trades over 1 mil USD sorted by filling date\n\n?etf sectors -> Show ETF sector data\n\n?option + Contract -> Gets information of the option contract, ex. ?option PYPL210820P00280000\n', 0, 'For more information visit https://tastocksystem.wordpress.com/.', 0, 0, 0)
    help_message = await message.channel.send(embed=embed)
    recent_message = 'help'
  elif message.content.startswith('?insider'):
    def url_get_contents(url):
      req = urllib.request.Request(url=url)
      thing2 = urllib.request.urlopen(req)
      return str(thing2.read())

    insider_range = 'latest day'
    if message.content.startswith('?insider recent'):
      str1 = 'http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=1&fdr=&td=0&tdr=&fdlyl=&fdlyh=&'
      str2 = 'daysago=&xp=1&xs=1&vl=1000&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil&'
      str3 = '&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1'
      url = str1+str2+str3

      xhtml = url_get_contents(url)

      thing = HTMLTableParser()
      thing.feed(xhtml)

      insider_table = pd.DataFrame(thing.tables[11])
      insider_table_str = insider_table.loc[:, 1:12].to_string(header=False, index=False)
      if len(insider_table_str) == 427:
        str1 = 'http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=7&fdr=&td=0&tdr=&fdlyl=&fdlyh=&'
        str2 = 'daysago=&xp=1&xs=1&vl=1000&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil&'
        str3 = '&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1'
        url = str1+str2+str3

        xhtml = url_get_contents(url)

        thing = HTMLTableParser()
        thing.feed(xhtml)

        insider_table = pd.DataFrame(thing.tables[11])
        insider_range = 'last week'

      insider_table_str = insider_table.loc[:, 1:12].to_string(header=False, index=False)
      print(len(insider_table_str))
      if len(insider_table_str) < 1900:
          content = 'Insider trades over 1 mil USD sorted by filling date over from the '+insider_range+':\n\n' + insider_table_str
      else:
        content = 'Insider trades over 1 mil USD sorted by filling date from the '+insider_range+':\n\n' + insider_table_str[:1900] + '...'
      print(content)
    else:
      str1 = 'http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=1&fdr=&td=0&tdr=&fdlyl=&fdlyh=&'
      str2 = 'daysago=&xp=1&xs=1&vl=1000&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol'
      str3 = '=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1'

      url = str1+str2+str3

      xhtml = url_get_contents(url)

      thing = HTMLTableParser()
      thing.feed(xhtml)

      insider_table = pd.DataFrame(thing.tables[11])
      insider_table_str = insider_table.loc[:, 1:12].to_string(header=False, index=False)
      if len(insider_table_str) == 427:
        str1 = 'http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=7&fdr=&td=0&tdr=&fdlyl=&fdlyh=&'
        str2 = 'daysago=&xp=1&xs=1&vl=1000&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol'
        str3 = '=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1'
        url = str1+str2+str3

        xhtml = url_get_contents(url)

        thing = HTMLTableParser()
        thing.feed(xhtml)

        insider_table = pd.DataFrame(thing.tables[11])
        insider_range = 'last week'

      insider_table_str = insider_table.loc[:, 1:12].to_string(headers=False, index=False)
      print(len(insider_table_str))
      if len(insider_table_str) < 1900:
          content = 'Insider trades over 1 mil USD sorted by value from the '+insider_range+':\n\n' + insider_table_str
      else:
        content = 'Insider trades over 1 mil USD sorted by value from the '+insider_range+':\n\n' + insider_table_str[:1900] + '...'
        insider_table_str = insider_table_str[:1900]
      print(content)

    embed = make_embed('Insider Trading', content, 0, 'For more info visit: http://openinsider.com/', 0, 0, 0)
    insider_message = await message.channel.send(embed=embed)
    recent_message = 'insider'

  elif message.content.startswith('?news'):
    url = 'https://api.nytimes.com/svc/topstories/v2/business.json?api-key={}'.format(NYT_KEY)
    response = requests.get(url)
    page = response.json()
    text = ''
    for record in page['results']:
      text = text + '- ' + record['title'] + '\n' + record['abstract'] + '\n' + record['short_url'] + '\n\n'
    content = text[:2000]
    embed = make_embed('News provided by NYT', content, 0, 'Copyright (c) 2021 The New York Times Company. All Rights Reserved.', 0, 0, 0)
    news_message = await message.channel.send(embed=embed)

    recent_message = 'news'

  elif message.content.startswith('?etf sectors'):
    etf_sector_table, etf_country_table = webscrape_etf_data()
    content = etf_sector_table[[0,4,7,10,16]][1:12].to_string()
    print(content)
    content = 'Sector; 3m Fund Flow; 3m Weighted Returns; AUM; Dividend\n' + content[:1900]
    embed = make_embed('ETF Sector', content, 0, 'Data from: https://etfdb.com/', 0, 0, 0)
    etf_sector_message = await message.channel.send(embed=embed)

  elif message.content.startswith('?option '):
    option = message.content
    option = option.replace('?option ', '')
    url = 'https://api.syncretism.io/ops/historical/' + option
    response = requests.get(url)
    page = response.json()
    ask = []
    bid = []
    timestamp = []
    implied_volatility = []
    vega = []
    theta = []
    delta = []
    gamma = []
    title = 'Option Contract: ' + option
    for record in page:
      ask.append(record['ask'])
      bid.append(record['bid'])
      timestamp.append(record['timestamp'])
      implied_volatility.append(record['impliedvolatility'])
      vega.append(record['vega'])
      theta.append(record['theta'])
      delta.append(record['delta'])
      gamma.append(record['gamma'])

    content = 'Current Implied Volatility: ' + str(implied_volatility[-1]) + '\nBid: ' + str(bid[-1]) + '\nAsk: ' + str(ask[-1])
    fig, (ax1, ax2) = plt.subplots(2, 1)
    fig.subplots_adjust(hspace=0.5)
    ax1.plot(timestamp, bid)
    ax1.plot(timestamp, ask)
    ax1.grid(True)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.legend(['Bid', 'Ask'])
    ax2.plot(timestamp, implied_volatility)
    ax2.plot(timestamp, vega)
    ax2.plot(timestamp, theta)
    ax2.plot(timestamp, delta)
    ax2.plot(timestamp, gamma)
    ax2.grid(True)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Value')
    ax2.legend(['Implied Volatility', 'Vega', 'Theta', 'Delta', 'Gamma'])
    fig.suptitle(option + '´s Option Greeks')
    fig.autofmt_xdate()
    fig.savefig('img.png')
    uploaded_image = im.upload_image('img.png', title='something')
    print(uploaded_image.link)
    img_link = uploaded_image.link
    footer = 'The data is from yahoo finance'
    embed = make_embed(title, content, img_link, footer, 0, 0, 0)
    reply_stock = await message.channel.send(embed=embed)
    os.remove('img.png')
    fig.clear(True)
    recent_message = 'option contract'
      

  elif message.content.startswith('?'):
    backtest = False
    insider = False
    senator = False
    etf = False
    temp_stock = str(message.content).replace('?', '')
    stock = get_stock(temp_stock)
    yf_stock = yf.Ticker(stock.upper())
    if message.content.startswith('?' + stock + ' fr '):
      temp_date = str(message.content).replace('?' + stock + ' fr ', '')
    elif message.content.startswith('?'+stock+' backtest'):
      backtest = True
      temp_date = '2010-01-01'
      short = False
      if message.content.startswith('?'+stock+' backtest sma '):
        if str(message.content)[-1] == 's':
          sma_n = str(message.content).replace(' +s', '')
          short = True
        else:
          sma_n = str(message.content)
        sma_n = int(sma_n.replace('?' + stock + ' backtest sma ', ''))
        data_stock = get_datastock(stock, temp_date)
        data_stock.index = pd.to_datetime(data_stock.index)
        adj_close_px = data_stock[['Adj Close']].copy()
        moving_avg = adj_close_px.rolling(window=sma_n).mean()
        date1 = data_stock.index[0]
        date3 = str(date1.date())
        date2 = date1 + datetime.timedelta(days=1)
        date4 = str(date2.date())
        date_p = date1 - datetime.timedelta(days=1)
        date5 = str(date_p.date())
        value = []
        dates = []
        print(date3)
        price = data_stock['Adj Close'].loc[date3]
        print(data_stock['Adj Close'].loc[date3])
        print(len(data_stock['Adj Close']))
        errors = 0
        pa = 'b'
        while date2 < datetime.datetime.today():
          try:
            if float(data_stock['Adj Close'].loc[date3]) > float(moving_avg['Adj Close'].loc[date3]):
              if pa == 'k':
                try:
                  price = price*(float(data_stock['Adj Close'].loc[date3])/float(data_stock['Adj Close'].loc[date5]))
                except:
                  errors += 1
              elif pa == 'b':
                pa = 'k'
            elif float(data_stock['Adj Close'].loc[date3]) < float(moving_avg['Adj Close'].loc[date3]):
              if pa == 'k':
                pa = 'b'
                price = price*(float(data_stock['Adj Close'].loc[date3])/float(data_stock['Adj Close'].loc[date5]))
              if short == True and pa == 'b':
                try:
                  price = price+(float(data_stock['Adj Close'].loc[date5])-float(data_stock['Adj Close'].loc[date3]))
                except:
                  errors += 1
          except:
            errors += 1
          value.append(price)
          dates.append(date1)
          date1 = date2
          date3 = date4
          date2 = date1 + datetime.timedelta(days=1)
          date4 = str(date2.date())
          date_p = date1 - datetime.timedelta(days=1)
          date5 = str(date_p.date())

        fig, ax = plt.subplots()
        ax.plot(data_stock[['Adj Close']], '-')
        ax.plot(moving_avg[['Adj Close']], '-')
        ax.plot(dates, value)
        ax.grid(True)
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        legend_sma = 'SMA '+str(sma_n)
        backtest_result = pd.DataFrame(value, index =dates, columns=['USD'])
        ax.legend(['Adjusted Close', legend_sma, 'Backtest']) 
        fig.suptitle(stock.upper() + '´s SMA '+legend_sma+' Backtest')
        fig.autofmt_xdate()
        fig.savefig('img.png')
        uploaded_image = im.upload_image('img.png', title='something')
        print(uploaded_image.link)
        img_link = uploaded_image.link
        os.remove('img.png')
        bt_std = backtest_result.std(axis=0)
        print(str(bt_std['USD']))
        bt_return = (backtest_result['USD'][-1]/backtest_result['USD'][0]-1)*100
        bt_sharpe = ((bt_return)-stock_info.get_live_price('^IRX'))/(bt_std['USD'])
        print(str(bt_sharpe))
        title = stock.upper() + '´s SMA '+legend_sma+' Backtest'
        content = 'Return: '+str(bt_return)+'%\nVolatility: '+str(bt_std['USD'])+'%\nSharpe Ratio: '+str(bt_sharpe)
        footer = 'Disclaimer: The result of this could be completly wrong.'
        embed = make_embed(title, content, img_link, footer, 0, 0, 0)
        reply_stock = await message.channel.send(embed=embed)
        recent_message = 'stock'
        fig.clear(True)

      elif message.content.startswith('?'+stock+' backtest ema'):
        if str(message.content)[-1] == 's':
          ema_n = str(message.content).replace(' s', '')
          short = True
        else:
          ema_n = str(message.content)
        ema_n = int(ema_n.replace('?' + stock + ' backtest ema ', ''))
        data_stock = get_datastock(stock, temp_date)
        modPrice = data_stock['Adj Close'].copy()
        adj_close_px = data_stock['Adj Close'].copy()
        moving_avg = adj_close_px.rolling(window=ema_n).mean()
        modPrice.ewm(span=ema_n, adjust=False).mean()
        modPrice.iloc[0:ema_n] = moving_avg[0:ema_n]
        print(str(modPrice))

        date1 = data_stock.index[0]
        date3 = str(date1.date())
        date2 = date1 + datetime.timedelta(days=1)
        date4 = str(date2.date())
        date_p = date1 - datetime.timedelta(days=1)
        date5 = str(date_p.date())
        value = []
        dates = []
        print(date3)
        price = data_stock['Adj Close'].loc[date3]
        print(data_stock['Adj Close'].loc[date3])
        print(len(data_stock['Adj Close']))
        errors = 0
        pa = 'b'
        while date2 < datetime.datetime.today():
          try:
            if float(data_stock['Adj Close'].loc[date3]) > float(modPrice.loc[date3]):
              if pa == 'k':
                try:
                  price = price*(float(data_stock['Adj Close'].loc[date3])/float(data_stock['Adj Close'].loc[date5]))
                except:
                  errors += 1
              elif pa == 'b':
                pa = 'k'
            elif float(data_stock['Adj Close'].loc[date3]) < float(modPrice.loc[date3]):
              if pa == 'k':
                pa = 'b'
                price = price*(float(data_stock['Adj Close'].loc[date3])/float(data_stock['Adj Close'].loc[date5]))
              if short == True and pa == 'b':
                try:
                  price = price+(float(data_stock['Adj Close'].loc[date5])-float(data_stock['Adj Close'].loc[date3]))
                except:
                  errors += 1
          except:
            errors += 1
          value.append(price)
          dates.append(date1)
          date1 = date2
          date3 = date4
          date2 = date1 + datetime.timedelta(days=1)
          date4 = str(date2.date())
          date_p = date1 - datetime.timedelta(days=1)
          date5 = str(date_p.date())

        fig, ax = plt.subplots()
        print(str(errors))
        print(str(data_stock))
        ax.plot(data_stock['Adj Close'], '-')
        ax.plot(modPrice, '-')
        ax.plot(dates, value)
        ax.grid(True)
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        legend_ema = 'EMA '+str(ema_n)
        backtest_result = pd.DataFrame(value, index=dates, columns=['USD'])
        ax.legend(['Adjusted Close', legend_ema, 'Backtest']) 
        fig.suptitle(stock.upper() + '´s EMA '+legend_ema+' Backtest')
        fig.autofmt_xdate()
        fig.savefig('img.png')
        uploaded_image = im.upload_image('img.png', title='something')
        print(uploaded_image.link)
        img_link = uploaded_image.link
        os.remove('img.png')
        bt_std = backtest_result.std(axis=0)
        print(str(bt_std['USD']))
        bt_return = (backtest_result['USD'][-1]/backtest_result['USD'][0]-1)*100
        bt_sharpe = ((bt_return)-stock_info.get_live_price('^IRX'))/(bt_std['USD'])
        print(str(bt_sharpe))
        title = stock.upper() + '´s EMA '+legend_ema+' Backtest'
        content = 'Return: '+str(bt_return)+'%\nVolatility: '+str(bt_std['USD'])+'%\nSharpe Ratio: '+str(bt_sharpe)
        footer = 'Disclaimer: The result of this could be completly wrong.'
        embed = make_embed(title, content, img_link, footer, 0, 0, 0)
        reply_stock = await message.channel.send(embed=embed)
        recent_message = 'stock'
        fig.clear(True)

    elif message.content.startswith('?'+stock+' insider'):
      insider = True
      def url_get_contents(url):
        req = urllib.request.Request(url=url)
        thing2 = urllib.request.urlopen(req)
        return str(thing2.read())
      str1 = 'http://openinsider.com/screener?s={}&o=&pl=&ph=&ll=&lh=&fd=0&fdr=&td=0&tdr=&fdlyl=&fdlyh=&'.format(stock)
      str2 = 'daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&'
      str3 = 'noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1'
      url = str1+str2+str3

      xhtml = url_get_contents(url)

      thing = HTMLTableParser()
      thing.feed(xhtml)


      insider_table = pd.DataFrame(thing.tables[11])
      insider_range = 'last week'
      stock_u = stock.upper()

      insider_table_str = insider_table.loc[:, 1:12].to_string(header=False, index=False)
      print(len(insider_table_str))
      if len(insider_table_str) < 1900:
          content = stock_u+' insider trades over 1 mil USD sorted by date:\n\n' + insider_table_str
      else:
        content = stock_u+' insider trades over 1 mil USD sorted by date:\n\n' + insider_table_str[:1900] + '...'
      print(content)
      title = 'Insider Trading in '+stock_u
      embed = make_embed( title, content, 0, 'For more info visit: http://openinsider.com/', 0, 0, 0)
      insider_message = await message.channel.send(embed=embed)
      recent_message = 'insider'
    elif message.content.startswith('?'+stock+' senator'):
      senator = True
      text_str = ''
      response = requests.get('https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_ticker_transactions.json')
      page = response.json()
      i = 0
      purchases = 0
      sales = 0
      transaction_amount = 0
      sales_worth_min = 0
      sales_worth_max = 0
      purchases_worth_max = 0
      purchases_worth_min = 0
      for record in page:
        i += 1
        if record['ticker'] == stock.upper():
          print(i)
          for transaction in record['transactions']:
            transaction_amount += 1
            amount = transaction['amount']
            amount = amount.replace('$', '')
            amount = amount.replace(' - ', ' ')
            amount = amount.replace(',', '')
            if transaction['type'] == 'Purchase':
              purchases += 1
              purchases_worth_min_temp = fix_amount(amount)
              print(purchases_worth_min_temp)
              temp = purchases_worth_min_temp + ' '
              purchases_worth_max_temp = amount.replace(temp, '')
              purchases_worth_max += int(purchases_worth_max_temp)
              purchases_worth_min += int(purchases_worth_min_temp)
            elif transaction['type'] == 'Sale (Partial)' or transaction['type'] == 'Sale (Full)':
              sales += 1
              sales_worth_min_temp = fix_amount(amount)
              print(sales_worth_min_temp)
              temp = sales_worth_min_temp + ' '
              sales_worth_max_temp = amount.replace(temp, '')
              sales_worth_max += int(sales_worth_max_temp)
              sales_worth_min += int(sales_worth_min_temp)
            text_str = text_str + '- ' + transaction['transaction_date'] + ': ' + transaction['amount'] + ' ' + transaction['type'] + ' by ' + transaction['senator'] + ' (' + transaction['owner'] + ')\n'
          break
      summary = 'Summary; Transactions: ' + str(transaction_amount) + ', Purchases: ' + str(purchases) + ' amounting to ' + str(purchases_worth_min) + '-' + str(purchases_worth_max) + '$, Sales: ' + str(sales) + ' amounting to ' + str(sales_worth_min) + '-' + str(sales_worth_max) + '$\n\n'
      text = summary + text_str
      if len(text) > 2000:
        text = summary + text_str[:1900] + '...'
      title = 'Trading by U.S. Senators in ' + stock.upper()
      embed = make_embed( title, text, 0, 'For more info visit: https://senatestockwatcher.com/', 0, 0, 0)
      senator_message = await message.channel.send(embed=embed)
      recent_message = 'senator'
      senator = True
      temp_date = '2010-01-01'
          
    else:
      temp_date = '2010-01-01'
    if backtest == False and insider == False and senator == False:
      url = 'https://financialmodelingprep.com/api/v3/etf/list?apikey={}'.format(FMP_API_KEY)
      response = requests.get(url)
      page = response.json()
      for record in page:
        if record['symbol'] == stock.upper():
          etf = True
          name = record['name']
          break

      data_stock = get_datastock(stock, temp_date)
      fig, ax = plt.subplots()
      ax.plot(data_stock[['Adj Close']], '-')
      ax.grid(True)
      ax.set_xlabel('Date')
      ax.set_ylabel('Price')
      fig.suptitle(stock.upper() + '´s Price Graph')
      fig.autofmt_xdate()
      fig.savefig('img.png')
      uploaded_image = im.upload_image('img.png', title='something')
      print(uploaded_image.link)
      img_link = uploaded_image.link
      footer = 'The data is from yahoo finance'
      
      if etf == True:
        title = name + ' Data'

        try:
          requestResponse = requests.get(" https://mboum.com/api/v1/qu/quote/profile/?symbol={}&apikey={}".format(stock, MBOUM_KEY))
          etf_data = requestResponse.json()
          desc_etf = etf_data['longBusinessSummary']
          content = desc_etf
        except:
          content = 'No description available.'
        recent_message = 'etf'
      else:
        title = stock.upper() + ' Data'
        url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol={}&apikey={}'.format(stock.upper(), os.getenv('KEY'))
        response = requests.get(url)
        dictr = response.json()
        try:
          desc_stock = str(dictr['Description'])
        except:
          desc_stock = 'No description available.'
        global profile
        profile = pd.json_normalize(dictr)
        profile = profile.transpose()

        if len(desc_stock) < 1900:
          content = '0️⃣ Index + Company Profile\n1️⃣ Overview\n2️⃣ Balance Sheet\n3️⃣ Cash Flow\n4️⃣ Income Statement\n5️⃣ Institutional Holders\n6️⃣ Risk Factors\n7️⃣ Discussion and analysis\n\n' + desc_stock
          print(len(desc_stock))
        else:
          content = '0️⃣ Index + Company Profile\n1️⃣ Overview\n2️⃣ Balance Sheet\n3️⃣ Cash Flow\n4️⃣ Income Statement\n5️⃣ Institutional Holders\n6️⃣ Risk Factors\n7️⃣ Discussion and analysis\n\n' + desc_stock[:1900] + '...'
          print(len(desc_stock))
        recent_message = 'stock'
      embed = make_embed(title, content, img_link, footer, 0, 0, 0)
      reply_stock = await message.channel.send(embed=embed)
      os.remove('img.png')
      fig.clear(True)

  @client.event
  async def on_reaction_add(reaction, user):
    if user == client.user:
      return
    elif reaction.message.author != client.user:
      return
    print(reaction)
    global counter_balance, counter_income, counter_cash, quarter_balance_sheet, annual_balance_sheet, quarter_cash_flow, annual_cash_flow, quarter_income_statement, annual_income_statement, ci, cc, cb
    if reaction.emoji == '0️⃣':
      if recent_message == 'stock':
        await reply_stock.edit(content=None, embed=embed)
      elif recent_message == 'market':
        await market_overview.edit(content=None, embed=embed)
    elif reaction.emoji == '1️⃣':
      if recent_message == 'stock':
        temp = '***__' + stock.upper() + ' Overview__***'
        table = str(profile)
        if len(table)<1950:
          text = temp + '\n```' + table + '```'
        else:
          text = temp + '\n```' + table[:1950] + '...' + '```'
          if len(table)<3900:
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          else:
            await message.author.send(temp + '\n```...' + table[1950:3900] + '...```')
            await message.author.send(temp + '\n```...' + table[3900:] + '```')
        await reply_stock.edit(content=text, embed=None)
      elif recent_message == 'market':
        dax = pdr.get_data_yahoo('^GDAXI', start=yesterday, end=datetime.date.today())
        dax_price = stock_info.get_live_price('^GDAXI')
        dax_pc = (dax_price/dax['Adj Close'][0]-1)*100
        nikk_225 = pdr.get_data_yahoo('^N225', start=datetime.datetime(2021, 4, 29), end=datetime.date.today())
        nikk_225_price = stock_info.get_live_price('^N225')
        nikk_225_pc = (nikk_225_price/nikk_225['Adj Close'][0]-1)*100
        hang_seng = pdr.get_data_yahoo('^HSI', start=yesterday, end=datetime.date.today())
        hang_seng_price = stock_info.get_live_price('^HSI')
        bric_50 = pdr.get_data_yahoo('^BRIC50D', start=yesterday, end=datetime.date.today())
        bric_50_price = stock_info.get_live_price('^BRIC50D')
        bric_50_pc = (bric_50_price/bric_50['Adj Close'][0]-1)*100
        hang_seng_pc = (hang_seng_price/hang_seng['Adj Close'][0]-1)*100
        dj_au = pdr.get_data_yahoo('^DJAU', start=yesterday, end=datetime.date.today())
        dj_au_price = stock_info.get_live_price('^DJAU')
        dj_au_pc = (dj_au_price/dj_au['Adj Close'][0]-1)*100
        dj_sa = pdr.get_data_yahoo('^ZADOW', start=yesterday, end=datetime.date.today())
        dj_sa_price = stock_info.get_live_price('^ZADOW')
        dj_sa_pc = (dj_sa_price/dj_sa['Adj Close'][0]-1)*100
        ftse_100 = stock_info.get_data("^FTSE", start_date = yesterday, end_date = datetime.date.today())
        ftse_100_price = stock_info.get_live_price('^FTSE')
        ftse_100_pc = (ftse_100_price/ftse_100['adjclose'][0]-1)*100
        moex = pdr.get_data_yahoo('IMOEX.ME', start=yesterday, end=datetime.date.today())
        moex_price = stock_info.get_live_price('IMOEX.ME')
        moex_pc = (moex_price/moex['Adj Close'][0]-1)*100
        text = 'USA:\n**S&P 500:**   '+str(round(sp_500_price, 2))+'; '+str(round(sp_500_pc, 2)) +'%\n**Nasdaq Comp:**   '+str(round(nsdq_c_price, 2))+'; '+str(round(nsdq_c_pc,2)) + '%\n\nEurope:\n'+'**DAX:**   '+str(round(dax_price, 2))+'; '+str(round(dax_pc,2))+'%\n**FTSE 100 GBP:**   '+str(round(ftse_100_price, 2))+'; '+str(round(ftse_100_pc,2))+'%\n**MOEX RUB:**   '+str(round(moex_price, 2))+'; '+str(round(moex_pc,2))+'%\n\nAsia:\n'+'**Nikkei 225:**   '+str(round(nikk_225_price, 2))+'; '+str(round(nikk_225_pc,2))+'%\n**Hang Seng:**   '+str(round(hang_seng_price, 2))+'; '+str(round(hang_seng_pc,2))+'%\n**DJ Bric 50:**   '+str(round(bric_50_price, 2))+'; '+str(round(bric_50_pc,2))+'%\n\nOther:\n'+'**DJ Australia AUD:**   '+str(round(dj_au_price, 2))+'; '+str(round(dj_au_pc,2))+'%\n**DJ South Africa ZAR:**   '+str(round(dj_sa_price, 2))+'; '+str(round(dj_sa_pc,2))+'%'
        embed_gm = make_embed('Global Markets', text, 0, 'For more info visit: https://www.avanza.se/marknadsoversikt.html', 0, 0, 0)
        await market_overview.edit(content=None, embed=embed_gm)
    elif reaction.emoji == '2️⃣':
      if recent_message == 'stock':
        
        quarter_balance_sheet, annual_balance_sheet = get_balance(stock)
        counter_balance = True
        counter_cash = False
        counter_income = False
        temp = '***__' + stock.upper() + ' Balance Sheet__***'
        table = annual_balance_sheet.iloc[0].to_string()
        if len(table)<1950:
          text = temp + '\n```' + table + '```'
        else:
          text = temp + '\n```' + table[:1950] + '...' + '```'
          await message.author.send(temp + '\n```...' + table[1950:] + '```')
        await reply_stock.edit(content=text, embed=None)
        await reply_stock.add_reaction('⬅️')
        await reply_stock.add_reaction('➡️')
      elif recent_message == 'market':
        cof = pdr.get_data_yahoo('CL=F', start=yesterday, end=datetime.date.today())
        cof_price = stock_info.get_live_price('CL=F')
        cof_pc = (cof_price/cof['Adj Close'][0]-1)*100
        au = pdr.get_data_yahoo('GC=F', start=yesterday, end=datetime.date.today())
        au_price = stock_info.get_live_price('GC=F')
        au_pc = (au_price/au['Adj Close'][0]-1)*100
        slv = pdr.get_data_yahoo('SI=F', start=yesterday, end=datetime.date.today())
        slv_price = stock_info.get_live_price('SI=F')
        slv_pc = (slv_price/slv['Adj Close'][0]-1)*100
        cop = pdr.get_data_yahoo('HG=F', start=yesterday, end=datetime.date.today())
        cop_price = stock_info.get_live_price('HG=F')
        cop_pc = (cop_price/cop['Adj Close'][0]-1)*100
        pltm = pdr.get_data_yahoo('PL=F', start=yesterday, end=datetime.date.today())
        pltm_price = stock_info.get_live_price('PL=F')
        pltm_pc = (pltm_price/pltm['Adj Close'][0]-1)*100
        pld = pdr.get_data_yahoo('PA=F', start=yesterday, end=datetime.date.today())
        pld_price = stock_info.get_live_price('PA=F')
        pld_pc = (pld_price/pld['Adj Close'][0]-1)*100
        sb = pdr.get_data_yahoo('ZS=F', start=yesterday, end=datetime.date.today())
        sb_price = stock_info.get_live_price('ZS=F')
        sb_pc = (sb_price/sb['Adj Close'][0]-1)*100
        crn = pdr.get_data_yahoo('ZC=F', start=yesterday, end=datetime.date.today())
        crn_price = stock_info.get_live_price('ZC=F')
        crn_pc = (crn_price/crn['Adj Close'][0]-1)*100
        oat = pdr.get_data_yahoo('ZO=F', start=yesterday, end=datetime.date.today())
        oat_price = stock_info.get_live_price('ZO=F')
        oat_pc = (oat_price/oat['Adj Close'][0]-1)*100
        cca = pdr.get_data_yahoo('CC=F', start=yesterday, end=datetime.date.today())
        cca_price = stock_info.get_live_price('CC=F')
        cca_pc = (cca_price/cca['Adj Close'][0]-1)*100
        cof = pdr.get_data_yahoo('KC=F', start=yesterday, end=datetime.date.today())
        cof_price = stock_info.get_live_price('KC=F')
        cof_pc = (cof_price/cof['Adj Close'][0]-1)*100
        cot = pdr.get_data_yahoo('CT=F', start=yesterday, end=datetime.date.today())
        cot_price = stock_info.get_live_price('CT=F')
        cot_pc = (cot_price/cot['Adj Close'][0]-1)*100
        sg = pdr.get_data_yahoo('SB=F', start=yesterday, end=datetime.date.today())
        sg_price = stock_info.get_live_price('SB=F')
        sg_pc = (sg_price/sg['Adj Close'][0]-1)*100
        ct = pdr.get_data_yahoo('LE=F', start=yesterday, end=datetime.date.today())
        ct_price = stock_info.get_live_price('LE=F')
        ct_pc = (ct_price/ct['Adj Close'][0]-1)*100
        lb = pdr.get_data_yahoo('LBS=F', start=yesterday, end=datetime.date.today())
        lb_price = stock_info.get_live_price('LBS=F')
        lb_pc = (lb_price/lb['Adj Close'][0]-1)*100
        ng = pdr.get_data_yahoo('NG=F', start=yesterday, end=datetime.date.today())
        ng_price = stock_info.get_live_price('NG=F')
        ng_pc = (ng_price/ng['Adj Close'][0]-1)*100
        text = 'Gas & Oil:\n**Crude Oil Futures:**   '+str(round(cof_price, 2))+'; '+str(round(cof_pc, 2))+'%\n**Natural Gas Prices:**   '+str(round(ng_price, 2))+'; '+str(round(ng_pc,2))+'%\n\nMetals:\n**Gold Futures:**   '+str(round(au_price, 2))+'; '+str(round(au_pc,2)) +'%\n**Silver Futures:**   '+str(round(slv_price, 2))+'; '+str(round(slv_pc,2))+'%\n**Copper Futures:**   '+str(round(cop_price, 2))+'; '+str(round(cop_pc,2))+'%\n**Platinum Futures:**   '+str(round(pltm_price, 2))+'; '+str(round(pltm_pc,2))+'%\n**Palladium Futures:**   '+str(round(pld_price, 2))+'; '+str(round(pld_pc,2))+'%\n**Platinum Futures:**   '+str(round(pltm_price, 2))+'; '+str(round(pltm_pc,2))+'%\n\nAgriculture:\n**Soybean Futures:**   '+str(round(sb_price, 2))+'; '+str(round(sb_pc,2))+'%\n**Corn Futures:**   '+str(round(crn_price, 2))+'; '+str(round(crn_pc,2))+'%\n**Oat Futures:**   '+str(round(oat_price, 2))+'; '+str(round(oat_pc,2))+'%\n**Cocoa Futures:**   '+str(round(cca_price, 2))+'; '+str(round(cca_pc,2))+'%\n**Coffee Futures:**   '+str(round(cof_price, 2))+'; '+str(round(cof_pc,2))+'%\n**Cotton Futures:**   '+str(round(cot_price, 2))+'; '+str(round(cot_pc,2))+'%\n**Sugar Futures:**   '+str(round(sg_price, 2))+'; '+str(round(sg_pc,2))+'%\n**Live Cattle Prices:**   '+str(round(ct_price, 2))+'; '+str(round(ct_pc,2))+'%\n\nOther:\n**Lumber Futures:**   '+str(round(lb_price, 2))+'; '+str(round(lb_pc,2))+'%'
        embed_gm = make_embed('Commodities', text, 0, 'For more info visit: https://www.avanza.se/marknadsoversikt.html', 0, 0, 0)
        await market_overview.edit(content=None, embed=embed_gm)
    elif reaction.emoji == '3️⃣':
      if recent_message == 'stock':
        
        quarter_cash_flow, annual_cash_flow = get_cash_flow(stock)
        counter_cash = True
        counter_income = False
        counter_balance = False
        temp = '***__' + stock.upper() + ' Cash Flow__***'
        table = annual_cash_flow.iloc[0].to_string()
        if len(table)<1950:
          text = temp + '\n```' + table + '```'
        else:
          text = temp + '\n```' + table[:1950] + '...' + '```'
          await message.author.send(temp + '\n```...' + table[1950:] + '```')
        await reply_stock.edit(content=text, embed=None)
        await reply_stock.add_reaction('⬅️')
        await reply_stock.add_reaction('➡️')
      elif recent_message == 'market':
        t13w = pdr.get_data_yahoo('^IRX', start=yesterday, end=datetime.date.today())
        t13w_price = stock_info.get_live_price('^IRX')
        t13w_pc = (t13w_price/t13w['Adj Close'][0]-1)*100
        t5y = pdr.get_data_yahoo('^FVX', start=yesterday, end=datetime.date.today())
        t5y_price = stock_info.get_live_price('^FVX')
        t5y_pc = (t5y_price/t5y['Adj Close'][0]-1)*100
        t10y = pdr.get_data_yahoo('^TNX', start=yesterday, end=datetime.date.today())
        t10y_price = stock_info.get_live_price('^TNX')
        t10y_pc = (t10y_price/t10y['Adj Close'][0]-1)*100
        t30y = pdr.get_data_yahoo('^TYX', start=yesterday, end=datetime.date.today())
        t30y_price = stock_info.get_live_price('^TYX')
        t30y_pc = (t30y_price/t30y['Adj Close'][0]-1)*100
        
        text = 'USA Treasury:\n**13 Week Treasury Bill:**   '+str(round(t13w_price, 2))+'; '+str(round(t13w_pc, 2)) +'%\n**Treasury Yield 5 Years:**   '+str(round(t5y_price, 2))+'; '+str(round(t5y_pc,2)) + '%\n**Treasury Yield 10 Years:**   '+str(round(t10y_price, 2))+'; '+str(round(t10y_pc,2))+'%\n**Treasury Yield 30 Years:**   '+str(round(t30y_price, 2))+'; '+str(round(t30y_pc,2))+'%'
        embed_gm = make_embed('Bonds', text, 0, 'For more info visit: https://www.avanza.se/marknadsoversikt.html', 0, 0, 0)
        await market_overview.edit(content=None, embed=embed_gm)
    elif reaction.emoji == '4️⃣':
      if recent_message == 'stock':
        
        quarter_income_statement, annual_income_statement = get_income(stock)
        counter_income = True
        counter_balance = False
        counter_cash = False
        temp = '***__' + stock.upper() + ' Income Statement__***'
        table = annual_income_statement.iloc[0].to_string()
        if len(table)<1950:
          text = temp + '\n```' + table + '```'
        else:
          text = temp + '\n```' + table[:1950] + '...' + '```'
          await message.author.send(temp + '\n```...' + table[1950:] + '```')
        await reply_stock.edit(content=text, embed=None)
        await reply_stock.add_reaction('⬅️')
        await reply_stock.add_reaction('➡️')
      elif recent_message == 'market':
        eurusd = pdr.get_data_yahoo('EURUSD=X', start=yesterday, end=datetime.date.today())
        eurusd_price = stock_info.get_live_price('EURUSD=X')
        eurusd_pc = (eurusd_price/eurusd['Adj Close'][0]-1)*100
        gbpusd = pdr.get_data_yahoo('GBPUSD=X', start=yesterday, end=datetime.date.today())
        gbpusd_price = stock_info.get_live_price('GBPUSD=X')
        gbpusd_pc = (gbpusd_price/gbpusd['Adj Close'][0]-1)*100
        jpy = pdr.get_data_yahoo('JPY=X', start=yesterday, end=datetime.date.today())
        jpy_price = stock_info.get_live_price('JPY=X')
        jpy_pc = (jpy_price/jpy['Adj Close'][0]-1)*100
        eursek = pdr.get_data_yahoo('EURSEK=X', start=yesterday, end=datetime.date.today())
        eursek_price = stock_info.get_live_price('EURSEK=X')
        eursek_pc = (eursek_price/eursek['Adj Close'][0]-1)*100
        eurchf = pdr.get_data_yahoo('EURCHF=X', start=datetime.datetime(2021, 4, 29), end=datetime.date.today())
        eurchf_price = stock_info.get_live_price('EURCHF=X')
        eurchf_pc = (eurchf_price/eurchf['Adj Close'][-2]-1)*100
        text = '**EUR/USD:**   '+str(round(eurusd_price,2))+'; '+str(round(eurusd_pc, 2))+'%\n**GBP/USD:**   '+str(round(gbpusd_price, 2))+'; '+str(round(gbpusd_pc,2))+'%\n**USD/JPY:**   '+str(round(jpy_price, 2))+'; '+str(round(jpy_pc,2))+'%\n**EUR/SEK:**   '+str(round(eursek_price, 2))+'; '+str(round(eursek_pc,2))+'%\n**EUR/CHF:**   '+str(round(eurchf_price, 2))+'; '+str(round(eurchf_pc,2))+'%'
        embed_gm = make_embed('Bonds', text, 0, 'For more info visit: https://www.avanza.se/marknadsoversikt.html', 0, 0, 0)
        await market_overview.edit(content=None, embed=embed_gm)
    elif reaction.emoji == '5️⃣':
      if recent_message == 'stock':
        temp = '***__' + stock.upper() + ' Institutional Holders__***'
        table = yf_stock.institutional_holders.to_string(index=False)
        text = temp + '\n```' + table + '```'
        await reply_stock.edit(content=text, embed=None)
    elif reaction.emoji == '6️⃣':
      if recent_message == 'stock':
        temp = '***__' + stock.upper() + ' Institutional Holders__***'
        l_rf, rf_str, headline = get_daa_or_rf(stock, 'rf')
        headline = headline + ' Risk Factors'
        rf_str = rf_str[:1900] + '...'
        embed_rf = make_embed(headline, rf_str, 0, 'For more info visit: https://eclect.us/', 0, 0, 0)
        await reply_stock.edit(content=None, embed=embed_rf)
    elif reaction.emoji == '7️⃣':
      if recent_message == 'stock':
        temp = '***__' + stock.upper() + ' Institutional Holders__***'
        l_daa, daa_str, headline = get_daa_or_rf(stock, 'daa')
        headline = headline + ' Discussion and Analysis'
        daa_str = daa_str[:1900] + '...'
        embed_daa = make_embed(headline, daa_str, 0, 'For more info visit: https://eclect.us/', 0, 0, 0)
        await reply_stock.edit(content=None, embed=embed_daa)
    elif reaction.emoji == '⬅️':
      if counter_balance == True:

        if cb != 0:
          cb -= 1
          temp = '***__' + stock.upper() + ' Balance Sheet__***'
          table = annual_balance_sheet.iloc[cb].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
           return
      elif counter_cash == True:

        if cc != 0:
          cc -= 1
          temp = '***__' + stock.upper() + ' Cash Flow__***'
          table = annual_cash_flow.iloc[cc].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
          return
      elif counter_income == True:

        if ci != 0:
          ci -= 1
          temp = '***__' + stock.upper() + ' Income Statement__***'
          table = annual_income_statement.iloc[ci].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
          return
    elif reaction.emoji == '➡️':
      if counter_balance == True:

        if cb != 4:
          cb += 1
          temp = '***__' + stock.upper() + ' Balance Sheet__***'
          table = annual_balance_sheet.iloc[cb].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
           return
      elif counter_cash == True:

        if cc != 4:
          cc += 1
          temp = '***__' + stock.upper() + ' Cash Flow__***'
          table = annual_cash_flow.iloc[cc].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
          return
      elif counter_income == True:

        if ci != 4:
          ci += 1
          temp = '***__' + stock.upper() + ' Income Statement__***'
          table = annual_income_statement.iloc[ci].to_string()
          if len(table)<1950:
            text = temp + '\n```' + table + '```'
          else:
            text = temp + '\n```' + table[:1950] + '...' + '```'
            await message.author.send(temp + '\n```...' + table[1950:] + '```')
          await reply_stock.edit(content=text, embed=None)
        else:
          return
    '''
    @client.event
    def on_message_edit(before, after):
      try:
        after.message.remove_reaction('➡️')
        after.message.remove_reaction('⬅️')
      except:
        print(0)
    '''
        
client.run(DISCORD_BOT_TOKEN)
