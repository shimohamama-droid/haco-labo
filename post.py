import os
import tweepy
from openai import OpenAI
from datetime import datetime

ALL_APPS = [
    {"name": "HACO PLANTS", "desc": "植物管理アプリ", "desc_en": "Plant collection manager", "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES", "desc": "靴コレクション管理", "desc_en": "Shoe collection manager", "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO Pet", "desc": "ペット管理アプリ", "desc_en": "Pet management app", "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO SUPPLE", "desc": "サプリ管理アプリ", "desc_en": "Supplement tracker", "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME", "desc": "香水コレクション管理", "desc_en": "Perfume collection manager", "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO Watch", "desc": "時計コレクション管理", "desc_en": "Watch collection manager", "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACOこども健康手帳", "desc": "子どもの健康記録アプリ", "desc_en": None, "url": "https://apps.apple.com/jp/app/id6761359841"},
    {"name": "HACO WISH", "desc": "欲しいもの管理アプリ", "desc_en": "Wishlist manager", "url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO FIGURE", "desc": "フィギュアコレクション管理", "desc_en": "Figure collection manager", "url": "https://apps.apple.com/jp/app/id6761713093"},
    {"name": "HACO COSME", "desc": "コスメ管理アプリ", "desc_en": "Cosmetics manager", "url": "https://apps.apple.com/jp/app/id6761446178"},
]

JA_APPS = ALL_APPS  # 全10アプリ日本語投稿
EN_APPS = [a for a in ALL_APPS if a["desc_en"] is not None]  # 9アプリ英語投稿

hour_utc = datetime.utcnow().hour

if 21 <= hour_utc or hour_utc < 7:
    is_japanese = True
    app_index = (hour_utc - 21) % len(JA_APPS) if hour_utc >= 21 else (hour_utc + 3) % len(JA_APPS)
    app = JA_APPS[app_index]
else:
    is_japanese = False
    app_index = (hour_utc - 7) % len(EN_APPS)
    app = EN_APPS[app_index]

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

if is_japanese:
    prompt = f"""
以下のiOSアプリのX投稿文を1つ書いてください。

アプリ名: {app['name']}
アプリ概要: {app['desc']}
URL: {app['url']}

条件:
- 全体で110文字以内
- 絵文字を1〜2個使う
- ハッシュタグを2個（#HACOLABO とアプリ関連1個）
- URLを末尾に
- 共感できる自然な日本語で
- 投稿文のみ出力すること
"""
else:
    prompt = f"""
Write one X (Twitter) post for the following iOS app.

App name: {app['name']}
Description: {app['desc_en']}
URL: {app['url']}

Rules:
- Within 110 characters total
- 1-2 emojis
- 2 hashtags (#HACOLABO + 1 relevant tag)
- URL at the end
- Natural, relatable tone (not salesy)
- In English
- Output the post text only
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
print(f"投稿完了: {tweet_text}")
