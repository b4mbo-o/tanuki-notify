import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict
import cloudscraper  # Bot対策回避ライブラリ
from dotenv import load_dotenv
import tweepy
from bs4 import BeautifulSoup
from urllib.parse import quote

# .envファイルを読み込み、環境変数を設定
load_dotenv()

# ==================================
# ===== 設 定 (Configuration) ======
# ==================================

SEARCH_KEYWORD = "ばんぶー"
BASE_URL = "https://b.2ch2.net/test/search.cgi?bbs=zatsudan&w="
ENCODED_KEYWORD = quote(SEARCH_KEYWORD.encode('cp932')) # 雑談たぬきはEUC-JPが使われることが多いと仮定
TARGET_URL = f"{BASE_URL}{ENCODED_KEYWORD}&t=b"

# 状態管理ファイル (前回チェック時のURLリストを保存)
STATE_FILE = Path("last_seen_urls.json")

# 簡易User-Agent (cloudscraperに渡すため)
SIMPLE_HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0)")
}

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

def call_scraping_target() -> Optional[List[Dict[str, str]]]:
    """
    cloudscraperを使用して対象URLからスレッドのタイトルとURLのリストを取得する。
    Bot対策を自動で回避する。
    """
    print(f"[scrape] {TARGET_URL} をチェック中 (Cloudscraper使用)...")
    
    # Cloudscraperのインスタンスを作成
    scraper = cloudscraper.create_scraper(
        delay=10, 
        browser={'custom': SIMPLE_HEADERS['User-Agent']}
    )

    try:
        # scraper.get() でリクエストを実行
        r = scraper.get(TARGET_URL, timeout=30)
        
        # 応答を確認 (200 OK以外は例外発生)
        r.raise_for_status() 
        
        r.encoding = r.apparent_encoding # 文字化け対策
        soup = BeautifulSoup(r.text, "html.parser")

        all_threads = []
        # 'div class="box"' の要素をすべて取得し、タイトルとURLを抽出
        for box in soup.select('div.box'):
            title_tag = box.select_one('a b span.c')
            url_tag = box.select_one('a')
            
            if title_tag and url_tag and url_tag.get('href'):
                title = title_tag.text.strip()
                # URL整形 (余計な 'https:///' を 'https://' に修正)
                url = url_tag['href'].replace('https:///', 'https://')
                
                all_threads.append({
                    "title": title,
                    "url": url
                })
        
        if not all_threads:
            print("[scrape] エラー: スレッド情報が見つかりませんでした。HTMLセレクタを確認してください。")
            return None
            
        return all_threads

    except Exception as e:
        print(f"[error] スクレイピング/アクセスエラー: {e}")
        return None

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
    """新着スレッドのタイトルとURLをXに通知する。"""
    print(f"[tweet] 新着スレッド {len(new_threads)} 件をツイートします。")
    
    # 新着スレッドの情報を整形
    message = f"🚨雑談たぬきにて【{SEARCH_KEYWORD}】の新着スレッドが {len(new_threads)} 件見つかりました😢\n"
    
    # 最大3件までツイートに含める
    for i, thread in enumerate(new_threads[:3]):
        # ツイート文字数制限を考慮してタイトルを短縮
        title_limit = 20 if i == 0 else 15
        truncated_title = thread['title'][:title_limit] + ('...' if len(thread['title']) > title_limit else '')
        
        message += f"\n👉 {truncated_title}\n{thread['url']}"

    # 4件以上ある場合は補足
    if len(new_threads) > 3:
        message += f"\n...他 {len(new_threads) - 3} 件。詳細は検索ページで確認してください。"
        message += f"\n{TARGET_URL}"
        
    message += f"\n#{SEARCH_KEYWORD} #雑談たぬき #たぬきに書くな"
    
    # 最終的な文字数チェック
    if len(message) > 280:
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
