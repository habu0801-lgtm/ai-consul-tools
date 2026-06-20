"""
shift-scheduler
---------------------------------------------
スタッフの希望休・イベント対応日をもとに、月間シフト案を自動生成するツール。

手作業で約90分かかっていたシフト作成業務を、専用UIから条件を入力するだけで
下書きを自動生成できる形に置き換える。

主な機能:
  1. スタッフ登録（氏名、週あたりの最大勤務日数等）
  2. 希望休の入力（スタッフごとに複数日選択可）
  3. イベント日の設定（必要人数を指定）
  4. ボタン一つで月間シフト下書きを自動生成
  5. 生成結果をCSVでダウンロード

実行方法:
  streamlit run shift_scheduler.py
"""

import calendar
import random
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="シフト自動生成ツール", layout="wide")


def generate_shift_draft(month_dates, staff_list, wish_off, event_days, default_required):
    """
    各日について、希望休のスタッフを除外したうえで、必要人数分を
    なるべく公平に（勤務回数が少ない人を優先して）割り当てる簡易ロジック。

    本格運用時は、週あたり最大勤務日数や連勤制限などの制約を
    追加していくことを想定した骨格として実装している。
    """
    work_count = {s["name"]: 0 for s in staff_list}
    rows = []

    for d in month_dates:
        required = event_days.get(d, default_required)
        weekday_label = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]

        available = [
            s["name"]
            for s in staff_list
            if d not in wish_off.get(s["name"], [])
        ]

        # 勤務回数が少ない人を優先しつつ、同数の場合はランダム性を持たせる
        available_sorted = sorted(available, key=lambda name: (work_count[name], random.random()))
        assigned = available_sorted[:required]

        for name in assigned:
            work_count[name] += 1

        rows.append(
            {
                "日付": f"{d.month}/{d.day}（{weekday_label}）",
                "必要人数": required,
                "割当人数": len(assigned),
                "担当スタッフ": "、".join(assigned) if assigned else "（割当なし・要確認）",
            }
        )

    return pd.DataFrame(rows)


# ============ セッション状態の初期化 ============
if "staff_list" not in st.session_state:
    st.session_state.staff_list = []  # [{"name": str, "max_per_week": int}]
if "wish_off" not in st.session_state:
    st.session_state.wish_off = {}  # {staff_name: [date, ...]}
if "event_days" not in st.session_state:
    st.session_state.event_days = {}  # {date: required_count}
if "generated_shift" not in st.session_state:
    st.session_state.generated_shift = None


# ============ サイドバー: 対象年月 ============
st.sidebar.header("対象月")
today = date.today()
target_year = st.sidebar.number_input("年", min_value=2020, max_value=2100, value=today.year)
target_month = st.sidebar.number_input("月", min_value=1, max_value=12, value=today.month)

_, num_days = calendar.monthrange(int(target_year), int(target_month))
month_dates = [date(int(target_year), int(target_month), d) for d in range(1, num_days + 1)]

st.title("📅 シフト自動生成ダッシュボード")
st.caption(f"{target_year}年{target_month}月のシフトを作成します（全{num_days}日間）")

tab_staff, tab_wishoff, tab_event, tab_generate = st.tabs(
    ["① スタッフ管理", "② 希望休入力", "③ イベント日設定", "④ シフト生成"]
)

# ============ ① スタッフ管理 ============
with tab_staff:
    st.subheader("スタッフ登録")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_name = st.text_input("スタッフ名", key="new_staff_name")
    with col2:
        max_per_week = st.number_input("週あたり最大勤務日数", min_value=1, max_value=7, value=5, key="new_staff_max")
    with col3:
        st.write("")
        st.write("")
        if st.button("追加する", key="add_staff"):
            if new_name and new_name not in [s["name"] for s in st.session_state.staff_list]:
                st.session_state.staff_list.append({"name": new_name, "max_per_week": max_per_week})
                st.success(f"{new_name} を追加しました")
                st.rerun()

    if st.session_state.staff_list:
        st.write("### 登録済みスタッフ")
        for i, s in enumerate(st.session_state.staff_list):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(s["name"])
            c2.write(f"週{s['max_per_week']}日まで")
            if c3.button("削除", key=f"del_staff_{i}"):
                st.session_state.staff_list.pop(i)
                st.rerun()
    else:
        st.info("スタッフが登録されていません。上のフォームから追加してください。")

# ============ ② 希望休入力 ============
with tab_wishoff:
    st.subheader("希望休入力")
    if not st.session_state.staff_list:
        st.warning("先に「① スタッフ管理」でスタッフを登録してください。")
    else:
        staff_names = [s["name"] for s in st.session_state.staff_list]
        selected_staff = st.selectbox("スタッフを選択", staff_names, key="wishoff_staff")

        current = st.session_state.wish_off.get(selected_staff, [])
        selected_dates = st.multiselect(
            f"{selected_staff} の希望休日",
            options=month_dates,
            default=current,
            format_func=lambda d: f"{d.day}日（{['月','火','水','木','金','土','日'][d.weekday()]}）",
            key="wishoff_dates",
        )
        if st.button("保存する", key="save_wishoff"):
            st.session_state.wish_off[selected_staff] = selected_dates
            st.success(f"{selected_staff} の希望休を保存しました（{len(selected_dates)}件）")

        if st.session_state.wish_off:
            st.write("### 登録済み希望休")
            for name, dates_list in st.session_state.wish_off.items():
                if dates_list:
                    days_str = "、".join(f"{d.day}日" for d in sorted(dates_list))
                    st.write(f"- **{name}**: {days_str}")

# ============ ③ イベント日設定 ============
with tab_event:
    st.subheader("イベント日設定（必要人数の多い日）")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        event_date = st.selectbox(
            "日付",
            options=month_dates,
            format_func=lambda d: f"{d.day}日（{['月','火','水','木','金','土','日'][d.weekday()]}）",
            key="event_date_select",
        )
    with col2:
        required_count = st.number_input("必要人数", min_value=1, max_value=20, value=3, key="event_required")
    with col3:
        st.write("")
        st.write("")
        if st.button("設定する", key="add_event"):
            st.session_state.event_days[event_date] = required_count
            st.success(f"{event_date.day}日を必要人数{required_count}名で設定しました")
            st.rerun()

    if st.session_state.event_days:
        st.write("### 登録済みイベント日")
        for d, count in sorted(st.session_state.event_days.items()):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"{d.day}日")
            c2.write(f"必要人数: {count}名")
            if c3.button("削除", key=f"del_event_{d}"):
                del st.session_state.event_days[d]
                st.rerun()

# ============ ④ シフト生成 ============
with tab_generate:
    st.subheader("シフト下書きの自動生成")

    default_required = st.number_input("通常日の基本必要人数", min_value=1, max_value=10, value=2, key="default_required")

    if st.button("🚀 シフトを自動生成する", type="primary"):
        if not st.session_state.staff_list:
            st.error("スタッフが登録されていません。")
        else:
            shift_table = generate_shift_draft(
                month_dates,
                st.session_state.staff_list,
                st.session_state.wish_off,
                st.session_state.event_days,
                default_required,
            )
            st.session_state.generated_shift = shift_table
            st.success("シフト下書きを生成しました。内容を確認のうえ調整してください。")

    if st.session_state.generated_shift is not None:
        st.write("### 生成結果（下書き）")
        st.dataframe(st.session_state.generated_shift, use_container_width=True)

        csv = st.session_state.generated_shift.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSVでダウンロード",
            data=csv,
            file_name=f"shift_{target_year}_{target_month:02d}.csv",
            mime="text/csv",
        )
