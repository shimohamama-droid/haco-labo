"""
url_fetcher.py
URL から本文テキストを取得・クリーニングするモジュール
"""

import re
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    raise ImportError(
        "requests / beautifulsoup4 が未インストールです。pip install requests beautifulsoup4 を実行してください。"
    ) from e

_DEFAULT_TIMEOUT = 30
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

# 除去するタグ
_REMOVE_TAGS = [
    "script", "style", "noscript", "header", "footer", "nav",
    "aside", "iframe", "svg", "button", "form", "input", "select",
    "meta", "link", "head",
]

# 除去する CSS クラス・ID パターン (部分一致)
_REMOVE_CLASS_PATTERNS = [
    "nav", "menu", "header", "footer", "sidebar", "breadcrumb",
    "ad", "banner", "popup", "modal", "cookie", "related",
    "recommend", "ranking", "campaign",
]


def _is_noise_element(tag) -> bool:
    """ナビ/フッター/広告等のノイズ要素か判定"""
    for attr in ("class", "id"):
        values = tag.get(attr, [])
        if isinstance(values, str):
            values = [values]
        for v in values:
            for pattern in _REMOVE_CLASS_PATTERNS:
                if pattern in v.lower():
                    return True
    return False


def _clean_soup(soup: "BeautifulSoup") -> str:
    """BeautifulSoup オブジェクトから本文テキストを抽出"""
    # 不要タグ削除
    for tag in soup.find_all(_REMOVE_TAGS):
        tag.decompose()

    # ノイズ要素削除
    for tag in soup.find_all(True):
        if _is_noise_element(tag):
            tag.decompose()

    # 本文候補を優先度順に探す
    body_candidates = [
        soup.find("article"),
        soup.find("main"),
        soup.find(id=re.compile(r"content|main|body", re.I)),
        soup.find(class_=re.compile(r"content|main|body|post|entry", re.I)),
        soup.find("body"),
    ]

    for candidate in body_candidates:
        if candidate:
            text = candidate.get_text(separator="\n", strip=True)
            # 最低限の長さがある場合に採用
            if len(text) > 100:
                return _normalize_text(text)

    return _normalize_text(soup.get_text(separator="\n", strip=True))


def _normalize_text(text: str) -> str:
    """連続する空白行を圧縮"""
    lines = text.splitlines()
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip():
            blank_count = 0
            cleaned.append(line.strip())
        else:
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()


def _fetch_rakuten(url: str, timeout: int) -> str | None:
    """楽天商品ページ向け追加処理"""
    resp = requests.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 楽天: 商品名・説明文エリアを優先
    for selector in [
        ".item-detail",
        "#item-detail",
        ".rakuten-product-detail",
        ".productDetail",
        ".item_desc",
    ]:
        el = soup.select_one(selector)
        if el:
            return _normalize_text(el.get_text(separator="\n", strip=True))

    return _clean_soup(soup)


def _fetch_appstore(url: str, timeout: int) -> str | None:
    """App Store ページ向け処理"""
    resp = requests.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # App Store: アプリ名・説明
    parts = []
    name_el = soup.find("h1", class_=re.compile(r"app-header__title|product-header__title", re.I))
    if name_el:
        parts.append(name_el.get_text(strip=True))

    desc_el = soup.find(class_=re.compile(r"section__description|app-description|product-hero__subtitle", re.I))
    if desc_el:
        parts.append(desc_el.get_text(separator="\n", strip=True))

    if parts:
        return _normalize_text("\n\n".join(parts))

    return _clean_soup(soup)


def fetch_clean_text(url: str, timeout: int = _DEFAULT_TIMEOUT) -> str | None:
    """
    URL から本文テキストを取得してクリーニングしたものを返す。

    Parameters
    ----------
    url : str
        取得対象の URL
    timeout : int
        タイムアウト秒数 (デフォルト 30)

    Returns
    -------
    str or None
        取得・クリーニングされた本文テキスト。失敗した場合は None。
    """
    if not url or not str(url).startswith("http"):
        return None

    url = str(url).strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    try:
        # ドメイン別の処理分岐
        if "item.rakuten.co.jp" in host or "rakuten.co.jp" in host:
            return _fetch_rakuten(url, timeout)

        if "apps.apple.com" in host or "itunes.apple.com" in host:
            return _fetch_appstore(url, timeout)

        # 汎用 (akoakostudio.com 等)
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return _clean_soup(soup)

    except Exception as e:
        print(f"[url_fetcher] URL 取得失敗 ({url}): {e}")
        return None
