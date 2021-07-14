# TA-Stock-System-Bot
[![Updated Badge](https://badges.pufler.dev/updated/northern-64bit/TA-Stock-System-Bot)](https://badges.pufler.dev)
[![Visits Badge](https://badges.pufler.dev/visits/northern-64bit/TA-Stock-System-Bot)](https://badges.pufler.dev)
[![Created Badge](https://badges.pufler.dev/created/northern-64bit/TA-Stock-System-Bot)](https://badges.pufler.dev)

A open source finance discord bot.

## Set Up
First of all you need to download the main file, then you have to enter the following API tokens in the beginning of the main file directly after the dependencies:
```python
IMGUR_CLIENT_ID = 'ENTER ID HERE' # Get the Imgur client_id here: https://apidocs.imgur.com/#intro
ALPHA_VANTAGE_KEY = 'ENTER KEY HERE' # Get the API key here: https://www.alphavantage.co/support/#api-key
NYT_KEY = 'ENTER KEY HERE' # Get your New York Times API key here: https://developer.nytimes.com/get-started
FMP_API_KEY = 'ENTER KEY HERE' # Get the Financial Modeling Prep API key here: https://financialmodelingprep.com/developer/docs
MBOUM_KEY = 'ENTER KEY HERE' # Get your MBOUM API key here: https://mboum.com/api/welcome
DISCORD_BOT_TOKEN = 'ENTER TOKEN HERE' # Get your Discord Bot token here: https://discord.com/developers
```
NOTE: You don't need to pay for any of those keys if you choose the free plan

## Commands
The bot has the following discord commands:

- ?help
- ? + Ticker -> Stock Chart going back to 2010.01.10, ex. ?aapl
- ? + Ticker + fr + date -> Stock Chart going back to the selected date, ex. ?aapl fr 2021.03.05
- ? + Ticker + backtest + sma/ema + Number (+ +s) -> Backtest the price crossing the sma/ema (+s adds shorting), ex. ?aapl backtest sma 10 +s
- ?market -> Shows an overview of the Global Markets
- ? + Ticker + senator -> Transactions by senators on the stock, ex. ?aapl senator
- ? + Ticker + insider -> Insider activity on the stock, ex. ?aapl insider
- ?news -> Delivers news from the business section of the NYT
- ?insider -> Shows insider trades over 1 mil USD sorted by value
- ?insider recent -> Shows insider trades over 1 mil USD sorted by filling date
- ?etf sectors -> Show ETF sector data
- ?option + Contract -> Gets information of the option contract, ex. ?option PYPL210820P00280000
