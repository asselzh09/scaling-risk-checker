#testchange
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ad Budget Planner", layout="centered")

# =========================
# Language (UI only)
# =========================
lang = st.selectbox("Language / Язык", ["English", "Русский"])

T = {
    "English": {
        "title": "Ad Budget Planner",
        "subtitle": "Estimate whether your ad budget is safe, profitable, and scalable.",

        "biz_stage": "Choose your situation",
        "new_business": "New business",
        "existing_business": "Existing business",

        "mode": "Choose input mode",
        "m_manual": "Enter business numbers manually",
        "m_csv": "Upload ad report (Meta CSV)",
        "m_funnel": "Enter ad funnel manually",

        "rev": "Total Revenue ($)",
        "cogs": "Total COGS ($)",
        "spend": "Ad Spend ($)",
        "orders": "Orders",
        "refund": "Refund Rate (%)",

        "upload_meta": "Upload ad report",
        "upload_csv": "Upload CSV",
        "upload_hint": "Upload Meta CSV to auto-fill ad spend and conversations. Then enter average order value, product cost, and conversion rate.",
        "preview": "Preview",

        "camp_col": "Campaign name column",
        "spend_col": "Ad spend column",
        "results_col": "Results column",
        "indicator_col": "Result type column",
        "select_campaigns": "Select campaigns to include",

        "derived": "### Derived from CSV",
        "bridge": "Connect ad data to business numbers",

        "close_rate": "Conversation to order rate",
        "aov": "Average order value ($)",
        "cogs_po": "Product cost per order ($)",

        "manual_funnel_header": "Manual ad funnel inputs",
        "spend_f": "Ad spend ($)",
        "convos": "Messaging conversations",
        "clicks": "Clicks (optional)",
        "impr": "Impressions (optional)",

        "scale_header": "Growth assumptions",
        "scale_inc": "Planned ad budget increase (%)",
        "scale_decay": "If budget increases, customer cost becomes more expensive by (%) per +100% spend",
        "note": "Example: 25% means if you double spend, getting one customer becomes about 25% more expensive.",

        "analyze": "Analyze",

        "no_msg_rows": "No rows found where Result indicator contains 'messaging_conversation_started'.",
        "conv_zero": "Conversations sum to 0. Can't proceed.",
        "warn_orders": "Estimated orders are below 1. I’ll still run with Orders=1 to avoid divide-by-zero.",
        "warn_convos": "Conversations must be > 0 to use this mode.",

        "status_hold": "🔴 HOLD — You are already losing money.",
        "status_fragile": "🟠 FRAGILE — Small efficiency loss makes you unprofitable.",
        "status_safe": "🟢 CONTROLLED — Your unit economics can handle some growth.",

        "bottleneck_neg": "Your unit economics are negative even before ads.",
        "bottleneck_cac": "Customer acquisition cost is your main growth risk.",
        "bottleneck_ref": "Refunds are reducing profitability.",
        "bottleneck_margin": "Low margin limits safe scaling.",
        "bottleneck_ok": "No major structural problem detected.",

        "baseline_hdr": "Current business snapshot",
        "meta_diag": "Ad diagnostics (optional)",
        "main_constraint": "Main Constraint",
        "sim_hdr": "Growth simulation",
        "safe_hdr": "Safe Growth Limit",
        "safe_line": "Maximum safe ad budget increase (profit ≥ 0)",
        "low_ceiling": "Low ceiling: aggressive scaling may quickly turn unprofitable unless margin, refunds, or CAC improve.",
        "table_hdr": "Scenario Table",
        "new_cac_na": "New customer cost: n/a (baseline CAC is 0)",

        # New business mode
        "newbiz_header": "New business planning",
        "planned_budget": "Planned ad budget ($)",
        "expected_cac": "Expected cost to get one customer ($)",
        "target_profit": "Target profit ($, optional)",
        "expected_orders": "Expected customers",
        "expected_revenue": "Expected revenue",
        "expected_profit": "Expected profit",
        "rec_budget": "Suggested ad budget for testing",
        "newbiz_result": "New business estimate",
        "newbiz_note": "This mode is for planning your first ad budget before you have real campaign data.",
    },
    "Русский": {
        "title": "Ad Budget Planner",
        "subtitle": "Оцените, безопасен ли ваш рекламный бюджет, будет ли он прибыльным и можно ли его масштабировать.",

        "biz_stage": "Выберите вашу ситуацию",
        "new_business": "Новый бизнес",
        "existing_business": "Есть действующий бизнес",

        "mode": "Выберите способ ввода",
        "m_manual": "Ввести цифры бизнеса вручную",
        "m_csv": "Загрузить рекламный отчёт (Meta CSV)",
        "m_funnel": "Ввести рекламную воронку вручную",

        "rev": "Общая выручка ($)",
        "cogs": "Общая себестоимость ($)",
        "spend": "Расход на рекламу ($)",
        "orders": "Заказы",
        "refund": "Процент возвратов (%)",

        "upload_meta": "Загрузить рекламный отчёт",
        "upload_csv": "Загрузить CSV",
        "upload_hint": "Загрузите Meta CSV, чтобы автоматически заполнить рекламный расход и диалоги. Затем введите средний чек, себестоимость и конверсию.",
        "preview": "Превью",

        "camp_col": "Колонка названия кампании",
        "spend_col": "Колонка расхода на рекламу",
        "results_col": "Колонка результатов",
        "indicator_col": "Колонка типа результата",
        "select_campaigns": "Выберите кампании",

        "derived": "### Получено из CSV",
        "bridge": "Связка рекламных данных с бизнес-данными",

        "close_rate": "Конверсия из диалога в заказ",
        "aov": "Средний чек ($)",
        "cogs_po": "Себестоимость одного заказа ($)",

        "manual_funnel_header": "Ввод рекламной воронки вручную",
        "spend_f": "Расход на рекламу ($)",
        "convos": "Диалоги",
        "clicks": "Клики (опционально)",
        "impr": "Показы (опционально)",

        "scale_header": "Параметры роста",
        "scale_inc": "Планируемое увеличение рекламного бюджета (%)",
        "scale_decay": "Если бюджет растёт, стоимость клиента дорожает на (%) при +100% бюджета",
        "note": "Пример: 25% означает, что если вы удвоите бюджет, привлечение одного клиента станет примерно на 25% дороже.",

        "analyze": "Рассчитать",

        "no_msg_rows": "Не найдено строк, где Result indicator содержит 'messaging_conversation_started'.",
        "conv_zero": "Сумма диалогов = 0. Невозможно продолжить.",
        "warn_orders": "Расчётные заказы меньше 1. Я всё равно запущу с Orders=1, чтобы избежать деления на ноль.",
        "warn_convos": "Диалоги должны быть > 0 для этого режима.",

        "status_hold": "🔴 HOLD — вы уже в минусе.",
        "status_fragile": "🟠 FRAGILE — небольшое ухудшение эффективности делает вас убыточными.",
        "status_safe": "🟢 CONTROLLED — юнит-экономика выдерживает некоторый рост.",

        "bottleneck_neg": "Юнит-экономика отрицательная ещё до рекламы.",
        "bottleneck_cac": "Стоимость привлечения клиента — главный риск роста.",
        "bottleneck_ref": "Возвраты снижают прибыльность.",
        "bottleneck_margin": "Низкая маржа ограничивает безопасный рост.",
        "bottleneck_ok": "Серьёзных структурных проблем не обнаружено.",

        "baseline_hdr": "Текущая картина бизнеса",
        "meta_diag": "Диагностика рекламы (опционально)",
        "main_constraint": "Главное ограничение",
        "sim_hdr": "Симуляция роста",
        "safe_hdr": "Предел безопасного роста",
        "safe_line": "Максимальное безопасное увеличение бюджета (прибыль ≥ 0)",
        "low_ceiling": "Низкий предел: агрессивный рост может быстро увести вас в минус, если не улучшить маржу, возвраты или CAC.",
        "table_hdr": "Таблица сценариев",
        "new_cac_na": "Новая стоимость клиента: n/a (базовый CAC = 0)",

        # New business mode
        "newbiz_header": "Планирование для нового бизнеса",
        "planned_budget": "Планируемый рекламный бюджет ($)",
        "expected_cac": "Ожидаемая стоимость привлечения одного клиента ($)",
        "target_profit": "Желаемая прибыль ($, опционально)",
        "expected_orders": "Ожидаемые клиенты",
        "expected_revenue": "Ожидаемая выручка",
        "expected_profit": "Ожидаемая прибыль",
        "rec_budget": "Рекомендуемый тестовый бюджет",
        "newbiz_result": "Оценка для нового бизнеса",
        "newbiz_note": "Этот режим нужен для планирования первого рекламного бюджета, если у вас ещё нет реальных рекламных данных.",
    },
}
t = T[lang]

# =========================
# Style
# =========================
st.markdown(
    """
<style>
.big-status {
    font-size: 24px;
    font-weight: bold;
    padding: 15px;
    border-radius: 8px;
}
.safe { background-color: #d4edda; color: #155724; }
.fragile { background-color: #fff3cd; color: #856404; }
.hold { background-color: #f8d7da; color: #721c24; }
.small-note { color: #666; font-size: 13px; }
.kpi { font-size: 16px; }
</style>
""",
    unsafe_allow_html=True,
)

st.title(t["title"])
st.write(t["subtitle"])

# -----------------------------
# Core model
# -----------------------------
def simulate_scale(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    spend_increase_pct: float,
    cac_deterioration_per_100_pct: float,
):
    rr = refund_rate_pct / 100.0
    g = spend_increase_pct / 100.0
    k = cac_deterioration_per_100_pct / 100.0

    orders = float(orders) if orders is not None else 0.0
    revenue = float(revenue) if revenue is not None else 0.0
    cogs = float(cogs) if cogs is not None else 0.0
    ad_spend = float(ad_spend) if ad_spend is not None else 0.0

    AOV = revenue / orders if orders > 0 else 0.0
    cogs_per_order = cogs / orders if orders > 0 else 0.0
    cac = ad_spend / orders if orders > 0 else 0.0

    baseline_refund_cost = revenue * rr
    baseline_profit = revenue - cogs - ad_spend - baseline_refund_cost

    break_even_cac = (AOV - cogs_per_order - (AOV * rr))
    margin_buffer = ((break_even_cac - cac) / break_even_cac) if break_even_cac > 0 else 0.0

    new_spend = ad_spend * (1 + g)

    if cac <= 0:
        new_cac = 0.0
        new_orders = orders
    else:
        new_cac = cac * (1 + k * g)
        new_orders = (new_spend / new_cac) if new_cac > 0 else orders

    new_revenue = AOV * new_orders
    new_cogs = cogs_per_order * new_orders
    new_refund_cost = new_revenue * rr
    new_profit = new_revenue - new_cogs - new_spend - new_refund_cost

    return {
        "AOV": AOV,
        "cogs_per_order": cogs_per_order,
        "cac": cac,
        "break_even_cac": break_even_cac,
        "margin_buffer": margin_buffer,
        "baseline_profit": baseline_profit,
        "baseline_refund_cost": baseline_refund_cost,
        "new_spend": new_spend,
        "new_cac": new_cac,
        "new_orders": new_orders,
        "new_revenue": new_revenue,
        "new_cogs": new_cogs,
        "new_refund_cost": new_refund_cost,
        "new_profit": new_profit,
    }

def find_safe_max_scale_pct(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    cac_deterioration_per_100_pct: float,
    max_search_pct: int = 300,
):
    last_safe = 0
    for pct in range(0, max_search_pct + 1):
        r = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate_pct,
            spend_increase_pct=pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
        )
        if r["new_profit"] >= 0:
            last_safe = pct
        else:
            break
    return last_safe

# -----------------------------
# Top hierarchy
# -----------------------------
BIZ_STAGE = {
    "new": t["new_business"],
    "existing": t["existing_business"],
}
biz_stage_label = st.radio(t["biz_stage"], list(BIZ_STAGE.values()), horizontal=True)
biz_stage = [k for k, v in BIZ_STAGE.items() if v == biz_stage_label][0]

st.divider()

# =============================
# NEW BUSINESS MODE
# =============================
if biz_stage == "new":
    st.subheader(t["newbiz_header"])
    st.caption(t["newbiz_note"])

    AOV = st.number_input(t["aov"], min_value=0.0, value=0.0)
    cogs_per_order = st.number_input(t["cogs_po"], min_value=0.0, value=0.0)
    expected_cac = st.number_input(t["expected_cac"], min_value=0.0, value=0.0)
    planned_budget = st.number_input(t["planned_budget"], min_value=0.0, value=0.0)
    refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0, value=0.0)
    target_profit = st.number_input(t["target_profit"], min_value=0.0, value=0.0)

    if st.button(t["analyze"]):
        rr = refund_rate / 100.0

        expected_orders = planned_budget / expected_cac if expected_cac > 0 else 0.0
        expected_revenue = expected_orders * AOV
        expected_cogs = expected_orders * cogs_per_order
        expected_refunds = expected_revenue * rr
        expected_profit = expected_revenue - expected_cogs - planned_budget - expected_refunds

        unit_profit_before_ads = AOV - cogs_per_order - (AOV * rr)

        if expected_profit < 0:
            status = t["status_hold"]
            status_class = "hold"
        elif unit_profit_before_ads > 0 and expected_cac >= unit_profit_before_ads * 0.85:
            status = t["status_fragile"]
            status_class = "fragile"
        else:
            status = t["status_safe"]
            status_class = "safe"

        suggested_budget = 0.0
        if expected_cac > 0 and target_profit > 0 and unit_profit_before_ads > expected_cac:
            profit_per_order_after_ads = unit_profit_before_ads - expected_cac
            needed_orders = target_profit / profit_per_order_after_ads
            suggested_budget = needed_orders * expected_cac

        st.subheader(t["newbiz_result"])
        st.write(f"{t['expected_orders']}: **{expected_orders:.1f}**")
        st.write(f"{t['expected_revenue']}: **${expected_revenue:.2f}**")
        st.write(f"{t['expected_profit']}: **${expected_profit:.2f}**")
        if suggested_budget > 0:
            st.write(f"{t['rec_budget']}: **${suggested_budget:.2f}**")
        st.markdown(f'<div class="big-status {status_class}">{status}</div>', unsafe_allow_html=True)

# =============================
# EXISTING BUSINESS MODE
# =============================
else:
    MODE = {
        "manual": t["m_manual"],
        "csv": t["m_csv"],
        "funnel": t["m_funnel"],
    }
    mode_label = st.radio(t["mode"], list(MODE.values()), horizontal=True)
    mode = [k for k, v in MODE.items() if v == mode_label][0]

    st.divider()

    revenue = 0.0
    cogs = 0.0
    ad_spend = 0.0
    orders = 1.0
    refund_rate = 0.0
    diag = {}

    if mode == "manual":
        revenue = st.number_input(t["rev"], min_value=0.0, value=0.0)
        cogs = st.number_input(t["cogs"], min_value=0.0, value=0.0)
        ad_spend = st.number_input(t["spend"], min_value=0.0, value=0.0)
        orders = st.number_input(t["orders"], min_value=1, value=1)
        refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0, value=0.0)

    elif mode == "csv":
        st.subheader(t["upload_meta"])
        uploaded = st.file_uploader(t["upload_csv"], type=["csv"])

        if not uploaded:
            st.info(t["upload_hint"])
            st.stop()

        df = pd.read_csv(uploaded)
        st.write(t["preview"])
        st.dataframe(df.head(10), use_container_width=True)

        cols = list(df.columns)

        def guess_index(name_candidates):
            for c in name_candidates:
                if c in cols:
                    return cols.index(c)
            return 0

        col_campaign = st.selectbox(t["camp_col"], cols, index=guess_index(["Campaign name", "Campaign", "campaign_name"]))
        col_spend = st.selectbox(t["spend_col"], cols, index=guess_index(["Amount spent (MYR)", "Amount spent", "Spend"]))
        col_results = st.selectbox(t["results_col"], cols, index=guess_index(["Results", "Result", "results"]))
        col_indicator = st.selectbox(t["indicator_col"], cols, index=guess_index(["Result indicator", "Action type", "Result type", "result_indicator"]))

        msg_mask = df[col_indicator].astype(str).str.contains("messaging_conversation_started", case=False, na=False)
        df_msg = df[msg_mask].copy()

        if df_msg.empty:
            st.error(t["no_msg_rows"])
            st.stop()

        campaigns = sorted(df_msg[col_campaign].astype(str).unique().tolist())
        selected = st.multiselect(t["select_campaigns"], campaigns, default=campaigns)

        df_sel = df_msg[df_msg[col_campaign].astype(str).isin(selected)].copy()
        df_sel[col_spend] = pd.to_numeric(df_sel[col_spend], errors="coerce").fillna(0.0)
        df_sel[col_results] = pd.to_numeric(df_sel[col_results], errors="coerce").fillna(0.0)

        meta_spend = float(df_sel[col_spend].sum())
        meta_convos = float(df_sel[col_results].sum())

        st.markdown(t["derived"])
        st.write(f"Spend (selected): **{meta_spend:.2f}**")
        st.write(f"Messaging conversations (selected): **{meta_convos:.0f}**")

        if meta_convos <= 0:
            st.error(t["conv_zero"])
            st.stop()

        cpa_msg = meta_spend / meta_convos
        st.write(f"Cost per conversation: **{cpa_msg:.2f}**")

        st.divider()
        st.subheader(t["bridge"])

        close_rate = st.number_input(t["close_rate"], min_value=0.0, max_value=1.0, value=0.20)
        AOV = st.number_input(t["aov"], min_value=0.0, value=0.0)
        cogs_per_order = st.number_input(t["cogs_po"], min_value=0.0, value=0.0)
        refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0, value=0.0)

        inferred_orders = meta_convos * close_rate
        if inferred_orders < 1:
            st.warning(t["warn_orders"])
            inferred_orders = 1.0

        ad_spend = meta_spend
        orders = float(inferred_orders)
        revenue = AOV * orders
        cogs = cogs_per_order * orders

        diag = {
            "cpa_msg": cpa_msg,
            "close_rate": close_rate,
            "implied_cac": (cpa_msg / close_rate) if close_rate > 0 else None,
        }

    else:
        st.subheader(t["manual_funnel_header"])
        spend = st.number_input(t["spend_f"], min_value=0.0, value=0.0)
        conversations = st.number_input(t["convos"], min_value=0.0, value=0.0)
        clicks = st.number_input(t["clicks"], min_value=0.0, value=0.0)
        impressions = st.number_input(t["impr"], min_value=0.0, value=0.0)

        close_rate = st.number_input(t["close_rate"], min_value=0.0, max_value=1.0, value=0.20)
        AOV = st.number_input(t["aov"], min_value=0.0, value=0.0)
        cogs_per_order = st.number_input(t["cogs_po"], min_value=0.0, value=0.0)
        refund_rate = st.number_input(t["refund"], min_value=0.0, max_value=100.0, value=0.0)

        if conversations <= 0:
            st.warning(t["warn_convos"])
            st.stop()

        cpa_msg = spend / conversations
        inferred_orders = conversations * close_rate
        if inferred_orders < 1:
            st.warning(t["warn_orders"])
            inferred_orders = 1.0

        ad_spend = float(spend)
        orders = float(inferred_orders)
        revenue = AOV * orders
        cogs = cogs_per_order * orders

        ctr = (clicks / impressions) if impressions > 0 else None
        cpc = (spend / clicks) if clicks > 0 else None
        cvr_msg = (conversations / clicks) if clicks > 0 else None

        diag = {
            "cpa_msg": cpa_msg,
            "close_rate": close_rate,
            "ctr": ctr,
            "cpc": cpc,
            "cvr_msg": cvr_msg,
            "implied_cac": (cpa_msg / close_rate) if close_rate > 0 else None,
        }

    st.divider()
    st.subheader(t["scale_header"])
    spend_increase_pct = st.slider(t["scale_inc"], 0, 300, 50)
    cac_deterioration_per_100 = st.slider(t["scale_decay"], 0, 100, 25)

    st.markdown(f'<div class="small-note">{t["note"]}</div>', unsafe_allow_html=True)

    if st.button(t["analyze"]):
        res = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate,
            spend_increase_pct=spend_increase_pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100,
        )

        if res["baseline_profit"] < 0:
            status = t["status_hold"]
            status_class = "hold"
        elif res["margin_buffer"] < 0.15:
            status = t["status_fragile"]
            status_class = "fragile"
        else:
            status = t["status_safe"]
            status_class = "safe"

        AOV = res["AOV"]
        cogs_per_order = res["cogs_per_order"]
        cac = res["cac"]
        break_even_cac = res["break_even_cac"]

        if break_even_cac <= 0:
            bottleneck = t["bottleneck_neg"]
        elif cac > break_even_cac:
            bottleneck = t["bottleneck_cac"]
        elif refund_rate > 8:
            bottleneck = t["bottleneck_ref"]
        elif AOV > 0 and (AOV - cogs_per_order) / AOV < 0.3:
            bottleneck = t["bottleneck_margin"]
        else:
            bottleneck = t["bottleneck_ok"]

        safe_scale_pct = find_safe_max_scale_pct(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate,
            cac_deterioration_per_100_pct=cac_deterioration_per_100,
            max_search_pct=300,
        )

        st.subheader(t["baseline_hdr"])
        st.write(f"Revenue: **${revenue:.2f}**")
        st.write(f"COGS: **${cogs:.2f}**")
        st.write(f"Ad Spend: **${ad_spend:.2f}**")
        st.write(f"Orders: **{orders:.1f}**")
        st.write(f"Average order value: **${AOV:.2f}**")
        st.write(f"Product cost per order: **${cogs_per_order:.2f}**")
        st.write(f"Customer acquisition cost: **${cac:.2f}**")
        st.write(f"Max cost per customer before losing profit: **${break_even_cac:.2f}**")
        st.write(f"Current Profit: **${res['baseline_profit']:.2f}**")
        st.markdown(f'<div class="big-status {status_class}">{status}</div>', unsafe_allow_html=True)

        if diag:
            st.subheader(t["meta_diag"])
            if diag.get("cpa_msg") is not None:
                st.write(f"Cost per conversation: **{diag['cpa_msg']:.2f}**")
            if diag.get("close_rate") is not None:
                st.write(f"Conversation to order rate: **{diag['close_rate']:.2%}**")
            if diag.get("implied_cac") is not None:
                st.write(f"Estimated customer acquisition cost: **{diag['implied_cac']:.2f}**")
            if diag.get("ctr") is not None:
                st.write(f"CTR: **{diag['ctr']:.2%}**")
            if diag.get("cpc") is not None:
                st.write(f"CPC: **{diag['cpc']:.2f}**")
            if diag.get("cvr_msg") is not None:
                st.write(f"Click to conversation rate: **{diag['cvr_msg']:.2%}**")

        st.subheader(t["main_constraint"])
        st.write(bottleneck)

        st.subheader(t["sim_hdr"])
        st.write(f"New ad spend: **${res['new_spend']:.2f}**")
        st.write(f"New customer acquisition cost: **${res['new_cac']:.2f}**" if res["new_cac"] > 0 else t["new_cac_na"])
        st.write(f"Forecast orders: **{res['new_orders']:.1f}**")
        st.write(f"Forecast revenue: **${res['new_revenue']:.2f}**")
        st.write(f"Forecast profit: **${res['new_profit']:.2f}**")

        st.subheader(t["safe_hdr"])
        st.write(f"{t['safe_line']}: **{safe_scale_pct}%**")
        if safe_scale_pct < 50:
            st.warning(t["low_ceiling"])

        st.subheader(t["table_hdr"])
        scenarios = [0, 25, 50, 75, 100, 150, 200, 250, 300]
        rows = []
        for pct in scenarios:
            r = simulate_scale(
                revenue=revenue,
                cogs=cogs,
                ad_spend=ad_spend,
                orders=orders,
                refund_rate_pct=refund_rate,
                spend_increase_pct=pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
            )
            rows.append(
                {
                    "Spend Increase %": pct,
                    "Forecast Spend": round(r["new_spend"], 2),
                    "Forecast CAC": round(r["new_cac"], 2) if r["new_cac"] > 0 else None,
                    "Forecast Orders": round(r["new_orders"], 1),
                    "Forecast Revenue": round(r["new_revenue"], 2),
                    "Forecast Profit": round(r["new_profit"], 2),
                }
            )

        df_out = pd.DataFrame(rows)

        def profit_flag(p):
            if p < 0:
                return "🔴"
            if revenue > 0 and p < (0.05 * revenue):
                return "🟠"
            return "🟢"

        df_out.insert(0, "Status", df_out["Forecast Profit"].apply(profit_flag))
        st.dataframe(df_out, use_container_width=True)