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
</style>
""",
    unsafe_allow_html=True,
)

st.title("Scaling Risk Checker")
st.write("Finance-only scaling simulation: spend increases → CAC deteriorates → volume and profit change.")


def simulate_scale(
    revenue: float,
    cogs: float,
    ad_spend: float,
    orders: float,
    refund_rate_pct: float,
    spend_increase_pct: float,
    cac_deterioration_per_100_pct: float,
):
    """
    Finance-only scaling model:
      - Spend scales by (1+g)
      - CAC deteriorates linearly by k*g  (k is per +100% spend)
      - Orders follow from spend and CAC: new_orders = new_spend / new_cac
      - Revenue/COGS/Refunds scale with new_orders (unit economics constant)
    """
    rr = refund_rate_pct / 100.0
    g = spend_increase_pct / 100.0
    k = cac_deterioration_per_100_pct / 100.0

    # Baseline unit economics
    AOV = revenue / orders if orders else 0.0
    cogs_per_order = cogs / orders if orders else 0.0
    cac = ad_spend / orders if orders else 0.0

    baseline_refund_cost = revenue * rr
    baseline_profit = revenue - cogs - ad_spend - baseline_refund_cost

    break_even_cac = (AOV - cogs_per_order - (AOV * rr))  # contribution margin per order before ads
    margin_buffer = ((break_even_cac - cac) / break_even_cac) if break_even_cac > 0 else 0.0

    # Scaling simulation
    new_spend = ad_spend * (1 + g)

    # Edge case: if CAC is 0 (no spend or orders weird), can't infer volume
    if cac <= 0:
        new_cac = 0.0
        new_orders = float(orders)
    else:
        new_cac = cac * (1 + k * g)
        new_orders = new_spend / new_cac if new_cac > 0 else float(orders)

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
    """
    Returns the maximum spend increase % (0..max_search_pct) such that forecast profit >= 0.
    Simple forward search; stops at first negative profit.
    """
    last_safe = 0
    for pct in range(0, max_search_pct + 1):
        res = simulate_scale(
            revenue=revenue,
            cogs=cogs,
            ad_spend=ad_spend,
            orders=orders,
            refund_rate_pct=refund_rate_pct,
            spend_increase_pct=pct,
            cac_deterioration_per_100_pct=cac_deterioration_per_100_pct,
        )
        if res["new_profit"] >= 0:
            last_safe = pct
        else:
            break
    return last_safe


# --- Inputs ---
revenue = st.number_input("Total Revenue ($)", min_value=0.0, value=0.0)
cogs = st.number_input("COGS ($)", min_value=0.0, value=0.0)
ad_spend = st.number_input("Ad Spend ($)", min_value=0.0, value=0.0)
orders = st.number_input("Orders", min_value=1, value=1)
refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0, value=0.0)

st.divider()
st.subheader("Scaling assumptions")
spend_increase_pct = st.slider("Simulate Spend Increase (%)", 0, 300, 50)
cac_deterioration_per_100 = st.slider("CAC deterioration per +100% spend (%)", 0, 100, 25)

st.markdown(
    '<div class="small-note">Tip: “CAC deterioration per +100% spend” means how much CAC worsens when you double spend. '
    'Example: 25% → doubling spend increases CAC by ~25%.</div>',
    unsafe_allow_html=True,
)

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

    # --- Status (baseline) ---
    if res["baseline_profit"] < 0:
        status = "🔴 HOLD — You are already losing money."
        status_class = "hold"
    elif res["margin_buffer"] < 0.15:
        status = "🟠 FRAGILE — Small efficiency loss makes you unprofitable."
        status_class = "fragile"
    else:
        status = "🟢 CONTROLLED — Unit economics can tolerate some scaling."
        status_class = "safe"

    # --- Bottleneck detection (baseline) ---
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

    # --- Safe scaling ceiling (B) ---
    safe_scale_pct = find_safe_max_scale_pct(
        revenue=revenue,
        cogs=cogs,
        ad_spend=ad_spend,
        orders=orders,
        refund_rate_pct=refund_rate,
        cac_deterioration_per_100_pct=cac_deterioration_per_100,
        max_search_pct=300,
    )

    # --- Output ---
    st.subheader("Baseline")
    st.write(f"AOV: ${AOV:.2f}")
    st.write(f"COGS per order: ${cogs_per_order:.2f}")
    st.write(f"CAC: ${cac:.2f}")
    st.write(f"Break-even CAC: ${break_even_cac:.2f}")
    st.write(f"Baseline Profit: ${res['baseline_profit']:.2f}")
    st.write(f"Margin Buffer: {res['margin_buffer']*100:.1f}%")
    st.markdown(f'<div class="big-status {status_class}">{status}</div>', unsafe_allow_html=True)

    st.subheader("Main Constraint")
    st.write(bottleneck)

    st.subheader("Scaling Simulation")
    st.write(f"New Spend: ${res['new_spend']:.2f}")
    st.write(f"New CAC (deteriorated): ${res['new_cac']:.2f}" if res["new_cac"] > 0 else "New CAC: n/a (baseline CAC is 0)")
    st.write(f"Forecast Orders: {res['new_orders']:.1f}")
    st.write(f"Forecast Revenue: ${res['new_revenue']:.2f}")
    st.write(f"Forecast Profit: ${res['new_profit']:.2f}")

    st.subheader("Safe Scaling Ceiling")
    st.write(f"Maximum safe spend increase (profit ≥ 0): **{safe_scale_pct}%**")
    if safe_scale_pct < 50:
        st.warning("Low ceiling: scaling aggressively will likely flip you negative unless margins/returns/CAC improve.")

    # --- Scenario comparison table (C) ---
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

    df = pd.DataFrame(rows)

    def profit_flag(x):
        if x < 0:
            return "🔴"
        if x < (0.05 * max(revenue, 1.0)):  # small positive profit vs revenue
            return "🟠"
        return "🟢"

    df.insert(0, "Status", df["Forecast Profit"].apply(profit_flag))
    st.dataframe(df, use_container_width=True)
