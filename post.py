import os
import tweepy
from openai import OpenAI
from datetime import datetime

# 日本語投稿用：11アプリ全部
ALL_APPS_JP = [
    {"name": "HACO Pet",          "desc": "ペットの健康記録",       "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO Watch",        "desc": "時計コレクション",       "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACO SUPPLE",       "desc": "サプリ管理",             "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME",      "desc": "香水コレクション",       "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO PLANTS",       "desc": "植物のお世話記録",       "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES",        "desc": "シューズコレクション",   "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO COSME",        "desc": "コスメ管理",             "url": "https://apps.apple.com/jp/app/id6761446178"},
    {"name": "HACOこども健康手帳", "desc": "子どもの健康記録",       "url": "https://apps.apple.com/jp/app/id6761359841"},
    {"name": "HACO WISH",         "desc": "欲しいものリスト",       "url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO LUNCH",        "desc": "お弁当の記録",           "url": "https://apps.apple.com/jp/app/id6761794696"},
    {"name": "HACO FIGURE",       "desc": "フィギュアコレクション", "url": "https://apps.apple.com/jp/app/id6761713093"},
]

# 英語投稿用：HACOこども健康手帳を除いた10アプリ（日本国内専用のため）
ALL_APPS_EN = [
    {"name": "HACO Pet",      "desc": "Pet health tracker",  "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO Watch",    "desc": "Watch collection",    "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACO SUPPLE",   "desc": "Supplement tracker",  "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME",  "desc": "Perfume collection",  "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO PLANTS",   "desc": "Plant care log",      "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES",    "desc": "Shoe collection",     "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO COSME",    "desc": "Cosmetics organizer", "url": "https://apps.apple.com/jp/app/id6761446178"},
    {"name": "HACO WISH",     "desc": "Wishlist with budget","url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO LUNCH",    "desc": "Lunchbox diary",      "url": "https://apps.apple.com/jp/app/id6761794696"},
    {"name": "HACO FIGURE",   "desc": "Figure collection",   "url": "https://apps.apple.com/jp/app/id6761713093"},
]

# 現在のUTC時刻から言語とアプリを決定
# JP: UTC 21,22,23,0,1,2,3,4,5,6,7 の11時間 → 11アプリを1個ずつ
# EN: UTC 8,9,10,11,12,13,14,15,16,17 の10時間 → 10アプリを1個ずつ
# UTC 18,19,20 は投稿なし（穴を作ってIndexErrorを防ぐ）
hour_utc = datetime.utcnow().hour

if hour_utc >= 21:
    is_japanese = True
    app_index = hour_utc - 21          # 21→0, 22→1, 23→2
    app = ALL_APPS_JP[app_index]
elif hour_utc <= 7:
    is_japanese = True
    app_index = hour_utc + 3           # 0→3 ... 7→10
    app = ALL_APPS_JP[app_index]
elif 8 <= hour_utc <= 17:
    is_japanese = False
    app_index = hour_utc - 8           # 8→0 ... 17→9
    app = ALL_APPS_EN[app_index]
else:
    # UTC 18,19,20 は投稿スキップ（安全弁）
    print(f"No post scheduled at UTC {hour_utc}. Skipping.")
    exit(0)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

if is_japanese:
    prompt = f"""
以下のiOSアプリのX投稿文を1つ書いてください。

アプリ名: {app['name']}
概要: {app['desc']}
URL: {app['url']}

【書き方のルール】
- 説明ではなく「感情」に寄せる
- 共感、または所有欲を刺激する
- 4行以内
- 最後に軽く行動を促す（例:「のぞいてみて」「ちょっと試してみて」など押し付けない誘い方）
- 全体で140文字以内（URL込み）
- 絵文字は1〜2個まで
- ハッシュタグは2個（#HACOLABO + アプリのテーマに合った1個）
- URLは末尾
- 投稿文のみ出力（前置きや説明は不要）
"""
else:
    prompt = f"""
Write one X (Twitter) post for the following iOS app.

App: {app['name']}
About: {app['desc']}
URL: {app['url']}

【Writing rules】
- Lead with emotion, not description
- Spark empathy or the joy of collecting/owning
- Maximum 4 lines
- End with a soft call to action (e.g. "take a peek", "give it a try" — never pushy)
- Within 200 characters total (including URL)
- 1–2 emojis maximum
- 2 hashtags (#HACOLABO + 1 relevant to the app's theme)
- URL at the end
- Output the post text only (no preamble)
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=400,
)
tweet_text = response.choices[0].message.content.strip()

x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)
x_client.create_tweet(text=tweet_text)

lang = "JA" if is_japanese else "EN"
print(f"投稿完了 [{lang}] {app['name']} (index={app_index}): {tweet_text}")
