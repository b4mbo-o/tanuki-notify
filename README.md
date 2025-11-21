# 🦝 Tanuki-Notify  
雑談たぬきで指定ワードの新着投稿を監視し、見つけたら自動で X(Twitter) にツイートしてくれる Python Bot です。

---

## ✨ Features
- 🔍 **雑談たぬきのスレッド検索を自動スクレイピング**
- 🆕 **新着スレッドのみ自動検知**
- 🐦 **X(Twitter) に自動ツイート**
- 💾 **前回チェック内容を JSON に保存し重複通知なし**
- 🌐 **Cloudscraper で bot 対策ページにも対応**
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
**この Bot を使う前に、必ず `main.py` の `SEARCH_KEYWORD` をあなたの監視したいワードに変更してください！**

```python
SEARCH_KEYWORD = "ばんぶー"   # ← ここを必ず書き換える！
```

これを変えないと、デフォのまま “ばんぶー” を追いかけ続けちゃうので注意！

---

## 🔧 Setup

### 1. `.env` を作成（ローカル実行する場合）

```
TW_CONSUMER_KEY=xxxx
TW_CONSUMER_SECRET=xxxx
TW_ACCESS_TOKEN=xxxx
TW_ACCESS_SECRET=xxxx
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
- 雑談たぬき側の HTML が変わるとセレクタ修正が必要
- X API のレート制限に注意
- GitHub Actions を使うと PC 不要で自動運用できておすすめ

---

## ⭐️ Author
Made by **b4mbo-o**
