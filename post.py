import os
import json
import tweepy
import anthropic
from datetime import datetime

# アプリリスト
APPS = [
    {"name": "HACO PLANTS", "desc": "植物管理アプリ", "desc_en": "Plant collection manager", "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES", "desc": "靴コレクション管理", "desc_en": "Shoe collection manager", "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO Pet", "desc": "ペット管理アプリ", "desc_en": "Pet management app", "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO SUPPLE", "desc": "サプリ管理アプリ", "desc_en": "Supplement tracker", "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME", "desc": "香水コレクション管理", "desc_en": "Perfume collection manager", "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO Watch", "desc": "時計コレクション管理", "desc_en": "Watch collection manager", "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACOこども健康手帳", "desc": "子どもの健康記録アプリ", "desc_en": "Kids health record app", "url": "https://apps.apple.com/jp/app/id6761359841"},
    {"name": "HACO WISH", "desc": "欲しいもの管理アプリ", "desc_en": "Wishlist manager", "url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO FIGURE", "desc": "フィギュアコレクション管理", "desc_en": "Figure collection manager", "url": "https://apps.apple.com/jp/app/id6761713093"},
    {"name": "HACO COSME", "desc": "コスメ管理アプリ", "desc_en": "Cosmetics manager", "url": "https://apps.apple.com/jp/app/id6761446178"},
]

day_index = datetime.now().day % len(APPS)
app = APPS[day_index]

hour = datetime.utcnow().hour
is_morning = hour < 6  # UTC 0時 = JST 9時

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

if is_morning:
    # 朝：日本語投稿
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
"""
else:
    # 夜：英語投稿
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
"""

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    messages=[{"role": "user", "content": prompt}]
)

tweet_text = message.content[0].text.strip()

x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)

x_client.create_tweet(text=tweet_text)
print(f"投稿完了: {tweet_text}")
