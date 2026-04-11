import os
import tweepy
from openai import OpenAI
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
day = now_jst.day
mode = os.environ.get("AKOAKO_MODE", "normal")

SLING_URL = "https://item.rakuten.co.jp/akoakostudio/sijira03/"
CAPE_URL  = "https://item.rakuten.co.jp/akoakostudio/ke-pu/"

PRODUCTS = {
    "sling": {
        "name": "日本製AKOAKOスリング",
        "desc": "赤ちゃんを抱っこしながら両手が使える、ママに寄り添うスリング。",
        "url": SLING_URL,
        "reviews": [
            "まさに魔法の袋！",
            "これがないと外出できない",
            "泣き止まなかった子がすぐ寝た",
            "片手が使えるだけで全然違う",
            "日本製で安心感が違う",
            "装着が簡単で毎日使ってる",
            "新生児から使えてコスパ最高",
        ],
        "hashtags": "#抱っこ紐 #新生児 #日本製 #スリング #育児グッズ",
    },
    "cape": {
        "name": "授乳ケープ",
        "desc": "外出先でもさっと使える、授乳をもっと気楽にしてくれるケープ。",
        "url": CAPE_URL,
        "reviews": [
            "外出が怖くなくなった",
            "さっとかぶれるのが最高",
            "日本製だから生地が全然違う",
            "授乳期の必需品すぎる",
            "おしゃれなのに実用的",
            "ワンオペの味方すぎる",
            "これで外出のハードルが下がった",
        ],
        "hashtags": "#授乳ケープ #新生児 #日本製 #授乳中 #育児グッズ",
    },
}

if mode == "point_day":
    product = PRODUCTS["sling"]
    point_day = True
else:
    product = PRODUCTS["sling"] if day % 2 == 1 else PRODUCTS["cape"]
    point_day = False

import random
review_sample = random.sample(product["reviews"], 2)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

if point_day:
    prompt = f"""
以下の商品について、楽天ポイントDayを告知するX投稿文を1つ書いてください。

商品名: {product['name']}
URL: {product['url']}
実際のレビューの声（参考にして）: {review_sample}

【書き方のルール】
- 「本日、楽天ポイントDay！」を冒頭か自然な流れで入れる（何倍かは書かない）
- レビューの言葉をそのまま or アレンジして使う
- 買い時感・お得感を感情で伝える
- 押し付けない楽天への誘導で締める
- ハッシュタグは末尾: {product['hashtags']}
- URLは末尾
- 投稿文のみ出力（前置き不要）
"""
else:
    prompt = f"""
以下の商品についてX投稿文を1つ書いてください。

商品名: {product['name']}
説明: {product['desc']}
URL: {product['url']}
実際のレビューの声（参考にして）: {review_sample}

【書き方のルール】
- レビューの言葉をそのまま or アレンジして共感を呼ぶ
- 育児の大変さ・解放感・安心感など感情に寄せる
- 説明文にならないようにする
- 押し付けない楽天への誘導で締める（「のぞいてみて」など）
- ハッシュタグは末尾: {product['hashtags']}
- URLは末尾
- 投稿文のみ出力（前置き不要）
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=600,
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
