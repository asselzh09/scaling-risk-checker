import io
import re

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from logic import (
    build_profit_curve,
    evaluate_decision_state,
    find_loss_point_spend,
    find_safe_max_scale_pct,
    format_money as logic_format_money,
    get_ads_verdict,
    get_best_next_move,
    get_bottleneck,
    get_data_quality_note,
    get_recommendation,
    get_recommendation_v2,
    get_status,
    is_projection_only,
    parse_number_series,
    profit_flag,
    safe_div,
    simulate_scale,
)
from texts import T

st.set_page_config(page_title="Ad Budget Planner", layout="centered")

# =========================
# Language
# =========================
lang = st.sidebar.selectbox("Language / Язык", ["English", "Русский"])
currency_symbol = st.sidebar.selectbox("Currency / Валюта", ["$", "₸", "₽", "฿", "€"])
t = T[lang]

# =========================
# Style
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Page header ── */
    h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }
    h2 { font-size: 1.15rem !important; font-weight: 600 !important; }
    h3 { font-size: 1rem !important; font-weight: 600 !important; }

    /* ── Status badge ── */
    .big-status {
        font-size: 1rem;
        font-weight: 700;
        padding: 13px 18px;
        border-radius: 8px;
        margin: 10px 0 16px 0;
        border-left: 4px solid;
        letter-spacing: 0.2px;
    }
    .safe    { border-color: #22c55e; color: #16a34a; background: rgba(34,197,94,0.08); }
    .fragile { border-color: #f59e0b; color: #b45309; background: rgba(245,158,11,0.08); }
    .hold    { border-color: #ef4444; color: #dc2626; background: rgba(239,68,68,0.08); }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(248,250,252,0.6);
        padding: 12px 14px;
        border-radius: 10px;
        transition: border-color 0.15s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(99,102,241,0.35);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.55;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }

    /* ── Tabs ── */
    div[data-testid="stTabs"] button {
        font-weight: 500;
        font-size: 0.85rem;
        letter-spacing: 0.1px;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        font-weight: 700;
    }

    /* ── Section dividers ── */
    hr { opacity: 0.12 !important; }

    /* ── Captions / hints ── */
    .small-note,
    div[data-testid="stCaptionContainer"] {
        font-size: 0.78rem !important;
        opacity: 0.5;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: rgba(248,250,252,0.9);
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        opacity: 0.5;
        margin-bottom: 8px;
    }

    /* ── Info / warning / success boxes ── */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
        font-size: 0.88rem !important;
    }

    /* ── Number inputs ── */
    div[data-testid="stNumberInput"] input {
        border-radius: 7px !important;
        font-size: 0.92rem !important;
    }

    /* ── Buttons ── */
    div[data-testid="stButton"] button {
        border-radius: 7px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(t["title"])
st.caption(t["subtitle"])


# =========================
# Helpers
# =========================
def format_money(v):
    return logic_format_money(v, currency_symbol)

def money_label(label: str) -> str:
    return label.replace("($)", f"({currency_symbol})")


def read_uploaded_report(uploaded_file):
    name = (getattr(uploaded_file, "name", "") or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)

    uploaded_file.seek(0)
    raw_bytes = uploaded_file.getvalue()

    best_df = None
    best_score = (-1, -1)

    for enc in ["utf-8", "utf-8-sig", "utf-16", "latin1", "cp1252"]:
        try:
            text = raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue

        for sep in [None, ",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(
                    io.StringIO(text),
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip",
                )
            except Exception:
                continue

            df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
            score = (
                len(df.columns),
                sum(not str(c).lower().startswith("unnamed") for c in df.columns),
            )

            if score > best_score:
                best_df = df
                best_score = score

        if best_df is not None and best_score[0] > 1:
            return best_df

    if best_df is not None:
        return best_df

    uploaded_file.seek(0)
    try:
        return pd.read_csv(
            uploaded_file,
            encoding="latin1",
            sep=None,
            engine="python",
            on_bad_lines="skip",
        )
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(
            uploaded_file,
            encoding="latin1",
            engine="python",
            on_bad_lines="skip",
        )


def guess_index_from_patterns(cols, patterns):
    normalized_cols = [re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip() for c in cols]

    for pattern in patterns:
        if pattern in cols:
            return cols.index(pattern)

    for pattern in patterns:
        pattern_norm = re.sub(r"[^a-z0-9]+", " ", pattern.lower()).strip()
        for idx, col_norm in enumerate(normalized_cols):
            if pattern_norm and pattern_norm in col_norm:
                return idx

    return 0
def plot_profit_curve(df_curve):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df_curve["ad_spend"], df_curve["profit"], marker="o")
    ax.axhline(0, linewidth=1)

    current_row = df_curve[df_curve["scale_pct"] == 0]
    current = current_row.iloc[0] if not current_row.empty else df_curve.iloc[0]
    peak_idx = df_curve["profit"].idxmax()
    peak = df_curve.loc[peak_idx]

    ax.scatter([current["ad_spend"]], [current["profit"]], s=60)
    ax.annotate(
        t["current_point"],
        (current["ad_spend"], current["profit"]),
        textcoords="offset points",
        xytext=(8, 8),
    )

    ax.scatter([peak["ad_spend"]], [peak["profit"]], s=60)
    ax.annotate(
        t["peak_point"],
        (peak["ad_spend"], peak["profit"]),
        textcoords="offset points",
        xytext=(8, -16),
    )

    breakeven_rows = df_curve[df_curve["profit"] <= 0]
    if len(breakeven_rows) > 0:
        be = breakeven_rows.iloc[0]
        ax.scatter([be["ad_spend"]], [be["profit"]], s=60)
        ax.annotate(
            t["breakeven_point"],
            (be["ad_spend"], be["profit"]),
            textcoords="offset points",
            xytext=(8, 8),
        )

    ax.set_xlabel("Ad Spend")
    ax.set_ylabel("Net Profit")
    ax.set_title(t["chart_hdr"])
    st.pyplot(fig)
    plt.close(fig)

    peak_profit = float(peak["profit"])
    peak_spend = float(peak["ad_spend"])
    cliff_detected = False
    if peak_idx < len(df_curve) - 1:
        final_profit = float(df_curve.iloc[-1]["profit"])
        cliff_detected = final_profit < peak_profit

    return peak_profit, peak_spend, cliff_detected


def tr(en, ru):
    return en if lang == "English" else ru


# =========================
# V2 App Flow
# =========================
analysis_goal_options = [
    ("validate_product", tr("Validate a new product", "Проверить новый товар или услугу")),
    ("test_campaign", tr("Test a campaign", "Проверить рекламу")),
    ("ads_profitability", tr("Understand if current ads are profitable", "Понять, приносит ли реклама прибыль")),
    ("decide_scale", tr("Decide whether to scale", "Решить, стоит ли увеличивать бюджет")),
    ("audit_expensive", tr("Audit why ads feel expensive", "Понять, почему реклама выходит дорогой")),
]
analysis_goal_map = dict(analysis_goal_options)

st.subheader(tr("What are you trying to do?", "Что вы хотите сделать?"))
analysis_goal = st.radio(
    "",
    options=[key for key, _ in analysis_goal_options],
    format_func=analysis_goal_map.get,
    horizontal=False,
    label_visibility="collapsed",
)

st.divider()
st.subheader(tr("Business context", "Информация о бизнесе"))

business_name = st.text_input(tr("Business name", "Название бизнеса"))

industry_options = [
    ("ecommerce", tr("E-commerce", "E-commerce")),
    ("services", tr("Services", "Услуги")),
    ("education", tr("Education", "Образование")),
    ("health_beauty", tr("Health / beauty", "Здоровье / красота")),
    ("b2b", tr("B2B", "B2B")),
    ("other", tr("Other", "Другое")),
]
sales_channel_options = [
    ("website", tr("Website checkout", "Покупка на сайте")),
    ("messaging", tr("WhatsApp / Telegram / DM", "WhatsApp / Telegram / личные сообщения")),
    ("consultation", tr("Call / consultation", "Звонок / консультация")),
    ("mixed", tr("Mixed", "Несколько способов")),
]
sales_cycle_options = [
    ("same_day", tr("Same day", "В тот же день")),
    ("days_2_7", tr("2-7 days", "2–7 дней")),
    ("weeks_1_2", tr("1-2 weeks", "1–2 недели")),
    ("longer", tr("Longer", "Дольше")),
]

ctx1, ctx2, ctx3 = st.columns(3)
with ctx1:
    industry = st.selectbox(
        tr("Industry", "Сфера бизнеса"),
        options=[key for key, _ in industry_options],
        format_func=dict(industry_options).get,
    )
with ctx2:
    sales_channel = st.selectbox(
        tr("Sales channel", "Как вы продаёте"),
        options=[key for key, _ in sales_channel_options],
        format_func=dict(sales_channel_options).get,
    )
with ctx3:
    sales_cycle = st.selectbox(
        tr("Sales cycle", "Сколько обычно длится продажа"),
        options=[key for key, _ in sales_cycle_options],
        format_func=dict(sales_cycle_options).get,
    )

repeat_purchase_default = st.radio(
    tr("Repeat purchase?", "Клиенты покупают повторно?"),
    options=["no", "yes"],
    format_func=lambda x: tr("No", "Нет") if x == "no" else tr("Yes", "Да"),
    horizontal=True,
)

st.divider()
st.subheader(tr("How do you want to analyze?", "Как хотите посчитать?"))

source_options = [
    ("upload_meta_report", tr("Upload Meta CSV/XLSX", "Загрузить рекламный отчёт")),
    ("manual_inputs_only", tr("Enter manually", "Ввести вручную")),
    ("новый_бизнес_assumptions_only", tr("New business / no campaign data yet", "Новый бизнес / пока нет данных по рекламе")),
]
source_key = st.radio(
    "",
    options=[key for key, _ in source_options],
    format_func=dict(source_options).get,
    horizontal=True,
    label_visibility="collapsed",
)

reported_spend = 0.0
reported_results = 0.0
reported_result_type = tr("Not detected", "Не определён")
detected_campaigns = 0
selected_campaigns = []
actual_paid_spend = 0.0
true_spend = 0.0
spend_reason = "none"
real_conversations = 0.0
qualified_leads = 0.0
real_orders = 0.0
refund_count = 0.0
lead_quality = "mixed"
aov = 0.0
cogs_per_order = 0.0
refund_rate_pct = 0.0
desired_profit_per_order = 0.0
max_acceptable_cac_pct_of_price = 0.0
repeat_purchase_value = 0.0
close_rate = 0.0
close_rate_confidence = "medium"
close_rate_source = "guess"
real_lead_definition = "осмысленное_обращение"
target_conversations = 20.0
goal_type = analysis_goal
budget_tolerance = "moderate"
cost_per_reported_result = 0.0
cost_per_conversation = 0.0
estimated_cac = 0.0
real_cac = None
break_even_cac = 0.0
target_cac = 0.0
gross_margin_pct = 0.0
refund_adjusted_margin = 0.0
target_cac_pct_of_price = 0.0
max_cost_per_conversation = 0.0
recommended_test_budget = 0.0
meta_counts_reflect_real = True
spend_overhead_pct = 0.0
used_conversations = 0.0
mode_key = "новый_бизнес" if source_key == "новый_бизнес_assumptions_only" else "ранний_тест"
confidence_label = tr("Low", "Низкая")
confidence_reasons = []
has_economics = False
spend_is_adjusted = False
recommendation_headline = ""
recommendation_points = []
low_confidence = True

if source_key == "новый_бизнес_assumptions_only":
    st.divider()
    st.subheader(tr("Plan a first test", "План первого теста"))

    nb1, nb2, nb3 = st.columns(3)
    with nb1:
        aov = st.number_input(money_label(tr("Average order value", "Средний чек")), min_value=0.0, value=120.0)
        cogs_per_order = st.number_input(money_label(tr("Product cost per order", "Себестоимость одного заказа")), min_value=0.0, value=45.0)
        refund_rate_pct = st.number_input(tr("Refund rate (%)", "Процент возвратов (%)"), min_value=0.0, max_value=100.0, value=5.0)
    with nb2:
        close_rate = st.number_input(tr("Expected close rate from conversation to order", "Ожидаемая конверсия в покупку"), min_value=0.0, max_value=1.0, value=0.2)
        expected_cost_per_conversation = st.number_input(money_label(tr("Expected cost per conversation", "Ожидаемая стоимость обращения")), min_value=0.0, value=3.5)
        expected_cac_input = st.number_input(money_label(tr("Expected customer acquisition cost (optional)", "Ожидаемая стоимость привлечения клиента (необязательно)")), min_value=0.0, value=0.0)
    with nb3:
        desired_profit_per_order = st.number_input(money_label(tr("Target profit per order", "Желаемая прибыль с заказа")), min_value=0.0, value=10.0)
        assumption_source = st.selectbox(
            tr("Assumption source", "Откуда взяты предположения"),
            options=["guess", "benchmark", "experience"],
            format_func=lambda x: {
                "guess": tr("Guess", "Предположение"),
                "benchmark": tr("Competitor benchmark", "Ориентир по конкурентам"),
                "experience": tr("Previous experience", "Ваш прошлый опыт"),
            }[x],
        )
        close_rate_source = "guess" if assumption_source == "guess" else "past_campaigns"

    threshold_option = st.selectbox(
        tr("How many conversations before judging?", "Сколько обращений собрать до оценки?"),
        options=[10, 20, 30, "custom"],
        format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
    )
    if threshold_option == "custom":
        target_conversations = float(
            st.number_input(tr("Custom target conversations", "Свой порог обращений"), min_value=1, value=20)
        )
    else:
        target_conversations = float(threshold_option)

    repeat_purchase_value = 0.0
    if repeat_purchase_default == "yes":
        repeat_purchase_value = st.number_input(
            tr("Expected repeat value", "Ожидаемая повторная выручка"),
            min_value=0.0,
            value=0.0,
        )

    break_even_cac = aov - cogs_per_order - (aov * refund_rate_pct / 100.0)
    target_cac = break_even_cac - desired_profit_per_order
    gross_margin_pct = safe_div(aov - cogs_per_order, aov) * 100 if aov > 0 else 0.0
    refund_adjusted_margin = break_even_cac
    target_cac_pct_of_price = safe_div(target_cac, aov) * 100 if aov > 0 else 0.0
    estimated_cac = expected_cac_input if expected_cac_input > 0 else safe_div(expected_cost_per_conversation, close_rate)
    max_cost_per_conversation = max(target_cac, 0.0) * close_rate
    recommended_test_budget = expected_cost_per_conversation * target_conversations
    scenario_orders = safe_div(recommended_test_budget, estimated_cac) if estimated_cac > 0 else 0.0
    scenario_revenue = scenario_orders * aov
    scenario_profit = scenario_orders * (aov - cogs_per_order - (aov * refund_rate_pct / 100.0) - estimated_cac)
    used_conversations = 0.0
    has_economics = aov > 0 and cogs_per_order >= 0
    decision_state = evaluate_decision_state(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=0.0,
        threshold=target_conversations,
        spend_is_adjusted=False,
        has_economics=has_economics,
        lead_quality="mixed",
        true_spend=0.0,
        close_rate_source=close_rate_source,
        lang=lang,
    )
    mode_key = decision_state["mode_key"]
    confidence_label = decision_state["confidence_label"]
    confidence_reasons = decision_state["confidence_reasons"]
    low_confidence = decision_state["low_confidence"]
    recommendation_headline, recommendation_points = get_recommendation_v2(
        mode_key=mode_key,
        true_spend=0.0,
        reported_spend=0.0,
        used_conversations=used_conversations,
        qualified_leads=0.0,
        real_orders=0.0,
        refund_count=0.0,
        lead_quality="mixed",
        break_even_cac=break_even_cac,
        target_cac=target_cac,
        cost_per_conversation=expected_cost_per_conversation,
        estimated_cac=estimated_cac,
        real_cac=None,
        max_cost_per_conversation=max_cost_per_conversation,
        recommended_test_budget=recommended_test_budget,
        target_conversations=target_conversations,
        close_rate_source=close_rate_source,
        lang=lang,
        currency_symbol=currency_symbol,
    )

    st.divider()
    st.subheader(tr("Decision", "Решение"))
    st.markdown(f'<div class="big-status fragile">{tr("Assumption-based plan", "Сценарий на основе предположений")}</div>', unsafe_allow_html=True)

    st.warning(
        tr(
            "Анализ с низкой надёжностью\n\nThis result is based on assumptions and/or incomplete downstream data. Use it for planning and validation, not as proof of profitability.",
            "Низкая надёжность анализа\n\nЭтот результат основан на предположениях и/или неполных данных ниже по воронке. Используйте его для планирования и валидации, а не как доказательство прибыльности.",
        )
    )

    b1, b2, b3 = st.columns(3)
    b1.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
    b2.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))
    b3.metric(tr("Max cost per conversation", "Максимальная стоимость обращения"), format_money(max_cost_per_conversation))

    b4 = st.columns(1)[0]
    b4.metric(tr("Validation budget", "Бюджет на валидацию"), format_money(recommended_test_budget))

    with st.expander(tr("Illustrative scenario only", "Примерный расчёт"), expanded=False):
        st.write(f"**{tr('If assumptions hold', 'Если предположения верны')}:**")
        st.write(f"- {tr('Illustrative orders', 'Примерное число заказов')}: **{scenario_orders:.1f}**")
        st.write(f"- {tr('Illustrative revenue', 'Примерная выручка')}: **{format_money(scenario_revenue)}**")
        st.write(f"- {tr('Illustrative profit', 'Примерная прибыль')}: **{format_money(scenario_profit)}**")

    st.subheader(tr("How reliable this analysis is", "Насколько надёжен этот анализ"))
    st.write(f"**{confidence_label}**")
    for reason in confidence_reasons:
        st.write(f"- {reason}")

    st.subheader(tr("What to do next", "Что делать дальше"))
    st.info(recommendation_headline)
    for point in recommendation_points:
        st.write(f"- {point}")

    st.subheader(tr("Key answers", "Ключевые ответы"))
    st.write(f"1. {tr('Can this business support ads in theory?', 'Может ли эта экономика выдержать рекламу?')} {tr('Yes, if CAC stays at or below', 'Да, если стоимость клиента держится на уровне или ниже')} **{format_money(max(target_cac, 0.0))}**.")
    st.write(f"2. {tr('Is the current data enough to judge?', 'Достаточно ли данных для вывода?')} {tr('No, this is still an assumption-based plan.', 'Нет, это пока сценарий на предположениях.')}")
    st.write(f"3. {tr('How much should be spent next to get evidence?', 'Сколько потратить дальше, чтобы получить доказательства?')} **{format_money(recommended_test_budget)}**.")
    st.write(f"4. {tr('Should we scale?', 'Стоит ли увеличивать бюджет?')} {tr('Not yet. Validate the assumptions first.', 'Пока нет. Сначала проверьте предположения на практике.')}")

else:
    tab_upload, tab_reality, tab_economics, tab_decision = st.tabs(
        [
            tr("① Upload & detect", "① Загрузка и данные"),
            tr("② Reality check", "② Проверка реальности"),
            tr("③ Economics", "③ Экономика"),
            tr("④ Decision", "④ Решение"),
        ]
    )

    with tab_upload:
        st.caption(tr("Step 1 of 4 — Enter your campaign source data. Then move to ② Reality check.", "Шаг 1 из 4 — Введите данные по рекламе. Затем перейдите в ② Проверка реальности."))
        st.subheader(tr("Campaign source", "Откуда взять данные по рекламе"))

        if source_key == "upload_meta_report":
            uploaded = st.file_uploader(tr("Upload file", "Загрузить файл отчёта"), type=["csv", "xlsx", "xls"])
            if not uploaded:
                st.info(tr("Upload a Meta report to detect spend and results.", "Загрузите рекламный отчёт, чтобы определить расходы и результаты."))
            else:
                try:
                    df = read_uploaded_report(uploaded)
                    st.write(tr("Preview first rows", "Первые строки"))
                    st.dataframe(df.head(10), use_container_width=True)

                    cols = list(df.columns)
                    col_campaign = st.selectbox(
                        tr("Campaign name", "Название рекламной кампании"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Campaign name", "Campaign", "campaign_name"]),
                    )
                    col_spend = st.selectbox(
                        tr("Spend", "Расход"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Amount spent (MYR)", "Amount spent", "Spend", "Amount spent (USD)"]),
                    )
                    col_results = st.selectbox(
                        tr("Results", "Результаты"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Results", "Result", "results"]),
                    )
                    col_indicator = st.selectbox(
                        tr("Result indicator", "Тип результата"),
                        cols,
                        index=guess_index_from_patterns(cols, ["Result indicator", "Action type", "Result type", "result_indicator"]),
                    )

                    indicator_series = df[col_indicator].astype(str).str.lower()
                    msg_mask = (
                        indicator_series.str.contains("messaging", na=False)
                        | indicator_series.str.contains("conversation", na=False)
                        | indicator_series.str.contains("message", na=False)
                    )
                    df_msg = df[msg_mask].copy()
                    if df_msg.empty:
                        st.warning(t["msg_fallback_all"])
                        df_msg = df.copy()

                    campaigns = sorted(df_msg[col_campaign].dropna().astype(str).unique().tolist())
                    selected_campaigns = st.multiselect(
                        tr("Select campaigns to include", "Выберите рекламные кампании"),
                        campaigns,
                        default=campaigns,
                    )
                    if selected_campaigns:
                        df_msg = df_msg[df_msg[col_campaign].astype(str).isin(selected_campaigns)].copy()

                    df_msg[col_spend] = parse_number_series(df_msg[col_spend])
                    df_msg[col_results] = parse_number_series(df_msg[col_results])

                    reported_spend = float(df_msg[col_spend].sum())
                    reported_results = float(df_msg[col_results].sum())
                    detected_campaigns = len(selected_campaigns) if selected_campaigns else len(campaigns)

                    unique_indicator_values = sorted(df[col_indicator].dropna().astype(str).unique().tolist())
                    # Build result type sample from the filtered (messaging + selected campaigns) data,
                    # not from the full original df — otherwise it shows unrelated result types.
                    filtered_indicator_values = sorted(df_msg[col_indicator].dropna().astype(str).unique().tolist())
                    sample_values = filtered_indicator_values[:5]
                    reported_result_type = ", ".join(sample_values) if sample_values else tr("Not detected", "Не определён")
                    cost_per_reported_result = safe_div(reported_spend, reported_results)

                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
                    s2.metric(tr("Reported results", "Результаты по отчёту"), f"{reported_results:.1f}")
                    s3.metric(tr("Campaigns found", "Найдено кампаний"), detected_campaigns)
                    s4.metric(tr("Cost per reported result", "Стоимость результата по отчёту"), format_money(cost_per_reported_result))

                    st.write(f"**{tr('Detected result type sample', 'Пример найденных типов результата')}:** {reported_result_type}")
                    st.write(tr("Unique indicator values", "Уникальные значения индикатора"))
                    st.dataframe(pd.DataFrame({col_indicator: unique_indicator_values}), use_container_width=True)
                except Exception as e:
                    st.error(f"{tr('Could not read the uploaded file.', 'Не удалось прочитать файл.')} {e}")

        else:
            st.caption(tr("Manual path for current campaign data.", "Ручной путь для данных текущей кампании."))
            m1, m2, m3 = st.columns(3)
            with m1:
                reported_spend = st.number_input(tr("Reported ad spend", "Расход по отчёту ($)"), min_value=0.0, value=0.0)
            with m2:
                reported_results = st.number_input(tr("Meta-reported conversations", "Обращения по данным Meta"), min_value=0.0, value=0.0)
            with m3:
                reported_result_type = st.text_input(tr("Reported result type", "Тип результата в отчёте"), value=tr("Conversation", "Диалог"))
            cost_per_reported_result = safe_div(reported_spend, reported_results)
            detected_campaigns = 1 if reported_spend > 0 or reported_results > 0 else 0

        meta_counts_reflect_real = st.radio(
            tr("Does Meta's result count reflect real business conversations?", "Отражает ли результат Meta реальные бизнес-диалоги?"),
            options=["yes", "no"],
            format_func=lambda x: tr("Yes", "Да") if x == "yes" else tr("No, I want to adjust it manually", "Нет, я хочу скорректировать это вручную"),
            horizontal=False,
        ) == "yes"

    with tab_reality:
        st.caption(tr("Step 2 of 4 — Correct Meta data with real numbers from your CRM/inbox. Then move to ③ Economics.", "Шаг 2 из 4 — Скорректируйте данные Meta реальными цифрами из CRM/инбокса. Затем перейдите на ③ Экономика."))
        st.subheader(tr("Correct Meta data with real business numbers", "Скорректируйте данные Meta реальными бизнес-данными"))

        default_paid_spend = reported_spend
        actual_paid_spend = st.number_input(
            tr("Actual amount paid", "Фактически оплачено"),
            min_value=0.0,
            value=float(default_paid_spend),
        )
        # Explicit override flag: lets user set spend to $0 intentionally.
        # Without this, entering 0 was silently ignored and reported_spend was reused.
        spend_override_active = st.checkbox(
            tr(
                "Override detected spend with the value above (including if it's $0)",
                "Использовать введённое значение вместо автоопределённого (включая $0)",
            ),
            value=False,
        )
        spend_reason = st.selectbox(
            tr("Difference reason", "Причина расхождения"),
            options=["none", "vat", "currency", "topup", "agency", "other"],
            format_func=lambda x: {
                "none": tr("No adjustment", "Без корректировки"),
                "vat": tr("VAT / tax", "НДС / налог"),
                "currency": tr("Currency conversion", "Конвертация валюты"),
                "topup": tr("Top-up fee", "Комиссия пополнения"),
                "agency": tr("Agency fee", "Комиссия агентства"),
                "other": tr("Other", "Другое"),
            }[x],
        )

        default_real_conversations = reported_results if meta_counts_reflect_real else 0.0
        real_conversations = st.number_input(
            tr("Actual meaningful conversations", "Реальные обращения"),
            min_value=0.0,
            value=float(default_real_conversations),
        )
        # Explicit override flag: lets user intentionally set conversations to 0.
        # Without this, entering 0 was silently ignored and reported_results was reused.
        convo_override_active = st.checkbox(
            tr(
                "Override Meta's conversation count with the value above (including if it's 0)",
                "Использовать введённое количество диалогов вместо данных Meta (включая 0)",
            ),
            value=meta_counts_reflect_real,
        )
        qualified_leads = st.number_input(tr("Qualified leads", "Квалифицированные обращения"), min_value=0.0, value=0.0)
        real_orders = st.number_input(tr("Orders", "Заказы"), min_value=0.0, value=0.0)
        refund_count = st.number_input(tr("Refunds / cancellations", "Возвраты / отмены"), min_value=0.0, value=0.0)
        lead_quality = st.selectbox(
            tr("Quality of leads", "Качество обращений"),
            options=["weak", "mixed", "strong"],
            format_func=lambda x: {
                "weak": tr("Weak", "Слабое"),
                "mixed": tr("Mixed", "Смешанное"),
                "strong": tr("Strong", "Сильное"),
            }[x],
        )

        # Use override values when the user explicitly opted in; otherwise fall back to reported values.
        true_spend = actual_paid_spend if spend_override_active else (actual_paid_spend if actual_paid_spend > 0 else reported_spend)
        used_conversations = real_conversations if convo_override_active else (real_conversations if real_conversations > 0 else reported_results)
        spend_is_adjusted = abs(actual_paid_spend - reported_spend) > 0.009
        spend_overhead_pct = safe_div(true_spend - reported_spend, reported_spend) * 100 if reported_spend > 0 else 0.0

        r1, r2, r3, r4 = st.columns(4)
        r1.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
        r2.metric(tr("Actual paid spend", "Фактически оплачено"), format_money(true_spend))
        r3.metric(tr("Used conversations", "Используемые обращения"), f"{used_conversations:.1f}")
        r4.metric(tr("Overhead %", "Разница в расходах %"), f"{spend_overhead_pct:.1f}%")

    with tab_economics:
        st.caption(tr("Step 3 of 4 — Fill in your unit economics. Then move to ④ Decision.", "Шаг 3 из 4 — Заполните юнит-экономику. Затем перейдите на ④ Решение."))
        st.subheader(tr("Business economics", "Экономика бизнеса"))

        e1, e2, e3 = st.columns(3)
        with e1:
            aov = st.number_input(money_label(tr("Average order value", "Средний чек")), min_value=0.0, value=0.0)
            cogs_per_order = st.number_input(money_label(tr("Product cost per order", "Себестоимость одного заказа")), min_value=0.0, value=0.0)
        with e2:
            refund_rate_pct = st.number_input(tr("Refund rate (%)", "Процент возвратов (%)"), min_value=0.0, max_value=100.0, value=0.0)
            desired_profit_per_order = st.number_input(money_label(tr("Target profit per order", "Желаемая прибыль с заказа")), min_value=0.0, value=0.0)
        with e3:
            max_acceptable_cac_pct_of_price = st.number_input(
                tr("Max acceptable CAC as % of price", "Макс. стоимость клиента, % от цены"),
                min_value=0.0,
                max_value=500.0,
                value=0.0,
            )

        repeat_purchase_value = 0.0
        if repeat_purchase_default == "yes":
            repeat_purchase_value = st.number_input(
                tr("Expected repeat value", "Ожидаемая повторная выручка"),
                min_value=0.0,
                value=0.0,
            )

        close_rate = st.number_input(
            tr("Close rate from conversation to order", "Конверсия в покупку"),
            min_value=0.0,
            max_value=1.0,
            value=0.20,
        )
        close_rate_confidence = st.selectbox(
            tr("Confidence in close rate", "Насколько вы уверены в конверсии в покупку"),
            options=["low", "medium", "high"],
            format_func=lambda x: {
                "low": tr("Low", "Низкая"),
                "medium": tr("Medium", "Средняя"),
                "high": tr("High", "Высокая"),
            }[x],
        )
        close_rate_source = st.selectbox(
            tr("Close rate is based on", "Откуда взята конверсия в покупку"),
            options=["real_data", "past_campaigns", "guess"],
            format_func=lambda x: {
                "real_data": tr("Real history", "Фактические данные"),
                "past_campaigns": tr("Previous campaigns", "Предыдущие кампании"),
                "guess": tr("Guess", "Предположение"),
            }[x],
        )
        real_lead_definition = st.selectbox(
            tr("What counts as a real lead?", "Что считать реальным обращением?"),
            options=["any_conversation", "осмысленное_обращение", "qualified_lead", "consultation_booked"],
            format_func=lambda x: {
                "any_conversation": tr("Any conversation", "Любой диалог"),
                "осмысленное_обращение": tr("Meaningful conversation", "Осмысленный диалог"),
                "qualified_lead": tr("Qualified lead", "Квалифицированный лид"),
                "consultation_booked": tr("Booked consultation", "Назначенная консультация"),
            }[x],
        )
        threshold_option = st.selectbox(
            tr("How many conversations do you want before judging the campaign?", "Сколько диалогов нужно до оценки кампании?"),
            options=[10, 20, 30, "custom"],
            format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
        )
        if threshold_option == "custom":
            target_conversations = float(
                st.number_input(tr("Custom target conversations", "Свой порог обращений"), min_value=1, value=20)
            )
        else:
            target_conversations = float(threshold_option)

        goal_type = st.selectbox(
            tr("What is your goal?", "Какова ваша цель?"),
            options=["validate_product", "break_even", "small_profit", "aggressive_growth"],
            format_func=lambda x: {
                "validate_product": tr("Validate demand", "Проверить спрос"),
                "break_even": tr("Break even", "Выйти в ноль"),
                "small_profit": tr("Small first-order profit", "Небольшая прибыль с первого заказа"),
                "aggressive_growth": tr("Aggressive growth", "Агрессивный рост"),
            }[x],
        )
        budget_tolerance = st.selectbox(
            tr("Budget tolerance", "Допуск по бюджету"),
            options=["conservative", "moderate", "aggressive"],
            format_func=lambda x: {
                "conservative": tr("Conservative", "Консервативный"),
                "moderate": tr("Moderate", "Умеренный"),
                "aggressive": tr("Aggressive", "Агрессивный"),
            }[x],
        )

        refund_cost = aov * refund_rate_pct / 100.0
        break_even_cac = aov - cogs_per_order - refund_cost
        target_cac = break_even_cac - desired_profit_per_order
        gross_margin_pct = safe_div(aov - cogs_per_order, aov) * 100 if aov > 0 else 0.0
        refund_adjusted_margin = break_even_cac
        target_cac_pct_of_price = safe_div(target_cac, aov) * 100 if aov > 0 else 0.0
        cost_per_conversation = safe_div(true_spend, used_conversations)
        estimated_cac = safe_div(cost_per_conversation, close_rate)
        real_cac = safe_div(true_spend, real_orders) if real_orders > 0 else None
        max_cost_per_conversation = max(target_cac, 0.0) * close_rate
        recommended_test_budget = target_conversations * cost_per_conversation
        has_economics = aov > 0 and cogs_per_order >= 0

        e4, e5, e6 = st.columns(3)
        e4.metric(tr("Gross margin %", "Валовая маржа %"), f"{gross_margin_pct:.1f}%")
        e5.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
        e6.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))

        e7, e8, e9 = st.columns(3)
        e7.metric(tr("Cost per conversation", "Стоимость обращения"), format_money(cost_per_conversation))
        e8.metric(tr("Estimated CAC", "Расчётная стоимость клиента"), format_money(estimated_cac))
        e9.metric(tr("Max cost per conversation", "Максимальная стоимость обращения"), format_money(max_cost_per_conversation))

    decision_state = evaluate_decision_state(
        source_key=source_key,
        used_conversations=used_conversations,
        real_orders=real_orders,
        threshold=target_conversations,
        spend_is_adjusted=spend_is_adjusted,
        has_economics=has_economics,
        lead_quality=lead_quality,
        true_spend=true_spend,
        close_rate_source=close_rate_source,
        lang=lang,
    )
    mode_key = decision_state["mode_key"]
    confidence_label = decision_state["confidence_label"]
    confidence_reasons = decision_state["confidence_reasons"]
    low_confidence = decision_state["low_confidence"]
    recommendation_headline, recommendation_points = get_recommendation_v2(
        mode_key=mode_key,
        true_spend=true_spend,
        reported_spend=reported_spend,
        used_conversations=used_conversations,
        qualified_leads=qualified_leads,
        real_orders=real_orders,
        refund_count=refund_count,
        lead_quality=lead_quality,
        break_even_cac=break_even_cac,
        target_cac=target_cac,
        cost_per_conversation=cost_per_conversation,
        estimated_cac=estimated_cac,
        real_cac=real_cac,
        max_cost_per_conversation=max_cost_per_conversation,
        recommended_test_budget=recommended_test_budget,
        target_conversations=target_conversations,
        close_rate_source=close_rate_source,
        lang=lang,
        currency_symbol=currency_symbol,
    )

    with tab_decision:
        # Guard: show a prompt if no meaningful data has been entered yet.
        # Allow zero spend (audit / planning use case) as long as economics are filled.
        _data_ready = aov > 0
        if not _data_ready:
            st.info(
                tr(
                    "⬅️ Fill in tabs ①, ②, and ③ first — at minimum enter Средний чек in ③ Economics — then come back here for your decision.",
                    "⬅️ Сначала заполните вкладки ①, ② и ③ — как минимум укажите средний чек в ③ Экономика — затем вернитесь сюда за выводом.",
                )
            )
            st.stop()
        st.subheader(tr("Decision", "Решение"))
        mode_label = {
            "новый_бизнес": tr("New Business", "Новый бизнес"),
            "ранний_тест": tr("Early test", "Ранний тест"),
            "данных_достаточно": tr("Validated", "Подтверждённый режим"),
        }.get(mode_key, tr("Early test", "Ранний тест"))
        mode_badge_class = "safe" if mode_key == "данных_достаточно" else "fragile"
        st.markdown(f'<div class="big-status {mode_badge_class}">{mode_label}</div>', unsafe_allow_html=True)

        meta_col, biz_col = st.columns(2)
        with meta_col:
            st.subheader(tr("What Meta reports", "Что сообщает Meta"))
            st.metric(tr("Reported spend", "Расход по отчёту"), format_money(reported_spend))
            st.metric(tr("Reported results", "Результаты по отчёту"), f"{reported_results:.1f}")
            st.metric(tr("Result type", "Тип результата"), reported_result_type[:32] if reported_result_type else tr("n/a", "н/д"))
            st.metric(tr("Cost per reported result", "Стоимость результата по отчёту"), format_money(cost_per_reported_result))
        with biz_col:
            st.subheader(tr("What the business actually saw", "Что бизнес увидел на самом деле"))
            st.metric(tr("Actual paid spend", "Фактически оплачено"), format_money(true_spend))
            st.metric(tr("Real conversations", "Реальные обращения"), f"{used_conversations:.1f}")
            st.metric(tr("Qualified leads", "Квалифицированные обращения"), f"{qualified_leads:.1f}")
            st.metric(tr("Orders", "Заказы"), f"{real_orders:.1f}")
            st.metric(
                tr("Quality of leads", "Качество обращений"),
                tr("Weak", "Слабое") if lead_quality == "weak" else tr("Mixed", "Смешанное") if lead_quality == "mixed" else tr("Strong", "Сильное"),
            )
            st.write(f"**{tr('Spend overhead %', 'Оверхед по расходу %')}:** {spend_overhead_pct:.1f}%")
            st.write(
                f"**{tr('Reason for difference', 'Причина расхождения')}:** "
                f"{ {'none': tr('No adjustment', 'Без корректировки'), 'vat': tr('VAT / tax', 'НДС / налог'), 'currency': tr('Currency conversion', 'Конвертация валюты'), 'topup': tr('Top-up fee', 'Комиссия пополнения'), 'agency': tr('Agency fee', 'Комиссия агентства'), 'other': tr('Other', 'Другое')}[spend_reason] }"
            )

        if low_confidence:
            st.warning(
                tr(
                    "Анализ с низкой надёжностью\n\nThis result is based on assumptions and/or incomplete downstream data. Use it for planning and validation, not as proof of profitability.",
                    "Низкая надёжность анализа\n\nЭтот результат основан на предположениях и/или неполных данных ниже по воронке. Используйте его для планирования и валидации, а не как доказательство прибыльности.",
                )
            )

        st.subheader(tr("Funnel comparison", "Сравнение воронки"))
        f1, f2, f3, f4 = st.columns(4)
        f1.metric(tr("Meta reported conversations", "Обращения по данным Meta"), f"{reported_results:.1f}")
        f2.metric(tr("Real conversations", "Реальные обращения"), f"{used_conversations:.1f}")
        f3.metric(tr("Qualified leads", "Квалифицированные обращения"), f"{qualified_leads:.1f}")
        f4.metric(tr("Orders", "Заказы"), f"{real_orders:.1f}")

        fp1, fp2, fp3 = st.columns(3)
        fp1.metric(
            tr("Real conversations / Meta reported", "Реальные / по Meta"),
            f"{safe_div(used_conversations, reported_results) * 100:.1f}%" if reported_results > 0 else tr("n/a", "н/д"),
        )
        fp2.metric(
            tr("Qualified leads / Real conversations", "Качественные / реальные"),
            f"{safe_div(qualified_leads, used_conversations) * 100:.1f}%" if used_conversations > 0 else tr("n/a", "н/д"),
        )
        base_for_orders = qualified_leads if qualified_leads > 0 else used_conversations
        fp3.metric(
            tr("Orders / Qualified", "Покупки / база"),
            f"{safe_div(real_orders, base_for_orders) * 100:.1f}%" if base_for_orders > 0 else tr("n/a", "н/д"),
        )

        st.subheader(tr("Business economics", "Экономика бизнеса"))
        x1, x2, x3 = st.columns(3)
        x1.metric("Средний чек", format_money(aov))
        x2.metric(tr("Product cost", "Себестоимость"), format_money(cogs_per_order))
        x3.metric(tr("Gross margin %", "Валовая маржа %"), f"{gross_margin_pct:.1f}%")
        x4, x5 = st.columns(2)
        x4.metric(tr("Break-even CAC", "Стоимость клиента без убытка"), format_money(break_even_cac))
        x5.metric(tr("Target CAC", "Желаемая стоимость клиента"), format_money(target_cac))
        st.write(f"**{tr('CAC as % of price', 'Стоимость клиента как % от цены')}:** {target_cac_pct_of_price:.1f}%")
        st.write(f"**{tr('Max cost per conversation', 'Максимальная стоимость обращения')}:** {format_money(max_cost_per_conversation)}")

        budget_header = tr("Recommended test budget", "Рекомендуемый бюджет на тест")
        st.subheader(budget_header)
        tb1, tb2, tb3, tb4 = st.columns(4)
        tb1.metric(tr("Budget for 10 conversations", "Бюджет на 10 обращений"), format_money(cost_per_conversation * 10))
        tb2.metric(tr("Budget for 20 conversations", "Бюджет на 20 обращений"), format_money(cost_per_conversation * 20))
        tb3.metric(tr("Budget for 30 conversations", "Бюджет на 30 обращений"), format_money(cost_per_conversation * 30))
        tb4.metric(tr("Budget for selected threshold", "Бюджет под выбранный порог"), format_money(recommended_test_budget))

        st.subheader(tr("How reliable this analysis is", "Насколько надёжен этот анализ"))
        st.write(f"**{tr('Confidence level', 'Уровень уверенности')}: {confidence_label}**")
        for reason in confidence_reasons:
            st.write(f"- {reason}")

        st.subheader(tr("What to do next", "Что делать дальше"))
        st.info(recommendation_headline)
        for point in recommendation_points:
            st.write(f"- {point}")

        if mode_key == "ранний_тест":
            st.subheader(tr("Track next", "Отслеживать дальше"))
            st.info(
                tr(
                    "Operational checklist for the next review cycle.",
                    "Операционный чек-лист к следующему циклу проверки.",
                )
            )
            for item in [
                tr("Actual paid spend", "Фактически оплаченный расход"),
                tr("Real conversations", "Реальные обращения"),
                tr("Qualified leads", "Квалифицированные обращения"),
                tr("First orders", "Первые заказы"),
                tr("Refunds / cancellations", "Возвраты / отмены"),
            ]:
                st.write(f"- {item}")

        st.subheader(tr("Key answers", "Ключевые ответы"))
        theory_answer = (
            tr("Yes, if CAC stays below target CAC.", "Да, если стоимость клиента ниже целевого уровня.")
            if target_cac > 0
            else tr("Not yet. The first-order economics do not currently support ads.", "Пока нет. Экономика первого заказа пока не поддерживает рекламу.")
        )
        data_answer = (
            tr("Yes, there is enough downstream evidence to judge.", "Да, данных ниже по воронке уже достаточно для оценки.")
            if mode_key == "данных_достаточно"
            else tr("Not yet. Gather more real conversations and orders first.", "Пока нет. Сначала соберите больше реальных диалогов и заказов.")
        )
        next_budget_answer = (
            format_money(recommended_test_budget)
            if recommended_test_budget > 0
            else tr("Need conversation cost first.", "Сначала нужна стоимость диалога.")
        )
        scale_answer = {
            "данных_достаточно": recommendation_headline,
            "ранний_тест": tr("Too early to judge profitability.", "Слишком рано судить о прибыльности."),
            "новый_бизнес": tr("Not yet. Validate assumptions first.", "Пока нет. Сначала проверьте предположения на практике."),
        }.get(mode_key, tr("Not enough data to judge yet.", "Данных пока недостаточно."))
        st.write(f"1. {tr('Can this business support ads in theory?', 'Может ли эта экономика выдержать рекламу?')} {theory_answer}")
        st.write(f"2. {tr('Is the current data enough to judge?', 'Достаточно ли текущих данных для вывода?')} {data_answer}")
        st.write(f"3. {tr('How much should be spent next to get enough evidence?', 'Сколько потратить дальше, чтобы получить достаточно данных?')} **{next_budget_answer}**")
        st.write(f"4. {tr('If evidence is strong enough, should we scale?', 'Если данных достаточно, стоит ли масштабироваться?')} {scale_answer}")

        if mode_key == "данных_достаточно" and not low_confidence and real_orders > 0 and aov > 0:
            st.divider()
            st.subheader(tr("Scale simulation", "Симуляция масштаба"))
            preset = st.radio(
                tr("How does ad efficiency usually behave when you scale?", "Как обычно меняется эффективность рекламы при росте?"),
                options=["optimistic", "realistic", "pessimistic"],
                format_func=lambda x: {
                    "optimistic": tr("Optimistic", "Оптимистично"),
                    "realistic": tr("Realistic", "Реалистично"),
                    "pessimistic": tr("Pessimistic", "Пессимистично"),
                }[x],
                horizontal=True,
            )
            default_decay = 10 if preset == "optimistic" else 25 if preset == "realistic" else 50
            spend_change_pct = st.slider(tr("Planned ad spend change (%)", "Планируемое изменение бюджета (%)"), -80, 300, 50)
            cac_deterioration_per_100 = st.slider(
                tr("If you double spend, how much can acquisition cost rise (%)?", "Если удвоить бюджет, на сколько может вырасти стоимость клиента (%)?"),
                0,
                100,
                default_decay,
            )

            model_revenue = aov * real_orders
            model_cogs = cogs_per_order * real_orders
            res = simulate_scale(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                spend_change_pct=spend_change_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
            )
            safe_scale_pct = find_safe_max_scale_pct(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
                max_search_pct=300,
            )
            df_curve = build_profit_curve(
                revenue=model_revenue,
                cogs=model_cogs,
                ad_spend=true_spend,
                orders=real_orders,
                refund_rate_pct=refund_rate_pct,
                cac_deterioration_per_100_pct=cac_deterioration_per_100,
            )
            peak_profit, peak_spend, cliff_detected = plot_profit_curve(df_curve)

            s1, s2, s3 = st.columns(3)
            s1.metric(tr("Forecast spend", "Расходы в расчёте"), format_money(res["new_spend"]))
            s2.metric(tr("Forecast profit", "Прибыль в расчёте"), format_money(res["new_profit"]))
            s3.metric(tr("Safe scale limit", "Безопасный лимит роста"), f"{safe_scale_pct}%")

            if cliff_detected:
                st.warning(tr("Profit cliff detected: scaling past the peak reduces profit.", "Обнаружен обрыв прибыли: рост выше пика снижает прибыль."))

            scenarios = [-50, -25, 0, 25, 50, 100, 150, 200]
            rows = []
            for pct in scenarios:
                r = simulate_scale(
                    revenue=model_revenue,
                    cogs=model_cogs,
                    ad_spend=true_spend,
                    orders=real_orders,
                    refund_rate_pct=refund_rate_pct,
                    spend_change_pct=pct,
                    cac_deterioration_per_100_pct=cac_deterioration_per_100,
                )
                rows.append(
                    {
                        tr("Spend change %", "Изменение бюджета, %"): pct,
                        tr("Ad spend", "Расход"): round(r["new_spend"], 2),
                        tr("CAC", "CAC"): round(r["new_cac"], 2) if r["new_cac"] > 0 else None,
                        tr("Orders", "Заказы"): round(r["new_orders"], 1),
                        tr("Revenue", "Выручка"): round(r["new_revenue"], 2),
                        tr("Profit", "Прибыль"): round(r["new_profit"], 2),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.sidebar.markdown(f"### {tr('Mode summary', 'Сводка режима')}")
if true_spend > 0 or source_key == "новый_бизнес_assumptions_only":
    st.sidebar.write(f"**{tr('Goal', 'Цель')}:** {analysis_goal_map[analysis_goal]}")
    st.sidebar.write(f"**{tr('Source', 'Источник')}:** {dict(source_options)[source_key]}")
    st.sidebar.write(
        f"**{tr('Classified mode', 'Классифицированный режим')}:** "
        f"{tr('New business', 'Новый бизнес') if mode_key == 'новый_бизнес' else tr('Early test', 'Ранний тест') if mode_key == 'ранний_тест' else tr('Validated', 'Подтверждённый режим')}"
    )
    st.sidebar.write(f"**{tr('Confidence', 'Уверенность')}:** {confidence_label}")
    if business_name:
        st.sidebar.write(f"**{tr('Business', 'Бизнес')}:** {business_name}")
else:
    st.sidebar.caption(tr("Fill in your data to see the summary here.", "Заполните данные, чтобы увидеть сводку."))
