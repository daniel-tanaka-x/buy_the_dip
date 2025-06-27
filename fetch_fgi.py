import requests  
import ccxt

exchange = ccxt.coincheck()
ticker = exchange.fetch_ticker('BTC/JPY')
print("BTC:", round(ticker['last']), "円")

fgi = requests.get("https://api.alternative.me/fng/").json()["data"][0]["value"] 
print("FGI:", fgi)
