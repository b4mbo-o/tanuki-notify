import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, List, Dict

import requests
from dotenv import load_dotenv
import tweepy
from urllib.parse import quote, urlparse, parse_qs

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

# .envファイルを読み込み、環境変数を設定
load_dotenv()

# ==================================
# ===== 設 定 (Configuration) ======
# ==================================

SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD", "").strip()
if not SEARCH_KEYWORD:
    print("❌ SEARCH_KEYWORD を .env に設定してください。")
    sys.exit(1)

ENCODED_KEYWORD = quote(SEARCH_KEYWORD.encode('cp932')) # 雑談たぬきはEUC-JPが使われることが多いと仮定
SEARCH_URL = f"https://b.2ch2.net/test/search.cgi?bbs=zatsudan&w={ENCODED_KEYWORD}&t=b"
JINA_PROXY_PREFIX = "https://r.jina.ai/"
MAX_THREADS = int(os.getenv("MAX_THREADS", "10"))  # 取得するスレッド数の上限
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

# 状態管理ファイル (前回チェック時のURLリストを保存)
STATE_FILE = Path("last_seen_urls.json")

# 簡易User-Agent (HTTPリクエスト用)
SIMPLE_HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0)")
}

# 接続再利用でわずかに高速化
SESSION = requests.Session()
SESSION.headers.update(SIMPLE_HEADERS)

# X API認証情報 (環境変数から取得)
CK = os.getenv("TW_CONSUMER_KEY")
CS = os.getenv("TW_CONSUMER_SECRET")
AT = os.getenv("TW_ACCESS_TOKEN")
AS = os.getenv("TW_ACCESS_SECRET")

if not all([CK, CS, AT, AS]):
    print("❌ OAuth1.0aの4キー (TW_CONSUMER_KEY/SECRET, TW_ACCESS_TOKEN/SECRET) を .env に設定してください。")
    sys.exit(1)

# Tweepy v2クライアントの初期化
client = tweepy.Client(
    consumer_key=CK,
    consumer_secret=CS,
    access_token=AT,
    access_token_secret=AS,
)
# ==================================================
# ===== スクレピング実行 (Scraping Execution) ======
# ==================================================

def to_jina_url(url: str) -> str:
    """r.jina.ai 経由で取得するためのURLを生成する。"""
    return f"{JINA_PROXY_PREFIX}{url}"

def fetch_text(url: str) -> Optional[str]:
    """
    r.jina.ai経由でテキストを取得し、失敗したらcloudscraperで直接取得する。
    """
    # r.jina.ai
    try:
        r = SESSION.get(to_jina_url(url), timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[warn] r.jina.ai経由での取得に失敗: {e}")

    # cloudscraper fallback
    if cloudscraper is None:
        print("[warn] cloudscraperがインストールされていないためフォールバック不可。")
        return None

    try:
        scraper = cloudscraper.create_scraper(
            delay=10,
            browser={'custom': SIMPLE_HEADERS['User-Agent']}
        )
        r = scraper.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except Exception as e:
        print(f"[warn] cloudscraper経由での取得に失敗: {e}")
        return None

def extract_thread_search_links(markdown_text: str) -> List[str]:
    """
    検索結果ページからスレッド内検索リンク
    (/test/read.cgi/zatsudan/<id>/i?q=...）を抽出する。
    """
    pattern = re.compile(
        r"(https?://b\.2ch2\.net)?/test/read\.cgi/zatsudan/(\d+)/+/i\?q=[^\s\"')>#]+",
        re.IGNORECASE,
    )
    seen = set()
    links = []

    for match in pattern.finditer(markdown_text):
        raw_url = match.group(0)
        if raw_url.startswith("http"):
            normalized = raw_url
        else:
            normalized = f"https://b.2ch2.net{raw_url}"

        # //i を /i に正規化
        normalized = normalized.replace("//i", "/i")

        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)

        if len(links) >= MAX_THREADS:
            break

    return links

def extract_q_links(markdown_text: str) -> List[Dict[str, str]]:
    """
    r.jina.ai のMarkdownから、?q=xxx を含むレスリンクを抽出し、見やすいタイトルを付与する。
    """
    q_link_pattern = re.compile(
        r"(https?://b\.2ch2\.net)?/test/read\.cgi/[^\s\"')>]+?q=[^\s\"')>#]+",
        re.IGNORECASE,
    )
    seen = set()
    links = []

    for match in q_link_pattern.finditer(markdown_text):
        raw_url = match.group(0)
        if raw_url.startswith("http"):
            normalized = raw_url
        else:
            normalized = f"https://b.2ch2.net{raw_url}"

        clean_url = normalized.rstrip("#")

        if clean_url in seen:
            continue
        seen.add(clean_url)

        parsed = urlparse(clean_url)
        query = parse_qs(parsed.query)
        q_value = query.get("q", [""])[0]

        # 数字のレス番号のみ対象とする
        if not q_value.isdigit():
            continue

        # パス末尾が /i となるため、その1つ前をスレッドIDとして扱う
        parts = parsed.path.rstrip("/").split("/")
        thread_id = parts[-2] if len(parts) >= 2 else "unknown"
        title = f"{thread_id} のレス {q_value}" if q_value else thread_id

        links.append({"title": title, "url": clean_url})

    return links

def call_scraping_target() -> Optional[List[Dict[str, str]]]:
    """
    検索結果からスレッドIDを抽出し、各スレッド内の ?q=レス番号 リンクを集約する。
    """
    print(f"[scrape] 検索ページ {SEARCH_URL} をチェック中 (r.jina.ai優先, fallbackにcloudscraper)...")

    search_text = fetch_text(SEARCH_URL)
    if not search_text:
        print("[error] 検索ページを取得できませんでした。")
        return None

    thread_links = extract_thread_search_links(search_text)
    if not thread_links:
        print("[error] 検索結果からスレッドリンクを抽出できませんでした。")
        return None

    all_res_links: List[Dict[str, str]] = []
    seen_urls = set()

    for thread_url in thread_links:
        text = fetch_text(thread_url)
        if not text:
            continue

        q_links = extract_q_links(text)
        for link in q_links:
            if link["url"] in seen_urls:
                continue
            seen_urls.add(link["url"])
            all_res_links.append(link)

    if not all_res_links:
        print("[scrape] エラー: レスリンクが見つかりませんでした。検索結果の形式を確認してください。")
        return None

    print(f"[scrape] 合計 {len(all_res_links)} 件のレスリンクを抽出しました。")
    return all_res_links

# ===================================================
# ===== メイン処理 (Main Logic - Single Run) ========
# ===================================================
# ... (main_check 関数は、新しい 'all_res_links' を使って前回同様に比較されるため、そのまま利用できます) ...
# ===================================================
# ===== 状態管理 (State Management) =================
# ===================================================

def load_state() -> List[str]:
    """最後に見たスレッドのURLリストをファイルから読み込む。"""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data.get("last_seen_urls", [])
        except Exception:
            return []
    return []

def save_state(urls: List[str]):
    """最新のスレッドのURLリストをファイルに保存する。"""
    STATE_FILE.write_text(
        json.dumps({"last_seen_urls": urls}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[state] {len(urls)}件のURLを保存しました。")

# ===================================================
# ===== ツイート処理 (Tweet Handling) ===============
# ===================================================

def tweet_notification(new_threads: List[Dict[str, str]]):
    """新着スレッドのタイトルとURLをXに通知する。（最多1件のみ詳細表示）"""
    print(f"[tweet] 新着スレッド {len(new_threads)} 件をツイートします。")
    
    # 🚨 修正点 1: 新着スレッドは1件目（最新）のみ詳細表示
    latest_thread = new_threads[0]
    new_count = len(new_threads)
    
    # メッセージの構築
    message = f"🦝雑談たぬきにて【{SEARCH_KEYWORD}】の新着投稿が見つかりました😢\n"
    
    # 最新の1件目のタイトルとURLを必ず表示
    message += f"\n🆕 最新スレッド (他{new_count - 1}件):\n"
    
    # タイトルをそのまま使用し、ハッシュタグが確実に表示されるようにメッセージ構造をシンプル化
    message += f"『{latest_thread['title']}』\n"
    message += f"{latest_thread['url']}"

    # 複数件あった場合は、検索結果ページへのリンクを追加
    if new_count > 1:
        message += f"\n\n👉 他 {new_count - 1} 件は、こちらで確認:\n"
        message += f"{SEARCH_URL}"
        
    message += f"\n\n#{SEARCH_KEYWORD} #雑談たぬき #たぬきに書くな"
    
    # 最終的な文字数チェック
    if len(message) > 280:
        # 最終手段としてメッセージを切り詰めるが、ハッシュタグが生き残る可能性が高い
        message = message[:277] + "..."

    try:
        client.create_tweet(text=message)
        print("[tweet] 通知を投稿しました。")
    except tweepy.TweepyException as e:
        print(f"[error] X (Twitter) 投稿失敗: {e}")

# ===================================================
# ===== メイン処理 (Main Logic - Single Run) ========
# ===================================================

def main_check():
    """Botのメイン処理。実行ごとに新着をチェックし、状態を更新する。"""
    print(f"== 雑談たぬき タイトル追跡ウォッチャー起動 ==")
    
    # 既存のURLリストを読み込み (前回までの既知スレッド)
    last_seen_urls = set(load_state())
    
    # 新しいスレッド情報を取得 (現在の検索結果)
    current_threads = call_scraping_target()
    
    if current_threads is None:
        print("処理を終了します。")
        return

    # 現在の全URLリストを作成
    current_urls = [t['url'] for t in current_threads]
    
    if not last_seen_urls:
        # 初回実行時: 基準値を設定して終了
        save_state(current_urls)
        print(f"[init] 初回実行。基準となる {len(current_urls)} 件のURLを設定して終了します。")
        return

    # 新着スレッドを特定 (現在のリストにあって、過去のリストにないもの)
    new_threads = []
    for thread in current_threads:
        if thread['url'] not in last_seen_urls:
            new_threads.append(thread)

    print(f"[check] 現在 {len(current_urls)} 件のスレッドを検出。記録済み {len(last_seen_urls)} 件。")

    if new_threads:
        print(f"🌟 新しいスレッドを {len(new_threads)} 件検出しました！")
        tweet_notification(new_threads)
        
        # 検出後、基準URLリストを最新のものに更新
        save_state(current_urls)
    else:
        print("✅ 新しいスレッドはありませんでした。")
    
    print("== 処理完了 ==")


if __name__ == "__main__":
    main_check()
