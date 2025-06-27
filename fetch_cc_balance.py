import os
import ccxt

api_key = os.environ["COINCHECK_API_KEY"]
api_secret = os.environ["COINCHECK_API_SECRET"]

exchange = ccxt.coincheck({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True, 
})

balance = exchange.fetch_balance()
for currency, info in balance['total'].items():
    if info > 0:
        print(f"{currency}: {info}")
