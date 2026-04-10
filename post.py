import os
import tweepy
from openai import OpenAI
from datetime import datetime

# 配信中の11アプリ（順番固定。日英ともに同じ順番でローテ）
ALL_APPS = [
    {"name": "HACO Pet",         "desc": "ペットの健康記録",         "desc_en": "Pet health tracker",        "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO Watch",       "desc": "時計コレクション",         "desc_en": "Watch collection",          "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACO SUPPLE",      "desc": "サプリ管理",               "desc_en": "Supplement tracker",        "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME",     "desc": "香水コレクション",         "desc_en": "Perfume collection",        "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO PLANTS",      "desc": "植物のお世話記録",         "desc_en": "Plant care log",            "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES",       "desc": "シューズコレクション",     "desc_en": "Shoe collection",           "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO COSME",       "desc": "コスメ管理",               "desc_en": "Cosmetics organizer",       "url": "https://apps.apple.com/jp/app/id6761446178"},
    {"name": "HACOこども健康手帳", "desc": "子どもの健康記録",         "desc_en": "Kids health record",        "url": "https://apps.apple.com/jp/app/id6761359841"},
    {"name": "HACO WISH",        "desc": "欲しいものリスト",         "desc_en": "Wishlist with budget",      "url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO LUNCH",       "desc": "お弁当の記録",             "desc_en": "Lunchbox diary",            "url": "https://apps.apple.com/jp/app/id6761794696"},
    {"name": "HACO FIGURE",      "desc": "フィギュアコレクション",   "desc_en": "Figure collection",         "url": "https://apps.apple.com/jp/app/id6761713093"},
]

# 現在のUTC時刻からアプリと言語を決定
hour_utc = datetime.utcnow().hour

# 日本語: UTC 21,22,23,0,1,2,3,4,5,6,7  → index 0〜10
# 英語  : UTC 8,9,10,11,12,13,14,15,16,17,18 → index 0〜10
if hour_utc >= 21:
    is_japanese = True
    app_index = hour_utc - 21          # 21→0, 22→1, 23→2
elif hour_utc <= 7:
    is_japanese = True
    app_index = hour_utc + 3           # 0→3, 1→4 ... 7→10
else:
    is_japanese = False
    app_index = hour_utc - 8           # 8→0, 9→1 ... 18→10

app = ALL_APPS[app_index]

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
About: {app['desc_en']}
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
