import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Scaling Risk Checker", layout="centered")

# =========================
# Language
# =========================
lang = st.selectbox("Language / Язык", ["English", "Русский"])

TEXT = {
    "English": {
        "title": "Scaling Risk Checker",
        "subtitle": "Upload Meta CSV or input manually. Then simulate scaling.",
        "mode": "Choose input mode",
        "manual_finance": "Manual finance",
        "manual_funnel": "Manual funnel (Meta-like)",
        "csv": "Meta CSV upload",
        "revenue": "Total Revenue ($)",
        "cogs": "Total COGS ($)",
        "ad_spend": "Ad Spend ($)",
        "orders": "Orders",
        "refund": "Refund Rate (%)",
        "spend": "Spend ($)",
        "results": "Results (conversations)",
        "close_rate": "Close rate (orders / conversations)",
        "aov": "Average Order Value ($)",
        "cogs_per_order": "COGS per order ($)",
        "scaling": "Scaling assumptions",
        "spend_increase": "Simulate Spend Increase (%)",
        "cac_decay": "CAC deterioration per +100% spend (%)",
        "analyze": "Analyze",
        "baseline": "Baseline",
        "simulation": "Simulation",
        "profit": "Profit",
        "safe": "Maximum safe scaling (profit ≥ 0)",
        "scenario": "Scenario table"
    },
    "Русский": {
        "title": "Проверка Риска Масштабирования",
        "subtitle": "Загрузите CSV из Meta или введите данные вручную.",
        "mode": "Выберите режим ввода",
        "manual_finance": "Финансы вручную",
        "manual_funnel": "Воронка вручную (как Meta)",
        "csv": "Загрузка Meta CSV",
        "revenue": "Общая выручка ($)",
        "cogs": "Себестоимость ($)",
        "ad_spend": "Рекламные расходы ($)",
        "orders": "Количество заказов",
        "refund": "Процент возвратов (%)",
        "spend": "Расход ($)",
        "results": "Результаты (диалоги)",
        "close_rate": "Конверсия в заказ",
        "aov": "Средний чек ($)",
        "cogs_per_order": "Себестоимость на заказ ($)",
        "scaling": "Параметры масштабирования",
        "spend_increase": "Увеличение бюджета (%)",
        "cac_decay": "Ухудшение CAC при +100% бюджета (%)",
        "analyze": "Рассчитать",
        "baseline": "Базовые показатели",
        "simulation": "Симуляция",
        "profit": "Прибыль",
        "safe": "Максимальное безопасное масштабирование (прибыль ≥ 0)",
        "scenario": "Таблица сценариев"
    }
}

t = TEXT[lang]

st.title(t["title"])
st.write(t["subtitle"])

# =========================
# Scaling Engine
# =========================
def simulate(revenue, cogs, ad_spend, orders, refund_rate,
             spend_growth_pct, cac_decay_pct):

    if orders <= 0:
        return None

    rr = refund_rate / 100
    g = spend_growth_pct / 100
    k = cac_decay_pct / 100

    AOV = revenue / orders
    cogs_per_order = cogs / orders
    cac = ad_spend / orders

    baseline_profit = revenue - cogs - ad_spend - revenue * rr

    new_spend = ad_spend * (1 + g)
    new_cac = cac * (1 + k * g)
    new_orders = new_spend / new_cac if new_cac > 0 else orders

    new_revenue = AOV * new_orders
    new_cogs = cogs_per_order * new_orders
    new_profit = new_revenue - new_cogs - new_spend - new_revenue * rr

    return {
        "baseline_profit": baseline_profit,
        "new_profit": new_profit,
        "cac": cac,
        "new_cac": new_cac
    }


def safe_ceiling(revenue, cogs, ad_spend, orders, refund_rate, cac_decay_pct):
    last_safe = 0
    for pct in range(0, 301):
        r = simulate(revenue, cogs, ad_spend, orders,
                     refund_rate, pct, cac_decay_pct)
        if r and r["new_profit"] >= 0:
            last_safe = pct
        else:
            break
    return last_safe


# =========================
# Mode
# =========================
mode = st.radio(
    t["mode"],
    [t["manual_finance"], t["manual_funnel"], t["csv"]]
)

st.divider()

revenue = 0
cogs = 0
ad_spend = 0
orders = 1
refund_rate = 0

# =========================
# Manual Finance
# =========================
if mode == t["manual_finance"]:
    revenue = st.number_input(t["revenue"], min_value=0.0)
    cogs = st.number_input(t["cogs"], min_value=0.0)
    ad_spend = st.number_input(t["ad_spend"], min_value=0.0)
    orders = st.number_input(t["orders"], min_value=1)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

# =========================
# Manual Funnel
# =========================
elif mode == t["manual_funnel"]:
    spend = st.number_input(t["spend"], min_value=0.0)
    results = st.number_input(t["results"], min_value=0.0)
    close_rate = st.number_input(t["close_rate"], 0.0, 1.0, 0.2)
    AOV = st.number_input(t["aov"], min_value=0.0)
    cogs_per_order = st.number_input(t["cogs_per_order"], min_value=0.0)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

    orders = max(results * close_rate, 1)
    revenue = AOV * orders
    cogs = cogs_per_order * orders
    ad_spend = spend

# =========================
# CSV Upload (Meta-safe)
# =========================
elif mode == t["csv"]:

    from io import StringIO

    def read_meta_csv(uploaded_file):
        raw = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        lines = raw.splitlines()

        header_idx = 0
        for i, line in enumerate(lines[:200]):
            if ("Campaign delivery" in line and "Results" in line) or \
               ("Amount spent" in line and "Results" in line):
                header_idx = i
                break

        table = "\n".join(lines[header_idx:])
        return pd.read_csv(StringIO(table), sep=None, engine="python")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if not uploaded:
        st.info("Upload Meta export CSV.")
        st.stop()

    df = read_meta_csv(uploaded)

    st.write("Preview:")
    st.dataframe(df.head(), use_container_width=True)

    # ---------- auto column detection ----------
    def pick_col(df, keywords):
        for col in df.columns:
            for k in keywords:
                if k.lower() in col.lower():
                    return col
        return None

    spend_col = pick_col(df, ["Amount spent", "Spend"])
    results_col = pick_col(df, ["Results"])

    if not spend_col or not results_col:
        st.error("Could not auto-detect Spend or Results column.")
        st.stop()

    meta_spend = pd.to_numeric(df[spend_col], errors="coerce").fillna(0).sum()
    meta_results = pd.to_numeric(df[results_col], errors="coerce").fillna(0).sum()

    st.write(f"Total Spend: {round(meta_spend,2)}")
    st.write(f"Total Results: {int(meta_results)}")

    if meta_results <= 0:
        st.warning("Results column sums to 0. Check your export.")
        st.stop()

    close_rate = st.number_input(t["close_rate"], 0.0, 1.0, 0.2)
    AOV = st.number_input(t["aov"], min_value=0.0)
    cogs_per_order = st.number_input(t["cogs_per_order"], min_value=0.0)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

    orders = max(meta_results * close_rate, 1)
    revenue = AOV * orders
    cogs = cogs_per_order * orders
    ad_spend = meta_spend

# =========================
# Scaling Inputs
# =========================
st.subheader(t["scaling"])
spend_growth = st.slider(t["spend_increase"], 0, 300, 50)
cac_decay = st.slider(t["cac_decay"], 0, 100, 25)

# =========================
# Analyze
# =========================
if st.button(t["analyze"]):

    result = simulate(revenue, cogs, ad_spend, orders,
                      refund_rate, spend_growth, cac_decay)

    if result:

        st.subheader(t["baseline"])
        st.write(f"{t['profit']}: {round(result['baseline_profit'], 2)}")

        st.subheader(t["simulation"])
        st.write(f"{t['profit']}: {round(result['new_profit'], 2)}")

        safe = safe_ceiling(revenue, cogs, ad_spend,
                            orders, refund_rate, cac_decay)

        st.subheader(t["safe"])
        st.write(f"{safe}%")

        st.subheader(t["scenario"])
        rows = []
        for pct in [0, 25, 50, 75, 100, 150, 200]:
            r = simulate(revenue, cogs, ad_spend,
                         orders, refund_rate, pct, cac_decay)
            rows.append({
                "Scale %": pct,
                "Profit": round(r["new_profit"], 2)
            })
        st.dataframe(pd.DataFrame(rows))
