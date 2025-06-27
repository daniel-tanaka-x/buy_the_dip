# Buy The Dip

恐怖・強欲指数に基づいた暗号通貨の自動取引ツール

## 実行環境

Python 3.13.1で実行

## セットアップ手順

リポジトリをクローンします：
```bash
git clone https://github.com/daniel-tanaka-x/buy_the_dip.git
```

プロジェクトディレクトリに移動します：
```bash
cd buy_the_dip
```

仮想環境を作成します：
```bash
python3 -m venv venv
```

仮想環境を有効化します：
```bash
source venv/bin/activate
```

pipをアップグレードします：
```bash
pip install --upgrade pip
```

必要なパッケージをインストールします：
```bash
pip install -r requirements.txt
```

## API設定

CoincheckのAPIキーとシークレットを環境変数に設定します：
```bash
echo 'export COINCHECK_API_KEY="Your API Key"' >> ~/.zshrc
```

```bash
echo 'export COINCHECK_API_SECRET="Your API Secret"' >> ~/.zshrc
```

設定を反映させます：
```bash
source ~/.zshrc
```

APIキーが正しく設定されているか確認します：
```bash
echo $COINCHECK_API_KEY
```

APIシークレットが正しく設定されているか確認します：
```bash
echo $COINCHECK_API_SECRET
```

## 使用方法

恐怖・強欲指数を取得します：
```bash
python3 fetch_fgi.py
```

Coincheckの残高を確認します：
```bash
python3 fetch_cc_balance.py
```

成行買い注文を出します：
```bash
python3 place_market_buy_order.py
```

メインの自動取引プログラムを実行します：
```bash
python3 main.py
```

## ログと取引履歴

エラーログを確認します：
```bash
cat error.log
```

取引履歴を確認します：
```bash
cat trades.csv
```

## 自動実行の設定

### Cronジョブの設定

Cronジョブを設定します：
```bash
crontab -e
```

以下のテキストデータをコピーペーストして、毎日午後3時にスクリプトを自動実行します：
```bash
0 15 * * * cd /Users/daniel-tanaka-x/buy_the_dip && /Users/daniel-tanaka-x/buy_the_dip/venv/bin/python3 main.py >> /Users/daniel-tanaka-x/buy_the_dip/logs/main.log 2>&1
```
ただしユーザー名は自分のPCのユーザー名に書き換える必要があります。

cronを保存するためには、:wq を入力したあとにEnterキーを押します。

```bash
:wq 
```

## スクリプト説明

- [`fetch_fgi.py`](fetch_fgi.py) - 暗号通貨市場の恐怖・強欲指数を取得します
- [`fetch_cc_balance.py`](fetch_cc_balance.py) - Coincheckアカウントの残高を確認します
- [`place_market_buy_order.py`](place_market_buy_order.py) - 成行買い注文を出します
- [`main.py`](main.py) - 恐怖・強欲指数に基づいて自動的に取引を行うメインプログラムです
