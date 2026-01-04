# 🦝 Tanuki-Notify  
雑談たぬきで指定ワードの新着投稿を監視し、見つけたら自動で X(Twitter) にツイートしてくれる Python Bot です。

---

## ✨ Features
- 🔍 **雑談たぬき本文検索 → スレID抽出 → 各スレ内の `q=番号` リンクを収集**
- 🆕 **増えたレスだけを検知し、JSONに記録して重複通知なし**
- 🐦 **X(Twitter) に自動ツイート**
- 🌐 **r.jina.ai 経由取得（Cloudflare回避）＋ cloudscraper フォールバック**
- ⚙️ **GitHub Actions で定期自動実行に対応**

---

## 📦 Requirements

`requirements.txt` に準拠：

```
requests
beautifulsoup4
tweepy
python-dotenv
cloudscraper
```

インストール：

```bash
pip install -r requirements.txt
```

---

## ⚠️ Important  
**この Bot を使う前に、`.env` の `SEARCH_KEYWORD` を必ず設定してください（デフォルトなし）。**

---

## 🔧 Setup

### 1. `.env` を作成（ローカル実行する場合）

```
SEARCH_KEYWORD=ばんぶー         # 監視ワード (EUC-JPでエンコードして検索します)
TW_CONSUMER_KEY=xxxx
TW_CONSUMER_SECRET=xxxx
TW_ACCESS_TOKEN=xxxx
TW_ACCESS_SECRET=xxxx

# 任意設定
# MAX_THREADS=10         # 検索結果から何件のスレッドを見に行くか
# REQUEST_TIMEOUT=10     # 1リクエストあたりのタイムアウト秒
# USER_AGENT=Mozilla/5.0 # UAを変えたい場合
```

---

## 🚀 GitHub Actions で自動化する

Forkして使っていただければサーバーレスで動かすことが可能です！

### ✨ できること
- GitHub サーバー上で **自動で tanuki-notify を起動**
- PC を起動してなくても OK
- 実行ログが GitHub 上で確認可能

### 🔧 GitHub Secrets の設定

X API のキーは Secrets に登録する必要があります。

GitHub → リポジトリ →  
**Settings → Secrets and variables → Actions → New repository secret**

以下を登録：

- `TW_CONSUMER_KEY`
- `TW_CONSUMER_SECRET`
- `TW_ACCESS_TOKEN`
- `TW_ACCESS_SECRET`

---

## ▶️ Usage

### ローカルで単発実行

```bash
python main.py
```

### GitHub Actions で実行  
GitHub の Actions タブ → ワークフローをクリック → “Run workflow” で手動実行もOK。

---

## 📁 File Structure

```
tanuki-notify/
│── main.py                # メインロジック
│── last_seen_urls.json    # 状態保存ファイル（自動生成）
│── requirements.txt
│── .github/workflows/
│      └── title_check.yml # GitHub Actions の自動実行設定
```

---

## 📝 Notes
- 検索結果 → スレ内検索ページを r.jina.ai 経由で取得します。落ちている場合は cloudscraper にフォールバックします。
- 初回実行時は `last_seen_urls.json` を初期化するだけでツイートしません。次回以降に新しい `q=番号` リンクが増えたらツイートします。
- 雑談たぬき側のHTMLやパラメータ仕様が変わると取得ロジックの修正が必要になる場合があります。
- X API のレート制限に注意。

---

## ⭐️ Author
Made by **b4mbo-o**
