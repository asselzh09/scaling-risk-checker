import streamlit as st
import pandas as pd

st.set_page_config(page_title="Scaling Risk Checker", layout="centered")

# -----------------------------
# Language selector
# -----------------------------
lang = st.selectbox("Language / Язык", ["English", "Русский"])

TEXT = {
    "English": {
        "title": "Scaling Risk Checker",
        "subtitle": "Upload Meta export or input manually. Then simulate scaling.",
        "mode": "Choose input mode",
        "manual_finance": "Manual finance",
        "meta_csv": "Meta CSV upload",
        "manual_funnel": "Manual funnel (Meta-like)",
        "revenue": "Total Revenue ($)",
        "cogs": "Total COGS ($)",
        "ad_spend": "Ad Spend ($)",
        "orders": "Orders",
        "refund": "Refund Rate (%)",
        "spend": "Spend ($)",
        "conversations": "Messaging conversations",
        "clicks": "Clicks (optional)",
        "impressions": "Impressions (optional)",
        "close_rate": "Close rate (orders / conversations)",
        "aov": "Average Order Value ($)",
        "cogs_per_order": "COGS per order ($)",
        "scaling": "Scaling assumptions",
        "spend_increase": "Simulate Spend Increase (%)",
        "cac_decay": "CAC deterioration per +100% spend (%)",
        "analyze": "Analyze",
        "baseline": "Baseline",
        "profit": "Profit",
        "constraint": "Main Constraint",
        "simulation": "Scaling Simulation",
        "safe_ceiling": "Safe Scaling Ceiling",
        "max_safe": "Maximum safe spend increase (profit ≥ 0)",
        "scenario": "Scaling Scenario Table"
    },
    "Русский": {
        "title": "Проверка Риска Масштабирования",
        "subtitle": "Загрузите Meta CSV или введите данные вручную. Затем смоделируйте масштабирование.",
        "mode": "Выберите режим ввода",
        "manual_finance": "Финансы вручную",
        "meta_csv": "Загрузка Meta CSV",
        "manual_funnel": "Воронка вручную (как Meta)",
        "revenue": "Общая выручка ($)",
        "cogs": "Себестоимость ($)",
        "ad_spend": "Рекламные расходы ($)",
        "orders": "Количество заказов",
        "refund": "Процент возвратов (%)",
        "spend": "Расход ($)",
        "conversations": "Диалоги (сообщения)",
        "clicks": "Клики (опционально)",
        "impressions": "Показы (опционально)",
        "close_rate": "Конверсия в заказ (заказы / диалоги)",
        "aov": "Средний чек ($)",
        "cogs_per_order": "Себестоимость на заказ ($)",
        "scaling": "Параметры масштабирования",
        "spend_increase": "Увеличение бюджета (%)",
        "cac_decay": "Ухудшение CAC при +100% бюджета (%)",
        "analyze": "Рассчитать",
        "baseline": "Базовые показатели",
        "profit": "Прибыль",
        "constraint": "Основное ограничение",
        "simulation": "Симуляция масштабирования",
        "safe_ceiling": "Предел безопасного масштабирования",
        "max_safe": "Максимальное безопасное увеличение бюджета (прибыль ≥ 0)",
        "scenario": "Таблица сценариев масштабирования"
    }
}

t = TEXT[lang]

st.title(t["title"])
st.write(t["subtitle"])

# -----------------------------
# Core scaling model
# -----------------------------
def simulate_scale(revenue, cogs, ad_spend, orders, refund_rate_pct,
                   spend_increase_pct, cac_deterioration_per_100_pct):

    rr = refund_rate_pct / 100
    g = spend_increase_pct / 100
    k = cac_deterioration_per_100_pct / 100

    AOV = revenue / orders if orders > 0 else 0
    cogs_per_order = cogs / orders if orders > 0 else 0
    cac = ad_spend / orders if orders > 0 else 0

    baseline_profit = revenue - cogs - ad_spend - revenue * rr
    break_even_cac = AOV - cogs_per_order - AOV * rr
    margin_buffer = ((break_even_cac - cac) / break_even_cac) if break_even_cac > 0 else 0

    new_spend = ad_spend * (1 + g)
    new_cac = cac * (1 + k * g) if cac > 0 else 0
    new_orders = new_spend / new_cac if new_cac > 0 else orders

    new_revenue = AOV * new_orders
    new_cogs = cogs_per_order * new_orders
    new_profit = new_revenue - new_cogs - new_spend - new_revenue * rr

    return {
        "AOV": AOV,
        "cogs_per_order": cogs_per_order,
        "cac": cac,
        "break_even_cac": break_even_cac,
        "margin_buffer": margin_buffer,
        "baseline_profit": baseline_profit,
        "new_spend": new_spend,
        "new_cac": new_cac,
        "new_orders": new_orders,
        "new_revenue": new_revenue,
        "new_profit": new_profit
    }


def find_safe_max_scale_pct(revenue, cogs, ad_spend, orders,
                            refund_rate_pct, cac_deterioration_per_100_pct):

    last_safe = 0
    for pct in range(0, 301):
        r = simulate_scale(
            revenue, cogs, ad_spend, orders,
            refund_rate_pct, pct,
            cac_deterioration_per_100_pct
        )
        if r["new_profit"] >= 0:
            last_safe = pct
        else:
            break
    return last_safe


# -----------------------------
# Mode selector
# -----------------------------
mode = st.radio(
    t["mode"],
    [t["manual_finance"], t["meta_csv"], t["manual_funnel"]]
)

st.divider()

revenue = 0
cogs = 0
ad_spend = 0
orders = 1
refund_rate = 0

# -----------------------------
# Manual finance
# -----------------------------
if mode == t["manual_finance"]:
    revenue = st.number_input(t["revenue"], min_value=0.0)
    cogs = st.number_input(t["cogs"], min_value=0.0)
    ad_spend = st.number_input(t["ad_spend"], min_value=0.0)
    orders = st.number_input(t["orders"], min_value=1)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

elif mode == t["meta_csv"]:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if not uploaded:
        st.info("Upload your Meta export CSV.")
        st.stop()

    df = pd.read_csv(uploaded)
    st.write("Preview:")
    st.dataframe(df.head(), use_container_width=True)

    cols = df.columns.tolist()

    col_spend = st.selectbox("Spend column", cols)
    col_results = st.selectbox("Results column", cols)
    col_indicator = st.selectbox("Result indicator column", cols)

    msg_mask = df[col_indicator].astype(str).str.contains(
        "messaging_conversation_started",
        case=False,
        na=False
    )

    df_msg = df[msg_mask]

    if df_msg.empty:
        st.error("No messaging_conversation_started rows found.")
        st.stop()

    meta_spend = pd.to_numeric(df_msg[col_spend], errors="coerce").fillna(0).sum()
    meta_convos = pd.to_numeric(df_msg[col_results], errors="coerce").fillna(0).sum()

    st.write(f"Spend: {meta_spend}")
    st.write(f"Conversations: {meta_convos}")

    if meta_convos <= 0:
        st.error("Conversations = 0.")
        st.stop()

    close_rate = st.number_input(t["close_rate"], min_value=0.0, max_value=1.0, value=0.2)
    AOV = st.number_input(t["aov"], min_value=0.0)
    cogs_per_order = st.number_input(t["cogs_per_order"], min_value=0.0)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

    orders = max(meta_convos * close_rate, 1)
    revenue = AOV * orders
    cogs = cogs_per_order * orders
    ad_spend = meta_spend

# -----------------------------
# Manual funnel
# -----------------------------
elif mode == t["manual_funnel"]:
    spend = st.number_input(t["spend"], min_value=0.0)
    conversations = st.number_input(t["conversations"], min_value=0.0)
    close_rate = st.number_input(t["close_rate"], min_value=0.0, max_value=1.0, value=0.2)
    AOV = st.number_input(t["aov"], min_value=0.0)
    cogs_per_order = st.number_input(t["cogs_per_order"], min_value=0.0)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0)

    orders = max(conversations * close_rate, 1)
    revenue = AOV * orders
    cogs = cogs_per_order * orders
    ad_spend = spend

# -----------------------------
# Scaling inputs
# -----------------------------
st.subheader(t["scaling"])
spend_increase_pct = st.slider(t["spend_increase"], 0, 300, 50)
cac_deterioration_per_100 = st.slider(t["cac_decay"], 0, 100, 25)

# -----------------------------
# Analyze
# -----------------------------
if st.button(t["analyze"]):

    result = simulate_scale(
        revenue, cogs, ad_spend, orders,
        refund_rate, spend_increase_pct,
        cac_deterioration_per_100
    )

    safe_pct = find_safe_max_scale_pct(
        revenue, cogs, ad_spend, orders,
        refund_rate, cac_deterioration_per_100
    )

    st.subheader(t["baseline"])
    st.write(f"CAC: {result['cac']:.2f}")
    st.write(f"{t['profit']}: {result['baseline_profit']:.2f}")

    st.subheader(t["simulation"])
    st.write(f"{t['profit']}: {result['new_profit']:.2f}")

    st.subheader(t["safe_ceiling"])
    st.write(f"{t['max_safe']}: {safe_pct}%")

    st.subheader(t["scenario"])
    rows = []
    for pct in [0, 25, 50, 75, 100, 150, 200]:
        r = simulate_scale(
            revenue, cogs, ad_spend, orders,
            refund_rate, pct,
            cac_deterioration_per_100
        )
        rows.append({
            "Scale %": pct,
            "Profit": round(r["new_profit"], 2)
        })
    st.dataframe(pd.DataFrame(rows))
