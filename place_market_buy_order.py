import os
import ccxt

api_key = os.getenv("COINCHECK_API_KEY")
api_secret = os.getenv("COINCHECK_API_SECRET")

exchange = ccxt.coincheck({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

symbol = 'BTC/JPY'
amount = 0.0001

order = exchange.create_order(
    symbol=symbol,
    type='market',
    side='buy',
    amount=amount
)
print("注文が完了しました。注文内容は以下の通りです。")
print(order)
