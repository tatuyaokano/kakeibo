from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from datetime import date
import pandas as pd
import os

app = FastAPI(title="家計簿API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "expenses.csv"

CATEGORIES = [
    "食費", "交通費", "住居費", "光熱費", "通信費",
    "医療費", "衣服・美容", "娯楽・趣味", "教育", "その他"
]


class Expense(BaseModel):
    date: str        # "YYYY-MM-DD"
    category: str
    amount: int
    memo: str = ""


def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["日付", "カテゴリ", "金額", "メモ"])


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


FORM_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>支出登録</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 16px; }}
    h1 {{ text-align: center; margin-bottom: 16px; font-size: 20px; color: #333; }}
    .card {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 16px; }}
    h2 {{ font-size: 15px; color: #555; margin-bottom: 12px; }}
    label {{ display: block; font-size: 13px; color: #666; margin-bottom: 6px; margin-top: 14px; }}
    input, select {{ width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 10px; outline: none; }}
    input:focus, select:focus {{ border-color: #4ECDC4; }}
    .btn {{ margin-top: 16px; width: 100%; padding: 14px; font-size: 16px; font-weight: bold; border: none; border-radius: 12px; cursor: pointer; }}
    .btn-save {{ background: #4ECDC4; color: white; }}
    .btn-send {{ background: #FF6B6B; color: white; }}
    .btn-send:disabled {{ background: #ccc; cursor: default; }}
    .msg {{ margin-top: 12px; padding: 12px; border-radius: 10px; text-align: center; font-size: 14px; }}
    .ok {{ background: #d4edda; color: #155724; }}
    .err {{ background: #f8d7da; color: #721c24; }}
    .badge {{ display: inline-block; background: #FF6B6B; color: white; border-radius: 12px; padding: 2px 8px; font-size: 13px; margin-left: 6px; }}
    .pending-list {{ margin-top: 8px; }}
    .pending-item {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
    .pending-item:last-child {{ border-bottom: none; }}
    .del-btn {{ background: none; border: none; color: #ccc; font-size: 18px; cursor: pointer; padding: 0 4px; margin-top: 0; width: auto; }}
    .empty {{ color: #aaa; font-size: 14px; text-align: center; padding: 12px 0; }}
  </style>
</head>
<body>
  <h1>💰 支出登録</h1>

  <!-- 入力フォーム -->
  <div class="card">
    <h2>支出を入力</h2>
    <div id="form-msg"></div>
    <label>日付</label>
    <input type="date" id="f-date" required>
    <label>カテゴリ</label>
    <select id="f-category">
      {options}
    </select>
    <label>金額（円）</label>
    <input type="number" id="f-amount" min="1" placeholder="例: 500">
    <label>メモ（任意）</label>
    <input type="text" id="f-memo" placeholder="例: コンビニ">
    <button class="btn btn-save" onclick="saveLocal()">一時保存（オフライン可）</button>
  </div>

  <!-- 未送信リスト -->
  <div class="card">
    <h2>未送信リスト <span class="badge" id="pending-count">0</span></h2>
    <div id="pending-list"></div>
    <div id="send-msg"></div>
    <button class="btn btn-send" id="send-btn" onclick="sendAll()" disabled>一括送信（帰宅後に押す）</button>
  </div>

  <script>
    const STORAGE_KEY = 'kakeibo_pending';

    // 今日の日付をセット
    document.getElementById('f-date').value = new Date().toLocaleDateString('sv-SE');

    function getPending() {{
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    }}
    function setPending(list) {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    }}

    function renderPending() {{
      const list = getPending();
      const el = document.getElementById('pending-list');
      const countEl = document.getElementById('pending-count');
      const sendBtn = document.getElementById('send-btn');
      countEl.textContent = list.length;
      sendBtn.disabled = list.length === 0;
      if (list.length === 0) {{
        el.innerHTML = '<div class="empty">未送信の支出はありません</div>';
        return;
      }}
      el.innerHTML = '<div class="pending-list">' + list.map((item, i) =>
        `<div class="pending-item">
          <span>${{item.date}} ${{item.category}}</span>
          <span>¥${{Number(item.amount).toLocaleString()}}</span>
          <button class="del-btn" onclick="deleteItem(${{i}})">✕</button>
        </div>`
      ).join('') + '</div>';
    }}

    function saveLocal() {{
      const d = document.getElementById('f-date').value;
      const c = document.getElementById('f-category').value;
      const a = document.getElementById('f-amount').value;
      const m = document.getElementById('f-memo').value;
      const msgEl = document.getElementById('form-msg');

      if (!d || !a || Number(a) <= 0) {{
        msgEl.innerHTML = '<div class="msg err">日付と金額を入力してください</div>';
        return;
      }}
      const list = getPending();
      list.push({{ date: d, category: c, amount: Number(a), memo: m }});
      setPending(list);

      document.getElementById('f-amount').value = '';
      document.getElementById('f-memo').value = '';
      document.getElementById('f-date').value = new Date().toLocaleDateString('sv-SE');
      msgEl.innerHTML = `<div class="msg ok">✅ 一時保存しました（${{c}} ¥${{Number(a).toLocaleString()}}）</div>`;
      setTimeout(() => {{ msgEl.innerHTML = ''; }}, 3000);
      renderPending();
    }}

    function deleteItem(i) {{
      const list = getPending();
      list.splice(i, 1);
      setPending(list);
      renderPending();
    }}

    async function sendAll() {{
      const list = getPending();
      if (list.length === 0) return;
      const sendBtn = document.getElementById('send-btn');
      const msgEl = document.getElementById('send-msg');
      sendBtn.disabled = true;
      sendBtn.textContent = '送信中...';
      msgEl.innerHTML = '';

      let success = 0, failed = 0;
      for (const item of list) {{
        try {{
          const res = await fetch('/add', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(item),
          }});
          if (res.ok) success++;
          else failed++;
        }} catch(e) {{
          failed++;
        }}
      }}

      if (failed === 0) {{
        setPending([]);
        msgEl.innerHTML = `<div class="msg ok">✅ ${{success}}件を送信しました！</div>`;
      }} else {{
        const remaining = getPending().slice(success);
        setPending(remaining);
        msgEl.innerHTML = `<div class="msg err">⚠️ ${{success}}件成功、${{failed}}件失敗。サーバーに接続できていません。</div>`;
      }}
      sendBtn.textContent = '一括送信（帰宅後に押す）';
      renderPending();
    }}

    renderPending();

    // オフラインHTMLからのインポート処理
    // kakeibo_offline.html が #import=<base64> を付けてリダイレクトしてくる
    (async function importFromHash() {{
      const hash = window.location.hash;
      if (!hash.startsWith('#import=')) return;

      const encoded = hash.slice('#import='.length);
      let items;
      try {{
        items = JSON.parse(decodeURIComponent(escape(atob(encoded))));
      }} catch(e) {{
        return;
      }}

      // ハッシュをすぐに消す（リロード時の二重送信防止）
      history.replaceState(null, '', '/');

      const msgEl = document.getElementById('send-msg');
      const sendBtn = document.getElementById('send-btn');
      msgEl.innerHTML = `<div class="msg" style="background:#fff3cd;color:#856404;">📲 オフライン記録 ${{items.length}}件を送信中...</div>`;

      let success = 0, failed = 0;
      const failedItems = [];
      for (const item of items) {{
        try {{
          const res = await fetch('/add', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(item),
          }});
          if (res.ok) success++;
          else {{ failed++; failedItems.push(item); }}
        }} catch(e) {{
          failed++;
          failedItems.push(item);
        }}
      }}

      if (failed === 0) {{
        // 全件成功 → GitHub PagesアプリにリダイレクトしてlocalStorageをクリアさせる
        setTimeout(() => {{
          window.location.href = 'https://tattu-cat.github.io/kakeibo/?cleared=1';
        }}, 1500);
        msgEl.innerHTML = `<div class="msg ok">✅ オフライン記録 ${{success}}件を取り込みました！GitHubアプリに戻ります...</div>`;
      }} else {{
        // 失敗分をlocalStorageに戻す
        const existing = getPending();
        setPending([...existing, ...failedItems]);
        msgEl.innerHTML = `<div class="msg err">⚠️ ${{success}}件成功、${{failed}}件失敗。</div>`;
        renderPending();
      }}
    }})();
  </script>
</body>
</html>
"""


def render_form():
    options = "\n".join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)
    return FORM_HTML.format(options=options)


@app.get("/", response_class=HTMLResponse)
def root():
    return render_form()


@app.get("/form", response_class=HTMLResponse)
def form_get():
    return render_form()


@app.get("/offline", response_class=FileResponse)
def offline_form():
    return FileResponse("kakeibo_offline.html", media_type="text/html")


@app.get("/categories")
def get_categories():
    return {"categories": CATEGORIES}


@app.post("/add")
def add_expense(expense: Expense):
    if expense.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"カテゴリが無効です: {expense.category}")
    if expense.amount <= 0:
        raise HTTPException(status_code=400, detail="金額は1以上にしてください")

    df = load_data()
    new_row = pd.DataFrame([{
        "日付": expense.date,
        "カテゴリ": expense.category,
        "金額": expense.amount,
        "メモ": expense.memo,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)

    return {
        "status": "ok",
        "message": f"追加しました: {expense.category} ¥{expense.amount:,}",
        "data": {
            "date": expense.date,
            "category": expense.category,
            "amount": expense.amount,
            "memo": expense.memo,
        }
    }


@app.get("/summary")
def get_summary():
    df = load_data()
    if df.empty:
        return {"total": 0, "count": 0, "by_category": {}}

    today = date.today()
    df["日付"] = pd.to_datetime(df["日付"])
    this_month = df[
        (df["日付"].dt.year == today.year) &
        (df["日付"].dt.month == today.month)
    ]

    by_category = this_month.groupby("カテゴリ")["金額"].sum().to_dict()

    return {
        "total": int(this_month["金額"].sum()),
        "count": len(this_month),
        "by_category": {k: int(v) for k, v in by_category.items()},
    }
