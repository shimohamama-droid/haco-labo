import os
import tweepy
import random
from openai import OpenAI
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)

HP_URL = "https://haco-labo.netlify.app"

# ====================================================================
# 投稿の切り口バリエーション
# 毎日ランダムに1つ選んで、その切り口でHPを紹介する投稿を生成
# ====================================================================
ANGLES = [
    {
        "theme": "ブランド全体の紹介",
        "context": "HACO LABOは小さくて、ていねいで、暮らしに寄り添うiPhoneアプリのブランド。コンセプトは「小さな道具を、たくさん作る場所」。"
    },
    {
        "theme": "暮らしの道具に焦点",
        "context": "暮らしの道具として17本のアプリがある。Pet、Watch、SUPPLE、PERFUME、PLANTS、SHOES、こども健康手帳、FIGURE、WISH、COSME、LUNCH、HOME、LOG、CARD、My Shelf、ACCESSORY、DANSHARI。毎日の小さな記録と、ちょっとの便利。"
    },
    {
        "theme": "コレクション系アプリの提案",
        "context": "好きなものを集めている人へ。HACO LABOには Watch、PERFUME、SHOES、FIGURE、COSME、ACCESSORY、My Shelf など、コレクションをきれいに整理できるアプリがある。"
    },
    {
        "theme": "毎日の記録系アプリの提案",
        "context": "暮らしの中の小さなことを残したい人へ。Pet、PLANTS、LUNCH、こども健康手帳、HOME、LOG、MIND など、日々の記録を支えるアプリがある。"
    },
    {
        "theme": "心の道具に焦点",
        "context": "考えごとや自分との対話に。MIND（思考の記録）、DESDAY（餓死回避メーター=おまもり計算機）、KIKI（モヤモヤを言葉にする場所）。"
    },
    {
        "theme": "お金まわりの道具",
        "context": "Side Money は副業収入を記録するアプリ。WISH は欲しいものリストと貯金シミュレーターつき。お金まわりの小さな台帳。"
    },
    {
        "theme": "ものを手放す人へ",
        "context": "DANSHARI は手放したものを記録するアプリ。捨てた理由、もう一度買いたいかをメモできる。ミニマルな暮らしの相棒。"
    },
    {
        "theme": "新作・最近の話",
        "context": "HACO LABOは小さなアプリをたくさん作っている。シンプルで、邪魔にならず、ずっと使える道具。HPですべて見られる。"
    },
    {
        "theme": "デザイン哲学",
        "context": "HACO LABOのアプリはどれもミニマル。背景は柔らかい灰色、文字は控えめ、操作はシンプル。日々の道具として静かに寄り添う。"
    },
    {
        "theme": "ユーザーの使い方提案",
        "context": "HACO LABOのアプリは、写真を撮って、メモを残して、ときどき見返す。それだけで日常がほんの少し整う。"
    },
]

angle = random.choice(ANGLES)

prompt = f"""
HACO LABOというiPhoneアプリのブランドを紹介するX投稿文を1つ書いてください。

【今日の切り口】
テーマ: {angle['theme']}
背景情報: {angle['context']}

【誘導先】
HP URL: {HP_URL}

【書き方のルール】
- 控えめで穏やかな文体
- 「便利!」「すごい!」のような押し付けがましい表現は使わない
- 派手な宣伝・煽り文句は使わない
- HACO LABOらしい世界観(小さくて、ていねいで、暮らしに寄り添う感じ)
- 投稿文の長さは120〜180字程度
- ハッシュタグは末尾に2〜4個: #HACOLABO #iPhoneアプリ など、テーマに合うものを選ぶ
- URLは末尾に入れる
- 投稿文のみ出力(前置き・後書き不要)
"""

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=600,
)
tweet_text = response.choices[0].message.content.strip()

# ====================================================================
# X 投稿
# ====================================================================
x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)
x_client.create_tweet(text=tweet_text)

print(f"投稿完了 [{angle['theme']}]: {tweet_text}")
