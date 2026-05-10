"""
claude_generator.py
Claude API を使ったテキスト生成モジュール
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートの .env を読み込む（.env の値で環境変数を上書き）
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

try:
    import anthropic
except ImportError as e:
    raise ImportError("anthropic パッケージが未インストールです。pip install anthropic>=0.40 を実行してください。") from e

_MODEL = "claude-sonnet-4-20250514"

# ------------------------------------------------------------------ #
#  システムプロンプト定義
# ------------------------------------------------------------------ #

_BRAND_RULES = {
    "AKOAKO": """
あなたは AKOAKO ブランドの SNS 担当者です。以下のブランド情報を必ず守って投稿文を作成してください。

【ブランド基本情報】
- ブランド歴 23 年、楽天出店 17 年、レビュー累計 10,000 件以上
- 「授乳ケープ」という商品カテゴリ名を日本で最初に命名したブランド
- AKOAKO はスリングブランドである

【主力商品コピー】
Sシリーズ（抱っこ紐）
  メイン: 赤ちゃんの体重が、半分になる抱っこ紐。
  サブ:   100g / 忘れる、抱っこ紐

授乳ケープ
  メイン: いつでもどこでも、My授乳室。
  サブ:   持ち運べる、授乳室。

【ハッシュタグルール（必ず守ること）】
◆ブランド系（必須・必ず両方含める）:
  #ベビースリング #スリング
  ※ AKOAKO はスリングブランドなので、この2つは絶対に外さないこと。

◆お悩み系（テーマや文脈に応じて 1〜3 個選ぶ。新規ママ層への検索リーチ用）:
  #新生児 #抱っこ #泣き続け #寝ない #抱っこ紐 #授乳ケープ #ママの味方
  ※ 文脈に合うものを積極的に選ぶこと（例: 軽さ訴求なら #新生児 #抱っこ がフィット）
""",
    "HACO_LABO": """
あなたは HACO LABO の SNS 担当者です。以下のブランド情報を必ず守って投稿文を作成してください。

【ブランド基本情報】
- 個人開発で 20 本の iOS アプリをリリース（本数のみ記載。内訳の詳細は書かない）
- AKOAKO ブランドや授乳ケープ命名の話は一切含めないこと（別ブランド扱い）

【ハッシュタグルール】
◆必須（必ず両方含める）: #個人開発 #iOSアプリ
◆推奨（1〜2 個選ぶ）: #HACOLABO #暮らしを整える
""",
}

_SNS_RULES = {
    "X": """
【X (Twitter) 投稿ルール — 厳守事項】
- 文字数: 絶対に 140 字以内（本文＋ハッシュタグ＋URL すべて含む）
  ※ 140 字を超えたら必ず自分で削って再構成すること。超過は投稿エラーになる。
  ※ URL は 23 字として計算すること（Twitter の t.co 短縮後）
- 構成: フック（1文）→ 本文 → ハッシュタグ → URL
- フックは読者が思わず続きを読みたくなる 1 文にすること
- 「便利！」「すごい！」のような押し付けがましい表現は避ける
- 投稿文のみ出力すること（前置き・後書き・説明文は一切不要）
""",
    "note": """
【note 記事ルール】
- 文字数: 1,500〜3,000 字
- 見出し (H2) を 3〜5 個使う
- 冒頭は挨拶なし、フックから始める
- 本文は読みやすい段落構成にすること
""",
    "Threads": """
【Threads 投稿ルール】
- 3 投稿構成 (本投稿 + リプ 1 + リプ 2)
- 各投稿 500 字以内
- 投稿の区切り文字は「---NEXT---」(前後に空行)
- 本投稿でフック、リプで詳細・CTAを展開
""",
    "TikTok": """
【TikTok 台本ルール】
- 動画長: 15〜30 秒を想定
- 出力形式:
  【テロップ案】全角 8 字以内のキャッチフレーズ (3〜5 枚分)
  【ナレーション】実際に読み上げるセリフ
  【キャプション】投稿説明文 80 字以内 (ハッシュタグ含む)
""",
}


def get_system_prompt(sheet_name: str, sns_name: str) -> str:
    """
    シート名 × SNS 名に応じたシステムプロンプトを返す。

    Parameters
    ----------
    sheet_name : str
        "AKOAKO" or "HACO_LABO"
    sns_name : str
        "X" / "note" / "Threads" / "TikTok"

    Returns
    -------
    str
        組み合わせたシステムプロンプト文字列
    """
    brand = _BRAND_RULES.get(sheet_name)
    if brand is None:
        raise ValueError(f"未対応のシート名: {sheet_name}。対応: {list(_BRAND_RULES)}")
    sns = _SNS_RULES.get(sns_name)
    if sns is None:
        raise ValueError(f"未対応の SNS: {sns_name}。対応: {list(_SNS_RULES)}")
    return brand.strip() + "\n\n" + sns.strip()


def generate(prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
    """
    Claude API を呼び出してテキストを生成する。

    Parameters
    ----------
    prompt : str
        ユーザーへのプロンプト
    system : str, optional
        システムプロンプト。省略時は汎用プロンプト
    max_tokens : int
        最大トークン数 (デフォルト 1024)

    Returns
    -------
    str
        生成されたテキスト
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY が設定されていません。\n"
            "  1) ~/.zshrc に export ANTHROPIC_API_KEY=sk-ant-... を追記するか\n"
            "  2) ~/Desktop/sns-auto/.env に ANTHROPIC_API_KEY=sk-ant-... を記入してください。"
        )

    client = anthropic.Anthropic(api_key=api_key)

    kwargs = {
        "model": _MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    message = client.messages.create(**kwargs)
    return message.content[0].text
