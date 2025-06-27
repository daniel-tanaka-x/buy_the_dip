import os
import ccxt
import requests
import pandas as pd
import logging
from datetime import datetime, date

# === ログ設定 ===
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# === 戦略パラメーター ===
fear_threshold    = 10      # FGIがこの値以下で買いシグナル
fear_multiplier   = 1.11    # 連続日数に応じた買い増し倍率
sell_half_target  = 3.00    # 300%上昇で半分売り
sell_full_target  = 3.95    # 395%上昇で残り全部売り
initial_cash      = 10000   # 初期予算（整数JPY）
history_days      = 7       # FGIを何日分取得して連続日数を数えるか
buy_divisions     = 10      # ポジションを何分割して買い増すか

# === 取引最小値 ===
MIN_BTC_ORDER = 0.00001
MIN_JPY_ORDER = 500  # JPYでの最小注文額

# === Coincheck APIキーの取得 ===
api_key = os.getenv("COINCHECK_API_KEY")
api_secret = os.getenv("COINCHECK_API_SECRET")
exchange = ccxt.coincheck({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# === 残高確認 ===
def get_jpy_balance():
    try:
        bal = exchange.fetch_balance()
        return bal.get('JPY', {}).get('free', 0.0)
    except Exception as e:
        logging.error(f"JPY残高取得失敗: {e}")
        return 0.0

def get_btc_balance():
    try:
        bal = exchange.fetch_balance()
        return bal.get('BTC', {}).get('free', 0.0)
    except Exception as e:
        logging.error(f"BTC残高取得失敗: {e}")
        return 0.0

# === FGI履歴取得・連続日数カウント ===
def fetch_fgi_history(days=history_days):
    try:
        url = f"https://api.alternative.me/fng/?limit={days}"
        data = requests.get(url, timeout=10).json().get('data', [])
        return [{'date': d['timestamp'], 'value': int(d['value'])} for d in data]
    except Exception as e:
        logging.error(f"FGI履歴取得失敗: {e}")
        now_ts = int(datetime.now().timestamp())
        return [{'date': now_ts, 'value': 50}]

def calculate_consecutive_fear_days(history):
    cnt = 0
    for day in history:
        if day['value'] <= fear_threshold:
            cnt += 1
        else:
            break
    return max(1, cnt)

# === 重複購入チェック ===
def already_bought_today(df: pd.DataFrame) -> bool:
    if df.empty: return False
    today = date.today().isoformat()
    for ts in df.get('buy_timestamp', pd.Series()).dropna():
        if pd.to_datetime(ts).date().isoformat() == today:
            return True
    return False

# === FGI & BTC価格取得 ===
def fetch_fgi():
    try:
        return int(requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
                   .json()['data'][0]['value'])
    except Exception as e:
        logging.error(f"FGI取得失敗: {e}")
        return 50
        
def fetch_btc_price():
    try:
        price = exchange.fetch_ticker("BTC/JPY").get('last')
        if not price or price <= 0:
            raise RuntimeError(f"不正なBTC価格: {price}")
        return price
    except Exception as e:
        logging.error(f"BTC価格取得失敗: {e}")
        raise

# === 成行注文 ===
def execute_market_buy(jpy_amount: float):
    try:
        if jpy_amount < MIN_JPY_ORDER:
            raise RuntimeError(f"注文金額不足: {jpy_amount} JPY")
        bal = get_jpy_balance() 
        if bal < jpy_amount:
            raise RuntimeError(f"残高不足: {bal}")
        price = fetch_btc_price()
        btc_amt = round(jpy_amount / price, 8)
        ord = exchange.create_order("BTC/JPY", "market", "buy", btc_amt)
        return ord.get('average', price), btc_amt, datetime.now().isoformat()
    except Exception as e:
        logging.error(f"買い注文失敗: {e}")
        return None, 0.0, None

def execute_market_sell(btc_amt: float):
    try:
        if btc_amt < MIN_BTC_ORDER:
            raise RuntimeError(f"売却量不足: {btc_amt}")
        bal = get_btc_balance()
        if bal < btc_amt:
            raise RuntimeError(f"BTC残高不足: {bal}")
        exchange.create_order("BTC/JPY", "market", "sell", btc_amt)
        return True, datetime.now().isoformat()
    except Exception as e:
        logging.error(f"売り注文失敗: {e}")
        return False, None

# === trades.csv 読み込み・初期化 ===
log_file = "trades.csv"
if os.path.exists(log_file):
    trades = pd.read_csv(log_file)
else:
    trades = pd.DataFrame(columns=[
        "id","buy_price","amount","remaining_amount",
        "sold","half_sold","buy_timestamp"
    ])
    # ファイルが存在しない場合は空の DataFrame を作成後、空ファイルとして書き出し
    trades.to_csv(log_file, index=False)

# === メイン処理 ===
print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] buy the dip戦略開始")

jpy_bal = get_jpy_balance()
btc_bal = fetch_btc_price()
fgi = fetch_fgi()
try:
    price = fetch_btc_price()
except:
    print("価格取得失敗で終了")
    exit(1)
print(f"FGI={fgi}, BTC価格={price}円, JPY残高={jpy_bal}, BTC残高={btc_bal}")

# --- 購入 ---
if fgi <= fear_threshold and not already_bought_today(trades):
    hist = fetch_fgi_history(history_days)
    days = calculate_consecutive_fear_days(hist)
    mult = min(fear_multiplier ** (days-1), buy_divisions)
    alloc = initial_cash / buy_divisions * mult
    buy_pr, amt, ts = execute_market_buy(alloc)
    if amt:
        new_row = pd.DataFrame([{
            'id': len(trades),
            'buy_price': price,
            'amount': amt,
            'remaining_amount': amt,
            'sold': False,
            'half_sold': False,
            'buy_timestamp': ts
        }])
        if trades.empty:
            trades = new_row.copy()
        else:
            trades = pd.concat([trades, new_row], ignore_index=True)
        trades.to_csv(log_file, index=False)
        print(f"買い記録: {amt} BTC @ {buy_price}")
    else:
        print("[スキップ] 買い記録なし")
else:
    print("[スキップ] 購入条件未達")

# --- 売却 ---
for i, row in trades.iterrows():
    if row.sold or row.remaining_amount <= 0:
        continue
    ratio = price / row.buy_price
    # 全売却
    if ratio >= sell_full_target:
        order = execute_market_sell(row.remaining_amount)
        if order:
            trades.at[i,'sold'] = True
            trades.at[i,'remaining_amount'] = 0
            trades.to_csv(log_file, index=False)
            print(f"全売却: {row.remaining_amount} BTC @ {price}円")
    # 半分売却
    elif ratio >= sell_half_target and not row.half_sold:
        half = round(row.remaining_amount * 0.5, 8)
        order = execute_market_sell(half)
        if order:
            trades.at[i,'half_sold'] = True
            trades.at[i,'remaining_amount'] = row.remaining_amount-half
            trades.to_csv(log_file, index=False)
            print(f"半分売却 id={row.id} {half} BTC")            

print("完了")
