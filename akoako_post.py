import os
import tweepy
from openai import OpenAI
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
day = now_jst.day
mode = os.environ.get("AKOAKO_MODE", "normal")  # "normal" or "point_day"

SLING_URL = "https://item.rakuten.co.jp/akoakostudio/sijira03/"
CAPE_URL  = "https://item.rakuten.co.jp/akoakostudio/ke-pu/"

PRODUCTS = {
    "sling": {
        "name": "シジラ織りスリング",
        "desc": "赤ちゃんを抱っこしながら両手が使える、ママに寄り添うスリング。",
        "url": SLING_URL,
    },
    "cape": {
        "name": "授乳ケープ",
        "desc": "外出先でもさっと使える、授乳をもっと気楽にしてくれるケープ。",
        "url": CAPE_URL,
    },
}

if mode == "point_day":
    product = PRODUCTS["sling"]
    point_day = True
else:
    # 奇数日→スリング、偶数日→ケープ
    product = PRODUCTS["sling"] if day % 2 == 1 else PRODUCTS["cape"]
    point_day = False

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

if point_day:
    prompt = f"""
以下の商品について、楽天ポイントDayを告知するX投稿文を1つ書いてください。

商品名: {product['name']}
URL: {product['url']}

【書き方のルール】
- 「本日、楽天ポイントDay！」を自然に入れる（何倍かは書かない）
- 買い時感・お得感を感情で伝える
- 4行以内
- 最後に楽天へ誘導（押し付けない）
- 全体で140文字以内（URL込み）
- 絵文字は1〜2個まで
- ハッシュタグは2個（#AKOAKO + #楽天ポイント）
- URLは末尾
- 投稿文のみ出力（前置き不要）
"""
else:
    prompt = f"""
以下の商品についてX投稿文を1つ書いてください。

商品名: {product['name']}
説明: {product['desc']}
URL: {product['url']}

【書き方のルール】
- 説明ではなく「感情」に寄せる（共感・育児の大変さ・解放感など）
- 4行以内
- 最後に楽天へ軽く誘導（例:「のぞいてみて」など押し付けない誘い方）
- 全体で140文字以内（URL込み）
- 絵文字は1〜2個まで
- ハッシュタグは2個（#AKOAKO + 商品テーマに合った1個）
- URLは末尾
- 投稿文のみ出力（前置き不要）
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=300,
)
tweet_text = response.choices[0].message.content.strip()

x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)
x_client.create_tweet(text=tweet_text)

label = "ポイントDay" if point_day else product['name']
print(f"投稿完了 [{label}]: {tweet_text}")
