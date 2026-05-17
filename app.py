import io
import re

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from logic import (
    build_profit_curve,
    evaluate_decision_state,
    find_safe_max_scale_pct,
    format_money as logic_format_money,
    get_recommendation_v2,
    parse_number_series,
    plausibility_note,
    safe_div,
    simulate_scale,
)
from texts import T

# =============================================================================
# Page config + CSS
# =============================================================================
st.set_page_config(page_title="Ad Budget Planner", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Page header */
    h1 { font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.3px; margin-bottom: 0.1rem !important; }
    h2 { font-size: 1.1rem !important; font-weight: 600 !important; margin-top: 1.4rem !important; }
    h3 { font-size: 0.98rem !important; font-weight: 600 !important; }

    /* Stepper */
    .stepper { display: flex; align-items: center; gap: 6px; margin: 18px 0 24px 0; flex-wrap: wrap; }
    .step-pill {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 7px 14px; border-radius: 999px;
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.1px;
        background: rgba(148,163,184,0.10); color: #94a3b8;
        border: 1px solid rgba(148,163,184,0.18);
    }
    .step-pill.active {
        background: #6366f1; color: #fff; border-color: #6366f1;
        box-shadow: 0 2px 8px rgba(99,102,241,0.25);
    }
    .step-pill.done {
        background: rgba(34,197,94,0.10); color: #16a34a; border-color: rgba(34,197,94,0.30);
    }
    .step-pill .num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 18px; height: 18px; border-radius: 999px;
        background: rgba(255,255,255,0.18); font-size: 0.7rem; font-weight: 700;
    }
    .step-pill.done .num { background: rgba(34,197,94,0.25); }
    .step-pill:not(.active):not(.done) .num { background: rgba(148,163,184,0.18); }
    .step-bar { flex: 1; height: 2px; background: rgba(148,163,184,0.18); border-radius: 2px; min-width: 12px; }
    .step-bar.done { background: rgba(34,197,94,0.40); }

    /* Status badge */
    .big-status {
        font-size: 1rem; font-weight: 700;
        padding: 14px 18px; border-radius: 10px;
        margin: 6px 0 16px 0; border-left: 4px solid;
        letter-spacing: 0.2px;
    }
    .safe    { border-color: #22c55e; color: #16a34a; background: rgba(34,197,94,0.08); }
    .fragile { border-color: #f59e0b; color: #b45309; background: rgba(245,158,11,0.08); }
    .hold    { border-color: #ef4444; color: #dc2626; background: rgba(239,68,68,0.08); }

    /* Section card */
    .section-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 12px;
        padding: 16px 18px 4px 18px;
        margin-bottom: 14px;
        background: rgba(248,250,252,0.4);
    }
    .section-card h3 { margin-top: 0.2rem !important; }
    .section-hint {
        font-size: 0.82rem; color: #64748b; margin-top: -2px; margin-bottom: 12px;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(248,250,252,0.6);
        padding: 12px 14px; border-radius: 10px;
        transition: border-color 0.15s;
    }
    div[data-testid="stMetric"]:hover { border-color: rgba(99,102,241,0.35); }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important; font-weight: 500 !important;
        text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.55;
    }
    div[data-testid="stMetricValue"] { font-size: 1.18rem !important; font-weight: 700 !important; }

    /* Captions */
    div[data-testid="stCaptionContainer"] { font-size: 0.82rem !important; opacity: 0.65; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: rgba(248,250,252,0.9); }
    section[data-testid="stSidebar"] h3 {
        font-size: 0.85rem !important; font-weight: 700 !important;
        text-transform: uppercase; letter-spacing: 0.6px;
        opacity: 0.55; margin-bottom: 6px;
    }
    .sb-row { font-size: 0.82rem; line-height: 1.55; opacity: 0.78; }
    .sb-row b { opacity: 1; }

    /* Alerts */
    div[data-testid="stAlert"] { border-radius: 9px !important; font-size: 0.88rem !important; }

    /* Inputs */
    div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
        border-radius: 7px !important; font-size: 0.92rem !important;
    }

    /* Buttons */
    div[data-testid="stButton"] button {
        border-radius: 8px !important; font-weight: 600 !important; font-size: 0.9rem !important;
    }
    .nav-row { margin-top: 18px; padding-top: 14px; border-top: 1px solid rgba(148,163,184,0.18); }

    /* Hero verdict */
    .hero-verdict {
        padding: 22px 24px; border-radius: 14px; margin-bottom: 18px;
        border: 1px solid; position: relative; overflow: hidden;
    }
    .hero-verdict.safe    { background: linear-gradient(135deg, rgba(34,197,94,0.10), rgba(34,197,94,0.04)); border-color: rgba(34,197,94,0.30); }
    .hero-verdict.fragile { background: linear-gradient(135deg, rgba(245,158,11,0.10), rgba(245,158,11,0.04)); border-color: rgba(245,158,11,0.35); }
    .hero-verdict.hold    { background: linear-gradient(135deg, rgba(239,68,68,0.10), rgba(239,68,68,0.04)); border-color: rgba(239,68,68,0.35); }
    .hero-verdict .label {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; opacity: 0.7; margin-bottom: 4px;
    }
    .hero-verdict .headline {
        font-size: 1.25rem; font-weight: 700; line-height: 1.35;
    }
    .hero-verdict.safe .label    { color: #16a34a; }
    .hero-verdict.fragile .label { color: #b45309; }
    .hero-verdict.hold .label    { color: #dc2626; }

    /* "What to do next" list block */
    .next-steps {
        background: rgba(99,102,241,0.06);
        border-left: 3px solid #6366f1;
        padding: 12px 16px; border-radius: 0 10px 10px 0;
        margin: 8px 0 14px 0;
    }
    .next-steps b { display: block; margin-bottom: 6px; font-size: 0.92rem; }
    .next-steps ul { margin: 4px 0 0 0; padding-left: 18px; }
    .next-steps li { font-size: 0.88rem; line-height: 1.5; margin-bottom: 4px; }

    /* Help link button */
    div[data-testid="stExpander"] summary p { font-size: 0.88rem !important; font-weight: 500 !important; }

    /* Source-of-data picker (radio styled as cards) */
    .source-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 6px; }
    @media (max-width: 720px) { .source-grid { grid-template-columns: 1fr; } }

    /* Inline input plausibility warning */
    .field-warn {
        font-size: 0.78rem; color: #b45309;
        background: rgba(245,158,11,0.08);
        border-left: 3px solid #f59e0b;
        padding: 6px 10px; border-radius: 0 6px 6px 0;
        margin: -6px 0 12px 0; line-height: 1.45;
    }

    /* Derived-from-data callout (a number we computed, not a guess) */
    .derived-box {
        font-size: 0.86rem; color: #15803d;
        background: rgba(34,197,94,0.08);
        border-left: 3px solid #22c55e;
        padding: 9px 12px; border-radius: 0 8px 8px 0;
        margin: 4px 0 10px 0; line-height: 1.5;
    }
    .derived-box b { font-weight: 700; }
    .derived-box .sub { color: #64748b; font-size: 0.78rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# Session state init — single source of truth across wizard steps
# =============================================================================
DEFAULTS = {
    "wizard_step": 1,

    # Step 1 — goal + context
    "goal": "decide_scale",
    "business_name": "",
    "industry": "ecommerce",
    "sales_channel": "messaging",
    "sales_cycle": "same_day",
    "repeat_purchase_default": "no",

    # Step 2 — data source
    "source_key": "upload_meta_report",

    # Step 3 — manual / upload inputs
    "reported_spend_input": 0.0,
    "reported_results_input": 0.0,
    "reported_result_type_input": "",

    # Reality check
    "actual_paid_spend": 0.0,
    "spend_override_active": False,
    "spend_reason": "none",
    "real_conversations": 0.0,
    "convo_override_active": False,
    "qualified_leads": 0.0,
    "real_orders": 0.0,
    "repeat_order_count": 0.0,
    "refund_count": 0.0,
    "lead_quality": "mixed",
    "meta_counts_reflect_real": True,

    # Economics
    "aov": 0.0,
    "cogs_per_order": 0.0,
    "refund_rate_pct": 0.0,
    "desired_profit_per_order": 0.0,
    "max_acceptable_cac_pct_of_price": 0.0,
    "repeat_purchase_value": 0.0,
    "close_rate": 0.20,
    "close_rate_confidence": "medium",
    "close_rate_source": "guess",
    "close_rate_use_manual": False,
    "refund_rate_use_manual": False,
    "real_lead_definition": "осмысленное_обращение",
    "threshold_option": 20,
    "custom_threshold": 20,
    "goal_type": "validate_product",
    "budget_tolerance": "moderate",

    # New business path
    "expected_cost_per_conversation": 3.5,
    "expected_cac_input": 0.0,
    "assumption_source": "guess",

    # Cached upload artefacts (so Back/Forward keep state)
    "_uploaded_df": None,
    "_uploaded_filename": None,
    "_col_campaign": None,
    "_col_spend": None,
    "_col_results": None,
    "_col_indicator": None,
    "_selected_campaigns": [],
    "_unique_indicators": [],
    "_manual_mode_forced": False,

    # Step 4 — scale simulation (slider keys NOT pre-initialised; defaults are
    # passed via the widget's `value` arg so changing the preset can re-seed
    # the deterioration slider on first render)
    "scale_preset": "realistic",

    # Phase 3 — derive CAC deterioration from history (advanced)
    "prior_period_cac": 0.0,
    "current_period_cac": 0.0,
    "prior_period_spend": 0.0,
    "current_period_spend": 0.0,
    "use_derived_deterioration": False,

    # Phase 4 — product mix tiers + multi-channel attribution (advanced)
    "tier1_name": "Product A",
    "tier1_share": 0.0,
    "tier1_aov": 0.0,
    "tier1_cogs": 0.0,
    "tier1_refund": 0.0,
    "tier2_name": "Product B",
    "tier2_share": 0.0,
    "tier2_aov": 0.0,
    "tier2_cogs": 0.0,
    "tier2_refund": 0.0,
    "tier3_name": "Product C",
    "tier3_share": 0.0,
    "tier3_aov": 0.0,
    "tier3_cogs": 0.0,
    "tier3_refund": 0.0,
    "attribution_pct": 100.0,
}
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# =============================================================================
# Sidebar — language, currency, progress summary
# =============================================================================
with st.sidebar:
    st.markdown("### Settings / Настройки")
    lang = st.selectbox("Language / Язык", ["English", "Русский"], index=1)
    currency_symbol = st.selectbox("Currency / Валюта", ["$", "₸", "₽", "฿", "€"])
    t = T[lang]

# =============================================================================
# Helpers
# =============================================================================
def tr(en, ru):
    return en if lang == "English" else ru


def format_money(v):
    return logic_format_money(v, currency_symbol)


def money_label(label: str) -> str:
    return label.replace("($)", f"({currency_symbol})")


def show_note(field: str, value, aov: float = 0.0):
    """Render a gentle inline plausibility warning under an input, if warranted."""
    note = plausibility_note(field, value, lang, aov=aov)
    if note:
        st.markdown(f"<div class='field-warn'>⚠️ {note}</div>", unsafe_allow_html=True)


def _effective_used_conversations() -> float:
    """Best available conversation count from the reality-check inputs."""
    s = st.session_state
    if s.convo_override_active:
        return float(s.real_conversations or 0.0)
    if (s.real_conversations or 0.0) > 0:
        return float(s.real_conversations)
    return float(s.reported_results_input or 0.0)


def close_rate_block():
    """Render the close-rate input. If real orders + conversations exist, derive
    it from those (a fact) and treat any manual entry as an optional override.
    Phase 2: replaces a guessed input with arithmetic on numbers the user already
    has. The manual input becomes a fallback only."""
    s = st.session_state
    used_conv = _effective_used_conversations()
    can_derive = (s.real_orders or 0.0) > 0 and used_conv > 0

    if can_derive:
        derived = float(s.real_orders) / used_conv
        st.markdown(
            f"<div class='derived-box'>"
            f"✓ <b>{tr('Close rate calculated from your real numbers', 'Конверсия посчитана по вашим реальным цифрам')}: "
            f"{derived:.1%}</b><br>"
            f"<span class='sub'>{int(s.real_orders)} {tr('orders', 'заказов')} ÷ "
            f"{int(used_conv)} {tr('conversations', 'обращений')} — "
            f"{tr('no guessing needed', 'гадать не нужно')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if derived > 1.0:
            st.markdown(
                f"<div class='field-warn'>⚠️ "
                f"{tr('More orders than conversations — your conversation count may be incomplete.', 'Заказов больше, чем обращений — возможно, обращения посчитаны не полностью.')}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.checkbox(
            tr("My real close rate is different — let me enter it manually",
               "Моя реальная конверсия другая — введу вручную"),
            key="close_rate_use_manual",
        )
        if s.close_rate_use_manual:
            st.number_input(
                tr("Close rate — manual override (conversation → order)",
                   "Конверсия — ручное значение (обращение → заказ)"),
                min_value=0.0, max_value=1.0, step=0.05, key="close_rate",
                help=tr("Only override if you know the calculated rate is wrong.",
                        "Меняйте, только если уверены, что расчётное значение неверно."),
            )
            show_note("close_rate", s.close_rate)
            s.close_rate_source = "guess"
        else:
            s.close_rate = derived
            s.close_rate_source = "real_data"
    else:
        st.number_input(
            tr("Close rate — estimate (conversation → order)",
               "Конверсия — оценка (обращение → заказ)"),
            min_value=0.0, max_value=1.0, step=0.05, key="close_rate",
            help=tr("0.20 means 20%. Once you enter real orders and conversations above, "
                    "we'll calculate this for you instead.",
                    "0.20 = 20%. Как только введёте реальные заказы и обращения выше, "
                    "мы посчитаем это значение за вас."),
        )
        show_note("close_rate", s.close_rate)


def refund_rate_block():
    """Phase 6: derive refund_rate_pct from refund_count / real_orders when
    real data exists. Mirrors the close_rate_block pattern — manual input
    becomes an opt-in fallback so users stop guessing a number they don't
    actually need to provide."""
    s = st.session_state
    real_orders = float(s.real_orders or 0.0)
    refund_count = float(s.refund_count or 0.0)
    can_derive = real_orders > 0

    if can_derive:
        derived = (refund_count / real_orders) * 100.0
        st.markdown(
            f"<div class='derived-box'>"
            f"✓ <b>{tr('Refund rate calculated from your real numbers', 'Процент возвратов посчитан по вашим реальным цифрам')}: "
            f"{derived:.1f}%</b><br>"
            f"<span class='sub'>{int(refund_count)} {tr('refunds', 'возвратов')} ÷ "
            f"{int(real_orders)} {tr('orders', 'заказов')} — "
            f"{tr('no guessing needed', 'гадать не нужно')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.checkbox(
            tr("My real refund rate is different — let me enter it manually",
               "Мой реальный процент возвратов другой — введу вручную"),
            key="refund_rate_use_manual",
        )
        if s.refund_rate_use_manual:
            st.number_input(
                tr("Refund rate (%) — manual override",
                   "Процент возвратов (%) — ручное значение"),
                min_value=0.0, max_value=100.0, key="refund_rate_pct",
                help=tr("Only override if you know the calculated rate is wrong.",
                        "Меняйте, только если уверены, что расчётное значение неверно."),
            )
            show_note("refund_rate_pct", s.refund_rate_pct)
        else:
            s.refund_rate_pct = derived
    else:
        st.number_input(
            tr("Refund rate (%) — estimate", "Процент возвратов (%) — оценка"),
            min_value=0.0, max_value=100.0, key="refund_rate_pct",
            help=tr("Once you enter real refunds and orders above, we'll calculate this for you.",
                    "Как только введёте реальные возвраты и заказы выше, мы посчитаем это сами."),
        )
        show_note("refund_rate_pct", s.refund_rate_pct)


def fill_example_data():
    """Phase 6: one-click prefill so first-time users can see what an answered
    form looks like without remembering their own numbers. Sets every relevant
    field for the current path to a small e-commerce scenario."""
    s = st.session_state
    s.aov = 50.0
    s.cogs_per_order = 20.0
    s.refund_rate_pct = 8.0  # used by new_biz; real path overrides via derivation
    s.desired_profit_per_order = 10.0
    if s.source_key == "новый_бизнес_assumptions_only":
        s.close_rate = 0.15
        s.expected_cost_per_conversation = 5.0
        s.expected_cac_input = 0.0
        s.assumption_source = "benchmark"
    else:
        if s.source_key == "manual_inputs_only":
            s.reported_spend_input = 2000.0
            s.reported_results_input = 100.0
            s.reported_result_type_input = "Conversation"
        s.actual_paid_spend = 2000.0
        s.spend_override_active = False
        s.real_conversations = 80.0
        s.convo_override_active = False
        s.real_orders = 12.0
        s.repeat_order_count = 3.0
        s.refund_count = 1.0
        s.qualified_leads = 60.0
        s.lead_quality = "mixed"
        s.close_rate_use_manual = False
        s.close_rate = 0.15
        s.refund_rate_use_manual = False


def render_example_button():
    """Render the 'Fill with example data' button + a one-line hint above it."""
    cols = st.columns([3, 2])
    with cols[1]:
        if st.button(
            tr("📋 Fill with example data", "📋 Подставить пример"),
            key=f"example_btn_step3_{st.session_state.source_key}",
            use_container_width=True,
            help=tr(
                "Pre-fills every field with a sample $2K e-commerce scenario so you can see how it works.",
                "Заполнит все поля примером ($2K e-commerce), чтобы увидеть, как работает инструмент.",
            ),
        ):
            fill_example_data()
            st.rerun()


def compute_blended_economics():
    """Phase 4: collapse the (optional) product-mix tiers into a single set of
    weighted AOV / COGS / refund% figures, plus per-tier rows for display.

    Returns (aov, cogs_per_order, refund_rate_pct, tiers, used_tiers).
    Falls back to the single AOV/COGS/refund fields when no tier is filled."""
    s = st.session_state
    tiers = []
    for i in (1, 2, 3):
        share = float(s.get(f"tier{i}_share", 0.0) or 0.0)
        aov = float(s.get(f"tier{i}_aov", 0.0) or 0.0)
        if share > 0 and aov > 0:
            tiers.append({
                "name": s.get(f"tier{i}_name") or f"Tier {i}",
                "share": share,
                "aov": aov,
                "cogs": float(s.get(f"tier{i}_cogs", 0.0) or 0.0),
                "refund": float(s.get(f"tier{i}_refund", 0.0) or 0.0),
            })

    total_share = sum(t["share"] for t in tiers)
    if not tiers or total_share <= 0:
        return (
            float(s.aov or 0.0),
            float(s.cogs_per_order or 0.0),
            float(s.refund_rate_pct or 0.0),
            [],
            False,
        )

    blended_aov = sum(t["aov"] * t["share"] / total_share for t in tiers)
    blended_cogs = sum(t["cogs"] * t["share"] / total_share for t in tiers)
    blended_refund = sum(t["refund"] * t["share"] / total_share for t in tiers)
    # Add per-tier break-even CAC so the constraint tier can be flagged later.
    for t in tiers:
        refund_cost = t["aov"] * t["refund"] / 100.0
        t["break_even_cac"] = t["aov"] - t["cogs"] - refund_cost
    return (blended_aov, blended_cogs, blended_refund, tiers, True)


def advanced_economics_block():
    """Phase 4: optional product-mix and attribution inputs behind a toggle.
    Casual users never see these. Tiers, when filled, replace the single AOV /
    COGS / refund inputs via blended weighted averages. Attribution scales the
    CAC denominator down when other channels also drive new orders."""
    with st.expander(
        tr("Advanced: product mix & attribution (optional)",
           "Дополнительно: разбивка по товарам и атрибуция (необязательно)"),
        expanded=False,
    ):
        st.caption(tr(
            "Use these only if 'one average order' or 'all spend acquires all orders' "
            "doesn't describe your business well.",
            "Заполняйте только если 'один средний чек' или 'весь расход привлекает все заказы' "
            "не описывают ваш бизнес.",
        ))

        st.markdown(f"**{tr('Multi-channel attribution', 'Атрибуция по каналам')}**")
        st.number_input(
            tr("Share of new-customer orders attributable to THIS ad spend (%)",
               "Доля заказов новых клиентов, привлечённых ИМЕННО этой рекламой (%)"),
            min_value=0.0, max_value=100.0, step=5.0,
            key="attribution_pct",
            help=tr(
                "Default 100%. If new orders also come from Google, email, organic, "
                "or referrals, lower this — we'll exclude the rest from CAC.",
                "По умолчанию 100%. Если новые заказы приходят и из Google, email, "
                "органики или рефералов — снизьте процент, лишнее не учтём в CAC.",
            ),
        )

        st.markdown("---")
        st.markdown(f"**{tr('Product mix', 'Разбивка по товарам')}**")
        st.caption(tr(
            "Up to 3 product tiers with their own price, cost, and refund rate. "
            "If shares are set, blended values override the single AOV/COGS/refund above. "
            "Leave blank to skip.",
            "До трёх категорий товаров со своей ценой, себестоимостью и возвратами. "
            "Если доли заданы, средневзвешенные значения заменят одиночные выше. "
            "Оставьте пустым, чтобы пропустить.",
        ))

        hdr1, hdr2, hdr3, hdr4, hdr5 = st.columns([2, 1, 1, 1, 1])
        hdr1.markdown(f"<small><b>{tr('Tier name', 'Название')}</b></small>", unsafe_allow_html=True)
        hdr2.markdown(f"<small><b>{tr('Share %', 'Доля %')}</b></small>", unsafe_allow_html=True)
        hdr3.markdown(f"<small><b>AOV</b></small>", unsafe_allow_html=True)
        hdr4.markdown(f"<small><b>{tr('Cost', 'Cебест.')}</b></small>", unsafe_allow_html=True)
        hdr5.markdown(f"<small><b>{tr('Refund %', 'Возвр %')}</b></small>", unsafe_allow_html=True)

        for i in (1, 2, 3):
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            with c1:
                st.text_input(f"name{i}", key=f"tier{i}_name", label_visibility="collapsed")
            with c2:
                st.number_input(f"share{i}", min_value=0.0, max_value=100.0,
                                key=f"tier{i}_share", label_visibility="collapsed")
            with c3:
                st.number_input(f"aov{i}", min_value=0.0, key=f"tier{i}_aov",
                                label_visibility="collapsed")
            with c4:
                st.number_input(f"cogs{i}", min_value=0.0, key=f"tier{i}_cogs",
                                label_visibility="collapsed")
            with c5:
                st.number_input(f"refund{i}", min_value=0.0, max_value=100.0,
                                key=f"tier{i}_refund", label_visibility="collapsed")

        blended_aov, blended_cogs, blended_refund, tiers, used = compute_blended_economics()
        if used:
            _share_total = sum(t["share"] for t in tiers)
            _share_warn = ""
            if abs(_share_total - 100.0) > 0.5:
                _share_warn = (
                    f" <span class='sub'>({tr('shares sum to', 'доли в сумме')} "
                    f"{_share_total:.0f}% — {tr('normalized', 'нормализованы')})</span>"
                )
            st.markdown(
                f"<div class='derived-box'>"
                f"✓ <b>{tr('Blended from tiers', 'Среднее по категориям')}</b>: "
                f"AOV {format_money(blended_aov)} · "
                f"{tr('cost', 'себестоимость')} {format_money(blended_cogs)} · "
                f"{tr('refunds', 'возвраты')} {blended_refund:.1f}%"
                f"{_share_warn}"
                f"</div>",
                unsafe_allow_html=True,
            )


def goto(n: int):
    st.session_state.wizard_step = n
    st.rerun()


def has_uploaded_meta_file() -> bool:
    """True if a Meta report file is in session — either parsed df or raw widget."""
    return (
        st.session_state.get("_uploaded_df") is not None
        or st.session_state.get("meta_uploader") is not None
    )


def force_upload_source_if_file_exists():
    """Prevent accidental fallback to manual mode if a file was already loaded."""
    if has_uploaded_meta_file() and not st.session_state.get("_manual_mode_forced", False):
        st.session_state.source_key = "upload_meta_report"


# Wizard step definitions (label visible on stepper)
STEPS = [
    ("goal",     tr("Goal",       "Цель")),
    ("source",   tr("Data",       "Данные")),
    ("numbers",  tr("Numbers",    "Цифры")),
    ("decision", tr("Decision",   "Решение")),
]


def render_stepper():
    current = st.session_state.wizard_step
    pills_html = []
    for i, (_, label) in enumerate(STEPS, start=1):
        if i < current:
            cls = "done"
            num_html = "✓"
        elif i == current:
            cls = "active"
            num_html = str(i)
        else:
            cls = ""
            num_html = str(i)
        pills_html.append(
            f'<span class="step-pill {cls}"><span class="num">{num_html}</span>{label}</span>'
        )
        if i < len(STEPS):
            bar_cls = "done" if i < current else ""
            pills_html.append(f'<span class="step-bar {bar_cls}"></span>')

    st.markdown(f'<div class="stepper">{"".join(pills_html)}</div>', unsafe_allow_html=True)


def nav_buttons(can_continue: bool = True, continue_label: str | None = None, on_continue=None):
    """Render Back / Continue navigation row at the bottom of a step."""
    st.markdown('<div class="nav-row"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 1, 4, 1, 1])
    step = st.session_state.wizard_step
    with cols[0]:
        if step > 1:
            if st.button(tr("← Back", "← Назад"), key=f"back_{step}", use_container_width=True):
                goto(step - 1)
    with cols[-1]:
        label = continue_label or tr("Continue →", "Дальше →")
        if st.button(
            label,
            key=f"next_{step}",
            type="primary",
            use_container_width=True,
            disabled=not can_continue,
        ):
            if on_continue is not None:
                on_continue()
            goto(step + 1)


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

            df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
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
        return pd.read_csv(uploaded_file, encoding="latin1", sep=None, engine="python", on_bad_lines="skip")
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1", engine="python", on_bad_lines="skip")


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


def plot_profit_curve(df_curve, df_low=None, df_high=None):
    """Render the profit-vs-spend chart.

    Phase 3: when df_low and df_high are provided, draw an uncertainty band
    between them (optimistic vs pessimistic scaling efficiency) and the central
    df_curve line on top. With a single df_curve, behaves as before."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    color = "#6366f1"
    band_color = "#a5b4fc"

    if df_low is not None and df_high is not None:
        # df_low has lower deterioration (more optimistic) → higher profit (upper bound).
        # df_high has higher deterioration (more pessimistic) → lower profit (lower bound).
        ax.fill_between(
            df_curve["ad_spend"],
            df_high["profit"],
            df_low["profit"],
            alpha=0.22, color=band_color, linewidth=0,
            label=tr("Uncertainty band (worse ↔ better scaling)",
                     "Диапазон неопределённости (хуже ↔ лучше)"),
        )

    ax.plot(df_curve["ad_spend"], df_curve["profit"], marker="o", linewidth=2,
            color=color, label=tr("Expected", "Ожидаемое"))
    ax.axhline(0, linewidth=1, color="#94a3b8")

    current_row = df_curve[df_curve["scale_pct"] == 0]
    current = current_row.iloc[0] if not current_row.empty else df_curve.iloc[0]
    peak_idx = df_curve["profit"].idxmax()
    peak = df_curve.loc[peak_idx]

    ax.scatter([current["ad_spend"]], [current["profit"]], s=70, zorder=5, color=color)
    ax.annotate(t["current_point"], (current["ad_spend"], current["profit"]),
                textcoords="offset points", xytext=(8, 8))
    ax.scatter([peak["ad_spend"]], [peak["profit"]], s=70, zorder=5, color=color)
    ax.annotate(t["peak_point"], (peak["ad_spend"], peak["profit"]),
                textcoords="offset points", xytext=(8, -16))

    breakeven_rows = df_curve[df_curve["profit"] <= 0]
    if len(breakeven_rows) > 0:
        be = breakeven_rows.iloc[0]
        ax.scatter([be["ad_spend"]], [be["profit"]], s=70, zorder=5, color=color)
        ax.annotate(t["breakeven_point"], (be["ad_spend"], be["profit"]),
                    textcoords="offset points", xytext=(8, 8))

    ax.set_xlabel("Ad Spend")
    ax.set_ylabel("Net Profit")
    ax.set_title(t["chart_hdr"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if df_low is not None and df_high is not None:
        ax.legend(loc="best", fontsize=8, frameon=False)
    st.pyplot(fig)
    plt.close(fig)

    peak_profit = float(peak["profit"])
    peak_spend = float(peak["ad_spend"])
    cliff_detected = False
    if peak_idx < len(df_curve) - 1:
        final_profit = float(df_curve.iloc[-1]["profit"])
        cliff_detected = final_profit < peak_profit
    return peak_profit, peak_spend, cliff_detected


# =============================================================================
# Page header + stepper
# =============================================================================
st.title(t["title"])
st.caption(t["subtitle"])
st.caption(
    f"Version: phases-1-4-trust-rebuild | "
    f"source={st.session_state.get('source_key')} | "
    f"uploaded={st.session_state.get('_uploaded_df') is not None}"
)
render_stepper()


# =============================================================================
# Domain option lists (used in multiple steps)
# =============================================================================
analysis_goal_options = [
    ("validate_product",  tr("Validate a new product", "Проверить новый товар или услугу")),
    ("test_campaign",     tr("Test a campaign", "Проверить рекламу")),
    ("ads_profitability", tr("Understand if current ads are profitable",
                             "Понять, приносит ли реклама прибыль")),
    ("decide_scale",      tr("Decide whether to scale", "Решить, стоит ли увеличивать бюджет")),
    ("audit_expensive",   tr("Audit why ads feel expensive",
                             "Понять, почему реклама выходит дорогой")),
]
analysis_goal_map = dict(analysis_goal_options)

industry_options = [
    ("ecommerce",     tr("E-commerce", "E-commerce")),
    ("services",      tr("Services", "Услуги")),
    ("education",     tr("Education", "Образование")),
    ("health_beauty", tr("Health / beauty", "Здоровье / красота")),
    ("b2b",           tr("B2B", "B2B")),
    ("other",         tr("Other", "Другое")),
]
sales_channel_options = [
    ("website",      tr("Website checkout", "Покупка на сайте")),
    ("messaging",    tr("WhatsApp / Telegram / DM", "WhatsApp / Telegram / личные сообщения")),
    ("consultation", tr("Call / consultation", "Звонок / консультация")),
    ("mixed",        tr("Mixed", "Несколько способов")),
]
sales_cycle_options = [
    ("same_day",   tr("Same day", "В тот же день")),
    ("days_2_7",   tr("2-7 days", "2–7 дней")),
    ("weeks_1_2",  tr("1-2 weeks", "1–2 недели")),
    ("longer",     tr("Longer", "Дольше")),
]

source_options = [
    ("upload_meta_report",
        tr("Upload Meta CSV/XLSX", "Загрузить отчёт Meta (CSV/XLSX)"),
        tr("Auto-detect spend and conversations from your ad report.",
           "Автоматически подтянем расход и обращения из отчёта.")),
    ("manual_inputs_only",
        tr("Enter manually", "Ввести вручную"),
        tr("Type your ad spend and conversations directly. Best if you don't have a file handy.",
           "Введите расход и обращения сами. Подойдёт, если файла под рукой нет.")),
    ("новый_бизнес_assumptions_only",
        tr("New business / no data yet", "Новый бизнес / пока нет данных"),
        tr("Plan your first ad test using assumptions about price, margin, and close rate.",
           "Спланируем первый тест по предположениям о цене, марже и конверсии.")),
]


# =============================================================================
# STEP 1 — Goal + business context
# =============================================================================
def step_goal():
    st.markdown(f"## {tr('What are you trying to do?', 'Что вы хотите сделать?')}")
    st.caption(tr(
        "Pick the question closest to your situation. We'll tailor the rest of the flow to it.",
        "Выберите задачу, ближе всего к вашей ситуации. Под неё подстроим весь дальнейший процесс."
    ))

    st.radio(
        " ",
        options=[k for k, _ in analysis_goal_options],
        format_func=analysis_goal_map.get,
        horizontal=False,
        label_visibility="collapsed",
        key="goal",
    )

    st.markdown(f"## {tr('A bit about your business', 'Немного о бизнесе')}")
    st.caption(tr(
        "These help calibrate the recommendation. Only the name is optional — feel free to skip it.",
        "Эти данные помогают точнее посчитать рекомендацию. Название можно пропустить."
    ))

    st.text_input(
        tr("Business name (optional)", "Название бизнеса (необязательно)"),
        key="business_name",
        placeholder=tr("e.g., Sunset Studio", "например, Sunset Studio"),
    )

    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            tr("Industry", "Сфера бизнеса"),
            options=[k for k, _ in industry_options],
            format_func=dict(industry_options).get,
            key="industry",
        )
    with c2:
        st.selectbox(
            tr("How do you sell?", "Как вы продаёте?"),
            options=[k for k, _ in sales_channel_options],
            format_func=dict(sales_channel_options).get,
            key="sales_channel",
            help=tr(
                "How most customers actually pay — through a checkout, in chat, or after a call.",
                "Как клиенты в основном платят — через сайт, в переписке или после звонка."
            ),
        )

    with st.expander(tr("More about the business (optional)", "Подробнее о бизнесе (необязательно)")):
        st.selectbox(
            tr("How long does a typical sale take?", "Сколько обычно длится продажа?"),
            options=[k for k, _ in sales_cycle_options],
            format_func=dict(sales_cycle_options).get,
            key="sales_cycle",
            help=tr(
                "From the first message/click to a confirmed paid order.",
                "От первого сообщения/клика до подтверждённого оплаченного заказа."
            ),
        )
        st.radio(
            tr("Do customers buy again?", "Клиенты покупают повторно?"),
            options=["no", "yes"],
            format_func=lambda x: tr("No", "Нет") if x == "no" else tr("Yes", "Да"),
            horizontal=True,
            key="repeat_purchase_default",
            help=tr(
                "If yes, we'll let you account for repeat revenue when judging customer cost.",
                "Если да — учтём повторную выручку при оценке стоимости клиента."
            ),
        )

    nav_buttons(can_continue=True)


# =============================================================================
# STEP 2 — Pick a data source
# =============================================================================
def step_source():
    st.markdown(f"## {tr('Where will the numbers come from?', 'Откуда возьмём цифры?')}")
    st.caption(tr(
        "Pick the option that matches what you have right now. You can always come back and switch.",
        "Выберите вариант, который соответствует вашим данным сейчас. Можно вернуться и поменять."
    ))

    # Custom card-style radio — track when user *explicitly* picks manual
    def _on_source_change():
        chosen = st.session_state.source_key
        if chosen == "manual_inputs_only":
            st.session_state._manual_mode_forced = True
        else:
            st.session_state._manual_mode_forced = False

    st.radio(
        " ",
        options=[k for k, _, _ in source_options],
        format_func=lambda k: next(label for kk, label, _ in source_options if kk == k),
        label_visibility="collapsed",
        key="source_key",
        on_change=_on_source_change,
    )

    chosen_desc = next(desc for k, _, desc in source_options if k == st.session_state.source_key)
    st.info(chosen_desc)

    nav_buttons(can_continue=True)


# =============================================================================
# STEP 3 — Numbers (branches by source)
# =============================================================================
def section_open(title: str, hint: str | None = None):
    st.markdown(f"### {title}")
    if hint:
        st.caption(hint)


# ---- 3a. New business (assumptions only) -----------------------------------
def step_numbers_new_biz():
    st.markdown(f"## {tr('Plan your first test', 'План первого теста')}")
    st.caption(tr(
        "We'll figure out your max safe customer cost and how big a budget makes sense for a first test.",
        "Посчитаем безопасную стоимость клиента и какой бюджет нужен на первый тест."
    ))

    render_example_button()

    section_open(
        tr("Order economics", "Экономика заказа"),
        tr("What you charge and what each order costs you to fulfil.",
           "Сколько берёте с заказа и сколько он вам стоит."),
    )
    c1, c2 = st.columns(2)
    with c1:
        st.number_input(
            money_label(tr("Average order value (AOV)", "Средний чек")),
            min_value=0.0,
            key="aov",
            help=tr(
                "How much one typical paid order brings in (before any discounts).",
                "Сколько в среднем приносит один оплаченный заказ (до скидок)."
            ),
        )
        st.number_input(
            money_label(tr("Product cost per order", "Себестоимость одного заказа")),
            min_value=0.0,
            key="cogs_per_order",
            help=tr(
                "Direct cost per order — product, packaging, fulfilment, payment fees.",
                "Прямые затраты на заказ — товар, упаковка, доставка, комиссия эквайринга."
            ),
        )
        show_note("cogs_per_order", st.session_state.cogs_per_order, aov=st.session_state.aov)
    with c2:
        st.number_input(
            tr("Refund rate (%)", "Процент возвратов (%)"),
            min_value=0.0, max_value=100.0,
            key="refund_rate_pct",
            help=tr(
                "Share of orders that get refunded or cancelled.",
                "Доля заказов, по которым происходит возврат или отмена."
            ),
        )
        show_note("refund_rate_pct", st.session_state.refund_rate_pct)
        st.number_input(
            money_label(tr("Target profit per order", "Желаемая прибыль с заказа")),
            min_value=0.0,
            key="desired_profit_per_order",
            help=tr(
                "What you want to keep per order after product cost AND ad cost.",
                "Сколько хотите оставлять с одного заказа после себестоимости И рекламы."
            ),
        )

    if st.session_state.repeat_purchase_default == "yes":
        # TODO(Phase 2): repeat_purchase_value is collected here but is not yet
        # used in any calculation (compute_decision_state / logic.py). Wire it
        # into the CAC / break-even math in Phase 2.
        st.number_input(
            money_label(tr("Expected repeat revenue per customer", "Ожидаемая повторная выручка с клиента")),
            min_value=0.0,
            key="repeat_purchase_value",
            help=tr(
                "Extra revenue from one customer after their first order. Use only if you have evidence customers come back.",
                "Дополнительная выручка с одного клиента после первой покупки. Используйте, если есть подтверждение, что клиенты возвращаются."
            ),
        )

    section_open(
        tr("Ad assumptions", "Предположения о рекламе"),
        tr("Your best guess for how the ad funnel will perform.",
           "Ваше лучшее предположение, как сработает рекламная воронка."),
    )
    c3, c4 = st.columns(2)
    with c3:
        st.number_input(
            tr("Expected close rate (conversation → order)", "Ожидаемая конверсия (обращение → заказ)"),
            min_value=0.0, max_value=1.0, step=0.05,
            key="close_rate",
            help=tr(
                "Fraction of conversations that become paid orders. 0.20 means 20%. "
                "Best taken from real data: paid orders ÷ meaningful conversations over the same period.",
                "Какая доля обращений становится оплаченным заказом. 0.20 = 20%. "
                "Лучше взять из реальных данных: оплаченные заказы ÷ осмысленные обращения за тот же период."
            ),
        )
        show_note("close_rate", st.session_state.close_rate)
        st.number_input(
            money_label(tr("Expected cost per conversation", "Ожидаемая стоимость одного обращения")),
            min_value=0.0,
            key="expected_cost_per_conversation",
            help=tr(
                "How much you expect to pay Meta to get one conversation/lead.",
                "Сколько ожидаете платить Meta за одно обращение/лид."
            ),
        )
    with c4:
        st.number_input(
            money_label(tr("Expected customer acquisition cost (optional)",
                           "Ожидаемая стоимость клиента (необязательно)")),
            min_value=0.0,
            key="expected_cac_input",
            help=tr(
                "Total ad cost to get one paying customer. Leave 0 to compute it from cost-per-conversation × close rate.",
                "Расход на рекламу на одного оплатившего клиента. Оставьте 0 — посчитаем из стоимости обращения и конверсии."
            ),
        )
        st.selectbox(
            tr("Where do these guesses come from?", "Откуда эти предположения?"),
            options=["guess", "benchmark", "experience"],
            format_func=lambda x: {
                "guess":      tr("Pure guess", "Просто предположение"),
                "benchmark":  tr("Competitor benchmark", "Ориентир по конкурентам"),
                "experience": tr("My past experience", "Мой прошлый опыт"),
            }[x],
            key="assumption_source",
            help=tr(
                "Affects the confidence rating of the result.",
                "Влияет на уровень надёжности итога."
            ),
        )

    with st.expander(tr("Advanced: validation threshold", "Дополнительно: порог проверки"), expanded=False):
        st.caption(tr(
            "How many conversations you want to collect before judging the test.",
            "Сколько обращений нужно собрать до оценки теста."
        ))
        opt = st.selectbox(
            tr("Target conversations", "Целевое число обращений"),
            options=[10, 20, 30, "custom"],
            format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
            key="threshold_option",
        )
        if opt == "custom":
            st.number_input(
                tr("Custom target", "Свой порог"),
                min_value=1, key="custom_threshold",
            )

    nav_buttons(can_continue=st.session_state.aov > 0)


# ---- 3b. Upload (Meta report) ----------------------------------------------
def step_numbers_upload():
    st.markdown(f"## {tr('Step 3 of 3 — Your numbers', 'Шаг 3 из 3 — Ваши цифры')}")
    st.caption(tr(
        "Upload your Meta report so we can detect spend and conversations. Then add the real-world numbers from your CRM and your unit economics.",
        "Загрузите отчёт Meta — определим расход и обращения. Затем добавьте реальные цифры из CRM и юнит-экономику."
    ))

    render_example_button()

    # ---- 1. Upload + auto-detect
    section_open(
        tr("① Upload Meta report", "① Загрузка отчёта Meta"),
        tr("CSV or XLSX exported from Ads Manager.",
           "CSV или XLSX, выгруженные из Ads Manager."),
    )
    uploaded = st.file_uploader(
        tr("Pick your file", "Выберите файл"),
        type=["csv", "xlsx", "xls"],
        key="meta_uploader",
    )
    if uploaded is not None:
        try:
            df = read_uploaded_report(uploaded)
            # If this is a different file, wipe stale column selections
            if uploaded.name != st.session_state.get("_uploaded_filename"):
                for _stale_key in ("_col_campaign", "_col_spend", "_col_results",
                                   "_col_indicator", "_selected_campaigns"):
                    st.session_state.pop(_stale_key, None)
            st.session_state._uploaded_df = df
            st.session_state._uploaded_filename = uploaded.name
            # Lock routing to upload mode the moment a file is successfully read
            st.session_state.source_key = "upload_meta_report"
            st.session_state._manual_mode_forced = False
        except Exception as e:
            st.error(f"{tr('Could not read the file.', 'Не удалось прочитать файл.')} {e}")
            st.session_state._uploaded_df = None

    df = st.session_state.get("_uploaded_df")

    if df is None:
        st.info(tr("Upload a file to continue.", "Загрузите файл, чтобы продолжить."))
    else:
        with st.expander(tr("Preview first 10 rows", "Предпросмотр первых 10 строк"), expanded=False):
            st.dataframe(df.head(10), use_container_width=True)

        cols = list(df.columns)
        cc1, cc2 = st.columns(2)
        with cc1:
            col_campaign = st.selectbox(
                tr("Column: campaign name", "Колонка: название кампании"),
                cols,
                index=guess_index_from_patterns(cols, ["Campaign name", "Campaign", "campaign_name"]),
                key="_col_campaign",
            )
            col_spend = st.selectbox(
                tr("Column: ad spend", "Колонка: расход"),
                cols,
                index=guess_index_from_patterns(cols, ["Amount spent (MYR)", "Amount spent", "Spend"]),
                key="_col_spend",
            )
        with cc2:
            col_results = st.selectbox(
                tr("Column: results", "Колонка: результаты"),
                cols,
                index=guess_index_from_patterns(cols, ["Results", "Result", "results"]),
                key="_col_results",
            )
            col_indicator = st.selectbox(
                tr("Column: result type", "Колонка: тип результата"),
                cols,
                index=guess_index_from_patterns(cols, ["Result indicator", "Action type", "Result type"]),
                key="_col_indicator",
            )

        # Guard: session-state may hold a stale column name from a previous file
        def _safe_col(name, fallback_cols):
            return name if name in df.columns else fallback_cols[0]

        col_campaign  = _safe_col(col_campaign,  cols)
        col_spend     = _safe_col(col_spend,     cols)
        col_results   = _safe_col(col_results,   cols)
        col_indicator = _safe_col(col_indicator, cols)

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
            tr("Include which campaigns?", "Какие кампании включить?"),
            campaigns,
            default=st.session_state.get("_selected_campaigns") or campaigns,
            key="_selected_campaigns",
        )
        if selected_campaigns:
            df_msg = df_msg[df_msg[col_campaign].astype(str).isin(selected_campaigns)].copy()

        df_msg[col_spend] = parse_number_series(df_msg[col_spend])
        df_msg[col_results] = parse_number_series(df_msg[col_results])

        st.session_state.reported_spend_input = float(df_msg[col_spend].sum())
        st.session_state.reported_results_input = float(df_msg[col_results].sum())

        # Pre-fill actual_paid_spend from report ONLY on fresh file load
        # (never overwrite real_conversations — user must enter that manually)
        _just_loaded = st.session_state.get("_autofill_done_for") != st.session_state.get("_uploaded_filename")
        if _just_loaded:
            if st.session_state.actual_paid_spend <= 0:
                st.session_state.actual_paid_spend = st.session_state.reported_spend_input
            st.session_state._autofill_done_for = st.session_state.get("_uploaded_filename")

        filtered_indicator_values = sorted(df_msg[col_indicator].dropna().astype(str).unique().tolist())
        sample_values = filtered_indicator_values[:5]
        st.session_state.reported_result_type_input = (
            ", ".join(sample_values) if sample_values else tr("Not detected", "Не определён")
        )

        s1, s2, s3 = st.columns(3)
        s1.metric(tr("Reported spend", "Расход по отчёту"),
                  format_money(st.session_state.reported_spend_input))
        s2.metric(tr("Reported results", "Результаты по отчёту"),
                  f"{st.session_state.reported_results_input:.1f}")
        s3.metric(tr("Campaigns included", "Кампаний учтено"),
                  len(selected_campaigns) if selected_campaigns else len(campaigns))

        # ── Campaign-level breakdown table (fix 2+3) ──────────────────────
        if not df_msg.empty and selected_campaigns:
            st.markdown(f"**{tr('Campaign breakdown', 'Разбивка по кампаниям')}**")

            # Detect date columns by common Meta naming patterns
            _date_patterns_start = ["reporting starts", "start date", "date start", "starts"]
            _date_patterns_end   = ["reporting ends",   "end date",   "date stop",  "ends"]
            date_col_start = next(
                (c for c in df_msg.columns
                 if any(p in c.lower() for p in _date_patterns_start)),
                None,
            )
            date_col_end = next(
                (c for c in df_msg.columns
                 if any(p in c.lower() for p in _date_patterns_end)
                 and c != date_col_start),
                None,
            )

            _agg = {
                tr("Spend", "Расход"):      (col_spend,   "sum"),
                tr("Results", "Результаты"): (col_results, "sum"),
            }
            if date_col_start:
                _agg[tr("From", "С")] = (date_col_start, "min")
            if date_col_end:
                _agg[tr("To", "По")]  = (date_col_end,   "max")

            grp = df_msg.groupby(col_campaign, as_index=False).agg(**_agg)

            _spend_col   = tr("Spend", "Расход")
            _results_col = tr("Results", "Результаты")
            grp[tr("Cost / result", "Стоимость / результат")] = grp.apply(
                lambda row: round(safe_div(row[_spend_col], row[_results_col]), 2)
                if row[_results_col] > 0 else None,
                axis=1,
            )
            grp[_spend_col]   = grp[_spend_col].round(2)
            grp[_results_col] = grp[_results_col].round(1)

            st.dataframe(grp, use_container_width=True, hide_index=True)

            # ── Mini-summary: best / worst / biggest campaign (feature 1) ──
            _cpr_col2 = tr("Cost / result", "Стоимость / результат")
            _grp_valid = grp[grp[_results_col] > 0].dropna(subset=[_cpr_col2])
            if len(_grp_valid) > 1:
                _best_row  = _grp_valid.loc[_grp_valid[_cpr_col2].idxmin()]
                _worst_row = _grp_valid.loc[_grp_valid[_cpr_col2].idxmax()]
                _big_row   = grp.loc[grp[_results_col].idxmax()]
                st.markdown(
                    f"🟢 **{tr('Cheapest cost/result', 'Лучшая цена/результат')}:** "
                    f"{_best_row[col_campaign]} — {format_money(_best_row[_cpr_col2])}  \n"
                    f"🔴 **{tr('Most expensive', 'Самая дорогая')}:** "
                    f"{_worst_row[col_campaign]} — {format_money(_worst_row[_cpr_col2])}  \n"
                    f"📊 **{tr('Highest volume', 'Наибольший объём')}:** "
                    f"{_big_row[col_campaign]} — "
                    f"{_big_row[_results_col]:.0f} {tr('results', 'результатов')}"
                )

    # ---- 2. Reality check
    st.markdown("")
    section_open(
        tr("② Reality check", "② Сверка с реальностью"),
        tr("Replace Meta's numbers with what you actually saw — paid spend, real conversations, real orders.",
           "Замените цифры Meta тем, что вы видели на самом деле — фактически оплачено, реальные обращения, заказы."),
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        st.number_input(
            money_label(tr("Actual paid spend", "Фактически оплачено")),
            min_value=0.0,
            key="actual_paid_spend",
            help=tr(
                "Real money that left your account, including VAT, top-up fees, agency fees.",
                "Реальные деньги со счёта — с НДС, комиссией пополнения, комиссией агентства."
            ),
        )
        st.checkbox(
            tr("Use this value even if it's 0", "Использовать это значение даже при 0"),
            key="spend_override_active",
        )
        st.number_input(
            tr("Real meaningful conversations", "Реальные осмысленные обращения"),
            min_value=0.0,
            key="real_conversations",
            help=tr(
                "Count of conversations that were actually about buying — not bots or junk.",
                "Сколько диалогов были реально про покупку — без ботов и мусора."
            ),
        )
        st.checkbox(
            tr("Use this value even if it's 0", "Использовать это значение даже при 0"),
            key="convo_override_active",
        )
    with rc2:
        st.number_input(
            tr("Orders", "Заказы"),
            min_value=0.0,
            key="real_orders",
            help=tr(
                "Paid orders attributable to these ads.",
                "Оплаченные заказы, которые можно отнести к этой рекламе."
            ),
        )
        st.number_input(
            tr("…of which repeat customers", "…из них повторных клиентов"),
            min_value=0.0,
            key="repeat_order_count",
            help=tr(
                "Orders from customers who had bought before. These weren't acquired by this ad spend, "
                "so they're excluded from cost-per-new-customer (CAC).",
                "Заказы от клиентов, которые уже покупали раньше. Их не привлекала эта реклама, "
                "поэтому они не учитываются в стоимости привлечения нового клиента (CAC)."
            ),
        )
        st.number_input(
            tr("Refunds / cancellations", "Возвраты / отмены"),
            min_value=0.0,
            key="refund_count",
        )

    with st.expander(tr("Advanced: lead quality and spend reason", "Дополнительно: качество лидов и причина расхождения")):
        st.selectbox(
            tr("Difference reason (paid vs reported)", "Причина разницы (оплачено vs отчёт)"),
            options=["none", "vat", "currency", "topup", "agency", "other"],
            format_func=lambda x: {
                "none":     tr("No adjustment", "Без корректировки"),
                "vat":      tr("VAT / tax", "НДС / налог"),
                "currency": tr("Currency conversion", "Конвертация валюты"),
                "topup":    tr("Top-up fee", "Комиссия пополнения"),
                "agency":   tr("Agency fee", "Комиссия агентства"),
                "other":    tr("Other", "Другое"),
            }[x],
            key="spend_reason",
        )
        st.number_input(
            tr("Qualified leads", "Квалифицированные обращения"),
            min_value=0.0, key="qualified_leads",
            help=tr(
                "Leads that fit your buyer profile, regardless of whether they bought.",
                "Лиды, подходящие под целевой профиль клиента, независимо от факта покупки."
            ),
        )
        st.selectbox(
            tr("Lead quality overall", "Качество обращений в целом"),
            options=["weak", "mixed", "strong"],
            format_func=lambda x: {"weak": tr("Weak", "Слабое"),
                                   "mixed": tr("Mixed", "Смешанное"),
                                   "strong": tr("Strong", "Сильное")}[x],
            key="lead_quality",
        )

    # ---- 3. Economics
    st.markdown("")
    section_open(
        tr("③ Order economics", "③ Экономика заказа"),
        tr("Your unit economics — what you charge, what it costs, how much you want to keep.",
           "Юнит-экономика — сколько берёте, сколько тратите на товар, сколько хотите оставлять."),
    )
    e1, e2 = st.columns(2)
    with e1:
        st.number_input(money_label(tr("Average order value (AOV)", "Средний чек")),
                        min_value=0.0, key="aov",
                        help=tr("How much one paid order brings in.",
                                "Сколько приносит один оплаченный заказ."))
        st.number_input(money_label(tr("Product cost per order", "Себестоимость одного заказа")),
                        min_value=0.0, key="cogs_per_order",
                        help=tr("Direct cost — product, packaging, fulfilment, payment fees.",
                                "Прямые затраты — товар, упаковка, доставка, комиссия эквайринга."))
        show_note("cogs_per_order", st.session_state.cogs_per_order, aov=st.session_state.aov)
    with e2:
        # Phase 6: refund rate is derived from refund_count / real_orders when
        # both exist; manual input is the fallback.
        refund_rate_block()
        st.number_input(money_label(tr("Target profit per order", "Желаемая прибыль с заказа")),
                        min_value=0.0, key="desired_profit_per_order",
                        help=tr("After product cost AND ad cost.",
                                "После себестоимости И стоимости рекламы."))

    if st.session_state.repeat_purchase_default == "yes":
        # TODO(Phase 2): repeat_purchase_value is collected but not yet used in
        # any calculation. Wire it into the CAC / break-even math in Phase 2.
        st.number_input(
            money_label(tr("Expected repeat revenue per customer", "Ожидаемая повторная выручка с клиента")),
            min_value=0.0, key="repeat_purchase_value",
        )

    # Phase 2: derive the close rate from real data when possible; fall back to
    # a manual estimate only when there isn't enough data to compute it.
    close_rate_block()

    # Phase 4: product mix + attribution, opt-in.
    advanced_economics_block()

    with st.expander(tr("Advanced: confidence, threshold, goal", "Дополнительно: уверенность, порог, цель")):
        st.selectbox(
            tr("Confidence in close rate", "Уверенность в конверсии"),
            options=["low", "medium", "high"],
            format_func=lambda x: {"low": tr("Low", "Низкая"),
                                   "medium": tr("Medium", "Средняя"),
                                   "high": tr("High", "Высокая")}[x],
            key="close_rate_confidence",
        )
        # Phase 2: close_rate_source is now set automatically by close_rate_block
        # (real_data when derived, guess when manually overridden) — no need for
        # a user-facing selectbox here.
        st.selectbox(
            tr("What counts as a real lead?", "Что считать реальным обращением?"),
            options=["any_conversation", "осмысленное_обращение", "qualified_lead", "consultation_booked"],
            format_func=lambda x: {
                "any_conversation":         tr("Any conversation", "Любой диалог"),
                "осмысленное_обращение":   tr("Meaningful conversation", "Осмысленный диалог"),
                "qualified_lead":           tr("Qualified lead", "Квалифицированный лид"),
                "consultation_booked":      tr("Booked consultation", "Назначенная консультация"),
            }[x],
            key="real_lead_definition",
        )
        opt = st.selectbox(
            tr("Conversations needed to judge", "Сколько диалогов нужно до оценки"),
            options=[10, 20, 30, "custom"],
            format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
            key="threshold_option",
        )
        if opt == "custom":
            st.number_input(tr("Custom target", "Свой порог"),
                            min_value=1, key="custom_threshold")
        st.selectbox(
            tr("Goal", "Цель"),
            options=["validate_product", "break_even", "small_profit", "aggressive_growth"],
            format_func=lambda x: {
                "validate_product":   tr("Validate demand", "Проверить спрос"),
                "break_even":         tr("Break even", "Выйти в ноль"),
                "small_profit":       tr("Small first-order profit", "Небольшая прибыль с первого заказа"),
                "aggressive_growth":  tr("Aggressive growth", "Агрессивный рост"),
            }[x],
            key="goal_type",
        )
        st.selectbox(
            tr("Budget tolerance", "Допуск по бюджету"),
            options=["conservative", "moderate", "aggressive"],
            format_func=lambda x: {"conservative": tr("Conservative", "Консервативный"),
                                   "moderate": tr("Moderate", "Умеренный"),
                                   "aggressive": tr("Aggressive", "Агрессивный")}[x],
            key="budget_tolerance",
        )
        st.number_input(
            tr("Max acceptable CAC as % of price", "Макс. стоимость клиента, % от цены"),
            min_value=0.0, max_value=500.0, key="max_acceptable_cac_pct_of_price",
        )

    nav_buttons(
        can_continue=st.session_state.aov > 0,
        continue_label=tr("See decision →", "К решению →"),
    )


# ---- 3c. Manual inputs only ------------------------------------------------
def step_numbers_manual():
    st.markdown(f"## {tr('Your numbers', 'Ваши цифры')}")
    st.caption(tr(
        "Enter what you spent and what came back, plus your unit economics. We'll do the rest.",
        "Введите, сколько потратили и что получили, плюс юнит-экономику. Остальное посчитаем."
    ))

    render_example_button()

    section_open(
        tr("① Ad spend & conversations", "① Расход и обращения"),
        tr("Reported numbers from Meta (or wherever you ran ads).",
           "Цифры из отчёта Meta (или того, где крутится реклама)."),
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        st.number_input(
            money_label(tr("Reported ad spend", "Расход по отчёту")),
            min_value=0.0, key="reported_spend_input",
            help=tr("What the ad platform shows as spent (before VAT/fees).",
                    "Что рекламный кабинет показывает как потраченное (до НДС/комиссий)."),
        )
    with m2:
        st.number_input(
            tr("Reported conversations", "Обращений по отчёту"),
            min_value=0.0, key="reported_results_input",
        )
    with m3:
        st.text_input(
            tr("Result type", "Тип результата"),
            key="reported_result_type_input",
            placeholder=tr("e.g., Conversation", "например, Диалог"),
        )

    st.markdown("")
    section_open(
        tr("② Reality check", "② Сверка с реальностью"),
        tr("What you actually saw — paid spend, real conversations, real orders.",
           "Что вы видели реально — фактически оплачено, реальные обращения, заказы."),
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        st.number_input(
            money_label(tr("Actual paid spend", "Фактически оплачено")),
            min_value=0.0, key="actual_paid_spend",
        )
        st.checkbox(tr("Use this even if 0", "Использовать даже при 0"),
                    key="spend_override_active")
        st.number_input(
            tr("Real meaningful conversations", "Реальные осмысленные обращения"),
            min_value=0.0, key="real_conversations",
        )
        st.checkbox(tr("Use this even if 0", "Использовать даже при 0"),
                    key="convo_override_active")
    with rc2:
        st.number_input(tr("Orders", "Заказы"),
                        min_value=0.0, key="real_orders")
        st.number_input(tr("…of which repeat customers", "…из них повторных клиентов"),
                        min_value=0.0, key="repeat_order_count",
                        help=tr("Orders from customers who had bought before. Excluded from cost-per-new-customer (CAC).",
                                "Заказы от клиентов, которые уже покупали. Не учитываются в стоимости привлечения нового клиента (CAC)."))
        st.number_input(tr("Refunds / cancellations", "Возвраты / отмены"),
                        min_value=0.0, key="refund_count")

    with st.expander(tr("Advanced: lead quality and spend reason", "Дополнительно: качество лидов и причина расхождения")):
        st.selectbox(
            tr("Difference reason (paid vs reported)", "Причина разницы (оплачено vs отчёт)"),
            options=["none", "vat", "currency", "topup", "agency", "other"],
            format_func=lambda x: {
                "none": tr("No adjustment", "Без корректировки"),
                "vat":  tr("VAT / tax", "НДС / налог"),
                "currency": tr("Currency conversion", "Конвертация валюты"),
                "topup":    tr("Top-up fee", "Комиссия пополнения"),
                "agency":   tr("Agency fee", "Комиссия агентства"),
                "other":    tr("Other", "Другое"),
            }[x],
            key="spend_reason",
        )
        st.number_input(tr("Qualified leads", "Квалифицированные обращения"),
                        min_value=0.0, key="qualified_leads")
        st.selectbox(
            tr("Lead quality overall", "Качество обращений в целом"),
            options=["weak", "mixed", "strong"],
            format_func=lambda x: {"weak": tr("Weak", "Слабое"),
                                   "mixed": tr("Mixed", "Смешанное"),
                                   "strong": tr("Strong", "Сильное")}[x],
            key="lead_quality",
        )

    st.markdown("")
    section_open(
        tr("③ Order economics", "③ Экономика заказа"),
        tr("Your unit economics.", "Юнит-экономика."),
    )
    e1, e2 = st.columns(2)
    with e1:
        st.number_input(money_label(tr("Average order value (AOV)", "Средний чек")),
                        min_value=0.0, key="aov")
        st.number_input(money_label(tr("Product cost per order", "Себестоимость одного заказа")),
                        min_value=0.0, key="cogs_per_order")
        show_note("cogs_per_order", st.session_state.cogs_per_order, aov=st.session_state.aov)
    with e2:
        # Phase 6: refund rate derived from refund_count / real_orders.
        refund_rate_block()
        st.number_input(money_label(tr("Target profit per order", "Желаемая прибыль с заказа")),
                        min_value=0.0, key="desired_profit_per_order")

    if st.session_state.repeat_purchase_default == "yes":
        # TODO(Phase 2): repeat_purchase_value is collected but not yet used in
        # any calculation. Wire it into the CAC / break-even math in Phase 2.
        st.number_input(money_label(tr("Expected repeat revenue per customer",
                                       "Ожидаемая повторная выручка с клиента")),
                        min_value=0.0, key="repeat_purchase_value")

    # Phase 2: derive the close rate from real data when possible.
    close_rate_block()

    # Phase 4: product mix + attribution, opt-in.
    advanced_economics_block()

    with st.expander(tr("Advanced: confidence, threshold, goal", "Дополнительно: уверенность, порог, цель")):
        st.selectbox(
            tr("Confidence in close rate", "Уверенность в конверсии"),
            options=["low", "medium", "high"],
            format_func=lambda x: {"low": tr("Low", "Низкая"),
                                   "medium": tr("Medium", "Средняя"),
                                   "high": tr("High", "Высокая")}[x],
            key="close_rate_confidence",
        )
        # Phase 2: close_rate_source is now set automatically by close_rate_block.
        opt = st.selectbox(
            tr("Conversations needed to judge", "Сколько диалогов нужно до оценки"),
            options=[10, 20, 30, "custom"],
            format_func=lambda x: tr("Custom", "Свой") if x == "custom" else str(x),
            key="threshold_option",
        )
        if opt == "custom":
            st.number_input(tr("Custom target", "Свой порог"),
                            min_value=1, key="custom_threshold")
        st.selectbox(
            tr("Goal", "Цель"),
            options=["validate_product", "break_even", "small_profit", "aggressive_growth"],
            format_func=lambda x: {
                "validate_product":  tr("Validate demand", "Проверить спрос"),
                "break_even":        tr("Break even", "Выйти в ноль"),
                "small_profit":      tr("Small first-order profit", "Небольшая прибыль с первого заказа"),
                "aggressive_growth": tr("Aggressive growth", "Агрессивный рост"),
            }[x],
            key="goal_type",
        )
        st.selectbox(
            tr("Budget tolerance", "Допуск по бюджету"),
            options=["conservative", "moderate", "aggressive"],
            format_func=lambda x: {"conservative": tr("Conservative", "Консервативный"),
                                   "moderate": tr("Moderate", "Умеренный"),
                                   "aggressive": tr("Aggressive", "Агрессивный")}[x],
            key="budget_tolerance",
        )

    nav_buttons(
        can_continue=st.session_state.aov > 0,
        continue_label=tr("See decision →", "К решению →"),
    )


def step_numbers():
    # Robustly ensure upload source is set if a file is present
    force_upload_source_if_file_exists()

    if st.session_state.source_key == "новый_бизнес_assumptions_only":
        step_numbers_new_biz()
    elif st.session_state.source_key == "upload_meta_report":
        step_numbers_upload()
    else:
        step_numbers_manual()


# =============================================================================
# STEP 4 — Decision (verdict at the top)
# =============================================================================
def compute_decision_state():
    """Compute everything needed to render the decision step.
    Returns a dict so the rendering code stays readable."""
    s = st.session_state

    # Resolve threshold
    threshold = s.custom_threshold if s.threshold_option == "custom" else float(s.threshold_option)

    # ----- New business path -----
    if s.source_key == "новый_бизнес_assumptions_only":
        break_even_cac = s.aov - s.cogs_per_order - (s.aov * s.refund_rate_pct / 100.0)
        target_cac = break_even_cac - s.desired_profit_per_order
        gross_margin_pct = safe_div(s.aov - s.cogs_per_order, s.aov) * 100 if s.aov > 0 else 0.0
        target_cac_pct_of_price = safe_div(target_cac, s.aov) * 100 if s.aov > 0 else 0.0
        # Phase 2: wire repeat_purchase_value into the calculation. We treat
        # repeat revenue at the same gross margin % as the first order — gives
        # a defensible LTV-aware break-even shown alongside (not replacing) the
        # first-order break-even.
        _repeat_value_nb = s.repeat_purchase_value if s.repeat_purchase_default == "yes" else 0.0
        _gm_frac_nb = safe_div(s.aov - s.cogs_per_order, s.aov)
        repeat_contribution = _repeat_value_nb * _gm_frac_nb
        break_even_cac_with_repeat = break_even_cac + repeat_contribution
        estimated_cac = (
            s.expected_cac_input if s.expected_cac_input > 0
            else safe_div(s.expected_cost_per_conversation, s.close_rate)
        )
        max_cost_per_conversation = max(target_cac, 0.0) * s.close_rate
        recommended_test_budget = s.expected_cost_per_conversation * threshold
        scenario_orders = safe_div(recommended_test_budget, estimated_cac) if estimated_cac > 0 else 0.0
        scenario_revenue = scenario_orders * s.aov
        scenario_profit = scenario_orders * (
            s.aov - s.cogs_per_order - (s.aov * s.refund_rate_pct / 100.0) - estimated_cac
        )
        has_economics = s.aov > 0 and s.cogs_per_order >= 0
        close_rate_source = "guess" if s.assumption_source == "guess" else "past_campaigns"

        decision_state = evaluate_decision_state(
            source_key=s.source_key, used_conversations=0.0, real_orders=0.0,
            threshold=threshold, spend_is_adjusted=False, has_economics=has_economics,
            lead_quality="mixed", true_spend=0.0, close_rate_source=close_rate_source,
            lang=lang,
        )
        recommendation_headline, recommendation_points = get_recommendation_v2(
            mode_key=decision_state["mode_key"], true_spend=0.0, reported_spend=0.0,
            used_conversations=0.0, qualified_leads=0.0, real_orders=0.0, refund_count=0.0,
            lead_quality="mixed", break_even_cac=break_even_cac, target_cac=target_cac,
            cost_per_conversation=s.expected_cost_per_conversation,
            estimated_cac=estimated_cac, real_cac=None,
            max_cost_per_conversation=max_cost_per_conversation,
            recommended_test_budget=recommended_test_budget,
            target_conversations=threshold, close_rate_source=close_rate_source,
            lang=lang, currency_symbol=currency_symbol,
        )

        return {
            "path": "new_biz",
            "decision_state": decision_state,
            "recommendation_headline": recommendation_headline,
            "recommendation_points": recommendation_points,
            "break_even_cac": break_even_cac,
            "break_even_cac_with_repeat": break_even_cac_with_repeat,
            "repeat_contribution": repeat_contribution,
            "target_cac": target_cac,
            "gross_margin_pct": gross_margin_pct,
            "target_cac_pct_of_price": target_cac_pct_of_price,
            "estimated_cac": estimated_cac,
            "max_cost_per_conversation": max_cost_per_conversation,
            "recommended_test_budget": recommended_test_budget,
            "scenario_orders": scenario_orders,
            "scenario_revenue": scenario_revenue,
            "scenario_profit": scenario_profit,
            "real_cac": None,
            "new_customer_orders": 0.0,
            "true_spend": 0.0,
            "used_conversations": 0.0,
            "cost_per_reported_result": 0.0,
            "cost_per_conversation": s.expected_cost_per_conversation,
            "spend_overhead_pct": 0.0,
            "threshold": threshold,
        }

    # ----- Upload / manual path -----
    reported_spend = s.reported_spend_input
    reported_results = s.reported_results_input
    reported_result_type = s.reported_result_type_input or tr("Not detected", "Не определён")
    cost_per_reported_result = safe_div(reported_spend, reported_results)

    true_spend = (
        s.actual_paid_spend if s.spend_override_active
        else (s.actual_paid_spend if s.actual_paid_spend > 0 else reported_spend)
    )
    used_conversations = (
        s.real_conversations if s.convo_override_active
        else (s.real_conversations if s.real_conversations > 0 else reported_results)
    )
    spend_is_adjusted = abs(s.actual_paid_spend - reported_spend) > 0.009
    spend_overhead_pct = safe_div(true_spend - reported_spend, reported_spend) * 100 if reported_spend > 0 else 0.0

    # Phase 4: blended economics from product tiers if user filled them; else
    # the single AOV/COGS/refund fields. eff_* are what the rest of the math
    # uses, so tier mode is transparent to everything downstream.
    eff_aov, eff_cogs, eff_refund_pct, tiers, used_tiers = compute_blended_economics()

    refund_cost = eff_aov * eff_refund_pct / 100.0
    break_even_cac = eff_aov - eff_cogs - refund_cost
    target_cac = break_even_cac - s.desired_profit_per_order
    gross_margin_pct = safe_div(eff_aov - eff_cogs, eff_aov) * 100 if eff_aov > 0 else 0.0
    target_cac_pct_of_price = safe_div(target_cac, eff_aov) * 100 if eff_aov > 0 else 0.0
    cost_per_conversation = safe_div(true_spend, used_conversations)
    estimated_cac = safe_div(cost_per_conversation, s.close_rate)

    # Phase 2: strip repeat customers out of the CAC denominator. Ad spend
    # acquires NEW customers; repeat orders weren't paid for here.
    new_customer_orders = max((s.real_orders or 0.0) - (s.repeat_order_count or 0.0), 0.0)
    # Phase 4: multi-channel attribution — only the share of new orders the
    # user attributes to THIS ad spend count toward CAC.
    _attr_frac = max(0.0, min(1.0, float(s.attribution_pct or 100.0) / 100.0))
    new_customer_orders_attr = new_customer_orders * _attr_frac
    real_cac = (
        safe_div(true_spend, new_customer_orders_attr)
        if new_customer_orders_attr > 0 else None
    )

    # Phase 2: wire repeat_purchase_value in. Apply the same gross margin % as
    # the first order — gives a defensible LTV-aware break-even shown ALONGSIDE
    # (not replacing) the first-order break-even. Recommendations stay on the
    # conservative first-order figure.
    _repeat_value = s.repeat_purchase_value if s.repeat_purchase_default == "yes" else 0.0
    _gm_frac = safe_div(eff_aov - eff_cogs, eff_aov)
    repeat_contribution = _repeat_value * _gm_frac
    break_even_cac_with_repeat = break_even_cac + repeat_contribution

    max_cost_per_conversation = max(target_cac, 0.0) * s.close_rate
    recommended_test_budget = threshold * cost_per_conversation
    has_economics = eff_aov > 0 and eff_cogs >= 0

    decision_state = evaluate_decision_state(
        source_key=s.source_key, used_conversations=used_conversations,
        real_orders=s.real_orders, threshold=threshold,
        spend_is_adjusted=spend_is_adjusted, has_economics=has_economics,
        lead_quality=s.lead_quality, true_spend=true_spend,
        close_rate_source=s.close_rate_source, lang=lang,
    )
    recommendation_headline, recommendation_points = get_recommendation_v2(
        mode_key=decision_state["mode_key"], true_spend=true_spend,
        reported_spend=reported_spend, used_conversations=used_conversations,
        qualified_leads=s.qualified_leads, real_orders=s.real_orders,
        refund_count=s.refund_count, lead_quality=s.lead_quality,
        break_even_cac=break_even_cac, target_cac=target_cac,
        cost_per_conversation=cost_per_conversation, estimated_cac=estimated_cac,
        real_cac=real_cac, max_cost_per_conversation=max_cost_per_conversation,
        recommended_test_budget=recommended_test_budget,
        target_conversations=threshold, close_rate_source=s.close_rate_source,
        lang=lang, currency_symbol=currency_symbol,
    )

    return {
        "path": "real",
        "decision_state": decision_state,
        "recommendation_headline": recommendation_headline,
        "recommendation_points": recommendation_points,
        "reported_spend": reported_spend,
        "reported_results": reported_results,
        "reported_result_type": reported_result_type,
        "cost_per_reported_result": cost_per_reported_result,
        "true_spend": true_spend,
        "used_conversations": used_conversations,
        "spend_overhead_pct": spend_overhead_pct,
        "break_even_cac": break_even_cac,
        "break_even_cac_with_repeat": break_even_cac_with_repeat,
        "repeat_contribution": repeat_contribution,
        "new_customer_orders": new_customer_orders,
        "new_customer_orders_attr": new_customer_orders_attr,
        "attribution_pct": float(s.attribution_pct or 100.0),
        "target_cac": target_cac,
        "gross_margin_pct": gross_margin_pct,
        "target_cac_pct_of_price": target_cac_pct_of_price,
        "cost_per_conversation": cost_per_conversation,
        "estimated_cac": estimated_cac,
        "real_cac": real_cac,
        "max_cost_per_conversation": max_cost_per_conversation,
        "recommended_test_budget": recommended_test_budget,
        "threshold": threshold,
        # Phase 4 — surface blended economics & tiers for the render code.
        "aov_effective": eff_aov,
        "cogs_per_order_effective": eff_cogs,
        "refund_rate_pct_effective": eff_refund_pct,
        "tiers": tiers,
        "used_tiers": used_tiers,
    }


def step_decision():
    s = st.session_state

    if s.aov <= 0:
        st.warning(tr(
            "We can't compute a decision yet — go back and enter at least the average order value (AOV).",
            "Не можем посчитать решение — вернитесь назад и укажите хотя бы средний чек."
        ))
        nav_buttons(can_continue=False)
        return

    d = compute_decision_state()
    ds = d["decision_state"]
    mode_key = ds["mode_key"]
    confidence_label = ds["confidence_label"]
    confidence_reasons = ds["confidence_reasons"]
    low_confidence = ds["low_confidence"]

    # ---- Hero verdict ----
    mode_to_label = {
        "новый_бизнес":      tr("Assumption-based plan", "План на предположениях"),
        "ранний_тест":        tr("Early test — keep gathering data", "Ранний тест — продолжайте собирать данные"),
        "данных_достаточно": tr("Validated mode", "Подтверждённый режим"),
    }
    mode_to_status = {
        "новый_бизнес":      "fragile",
        "ранний_тест":        "fragile",
        "данных_достаточно": "safe",
    }
    status_class = mode_to_status.get(mode_key, "fragile")
    headline = d["recommendation_headline"] or mode_to_label.get(mode_key, "")

    st.markdown(
        f"""
        <div class="hero-verdict {status_class}">
            <div class="label">{mode_to_label.get(mode_key, '')}</div>
            <div class="headline">{headline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Top key metrics ----
    if d["path"] == "new_biz":
        m1, m2, m3 = st.columns(3)
        m1.metric(
            tr("Break-even CAC", "Стоимость клиента без убытка"),
            format_money(d["break_even_cac"]),
            help=tr("Above this, ads start losing money — before any profit goal.",
                    "Выше этого — реклама уже в минус, без учёта желаемой прибыли."),
        )
        m2.metric(
            tr("Target CAC", "Желаемая стоимость клиента"),
            format_money(d["target_cac"]),
            help=tr("Customer cost that hits both the break-even AND your target profit.",
                    "Стоимость клиента, при которой и не в минус, и есть желаемая прибыль."),
        )
        m3.metric(
            tr("Validation budget", "Бюджет на валидацию"),
            format_money(d["recommended_test_budget"]),
            help=tr("Roughly what you should be ready to spend before judging the test.",
                    "Примерный бюджет, который стоит быть готовым потратить до оценки теста."),
        )
        # Phase 2: surface LTV-aware break-even when repeat revenue is set.
        _repeat_contrib_nb = float(d.get("repeat_contribution", 0.0))
        if _repeat_contrib_nb > 0:
            _be_with_repeat_nb = float(d.get("break_even_cac_with_repeat", d["break_even_cac"]))
            st.caption(tr(
                f"With expected repeat revenue, break-even CAC rises to "
                f"{format_money(_be_with_repeat_nb)} (+{format_money(_repeat_contrib_nb)} per customer).",
                f"С учётом ожидаемой повторной выручки точка безубытка CAC поднимается до "
                f"{format_money(_be_with_repeat_nb)} (+{format_money(_repeat_contrib_nb)} с клиента).",
            ))
    else:
        real_cac_value = d["real_cac"]
        m1, m2, m3 = st.columns(3)
        m1.metric(
            tr("Real CAC (per new customer)", "Реальный CAC (за нового клиента)"),
            format_money(real_cac_value) if real_cac_value is not None
            else tr("No new orders yet", "Новых заказов пока нет"),
            help=tr("Actual cost per NEW paying customer = paid spend ÷ new-customer orders. "
                    "Repeat orders are excluded because this ad spend didn't acquire them.",
                    "Фактическая стоимость нового клиента = оплачено ÷ заказы новых клиентов. "
                    "Повторные заказы исключены — их не привлекала эта реклама."),
        )
        m2.metric(
            tr("Target CAC", "Желаемая CAC"),
            format_money(d["target_cac"]),
        )
        m3.metric(
            tr("Break-even CAC", "Точка безубытка по CAC"),
            format_money(d["break_even_cac"]),
            help=tr("Per first order, before any repeat revenue.",
                    "За первый заказ, без учёта повторной выручки."),
        )

        # Phase 2: surface attribution + LTV-aware break-even when relevant.
        _repeat_orders = float(s.repeat_order_count or 0.0)
        _new_orders = float(d.get("new_customer_orders", 0.0))
        _repeat_contrib = float(d.get("repeat_contribution", 0.0))
        _be_with_repeat = float(d.get("break_even_cac_with_repeat", d["break_even_cac"]))

        _notes = []
        if _repeat_orders > 0 and (s.real_orders or 0) > 0:
            _notes.append(tr(
                f"CAC is computed on {int(_new_orders)} new-customer orders "
                f"({int(_repeat_orders)} repeat orders excluded).",
                f"CAC посчитан по {int(_new_orders)} заказам новых клиентов "
                f"({int(_repeat_orders)} повторных заказов исключены).",
            ))
        # Phase 4: attribution caption when user dialled it below 100%.
        _attr_pct_view = float(d.get("attribution_pct", 100.0))
        if _attr_pct_view < 100.0 and _new_orders > 0:
            _attributable = float(d.get("new_customer_orders_attr", _new_orders))
            _notes.append(tr(
                f"Attribution set to {_attr_pct_view:.0f}% — CAC counts only "
                f"{_attributable:.1f} of {_new_orders:.0f} new-customer orders.",
                f"Атрибуция {_attr_pct_view:.0f}% — в CAC учтены только "
                f"{_attributable:.1f} из {_new_orders:.0f} заказов новых клиентов.",
            ))
        if _repeat_contrib > 0:
            _notes.append(tr(
                f"With expected repeat revenue, break-even CAC rises to "
                f"{format_money(_be_with_repeat)} (+{format_money(_repeat_contrib)} per customer).",
                f"С учётом ожидаемой повторной выручки точка безубытка CAC поднимается до "
                f"{format_money(_be_with_repeat)} (+{format_money(_repeat_contrib)} с клиента).",
            ))
        if _notes:
            st.caption(" · ".join(_notes))

        # Phase 4: per-tier break-even table when product mix is set.
        if d.get("used_tiers"):
            _tiers_data = d.get("tiers", [])
            if _tiers_data:
                _tier_rows = [{
                    tr("Tier", "Категория"): t["name"],
                    tr("Share %", "Доля %"): round(t["share"], 1),
                    tr("AOV", "AOV"): round(t["aov"], 2),
                    tr("Cost", "Себест."): round(t["cogs"], 2),
                    tr("Refund %", "Возвр %"): round(t["refund"], 1),
                    tr("Break-even CAC", "Безубыток CAC"): round(t["break_even_cac"], 2),
                } for t in _tiers_data]
                _constraint = min(_tiers_data, key=lambda t: t["break_even_cac"])
                st.markdown(f"**{tr('Per-tier break-even', 'Безубыток по категориям')}**")
                st.dataframe(pd.DataFrame(_tier_rows), use_container_width=True, hide_index=True)
                st.caption(tr(
                    f"Constraint tier: '{_constraint['name']}' caps safe CAC at "
                    f"{format_money(_constraint['break_even_cac'])}. "
                    f"If you must keep this tier profitable on its own, the blended figure overstates safe CAC.",
                    f"Ограничивающая категория: '{_constraint['name']}' держит безопасный CAC на уровне "
                    f"{format_money(_constraint['break_even_cac'])}. "
                    f"Если её нужно сохранять прибыльной отдельно — средневзвешенный CAC завышает безопасный уровень.",
                ))

    # ---- Meta vs Reality table (feature 2) ----
    if d["path"] == "real":
        _cpr       = d.get("cost_per_reported_result", 0)
        _cpc       = d.get("cost_per_conversation", 0)
        _rep_res   = d.get("reported_results", 0)
        _real_conv = d.get("used_conversations", 0)
        _rep_sp    = d.get("reported_spend", 0)
        _real_sp   = d.get("true_spend", 0)

        if _rep_res > 0 or _rep_sp > 0 or _real_conv > 0 or _real_sp > 0:
            st.markdown(f"**{tr('Meta vs Reality', 'Meta vs реальность')}**")
            _mv_df = pd.DataFrame({
                tr("Metric", "Метрика"): [
                    tr("Conversations / results", "Диалоги / результаты"),
                    tr("Ad spend", "Расход на рекламу"),
                    tr("Cost per dialogue", "Стоимость диалога"),
                ],
                "Meta": [
                    f"{_rep_res:.0f}" if _rep_res > 0 else "—",
                    format_money(_rep_sp) if _rep_sp > 0 else "—",
                    format_money(_cpr) if _cpr > 0 else "—",
                ],
                tr("Reality", "Реальность"): [
                    f"{_real_conv:.0f}" if _real_conv > 0 else tr("not entered", "не введено"),
                    format_money(_real_sp) if _real_sp > 0 else "—",
                    format_money(_cpc) if _cpc > 0 else tr("need real convos", "нужны реальные обращения"),
                ],
            }).set_index(tr("Metric", "Метрика"))
            st.table(_mv_df)

    # ---- What to do next ----
    if d["recommendation_points"]:
        bullets = "".join(f"<li>{p}</li>" for p in d["recommendation_points"])
        st.markdown(
            f"""
            <div class="next-steps">
              <b>{tr('What to do next', 'Что делать дальше')}</b>
              <ul>{bullets}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- Low-confidence callout ----
    if low_confidence:
        st.warning(tr(
            "Low-confidence analysis — based on assumptions or incomplete downstream data. "
            "Use it for planning, not as proof of profitability.",
            "Низкая надёжность — анализ опирается на предположения или неполные данные ниже по воронке. "
            "Используйте для планирования, не как доказательство прибыльности."
        ))

    # ---- Data sufficiency check (feature 3) ----
    if d["path"] == "real":
        _thresh    = d.get("threshold", 20)
        _n_convos  = d.get("used_conversations", 0)
        _n_orders  = s.real_orders

        st.markdown(f"**{tr('Data sufficiency check', 'Проверка достаточности данных')}**")
        _ad_ok     = _n_convos >= _thresh
        _profit_ok = _n_orders >= 3

        if _ad_ok:
            st.success(tr(
                f"✅ {int(_n_convos)} conversations — enough for an ad-signal verdict.",
                f"✅ {int(_n_convos)} обращений — достаточно для вывода по рекламному сигналу.",
            ))
        else:
            _need = int(_thresh - _n_convos)
            st.warning(tr(
                f"⚠️ {int(_n_convos)} conversations — not enough for an ad-signal verdict yet "
                f"(need {_need} more to reach target of {int(_thresh)}).",
                f"⚠️ {int(_n_convos)} обращений — недостаточно для вывода по рекламному сигналу "
                f"(нужно ещё {_need}, чтобы достичь порога {int(_thresh)}).",
            ))

        if _profit_ok:
            st.success(tr(
                f"✅ {int(_n_orders)} orders — enough to evaluate first-order profitability.",
                f"✅ {int(_n_orders)} заказов — достаточно для оценки прибыльности первого заказа.",
            ))
        elif _n_orders > 0:
            st.warning(tr(
                f"⚠️ {int(_n_orders)} order(s) — need at least 3 real orders for a profit verdict.",
                f"⚠️ {int(_n_orders)} заказ(ов) — нужно минимум 3 реальных заказа для вывода о прибыли.",
            ))
        else:
            st.warning(tr(
                "⚠️ No real orders yet — required to evaluate profitability.",
                "⚠️ Реальных заказов нет — они нужны для оценки прибыли.",
            ))

    # ---- Reliability ----
    with st.expander(tr("Reliability of this analysis", "Насколько надёжен этот анализ"), expanded=False):
        st.markdown(f"**{tr('Confidence', 'Уверенность')}: {confidence_label}**")
        for reason in confidence_reasons:
            st.markdown(f"- {reason}")

    # ---- Detailed funnel + economics (only for non-new-biz path) ----
    if d["path"] == "real":
        with st.expander(tr("Detailed funnel and economics", "Подробно: воронка и экономика"), expanded=False):
            meta_col, biz_col = st.columns(2)
            with meta_col:
                st.markdown(f"**{tr('What Meta reports', 'Что сообщает Meta')}**")
                st.metric(tr("Reported spend", "Расход по отчёту"),
                          format_money(d["reported_spend"]))
                st.metric(tr("Reported results", "Результаты по отчёту"),
                          f"{d['reported_results']:.1f}")
                st.metric(tr("Result type", "Тип результата"),
                          (d["reported_result_type"] or "")[:32] or tr("n/a", "н/д"))
                st.metric(tr("Cost per reported result", "Стоимость результата по отчёту"),
                          format_money(d["cost_per_reported_result"]))
            with biz_col:
                st.markdown(f"**{tr('What you actually saw', 'Что вы увидели на самом деле')}**")
                st.metric(tr("Actual paid spend", "Фактически оплачено"),
                          format_money(d["true_spend"]))
                st.metric(tr("Real conversations", "Реальные обращения"),
                          f"{d['used_conversations']:.1f}")
                st.metric(tr("Qualified leads", "Квалифицированные обращения"),
                          f"{s.qualified_leads:.1f}")
                st.metric(tr("Orders", "Заказы"), f"{s.real_orders:.1f}")

            st.markdown(f"**{tr('Funnel comparison', 'Сравнение воронки')}**")
            f1, f2, f3, f4 = st.columns(4)
            f1.metric(tr("Meta convos", "Meta"), f"{d['reported_results']:.1f}")
            f2.metric(tr("Real convos", "Реальные"), f"{d['used_conversations']:.1f}")
            f3.metric(tr("Qualified", "Качественные"), f"{s.qualified_leads:.1f}")
            f4.metric(tr("Orders", "Заказы"), f"{s.real_orders:.1f}")

            fp1, fp2, fp3 = st.columns(3)
            fp1.metric(
                tr("Real / Meta", "Реальные / Meta"),
                f"{safe_div(d['used_conversations'], d['reported_results']) * 100:.1f}%"
                if d['reported_results'] > 0 else tr("n/a", "н/д"),
            )
            fp2.metric(
                tr("Qualified / Real", "Качество / реальные"),
                f"{safe_div(s.qualified_leads, d['used_conversations']) * 100:.1f}%"
                if d['used_conversations'] > 0 else tr("n/a", "н/д"),
            )
            base_for_orders = s.qualified_leads if s.qualified_leads > 0 else d["used_conversations"]
            fp3.metric(
                tr("Orders / base", "Заказы / база"),
                f"{safe_div(s.real_orders, base_for_orders) * 100:.1f}%"
                if base_for_orders > 0 else tr("n/a", "н/д"),
            )

            st.markdown(f"**{tr('Order economics', 'Экономика заказа')}**")
            x1, x2, x3 = st.columns(3)
            _x_aov = d.get("aov_effective", s.aov)
            _x_cogs = d.get("cogs_per_order_effective", s.cogs_per_order)
            _aov_label = tr("AOV (blended)", "Средний чек (средневзв.)") if d.get("used_tiers") else tr("AOV", "Средний чек")
            _cogs_label = tr("Product cost (blended)", "Себестоимость (средневзв.)") if d.get("used_tiers") else tr("Product cost", "Себестоимость")
            x1.metric(_aov_label, format_money(_x_aov))
            x2.metric(_cogs_label, format_money(_x_cogs))
            x3.metric(tr("Gross margin %", "Валовая маржа %"), f"{d['gross_margin_pct']:.1f}%")

            st.markdown(f"**{tr('Recommended test budget at this conversation cost',  'Рекомендуемый тестовый бюджет при текущей стоимости диалога')}**")
            cb = d["cost_per_conversation"]
            tb1, tb2, tb3, tb4 = st.columns(4)
            tb1.metric(tr("10 convos", "10 обращений"), format_money(cb * 10))
            tb2.metric(tr("20 convos", "20 обращений"), format_money(cb * 20))
            tb3.metric(tr("30 convos", "30 обращений"), format_money(cb * 30))
            tb4.metric(tr("Selected target", "Выбранный порог"),
                       format_money(d["recommended_test_budget"]))

    # ---- New-biz illustrative scenario ----
    if d["path"] == "new_biz":
        with st.expander(tr("Illustrative scenario (if assumptions hold)",
                            "Примерный сценарий (если предположения верны)")):
            st.markdown(f"- {tr('Illustrative orders', 'Примерное число заказов')}: **{d['scenario_orders']:.1f}**")
            st.markdown(f"- {tr('Illustrative revenue', 'Примерная выручка')}: **{format_money(d['scenario_revenue'])}**")
            st.markdown(f"- {tr('Illustrative profit', 'Примерная прибыль')}: **{format_money(d['scenario_profit'])}**")

    # ---- Key answers ----
    with st.expander(tr("Key answers to the 4 core questions", "Ответы на 4 ключевых вопроса"), expanded=False):
        theory_answer = (
            tr("Yes, if CAC stays below target CAC.",
               "Да, если стоимость клиента ниже целевой.")
            if d["target_cac"] > 0
            else tr("Not yet. The first-order economics don't currently support ads.",
                    "Пока нет. Экономика первого заказа не поддерживает рекламу.")
        )
        data_answer = (
            tr("Yes, there is enough downstream evidence.",
               "Да, данных ниже по воронке достаточно.")
            if mode_key == "данных_достаточно"
            else tr("Not yet. Gather more real conversations and orders first.",
                    "Пока нет. Нужно больше реальных диалогов и заказов.")
        )
        next_budget = (
            format_money(d["recommended_test_budget"])
            + (tr(" (rough estimate — low confidence)", " (примерно — низкая надёжность)")
               if low_confidence else "")
            if d["recommended_test_budget"] > 0
            else tr("Need conversation cost first.", "Сначала нужна стоимость диалога.")
        )
        scale_answer = {
            "данных_достаточно": d["recommendation_headline"],
            "ранний_тест":        tr("Too early to judge profitability.",
                                     "Слишком рано судить о прибыльности."),
            "новый_бизнес":      tr("Not yet. Validate assumptions first.",
                                     "Пока нет. Сначала проверьте предположения."),
        }.get(mode_key, tr("Not enough data yet.", "Данных пока недостаточно."))

        st.markdown(f"**1.** {tr('Can this business support ads in theory?', 'Может ли экономика выдержать рекламу?')} — {theory_answer}")
        st.markdown(f"**2.** {tr('Is the data enough to judge?', 'Достаточно ли данных для вывода?')} — {data_answer}")
        st.markdown(f"**3.** {tr('How much to spend next to get evidence?', 'Сколько потратить дальше для доказательств?')} — **{next_budget}**")
        st.markdown(f"**4.** {tr('If evidence is strong, should we scale?', 'Если данных достаточно — стоит ли масштабироваться?')} — {scale_answer}")

    # ---- Scale simulation (show whenever we have real orders, with caveats) ----
    if (
        d["path"] == "real"
        and s.real_orders > 0
        and s.aov > 0
    ):
        with st.expander(tr("Scale simulation", "Симуляция масштаба"), expanded=False):
            if low_confidence or mode_key != "данных_достаточно":
                st.info(tr(
                    "Limited data — treat this simulation as a directional estimate, not a forecast.",
                    "Мало данных — воспринимайте симуляцию как ориентир, а не как прогноз.",
                ))
            preset = st.radio(
                tr("How does ad efficiency usually behave when you scale?",
                   "Как обычно меняется эффективность при росте бюджета?"),
                options=["optimistic", "realistic", "pessimistic"],
                format_func=lambda x: {"optimistic": tr("Optimistic", "Оптимистично"),
                                       "realistic": tr("Realistic", "Реалистично"),
                                       "pessimistic": tr("Pessimistic", "Пессимистично")}[x],
                horizontal=True,
                key="scale_preset",
            )
            default_decay = 10 if preset == "optimistic" else 25 if preset == "realistic" else 50
            spend_change_pct = st.slider(
                tr("Planned ad spend change (%)", "Изменение бюджета (%)"),
                -80, 300, 50,
                key="spend_change_pct",
            )
            cac_deterioration_per_100 = st.slider(
                tr("If you double spend, how much can CAC rise (%)?",
                   "При удвоении бюджета — на сколько вырастет CAC (%)?"),
                0, 100, default_decay,
                # Key includes preset so Streamlit resets the slider when preset changes
                key=f"cac_deterioration_{preset}",
            )

            # Phase 3: derive CAC deterioration from a real prior period.
            with st.expander(
                tr("Advanced: calculate deterioration from your history",
                   "Дополнительно: рассчитать снижение по вашей истории"),
                expanded=False,
            ):
                st.caption(tr(
                    "If you ran ads in a prior period, we can derive your real "
                    "deterioration from that instead of guessing.",
                    "Если у вас есть прошлый период, мы можем рассчитать реальное "
                    "снижение по нему вместо предположения.",
                ))
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.number_input(
                        money_label(tr("Prior period — CAC", "Прошлый период — CAC")),
                        min_value=0.0, key="prior_period_cac",
                    )
                    st.number_input(
                        money_label(tr("Prior period — ad spend", "Прошлый период — расход")),
                        min_value=0.0, key="prior_period_spend",
                    )
                with dc2:
                    st.number_input(
                        money_label(tr("Current period — CAC", "Текущий период — CAC")),
                        min_value=0.0, key="current_period_cac",
                    )
                    st.number_input(
                        money_label(tr("Current period — ad spend", "Текущий период — расход")),
                        min_value=0.0, key="current_period_spend",
                    )

                k_derived = None
                _has_history = (
                    s.prior_period_cac > 0 and s.current_period_cac > 0
                    and s.prior_period_spend > 0 and s.current_period_spend > 0
                )
                if _has_history:
                    _g_obs = (s.current_period_spend - s.prior_period_spend) / s.prior_period_spend
                    if abs(_g_obs) >= 0.05:
                        _cac_ratio = s.current_period_cac / s.prior_period_cac
                        _k_raw = ((_cac_ratio - 1) / _g_obs) * 100.0
                        k_derived = max(0.0, min(100.0, _k_raw))
                        st.markdown(
                            f"<div class='derived-box'>"
                            f"✓ <b>{tr('Deterioration from your data', 'Снижение по вашим данным')}: "
                            f"{k_derived:.0f}%</b><br>"
                            f"<span class='sub'>"
                            f"{tr('Spend changed', 'Бюджет изменился на')} {_g_obs*100:+.0f}%, "
                            f"{tr('CAC changed', 'CAC изменился на')} {(_cac_ratio-1)*100:+.0f}% — "
                            f"{tr('no guessing needed', 'гадать не нужно')}"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )
                        st.checkbox(
                            tr("Use this derived deterioration instead of the slider above",
                               "Использовать расчётное значение вместо ползунка выше"),
                            key="use_derived_deterioration",
                        )
                    else:
                        st.caption(tr(
                            "Spend change between periods is too small to derive a reliable rate (need ≥5%).",
                            "Изменение бюджета между периодами слишком мало для надёжного расчёта (нужно ≥5%).",
                        ))

            # Phase 3: central deterioration — derived if user opted in, else slider.
            k_mid = (
                float(k_derived) if (k_derived is not None and s.use_derived_deterioration)
                else float(cac_deterioration_per_100)
            )
            k_low = max(0.0, k_mid - 15.0)   # more optimistic
            k_high = min(100.0, k_mid + 25.0)  # more pessimistic

            # Phase 4: use blended (tier-aware) economics when product mix is set.
            _eff_aov = d.get("aov_effective", s.aov)
            _eff_cogs = d.get("cogs_per_order_effective", s.cogs_per_order)
            _eff_refund = d.get("refund_rate_pct_effective", s.refund_rate_pct)
            model_revenue = _eff_aov * s.real_orders
            model_cogs = _eff_cogs * s.real_orders

            def _sim(pct, k):
                return simulate_scale(
                    revenue=model_revenue, cogs=model_cogs, ad_spend=d["true_spend"],
                    orders=s.real_orders, refund_rate_pct=_eff_refund,
                    spend_change_pct=pct, cac_deterioration_per_100_pct=k,
                )

            def _curve(k):
                return build_profit_curve(
                    revenue=model_revenue, cogs=model_cogs, ad_spend=d["true_spend"],
                    orders=s.real_orders, refund_rate_pct=_eff_refund,
                    cac_deterioration_per_100_pct=k,
                )

            res = _sim(spend_change_pct, k_mid)
            res_low = _sim(spend_change_pct, k_low)
            res_high = _sim(spend_change_pct, k_high)

            df_curve_mid = _curve(k_mid)
            df_curve_low = _curve(k_low)   # optimistic → upper bound
            df_curve_high = _curve(k_high)  # pessimistic → lower bound

            safe_mid = find_safe_max_scale_pct(
                revenue=model_revenue, cogs=model_cogs, ad_spend=d["true_spend"],
                orders=s.real_orders, refund_rate_pct=_eff_refund,
                cac_deterioration_per_100_pct=k_mid, max_search_pct=300,
            )
            safe_low = find_safe_max_scale_pct(
                revenue=model_revenue, cogs=model_cogs, ad_spend=d["true_spend"],
                orders=s.real_orders, refund_rate_pct=_eff_refund,
                cac_deterioration_per_100_pct=k_high, max_search_pct=300,
            )
            safe_high = find_safe_max_scale_pct(
                revenue=model_revenue, cogs=model_cogs, ad_spend=d["true_spend"],
                orders=s.real_orders, refund_rate_pct=_eff_refund,
                cac_deterioration_per_100_pct=k_low, max_search_pct=300,
            )

            _, _, cliff_detected = plot_profit_curve(
                df_curve_mid, df_low=df_curve_low, df_high=df_curve_high,
            )
            st.caption(tr(
                "Shaded band = profit if scaling is more / less efficient than your central estimate. "
                "When inputs are uncertain, the band widens — treat the band, not the line, as the answer.",
                "Заштрихованная полоса = прибыль, если рост окажется лучше или хуже центральной оценки. "
                "Когда исходные данные неточные, полоса шире — ориентируйтесь на полосу, а не на линию.",
            ))

            sm1, sm2, sm3 = st.columns(3)
            sm1.metric(tr("Forecast spend", "Расход в расчёте"), format_money(res["new_spend"]))
            sm2.metric(
                tr("Forecast profit (range)", "Прибыль (диапазон)"),
                f"{format_money(res_high['new_profit'])} – {format_money(res_low['new_profit'])}",
                help=tr(
                    f"Pessimistic – optimistic scaling. Central estimate: {format_money(res['new_profit'])}.",
                    f"Пессимистично – оптимистично. Центральная оценка: {format_money(res['new_profit'])}.",
                ),
            )
            sm3.metric(
                tr("Safe scale limit (range)", "Безопасный лимит роста (диапазон)"),
                f"{safe_low}% – {safe_high}%",
                help=tr(
                    f"Pessimistic – optimistic. Central estimate: {safe_mid}%.",
                    f"Пессимистично – оптимистично. Центральная оценка: {safe_mid}%.",
                ),
            )

            if cliff_detected:
                st.warning(tr(
                    "Profit cliff detected: scaling past the peak reduces profit.",
                    "Обнаружен обрыв прибыли: рост выше пика снижает прибыль."
                ))

            scenarios = [-50, -25, 0, 25, 50, 100, 150, 200]
            rows = []
            for pct in scenarios:
                r_mid = _sim(pct, k_mid)
                r_low = _sim(pct, k_low)
                r_high = _sim(pct, k_high)
                rows.append({
                    tr("Spend change %", "Изменение бюджета, %"): pct,
                    tr("Ad spend", "Расход"): round(r_mid["new_spend"], 2),
                    tr("CAC", "CAC"): round(r_mid["new_cac"], 2) if r_mid["new_cac"] > 0 else None,
                    tr("Orders", "Заказы"): round(r_mid["new_orders"], 1),
                    tr("Revenue", "Выручка"): round(r_mid["new_revenue"], 2),
                    tr("Profit (expected)", "Прибыль (ожидаемая)"): round(r_mid["new_profit"], 2),
                    tr("Profit range (low – high)", "Диапазон (низ – верх)"):
                        f"{format_money(r_high['new_profit'])} – {format_money(r_low['new_profit'])}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # ---- What to ask the client next (feature 4) ----
    if d["path"] == "real":
        _missing_items = []
        if s.aov <= 0:
            _missing_items.append(tr(
                "Average order value (AOV) — what does one sale bring in?",
                "Средний чек — сколько приносит одна продажа?",
            ))
        if s.cogs_per_order <= 0:
            _missing_items.append(tr(
                "Product cost per order — product, packaging, fulfilment, fees.",
                "Себестоимость заказа — товар, упаковка, доставка, комиссия эквайринга.",
            ))
        if s.real_orders <= 0:
            _missing_items.append(tr(
                "Real paid orders — from CRM or bank (not Meta attribution).",
                "Реальные оплаченные заказы — из CRM или банка (не атрибуция Meta).",
            ))
        if s.refund_count <= 0 and s.refund_rate_pct <= 0:
            _missing_items.append(tr(
                "Refunds / cancellations — how many orders were returned this period?",
                "Возвраты / отмены — сколько заказов вернули за этот период?",
            ))
        if s.real_conversations <= 0:
            _missing_items.append(tr(
                "Real conversations — how many chats were actually about buying (not bots)?",
                "Реальные обращения — сколько диалогов были реально про покупку (без ботов)?",
            ))

        _always_items = [
            tr(
                "Were there any promotions, discounts, or external events this period?",
                "Были ли акции, скидки или внешние события в этот период?",
            ),
            tr(
                "Which audience / placement / creative was used?",
                "Какая аудитория / плейсмент / креатив использовались?",
            ),
            tr(
                "How long does a typical sale take from first message to payment?",
                "Сколько времени от первого сообщения до оплаты?",
            ),
            tr(
                "Do customers buy again? If yes, what's the average repeat revenue?",
                "Покупают ли клиенты повторно? Если да — какая средняя повторная выручка?",
            ),
        ]

        _exp_label = (
            tr("⚠️ What to ask the client next", "⚠️ Что спросить у клиента дальше")
            if _missing_items
            else tr("✅ What else to ask the client", "✅ Что ещё можно спросить у клиента")
        )
        with st.expander(_exp_label, expanded=bool(_missing_items)):
            if _missing_items:
                st.caption(tr(
                    "To complete this analysis, ask the business owner:",
                    "Чтобы завершить анализ, спросите у владельца бизнеса:",
                ))
                for _itm in _missing_items:
                    st.markdown(f"- ☐ {_itm}")
                if _always_items:
                    st.markdown("---")
                    st.caption(tr("Also useful to ask:", "Также полезно уточнить:"))
                    for _itm in _always_items:
                        st.markdown(f"- ☐ {_itm}")
            else:
                st.caption(tr(
                    "All key data is in. You can still ask:",
                    "Все ключевые данные заполнены. Можно дополнительно спросить:",
                ))
                for _itm in _always_items:
                    st.markdown(f"- ☐ {_itm}")

    # ---- Footer nav: Back / Start over ----
    st.markdown('<div class="nav-row"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 1, 4, 1, 1])
    with cols[0]:
        if st.button(tr("← Edit inputs", "← Изменить ввод"),
                     key="decision_edit_inputs", use_container_width=True):
            goto(3)
    with cols[-1]:
        if st.button(tr("Start over", "Начать заново"),
                     key="decision_start_over", use_container_width=True):
            for k in list(st.session_state.keys()):
                if not k.startswith("_streamlit"):
                    del st.session_state[k]
            st.rerun()


# =============================================================================
# Sidebar progress summary (always visible)
# =============================================================================
with st.sidebar:
    st.markdown("---")
    st.markdown(f"### {tr('Your progress', 'Ваш прогресс')}")
    step = st.session_state.wizard_step
    sb_lines = []
    sb_lines.append(
        f"<div class='sb-row'><b>{tr('Step', 'Шаг')}:</b> {step} / {len(STEPS)} — {STEPS[step-1][1]}</div>"
    )
    if step >= 2:
        sb_lines.append(
            f"<div class='sb-row'><b>{tr('Goal', 'Цель')}:</b> {analysis_goal_map[st.session_state.goal]}</div>"
        )
    if step >= 3:
        src_label = next(label for k, label, _ in source_options if k == st.session_state.source_key)
        sb_lines.append(
            f"<div class='sb-row'><b>{tr('Source', 'Источник')}:</b> {src_label}</div>"
        )
    if st.session_state.business_name:
        sb_lines.append(
            f"<div class='sb-row'><b>{tr('Business', 'Бизнес')}:</b> {st.session_state.business_name}</div>"
        )
    if step == 4 and st.session_state.aov > 0:
        try:
            d_preview = compute_decision_state()
            mode_key = d_preview["decision_state"]["mode_key"]
            mode_label = {
                "новый_бизнес":      tr("Plan", "План"),
                "ранний_тест":        tr("Early test", "Ранний тест"),
                "данных_достаточно": tr("Validated", "Подтверждено"),
            }.get(mode_key, "")
            sb_lines.append(
                f"<div class='sb-row'><b>{tr('Mode', 'Режим')}:</b> {mode_label}</div>"
            )
            sb_lines.append(
                f"<div class='sb-row'><b>{tr('Confidence', 'Уверенность')}:</b> {d_preview['decision_state']['confidence_label']}</div>"
            )
        except Exception:
            pass
    st.markdown("\n".join(sb_lines), unsafe_allow_html=True)

    st.markdown("---")
    if st.button(tr("Reset all", "Сбросить всё"), use_container_width=True, key="sb_reset"):
        for k in list(st.session_state.keys()):
            if not k.startswith("_streamlit"):
                del st.session_state[k]
        st.rerun()


# =============================================================================
# Main: render the current step
# =============================================================================
step = st.session_state.wizard_step
if step == 1:
    step_goal()
elif step == 2:
    step_source()
elif step == 3:
    step_numbers()
elif step == 4:
    step_decision()
else:
    st.session_state.wizard_step = 1
    st.rerun()
