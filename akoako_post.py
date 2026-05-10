"""
akoako_post.py
AKOAKO_HACO_SNS投稿台帳.xlsx の AKOAKO シートを起点に X (Twitter) へ自動投稿。

GitHub Actions で実行される。
  - Actions Secrets から認証情報を読む (X_API_KEY 等 + ANTHROPIC_API_KEY)
  - posted_log.json で重複投稿を防ぐ（ワークフローがコミットして永続化）

使い方（workflow_dispatch から）:
  --dry-run  投稿せず文章確認のみ
  --date     YYYY-MM-DD で対象日付指定（省略時は今日）
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from lib.excel_reader import read_today_rows
from lib.claude_generator import generate, get_system_prompt
from lib.url_fetcher import fetch_clean_text

LOG_PATH = ROOT / "posted_log.json"
X_CHAR_LIMIT = 140
URL_CHAR_COUNT = 23   # Twitter の t.co 短縮後の固定文字数
BODY_LIMIT = X_CHAR_LIMIT - URL_CHAR_COUNT - 1  # 本文+ハッシュタグの上限 (116字)

OMADANI_TAGS = [
    "#新生児", "#抱っこ", "#泣き続け", "#寝ない",
    "#抱っこ紐", "#授乳ケープ", "#ママの味方",
]


# ------------------------------------------------------------------ #
#  posted_log.json
# ------------------------------------------------------------------ #

def _load_log() -> list:
    if not LOG_PATH.exists():
        return []
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_log(log: list) -> None:
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_posted(log: list, sheet_name: str, row_num: int) -> bool:
    return any(
        e.get("sheet") == sheet_name and e.get("row_num") == row_num
        for e in log
    )


def _append_log(log: list, sheet_name: str, row_num: int, tweet_id: str) -> None:
    log.append({
        "sheet": sheet_name,
        "row_num": row_num,
        "posted_at": datetime.now().isoformat(),
        "tweet_id": tweet_id,
    })


# ------------------------------------------------------------------ #
#  X クライアント初期化
# ------------------------------------------------------------------ #

def _init_x_client():
    try:
        import tweepy
    except ImportError:
        print("[ERROR] tweepy が未インストールです。pip install tweepy を実行してください。")
        sys.exit(1)

    keys = {
        "consumer_key":        os.environ.get("X_API_KEY", "").strip(),
        "consumer_secret":     os.environ.get("X_API_SECRET", "").strip(),
        "access_token":        os.environ.get("X_ACCESS_TOKEN", "").strip(),
        "access_token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip(),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print("[ERROR] X API Secrets が設定されていません:", missing)
        print("        GitHub リポジトリの Settings → Secrets に以下を登録してください:")
        for k in missing:
            print(f"          {k.upper().replace('consumer_key', 'X_API_KEY')}")
        sys.exit(1)

    return tweepy.Client(**keys)


# ------------------------------------------------------------------ #
#  テキスト生成（リトライ + 自動トリム付き）
# ------------------------------------------------------------------ #

def _build_prompt(row: dict, page_text: str) -> str:
    ref_url = row.get("参照URL") or ""
    url_note = (
        f"※ URL ({ref_url}) は末尾に別途付けます。あなたが書くのは「本文＋ハッシュタグ」のみ。\n"
        f"  本文＋ハッシュタグは {BODY_LIMIT} 字以内（= 140 - 23[URL換算] - 1[改行]）に収めること。\n"
    ) if ref_url else f"  本文＋ハッシュタグは {X_CHAR_LIMIT} 字以内にすること。\n"

    url_context = f"\n\n【参照ページ本文（抜粋）】\n{page_text[:800]}" if page_text else ""

    return (
        f"テーマ: {row['テーマ']}\n"
        f"参照URL: {ref_url or 'なし'}\n"
        f"メモ: {row.get('メモ') or 'なし'}"
        f"{url_context}\n\n"
        "【文字数ルール（最重要）】\n"
        f"{url_note}"
        "  超えた場合は本文を削って収めること。\n\n"
        "上記の情報をもとに X (Twitter) 投稿文（本文＋ハッシュタグのみ）を作成してください。\n"
        "URL は書かないこと。前置き・説明文は不要。投稿文のみ出力。"
    )


def _trim_to_limit(text: str) -> str:
    """最終手段: 機械的に BODY_LIMIT 字以内に収める（ハッシュタグ行を保持）。"""
    if len(text) <= BODY_LIMIT:
        return text
    lines = text.splitlines()
    tag_lines = [l for l in lines if l.strip().startswith("#")]
    body_lines = [l for l in lines if not l.strip().startswith("#")]
    tags_str = "\n".join(tag_lines)
    body_str = "\n".join(body_lines).strip()
    available = BODY_LIMIT - len(tags_str) - (1 if tags_str else 0)
    trimmed = body_str[:available].rstrip()
    for punct in ["。", "！", "？"]:
        idx = trimmed.rfind(punct)
        if idx > available * 0.6:
            trimmed = trimmed[: idx + 1]
            break
    return f"{trimmed}\n{tags_str}" if tags_str else trimmed


def _generate_body(sheet_name: str, row: dict, page_text: str) -> str | None:
    system = get_system_prompt(sheet_name, "X")
    prompt = _build_prompt(row, page_text)

    for attempt in range(1, 3):
        try:
            text = generate(prompt, system=system, max_tokens=400).strip()
        except Exception as e:
            print(f"  [ERROR] Claude API 失敗: {e}")
            return None

        if len(text) <= BODY_LIMIT:
            return text

        if attempt == 1:
            over = len(text) - BODY_LIMIT
            print(f"  [RETRY] {len(text)}字（{over}字超過）→ 再生成")
            prompt = (
                f"以下の投稿文は {len(text)} 字あり、上限 {BODY_LIMIT} 字を {over} 字超えています。\n"
                f"必須ハッシュタグ (#ベビースリング #スリング) と お悩み系タグ 1〜2個 を残したまま、\n"
                f"{BODY_LIMIT} 字以内に削ってください。投稿文のみ出力。\n\n"
                f"【現在の投稿文】\n{text}"
            )

    print("  [TRIM] 自動トリム実施")
    return _trim_to_limit(text)


# ------------------------------------------------------------------ #
#  1行の処理
# ------------------------------------------------------------------ #

def _process_row(sheet_name: str, row: dict, x_client, log: list, dry_run: bool) -> bool:
    row_num = row["row_num"]
    theme = row.get("テーマ") or f"行{row_num}"
    ref_url = row.get("参照URL") or ""

    print(f"\n--- [{sheet_name}] 行{row_num}: {theme} ---")

    # 重複チェック
    if _is_posted(log, sheet_name, row_num):
        print("  [SKIP] 投稿済み (posted_log)")
        return False

    # 優先SNS フィルタ（空欄 or X を含む行のみ）
    sns_list = row.get("優先SNS") or []
    if sns_list and "X" not in sns_list:
        print(f"  [SKIP] 優先SNS={sns_list} に X が含まれない")
        return False

    # ① URL 取得（失敗しても続行）
    page_text = ""
    if ref_url:
        print(f"  URL 取得: {ref_url}")
        page_text = fetch_clean_text(ref_url) or ""
        if page_text:
            print(f"  → 取得成功 ({len(page_text)}字)")
        else:
            print("  → 取得失敗（メモ情報のみで生成）")

    # ② Claude でテキスト生成
    print("  Claude 生成中...")
    body = _generate_body(sheet_name, row, page_text)
    if body is None:
        print("  [SKIP] 生成失敗")
        return False

    # ③ 文字数チェック
    effective = len(body) + (URL_CHAR_COUNT + 1 if ref_url else 0)
    within_limit = effective <= X_CHAR_LIMIT
    print(f"  文字数: {effective}字 ({'OK' if within_limit else 'WARNING: 超過'})")
    if not within_limit:
        print(f"  [WARNING] 140字超過のため投稿しません")

    # ④ ハッシュタグ検証（AKOAKO のみ）
    if sheet_name == "AKOAKO":
        missing = [t for t in ["#ベビースリング", "#スリング"] if t not in body]
        if missing:
            print(f"  [WARNING] 必須タグ不足: {missing}")
        else:
            print("  必須タグ: OK (#ベビースリング #スリング)")
        found = [t for t in OMADANI_TAGS if t in body]
        print(f"  お悩み系タグ: {found if found else '(なし)'}")

    # 最終ツイート（本文 + URL）
    final_tweet = f"{body}\n{ref_url}" if ref_url else body

    print()
    print("  【投稿文（最終）】")
    print("  " + final_tweet.replace("\n", "\n  "))

    # dry-run はここで終了
    if dry_run:
        print("\n  [DRY-RUN] 投稿スキップ")
        return True

    if not within_limit:
        return False

    # ⑤ X 投稿
    try:
        resp = x_client.create_tweet(text=final_tweet)
        tweet_id = str(resp.data["id"])
        print(f"  [OK] 投稿完了: tweet_id={tweet_id}")
        _append_log(log, sheet_name, row_num, tweet_id)
        return True
    except Exception as e:
        print(f"  [ERROR] X 投稿失敗: {e}")
        return False


# ------------------------------------------------------------------ #
#  メイン
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="AKOAKO X 自動投稿 bot")
    parser.add_argument("--dry-run", action="store_true", help="投稿せず文章確認のみ")
    parser.add_argument("--date", help="対象日付 YYYY-MM-DD（省略時は今日）")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()
    mode = "[DRY-RUN]" if args.dry_run else "[本番]"

    print(f"\n{'='*60}")
    print(f"AKOAKO X 自動投稿  {mode}  対象日: {target}")
    print(f"{'='*60}")

    x_client = None if args.dry_run else _init_x_client()
    log = _load_log()
    posted = 0
    skipped = 0

    # HACO_LABO は haco_post.py が担当なので AKOAKO のみ処理
    try:
        rows = read_today_rows("AKOAKO", target_date=target)
    except Exception as e:
        print(f"[ERROR] AKOAKO シート読み取り失敗: {e}")
        sys.exit(1)

    if not rows:
        print(f"\nAKOAKO: {target} の投稿予定行なし（投稿済みを除く）")
    else:
        print(f"\nAKOAKO: {len(rows)}行 取得")
        for row in rows:
            if _process_row("AKOAKO", row, x_client, log, args.dry_run):
                posted += 1
            else:
                skipped += 1

    # posted_log.json 保存（dry-run 時は保存しない）
    if not args.dry_run and posted > 0:
        _save_log(log)
        print(f"\n[INFO] posted_log.json 更新 ({posted}件追記)")

    print(f"\n{'='*60}")
    print(f"完了: 投稿={posted}件  スキップ={skipped}件")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
