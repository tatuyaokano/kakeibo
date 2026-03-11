# 家計簿・支出管理アプリ

PC（Mac）とiPhoneで連携する家計簿アプリです。外出中はオフラインで支出を記録し、帰宅後にまとめてMacへ送信できます。

## 構成

```
kakeibo/
├── index.html          ← スマホ用PWA（GitHub Pages）
├── sw.js               ← Service Worker（オフラインキャッシュ）
└── mac-server/
    ├── app.py          ← Streamlit分析画面
    ├── api.py          ← FastAPI サーバー
    ├── kakeibo_offline.html
    ├── requirements.txt
    └── 家計簿を起動.command
```

## Mac側のセットアップ

```bash
# 依存関係のインストール
pip install -r mac-server/requirements.txt

# サーバー起動
cd mac-server
uvicorn api:app --host 0.0.0.0 --port 8000 &
streamlit run app.py --server.headless true
```

または **「家計簿を起動.command」** をダブルクリックすると両サーバーが自動起動します。

## アーキテクチャ

| サービス | ポート | 用途 |
|---------|--------|------|
| Streamlit | 8501 | PC向けグラフ・分析画面 |
| FastAPI | 8000 | スマホ向け入力フォーム・API |

## スマホ連携（オフライン対応）

### 外出中オフライン記録（推奨）
1. **https://tattu-cat.github.io/kakeibo/** をiPhoneのSafariで開く
2. ホーム画面に追加するとオフラインでも動作（Service Workerによりキャッシュ）
3. 外出中に「一時保存」で支出を記録
4. 帰宅後、設定欄にMacのIPアドレスを入力 → 「一括送信」

MacのIPアドレスは `.command` 起動時にコンソールに表示されます。

### 送信の仕組み
```
GitHub PagesアプリでIPを設定 → 「一括送信」
  → http://<MAC_IP>:8000/#import=<base64データ> に遷移
  → Mac側フォームが自動インポート・送信
  → 成功後 GitHub Pages に戻り、未送信リストを自動クリア
```

### 通常利用（同じWiFi下）
- `http://<MAC_IP>:8000` にSafariで直接アクセスして入力も可能

## データ構造（expenses.csv）

| カラム | 型 | 説明 |
|--------|-----|------|
| 日付 | YYYY-MM-DD | 支出日 |
| カテゴリ | string | 食費/交通費/住居費/光熱費/通信費/医療費/衣服・美容/娯楽・趣味/教育/その他 |
| 金額 | int | 円単位 |
| メモ | string | 任意のメモ |

## API エンドポイント

| エンドポイント | 説明 |
|--------------|------|
| `GET /` | スマホ用入力フォーム（`#import=` ハッシュで自動インポート） |
| `GET /offline` | kakeibo_offline.html を配信 |
| `POST /add` | 支出登録（JSON） |
| `GET /summary` | 今月のサマリー取得 |
| `GET /categories` | カテゴリ一覧取得 |

## 依存ライブラリ

```
streamlit, pandas, plotly, fastapi, uvicorn, python-multipart
```
