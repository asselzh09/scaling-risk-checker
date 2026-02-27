import streamlit as st
import pandas as pd

st.set_page_config(page_title="Scaling Risk Checker", layout="centered")

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

st.title("Scaling Risk Checker")
st.write("Upload Meta export or input manually. Then simulate spend scaling with efficiency deterioration.")


# -----------------------------
# Core model (finance-only scaling)
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

    # Baseline unit economics
    AOV = revenue / orders if orders > 0 else 0.0
    cogs_per_order = cogs / orders if orders > 0 else 0.0
    cac = ad_spend / orders if orders > 0 else 0.0

    baseline_refund_cost = revenue * rr
    baseline_profit = revenue - cogs - ad_spend - baseline_refund_cost

    # max CAC per order you can pay while staying at profit >= 0
    break_even_cac = (AOV - cogs_per_order - (AOV * rr))
    margin_buffer = ((break_even_cac - cac) / break_even_cac) if break_even_cac > 0 else 0.0

    # Scaling simulation
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
        "rr": rr,
        "g": g,
        "k": k,
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
# Input mode
# -----------------------------
mode = st.radio(
    "Choose input mode",
    ["Manual finance", "Meta CSV upload", "Manual funnel (Meta-like)"],
    horizontal=True,
)

st.divider()

# These will be filled by the selected mode:
revenue = 0.0
cogs = 0.0
ad_spend = 0.0
orders = 1.0
refund_rate = 0.0

# Extra diagnostics for Meta modes
diag = {}

if mode == "Manual finance":
    revenue = st.number_input("Total Revenue ($)", min_value=0.0, value=0.0)
    cogs = st.number_input("Total COGS ($)", min_value=0.0, value=0.0)
    ad_spend = st.number_input("Ad Spend ($)", min_value=0.0, value=0.0)
    orders = st.number_input("Orders", min_value=1, value=1)
    refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0, value=0.0)

elif mode == "Meta CSV upload":
    st.subheader("Upload Meta export")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if not uploaded:
        st.info("Upload your Meta export CSV to auto-fill Spend + Conversations. You'll still input AOV/COGS + close rate.")
        st.stop()

    df = pd.read_csv(uploaded)
    st.write("Preview")
    st.dataframe(df.head(10), use_container_width=True)

    cols = list(df.columns)

    # Map columns (so it works with different export headers)
    def guess_index(name_candidates):
        for c in name_candidates:
            if c in cols:
                return cols.index(c)
        return 0

    col_campaign = st.selectbox("Campaign name column", cols, index=guess_index(["Campaign name", "Campaign", "campaign_name"]))
    col_spend = st.selectbox("Spend column", cols, index=guess_index(["Amount spent (MYR)", "Amount spent", "Spend"]))
    col_results = st.selectbox("Results column", cols, index=guess_index(["Results", "Result", "results"]))
    col_indicator = st.selectbox("Result indicator column", cols, index=guess_index(["Result indicator", "Action type", "Result type", "result_indicator"]))

    msg_mask = df[col_indicator].astype(str).str.contains("messaging_conversation_started", case=False, na=False)
    df_msg = df[msg_mask].copy()

    if df_msg.empty:
        st.error("No rows found where Result indicator contains 'messaging_conversation_started'.")
        st.stop()

    campaigns = sorted(df_msg[col_campaign].astype(str).unique().tolist())
    selected = st.multiselect("Select campaigns to include", campaigns, default=campaigns)

    df_sel = df_msg[df_msg[col_campaign].astype(str).isin(selected)].copy()
    df_sel[col_spend] = pd.to_numeric(df_sel[col_spend], errors="coerce").fillna(0.0)
    df_sel[col_results] = pd.to_numeric(df_sel[col_results], errors="coerce").fillna(0.0)

    meta_spend = float(df_sel[col_spend].sum())
    meta_convos = float(df_sel[col_results].sum())

    st.markdown("### Derived from CSV")
    st.write(f"Spend (selected): **{meta_spend:.2f}**")
    st.write(f"Messaging conversations (selected): **{meta_convos:.0f}**")

    if meta_convos <= 0:
        st.error("Conversations sum to 0. Can't proceed.")
        st.stop()

    cpa_msg = meta_spend / meta_convos
    st.write(f"CPA (message conversation): **{cpa_msg:.2f}**")

    st.divider()
    st.subheader("Bridge Meta → Finance")

    close_rate = st.number_input("Close rate (orders / conversations)", min_value=0.0, max_value=1.0, value=0.20, help="If 20% of chats become orders, use 0.20")
    AOV = st.number_input("AOV ($) (average order value)", min_value=0.0, value=0.0)
    cogs_per_order = st.number_input("COGS per order ($)", min_value=0.0, value=0.0)
    refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0, value=0.0)

    inferred_orders = meta_convos * close_rate
    if inferred_orders < 1:
        st.warning("Inferred orders < 1. Close rate might be too low or dataset too small. I’ll still run with Orders=1 to avoid divide-by-zero.")
        inferred_orders = 1.0

    ad_spend = meta_spend
    orders = float(inferred_orders)
    revenue = AOV * orders
    cogs = cogs_per_order * orders

    diag = {
        "meta_convos": meta_convos,
        "cpa_msg": cpa_msg,
        "close_rate": close_rate,
        "implied_cac": (cpa_msg / close_rate) if close_rate > 0 else None,
    }

else:  # Manual funnel (Meta-like)
    st.subheader("Manual funnel inputs (Meta-like)")
    spend = st.number_input("Spend ($)", min_value=0.0, value=0.0)
    conversations = st.number_input("Messaging conversations", min_value=0.0, value=0.0)
    clicks = st.number_input("Clicks (optional, for diagnostics)", min_value=0.0, value=0.0)
    impressions = st.number_input("Impressions (optional, for diagnostics)", min_value=0.0, value=0.0)

    close_rate = st.number_input("Close rate (orders / conversations)", min_value=0.0, max_value=1.0, value=0.20)
    AOV = st.number_input("AOV ($)", min_value=0.0, value=0.0)
    cogs_per_order = st.number_input("COGS per order ($)", min_value=0.0, value=0.0)
    refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0, value=0.0)

    if conversations <= 0:
        st.warning("Conversations must be > 0 to use funnel mode.")
        st.stop()

    cpa_msg = spend / conversations
    inferred_orders = conversations * close_rate
    if inferred_orders < 1:
        st.warning("Inferred orders < 1. I’ll run with Orders=1 to avoid divide-by-zero.")
        inferred_orders = 1.0

    ad_spend = float(spend)
    orders = float(inferred_orders)
    revenue = AOV * orders
    cogs = cogs_per_order * orders

    # Diagnostics (optional)
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


# -----------------------------
# Scaling assumptions
# -----------------------------
st.divider()
st.subheader("Scaling assumptions")
spend_increase_pct = st.slider("Simulate Spend Increase (%)", 0, 300, 50)
cac_deterioration_per_100 = st.slider("CAC deterioration per +100% spend (%)", 0, 100, 25)

st.markdown(
    '<div class="small-note">“CAC deterioration per +100% spend” = how much CAC worsens when you double spend. '
    'Example: 25% → doubling spend increases CAC by ~25%.</div>',
    unsafe_allow_html=True,
)

# -----------------------------
# Analyze
# -----------------------------
if st.button("Analyze"):
    res = simulate_scale(
        revenue=revenue,
        cogs=cogs,
        ad_spend=ad_spend,
        orders=orders,
        refund_rate_pct=refund_rate,
        spend_increase_pct=spend_increase_pct,
        cac_deterioration_per_100_pct=cac_deterioration_per_100,
    )

    # Status
    if res["baseline_profit"] < 0:
        status = "🔴 HOLD — You are already losing money."
        status_class = "hold"
    elif res["margin_buffer"] < 0.15:
        status = "🟠 FRAGILE — Small efficiency loss makes you unprofitable."
        status_class = "fragile"
    else:
        status = "🟢 CONTROLLED — Unit economics can tolerate some scaling."
        status_class = "safe"

    # Bottleneck (baseline)
    AOV = res["AOV"]
    cogs_per_order = res["cogs_per_order"]
    cac = res["cac"]
    break_even_cac = res["break_even_cac"]

    if break_even_cac <= 0:
        bottleneck = "Unit economics are negative even before ads (price/margin/refunds problem)."
    elif cac > break_even_cac:
        bottleneck = "High CAC is your primary scaling risk."
    elif refund_rate > 8:
        bottleneck = "Refund rate is shrinking your ad tolerance."
    elif AOV > 0 and (AOV - cogs_per_order) / AOV < 0.3:
        bottleneck = "Low gross margin limits safe scaling."
    else:
        bottleneck = "No major structural constraint detected."

    # Safe scaling ceiling
    safe_scale_pct = find_safe_max_scale_pct(
        revenue=revenue,
        cogs=cogs,
        ad_spend=ad_spend,
        orders=orders,
        refund_rate_pct=refund_rate,
        cac_deterioration_per_100_pct=cac_deterioration_per_100,
        max_search_pct=300,
    )

    # Outputs
    st.subheader("Baseline (derived)")
    st.write(f"Revenue: **${revenue:.2f}**")
    st.write(f"COGS: **${cogs:.2f}**")
    st.write(f"Spend: **${ad_spend:.2f}**")
    st.write(f"Orders: **{orders:.1f}**")
    st.write(f"AOV: **${AOV:.2f}**")
    st.write(f"COGS per order: **${cogs_per_order:.2f}**")
    st.write(f"CAC: **${cac:.2f}**")
    st.write(f"Break-even CAC: **${break_even_cac:.2f}**")
    st.write(f"Baseline Profit: **${res['baseline_profit']:.2f}**")
    st.write(f"Margin Buffer: **{res['margin_buffer']*100:.1f}%**")
    st.markdown(f'<div class="big-status {status_class}">{status}</div>', unsafe_allow_html=True)

    if diag:
        st.subheader("Meta diagnostics (if provided)")
        if diag.get("cpa_msg") is not None:
            st.write(f"CPA (message conversation): **{diag['cpa_msg']:.2f}**")
        if diag.get("close_rate") is not None:
            st.write(f"Close rate: **{diag['close_rate']:.2%}**")
        if diag.get("implied_cac") is not None:
            st.write(f"Implied CAC from Meta: **{diag['implied_cac']:.2f}**")
        if diag.get("ctr") is not None:
            st.write(f"CTR: **{diag['ctr']:.2%}**")
        if diag.get("cpc") is not None:
            st.write(f"CPC: **{diag['cpc']:.2f}**")
        if diag.get("cvr_msg") is not None:
            st.write(f"CVR (click→message): **{diag['cvr_msg']:.2%}**")

    st.subheader("Main Constraint")
    st.write(bottleneck)

    st.subheader("Scaling Simulation (selected)")
    st.write(f"New Spend: **${res['new_spend']:.2f}**")
    st.write(f"New CAC (deteriorated): **${res['new_cac']:.2f}**" if res["new_cac"] > 0 else "New CAC: n/a (baseline CAC is 0)")
    st.write(f"Forecast Orders: **{res['new_orders']:.1f}**")
    st.write(f"Forecast Revenue: **${res['new_revenue']:.2f}**")
    st.write(f"Forecast Profit: **${res['new_profit']:.2f}**")

    st.subheader("Safe Scaling Ceiling")
    st.write(f"Maximum safe spend increase (profit ≥ 0): **{safe_scale_pct}%**")
    if safe_scale_pct < 50:
        st.warning("Low ceiling: scaling aggressively will likely flip you negative unless margins/returns/CAC improve.")

    # Scenario table
    st.subheader("Scaling Scenario Table")
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
