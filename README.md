# 🎋 たぬきうぉっちゃー (雑談たぬき 新着スレッド通知 Bot)

特定のキーワード（現在 **"ばんぶー"**）を含む新しいスレッドが、雑談たぬきの検索結果ページに現れた際に、X (旧Twitter) へ自動で通知する Bot です。

---

## ⚙️ 動作の仕組み

1.  **スケジューリング**: GitHub Actions の cron 設定（**1時間に1回**）で `main.py` を実行します。
2.  **キーワード処理**: `main.py` 内で定義された `SEARCH_KEYWORD` を利用して、URLエンコーディングを行い、監視対象の URL を生成します。（エンコード方式は CP932 を使用）
3.  **スクレイピング**: `cloudscraper` で検索結果ページにアクセスし、表示されている全スレッドの URL リストを取得します。
4.  **新着の検知**: 前回実行時に `actions` ブランチに保存された `last_seen_urls.json` と現在のリストを比較し、**新しく追加されたスレッド**を特定します。
5.  **通知**: 新着スレッドがあった場合、その**タイトルとURL**を含む通知をXに投稿します。
6.  **永続化**: 現在の URL リストを `last_seen_urls.json` に上書きし、ブランチに自動でコミット・プッシュして状態を記憶します。

---

## 🚀 セットアップ手順

Botを動作させるために、以下の手順で環境を設定してください。(Forkしてね)

### 1. 依存ファイルの配置とファイル名確認

以下のファイルがリポジトリのルートに存在し、`main.py` 内の `SEARCH_KEYWORD` が希望のワードになっていることを確認してください。

* `main.py` (Bot本体スクリプト)
* `requirements.txt` (依存ライブラリ一覧：`cloudscraper`, `tweepy` などを含む)
* `.github/workflows/title_check.yml` (GitHub Actions設定ファイル)

### 2. X (Twitter) Developer Secrets の設定 (必須)

GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** に移動し、以下の4つのシークレット（秘密情報）を登録します。

| シークレット名 | 概要 |
| :--- | :--- |
| `TW_CONSUMER_KEY` | X App の API Key |
| `TW_CONSUMER_SECRET` | X App の API Secret |
| `TW_ACCESS_TOKEN` | X App の Access Token |
| `TW_ACCESS_SECRET` | X App の Access Token Secret |
:
  contents: write
