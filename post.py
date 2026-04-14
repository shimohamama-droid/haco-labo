import os
import tweepy
from openai import OpenAI
from datetime import datetime

# 日本語投稿用：全アプリ（こども健康手帳含む）
ALL_APPS_JP = [
    {"name": "HACO Pet",          "desc": "ペットの健康記録",     "url": "https://apps.apple.com/jp/app/id6761163943"},
    {"name": "HACO Watch",        "desc": "時計コレクション",     "url": "https://apps.apple.com/jp/app/id6761672859"},
    {"name": "HACO SUPPLE",       "desc": "サプリ管理",           "url": "https://apps.apple.com/jp/app/id6761284730"},
    {"name": "HACO PERFUME",      "desc": "香水コレクション",     "url": "https://apps.apple.com/jp/app/id6760983145"},
    {"name": "HACO PLANTS",       "desc": "植物のお世話記録",     "url": "https://apps.apple.com/jp/app/id6761411222"},
    {"name": "HACO SHOES",        "desc": "シューズコレクション", "url": "https://apps.apple.com/jp/app/id6761321216"},
    {"name": "HACO COSME",        "desc": "コスメ管理",           "url": "https://apps.apple.com/jp/app/id6761446178"},
    {"name": "HACO WISH",         "desc": "欲しいものリスト",     "url": "https://apps.apple.com/jp/app/id6761754227"},
    {"name": "HACO LUNCH",        "desc": "お弁当記録",           "url": "https://apps.apple.com/jp/app/id6761794696"},
    {"name": "HACO FIGURE",       "desc": "フィギュアコレクション","url": "https://apps.apple.com/jp/app/id6761713093"},
    {"name": "HACOこども健康手帳", "desc": "子どもの健康記録",     "url": "https://apps.apple.com/jp/app/id6761359841"},
    {"name": "HACO HOME",         "desc": "家のメンテナンス記録", "url": "https://apps.apple.com/jp/app/id6761870347"},
    {"name": "HACO Side Money",   "desc": "副業収入の記録",       "url": "https://apps.apple.com/jp/app/id6760634061"},
    {"name": "HACO LOG",          "desc": "映画ドラマ記録",       "url": "https://apps.apple.com/jp/app/id6761961898"},
    {"name": "HACO CARD",         "desc": "カードコレクション",   "url": "https://apps.apple.com/jp/app/id6761989730"},
    {"name": "HACO My Shelf",     "desc": "本棚管理",             "url": "https://apps.apple.com/jp/app/id6762028730"},
    {"name": "HACO ACCESSORY",    "desc": "アクセサリー管理",     "url": "https://apps.apple.com/jp/app/id6761980946"},
    {"name": "HACO MIND",         "desc": "アイデア・思考メモ",   "url": "https://apps.apple.com/jp/app/id6761976675"},
    {"name": "HACO DESDAY",       "desc": "資産の生存確認メーター","url": "https://apps.apple.com/jp/app/id6762077816"},
    {"name": "HACO DANSHARI",     "desc": "断捨離記録",           "url": "https://apps.apple.com/jp/app/id6762079882"},
]

# 日本語ローテーション設定
JP_ROTATE_A = ALL_APPS_JP[0:5]   # Pet, Watch, SUPPLE, PERFUME, PLANTS
JP_ROTATE_B = ALL_APPS_JP[5:10]  # SHOES, COSME, WISH, LUNCH, FIGURE
JP_KENKO     = ALL_APPS_JP[10]   # こども健康手帳

# 英語投稿用：全アプリ（Side Money, LOG, CARD以降含む）
ALL_APPS_EN = [
    {"name": "HACO Pet",        "desc": "Pet health tracker",        "url": "https://apps.apple.com/app/id6761163943"},
    {"name": "HACO Watch",      "desc": "Watch collection",          "url": "https://apps.apple.com/app/id6761672859"},
    {"name": "HACO SUPPLE",     "desc": "Supplement tracker",        "url": "https://apps.apple.com/app/id6761284730"},
    {"name": "HACO PERFUME",    "desc": "Perfume collection",        "url": "https://apps.apple.com/app/id6760983145"},
    {"name": "HACO PLANTS",     "desc": "Plant care log",            "url": "https://apps.apple.com/app/id6761411222"},
    {"name": "HACO SHOES",      "desc": "Shoe collection",           "url": "https://apps.apple.com/app/id6761321216"},
    {"name": "HACO COSME",      "desc": "Cosmetics organizer",       "url": "https://apps.apple.com/app/id6761446178"},
    {"name": "HACO WISH",       "desc": "Wishlist with budget",      "url": "https://apps.apple.com/app/id6761754227"},
    {"name": "HACO LUNCH",      "desc": "Lunchbox diary",            "url": "https://apps.apple.com/app/id6761794696"},
    {"name": "HACO FIGURE",     "desc": "Figure collection",         "url": "https://apps.apple.com/app/id6761713093"},
    {"name": "HACO HOME",       "desc": "Home maintenance log",      "url": "https://apps.apple.com/app/id6761870347"},
    {"name": "HACO Side Money", "desc": "Side income tracker",       "url": "https://apps.apple.com/app/id6760634061"},
    {"name": "HACO LOG",        "desc": "Movie & drama log",         "url": "https://apps.apple.com/app/id6761961898"},
    {"name": "HACO CARD",       "desc": "Card collection",           "url": "https://apps.apple.com/app/id6761989730"},
    {"name": "HACO My Shelf",   "desc": "My shelf & book tracker",   "url": "https://apps.apple.com/app/id6762028730"},
    {"name": "HACO ACCESSORY",  "desc": "Accessories organizer",     "url": "https://apps.apple.com/app/id6761980946"},
    {"name": "HACO MIND",       "desc": "Idea & thought notes",      "url": "https://apps.apple.com/app/id6761976675"},
    {"name": "HACO DESDAY",     "desc": "Asset survival meter",      "url": "https://apps.apple.com/app/id6762077816"},
    {"name": "HACO DANSHARI",   "desc": "Declutter tracker",         "url": "https://apps.apple.com/app/id6762079882"},
]

# UTC時刻から投稿アプリを決定
# JP: UTC 22,23,0,1,2,3 の6時間 = 6アプリ（こども健康手帳は毎日+ローテ5個）
# EN: UTC 4,5,6,7,8,9,10,11,12,13,14,15 の12時間 = 12アプリを1個ずつ
now = datetime.utcnow()
hour_utc = now.hour

if hour_utc == 22:
    # JST 7:00, 8:00 (UTC 22, 23)
    is_japanese = True
    jp_slot = hour_utc - 22  # 0 or 1
elif hour_utc <= 3:
    # JST 9:00-13:00 (UTC 0, 1, 2, 3)
    is_japanese = True
    jp_slot = hour_utc + 2  # 2, 3, 4, 5
elif 4 <= hour_utc <= 15:
    # JST 13:00-24:00 (UTC 4-15)
    is_japanese = False
    app_index = hour_utc - 4  # 0-11
    app = ALL_APPS_EN[app_index % len(ALL_APPS_EN)]
else:
    # UTC 16-21 は投稿スキップ (夕)
    print(f"No post scheduled at UTC {hour_utc}. Skipping.")
    exit(0)

# JPの場合: slot 0 はこども健康手帳固定、slot 1-5 は日毎で前半/後半ローテ
if is_japanese:
    if jp_slot == 0:
        app = JP_KENKO
    else:
        # 日付の偶数/奇数で前半5個・後半5個を切替
        day = now.day
        rotate = JP_ROTATE_A if day % 2 == 0 else JP_ROTATE_B
        app = rotate[jp_slot - 1]  # slot 1-5 → index 0-4

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

if is_japanese:
    prompt = f"""
以下のiOSアプリの投稿文を1つ書いてください。

アプリ名：{app['name']}
概要：{app['desc']}
URL：{app['url']}

【書き方のルール】
- 説明ではなく「行動」を想像する
- 共感、または生活充実感を刺激する
- 4行以内
- 最後に締める行動を促す（例：「のぞいてみて」「ちょっと試してみて」など押し付けない優しい声）
- 絵文字は1〜2個まで
- 総文字数は140文字まで（URL込み）
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

[Writing rules]
- Lead with emotion, not description
- Spark empathy or the joy of collecting/owning
- Maximum 4 lines
- End with a soft call to action (e.g. "take a peek", "give it a try" - never pushy)
- Within 200 characters total (including URL)
- 1-2 emojis maximum
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
print(f"投稿完了 [{lang}] {app['name']}: {tweet_text}")
