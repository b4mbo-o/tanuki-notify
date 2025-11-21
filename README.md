# 🎋 Banbu Watcher (雑談たぬき 新着スレッド通知 Bot)

特定のキーワード（現在「ばんぶー」）を含む新しいスレッドが、雑談たぬきの検索結果ページに現れた際に、X (旧Twitter) へ自動で通知する Bot です。

本 Bot は **GitHub Actions の無料枠**内で、Bot対策回避ライブラリ **`cloudscraper`** を使用して安定して動作するように設計されています。

---

## ⚙️ 動作の仕組み

1.  **スケジューリング**: GitHub Actions の cron 設定（現在**2時間に1回**）で `title_watch_final.py` を実行します。
2.  **スクレイピング**: `cloudscraper` で検索結果ページにアクセスし、表示されている全スレッドのタイトルと URL を取得します。
3.  **状態管理**: 前回実行時に保存した `last_seen_urls.json` のリストと比較し、**新しく追加されたスレッド**を特定します。
4.  **通知**: 新着スレッドがあった場合、その**タイトルとURL**を含む通知をXに投稿します。
5.  **永続化**: 最後に、現在の URL リストを `last_seen_urls.json` に上書きし、**GitHub に自動でコミット・プッシュ**して状態を記憶します。

---

## 🚀 セットアップ手順

Botを動作させるために、以下の手順で環境を設定してください。

### 1. 依存ファイルの配置

以下の3つのファイルをリポジトリのルートに配置します。

* `title_watch_final.py` (Bot本体スクリプト)
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

### 3. 初回実行とデプロイ

1.  上記ファイルをリポジトリにプッシュします。
2.  GitHubの **Actions** タブを開き、`Thread Title Watcher` ワークフローを選択します。
3.  右上の **Run workflow** ボタンを押し、**手動で一度実行します**。
    * これにより、現在のスレッドリストが `last_seen_urls.json` に保存され、Botの基準状態が設定されます。この初回実行ではツイートはされません。
4.  以降は、設定した cron スケジュール（2時間に1回）に従って自動実行されます。
