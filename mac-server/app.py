import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import os

st.set_page_config(page_title="家計簿", page_icon="💰", layout="wide")

DATA_FILE = "expenses.csv"

CATEGORIES = [
    "食費", "交通費", "住居費", "光熱費", "通信費",
    "医療費", "衣服・美容", "娯楽・趣味", "教育", "その他"
]

CATEGORY_COLORS = {
    "食費": "#FF6B6B",
    "交通費": "#4ECDC4",
    "住居費": "#45B7D1",
    "光熱費": "#FFA07A",
    "通信費": "#98D8C8",
    "医療費": "#F7DC6F",
    "衣服・美容": "#BB8FCE",
    "娯楽・趣味": "#85C1E9",
    "教育": "#82E0AA",
    "その他": "#AEB6BF",
}


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["日付"])
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        return df
    return pd.DataFrame(columns=["日付", "カテゴリ", "金額", "メモ"])


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def add_expense(expense_date, category, amount, memo):
    df = load_data()
    new_row = pd.DataFrame([{
        "日付": expense_date,
        "カテゴリ": category,
        "金額": amount,
        "メモ": memo,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)


def delete_expense(index):
    df = load_data()
    df = df.drop(index=index).reset_index(drop=True)
    save_data(df)


def update_expense(index, expense_date, category, amount, memo):
    df = load_data()
    df.at[index, "日付"] = expense_date
    df.at[index, "カテゴリ"] = category
    df.at[index, "金額"] = amount
    df.at[index, "メモ"] = memo
    save_data(df)


# --- レイアウト ---
st.title("💰 家計簿・支出管理")

tab_input, tab_list, tab_chart = st.tabs(["✏️ 支出入力", "📋 支出一覧", "📊 グラフ分析"])

# =====================
# タブ1: 支出入力
# =====================
with tab_input:
    st.subheader("支出を記録する")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("日付", value=date.today())
            category = st.selectbox("カテゴリ", CATEGORIES)
        with col2:
            amount = st.number_input("金額（円）", min_value=1, step=100, value=1000)
            memo = st.text_input("メモ（任意）", placeholder="例：スーパーで食材購入")

        submitted = st.form_submit_button("追加する", use_container_width=True, type="primary")
        if submitted:
            add_expense(expense_date, category, amount, memo)
            st.success(f"追加しました: {category} ¥{amount:,}")
            st.rerun()

    # 今月のサマリー（前月比付き）
    df = load_data()
    if not df.empty:
        today = date.today()
        last_month_date = today - relativedelta(months=1)

        def month_total(df, y, m):
            return df[
                (pd.to_datetime(df["日付"]).dt.year == y) &
                (pd.to_datetime(df["日付"]).dt.month == m)
            ]["金額"].sum()

        this_total = month_total(df, today.year, today.month)
        last_total = month_total(df, last_month_date.year, last_month_date.month)
        delta = this_total - last_total
        delta_str = f"+¥{delta:,.0f}" if delta >= 0 else f"-¥{abs(delta):,.0f}"

        this_month = df[
            (pd.to_datetime(df["日付"]).dt.year == today.year) &
            (pd.to_datetime(df["日付"]).dt.month == today.month)
        ]

        st.divider()
        st.subheader("今月のサマリー")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("今月の合計支出", f"¥{this_total:,.0f}")
        m2.metric("先月比", delta_str, delta_percent := f"{(delta/last_total*100):.1f}%" if last_total else "—")
        m3.metric("今月の件数", f"{len(this_month)} 件")
        if not this_month.empty:
            top_cat = this_month.groupby("カテゴリ")["金額"].sum().idxmax()
            m4.metric("最多カテゴリ", top_cat)

# =====================
# タブ2: 支出一覧（編集機能付き）
# =====================
with tab_list:
    st.subheader("支出一覧")
    df = load_data()

    if df.empty:
        st.info("まだ支出が登録されていません。")
    else:
        # フィルター
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            all_months = sorted(
                pd.to_datetime(df["日付"]).dt.to_period("M").unique().astype(str),
                reverse=True
            )
            selected_month = st.selectbox("月で絞り込み", ["すべて"] + all_months)
        with col_f2:
            selected_cat = st.selectbox("カテゴリで絞り込み", ["すべて"] + CATEGORIES)

        filtered = df.copy()
        if selected_month != "すべて":
            filtered = filtered[
                pd.to_datetime(filtered["日付"]).dt.to_period("M").astype(str) == selected_month
            ]
        if selected_cat != "すべて":
            filtered = filtered[filtered["カテゴリ"] == selected_cat]

        filtered_sorted = filtered.sort_values("日付", ascending=False).reset_index()
        original_indices = filtered_sorted["index"].tolist()

        st.write(f"**{len(filtered_sorted)} 件**（合計: ¥{filtered['金額'].sum():,.0f}）")

        # 編集中の行を管理
        if "editing_index" not in st.session_state:
            st.session_state.editing_index = None

        for i, (_, row) in enumerate(filtered_sorted.iterrows()):
            orig_idx = original_indices[i]

            if st.session_state.editing_index == orig_idx:
                # 編集フォーム
                with st.container(border=True):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_date = st.date_input("日付", value=pd.to_datetime(row["日付"]).date(), key=f"ed_{orig_idx}")
                        new_cat = st.selectbox("カテゴリ", CATEGORIES, index=CATEGORIES.index(row["カテゴリ"]), key=f"ec_{orig_idx}")
                    with ec2:
                        new_amount = st.number_input("金額（円）", min_value=1, value=int(row["金額"]), key=f"ea_{orig_idx}")
                        new_memo = st.text_input("メモ", value=row["メモ"] if pd.notna(row["メモ"]) else "", key=f"em_{orig_idx}")
                    eb1, eb2 = st.columns(2)
                    if eb1.button("保存", key=f"save_{orig_idx}", type="primary", use_container_width=True):
                        update_expense(orig_idx, new_date, new_cat, new_amount, new_memo)
                        st.session_state.editing_index = None
                        st.rerun()
                    if eb2.button("キャンセル", key=f"cancel_{orig_idx}", use_container_width=True):
                        st.session_state.editing_index = None
                        st.rerun()
            else:
                # 通常表示
                col_a, col_b, col_c, col_d, col_e, col_f = st.columns([2, 2, 2, 3, 1, 1])
                col_a.write(str(row["日付"]))
                col_b.write(row["カテゴリ"])
                col_c.write(f"¥{int(row['金額']):,}")
                col_d.write(row["メモ"] if pd.notna(row["メモ"]) and row["メモ"] else "—")
                if col_e.button("✏️", key=f"edit_{i}_{orig_idx}"):
                    st.session_state.editing_index = orig_idx
                    st.rerun()
                if col_f.button("🗑️", key=f"del_{i}_{orig_idx}"):
                    delete_expense(orig_idx)
                    st.rerun()

# =====================
# タブ3: グラフ分析
# =====================
with tab_chart:
    st.subheader("グラフ分析")
    df = load_data()

    if df.empty:
        st.info("まだ支出が登録されていません。")
    else:
        df["年月"] = pd.to_datetime(df["日付"]).dt.to_period("M").astype(str)

        # 前月比カテゴリ別
        today = date.today()
        last_month_date = today - relativedelta(months=1)
        this_m = df[
            (pd.to_datetime(df["日付"]).dt.year == today.year) &
            (pd.to_datetime(df["日付"]).dt.month == today.month)
        ]
        last_m = df[
            (pd.to_datetime(df["日付"]).dt.year == last_month_date.year) &
            (pd.to_datetime(df["日付"]).dt.month == last_month_date.month)
        ]
        if not this_m.empty and not last_m.empty:
            st.markdown("**今月 vs 先月（カテゴリ別比較）**")
            this_cat = this_m.groupby("カテゴリ")["金額"].sum().rename("今月")
            last_cat = last_m.groupby("カテゴリ")["金額"].sum().rename("先月")
            compare = pd.concat([this_cat, last_cat], axis=1).fillna(0).reset_index()
            fig_compare = go.Figure()
            fig_compare.add_bar(name="先月", x=compare["カテゴリ"], y=compare["先月"], marker_color="#AEB6BF")
            fig_compare.add_bar(name="今月", x=compare["カテゴリ"], y=compare["今月"], marker_color="#FF6B6B")
            fig_compare.update_layout(barmode="group", yaxis_title="金額（円）", margin=dict(t=20, b=20))
            st.plotly_chart(fig_compare, use_container_width=True)
            st.divider()

        col_g1, col_g2 = st.columns(2)

        # --- 円グラフ: カテゴリ別合計 ---
        with col_g1:
            st.markdown("**カテゴリ別支出（全期間）**")
            cat_sum = df.groupby("カテゴリ")["金額"].sum().reset_index()
            fig_pie = px.pie(
                cat_sum,
                names="カテゴリ",
                values="金額",
                color="カテゴリ",
                color_discrete_map=CATEGORY_COLORS,
                hole=0.4,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 棒グラフ: 月別合計 ---
        with col_g2:
            st.markdown("**月別支出推移**")
            monthly = df.groupby("年月")["金額"].sum().reset_index().sort_values("年月")
            fig_bar = px.bar(
                monthly,
                x="年月",
                y="金額",
                text_auto=True,
                color_discrete_sequence=["#4ECDC4"],
            )
            fig_bar.update_traces(texttemplate="¥%{y:,.0f}", textposition="outside")
            fig_bar.update_layout(
                xaxis_title="月",
                yaxis_title="金額（円）",
                margin=dict(t=40, b=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- 積み上げ棒グラフ: 月別カテゴリ内訳 ---
        st.markdown("**月別カテゴリ内訳**")
        monthly_cat = df.groupby(["年月", "カテゴリ"])["金額"].sum().reset_index().sort_values("年月")
        fig_stack = px.bar(
            monthly_cat,
            x="年月",
            y="金額",
            color="カテゴリ",
            color_discrete_map=CATEGORY_COLORS,
            barmode="stack",
        )
        fig_stack.update_layout(
            xaxis_title="月",
            yaxis_title="金額（円）",
            legend_title="カテゴリ",
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_stack, use_container_width=True)
