# taikai 流行語大会

その日の流行語を記録する Web アプリ（Django 4.2 / Supabase / Vercel）。

## 機能
- 日付ごとの「大会」に、受賞した流行語（言葉・言った人・内容・画像）を登録
- 賞は 優勝 / 準優勝 / 審査員特別賞 を初期登録。「賞の設定」ページから追加・並べ替え・使用停止ができる
- 期間ごとの大会テーマソング（開催日に合う曲を自動表示）
- キーワード検索、言った人別の受賞回数ランキング
- ログインなし・管理画面なし（URL を知っている人は誰でも登録・編集できる）

## 構成
| 用途 | ローカル | 本番 |
|---|---|---|
| アプリ | `runserver` | Vercel（Python サーバーレス関数） |
| DB | SQLite (`db.sqlite3`) | Supabase Postgres（Transaction pooler） |
| 画像 | `media/` | Supabase Storage（S3 互換、公開バケット） |

`.env`（または環境変数）に `DATABASE_URL` / `SUPABASE_*` があれば Supabase、無ければローカルを使う。

## ローカル開発
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## 本番（Supabase + Vercel）セットアップ

### 1. Supabase
1. プロジェクトを作成（リージョンは Tokyo 推奨）
2. **Connect → Transaction pooler** の接続文字列（port 6543）を控える → `DATABASE_URL`
3. **Storage → New bucket** で `entry-images` を作成し、**Public bucket をオン**
4. **Storage → S3 Connection** で Access key を発行 → `SUPABASE_S3_ACCESS_KEY_ID` / `SUPABASE_S3_SECRET_ACCESS_KEY`。同じ画面の Region を `SUPABASE_STORAGE_REGION` に
5. プロジェクト URL `https://<ref>.supabase.co` の `<ref>` → `SUPABASE_PROJECT_REF`

### 2. テーブル作成（手元から1回）
```bash
cp .env.example .env   # 値を記入
.venv/bin/python manage.py migrate
```
モデルを変更したときも、デプロイ前に同じく `migrate` を実行する。

### 3. Vercel
1. GitHub にリポジトリを push し、Vercel で Import（Framework Preset: Other）
2. Environment Variables に `.env.example` の項目を登録（`DJANGO_SECRET_KEY` は長いランダム文字列）
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
3. Deploy

### 注意
- Vercel のリクエスト上限が 4.5MB のため、画像は 4MB までに制限している

## テスト
```bash
.venv/bin/python manage.py test contests
```
