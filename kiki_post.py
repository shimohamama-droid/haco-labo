import os
import tweepy

# 環境変数からXのAPIキーを取得
API_KEY = os.environ["X_API_KEY"]
API_SECRET = os.environ["X_API_SECRET"]
ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["X_ACCESS_SECRET"]

# 投稿文（固定）
TWEET_TEXT = """何から動けばいいかわからない時って、
能力不足じゃなくて「整理不足」なことが多いです。

モヤモヤを言語化すると、
次にやることが見えてきます。

思考整理サポートはこちら👇
https://coconala.com/services/4177005"""


def main():
    # Tweepy v2クライアントで認証
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,
    )

    # 投稿
    response = client.create_tweet(text=TWEET_TEXT)
    print(f"✅ 投稿成功: tweet_id = {response.data['id']}")


if __name__ == "__main__":
    main()
