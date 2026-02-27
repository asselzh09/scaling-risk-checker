import streamlit as st

st.set_page_config(page_title="Scaling Risk Checker", layout="centered")

st.markdown("""
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
</style>
""", unsafe_allow_html=True)

st.title("Scaling Risk Checker")
st.write("Finance-only scaling simulation: spend increases → CAC deteriorates → volume and profit change.")

# --- Inputs ---
revenue = st.number_input("Total Revenue ($)", min_value=0.0, value=0.0)
cogs = st.number_input("COGS ($)", min_value=0.0, value=0.0)
ad_spend = st.number_input("Ad Spend ($)", min_value=0.0, value=0.0)
orders = st.number_input("Orders", min_value=1, value=1)
refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0, value=0.0)

st.divider()
st.subheader("Scaling assumptions")

spend_increase_pct = st.slider("Simulate Spend Increase (%)", 0, 300, 50)
# k = how much CAC worsens per +100% spend. Example 0.25 => +25% CAC when doubling spend
cac_deterioration_per_100 = st.slider("CAC deterioration per +100% spend (%)", 0, 100, 25)

if st.button("Analyze"):

    # --- Baseline unit economics ---
    rr = refund_rate / 100.0
    AOV = revenue / orders if orders else 0.0
    cogs_per_order = cogs / orders if orders else 0.0

    # Baseline CAC (actual)
    cac = ad_spend / orders if orders else 0.0

    # Baseline profit (your current net contribution, but consistent naming)
    baseline_refund_cost = revenue * rr
    baseline_profit = revenue - cogs - ad_spend - baseline_refund_cost

    # Break-even CAC per order (max CAC you can pay before profit goes negative)
    break_even_cac = (AOV - cogs_per_order - (AOV * rr))  # = contribution margin per order before ads

    # Margin buffer vs current CAC
    margin_buffer = ((break_even_cac - cac) / break_even_cac) if break_even_cac > 0 else 0.0

    # --- Status (baseline) ---
    if baseline_profit < 0:
        status = "🔴 HOLD — You are already losing money."
    elif margin_buffer < 0.15:
        status = "🟠 FRAGILE — Small efficiency loss makes you unprofitable."
    else:
        status = "🟢 CONTROLLED — Unit economics can tolerate some scaling."

    # --- Bottleneck detection (baseline) ---
    if break_even_cac <= 0:
        bottleneck = "Unit economics are negative even before ads (price/margin/refunds problem)."
    elif cac > break_even_cac:
        bottleneck = "High CAC is your primary scaling risk."
    elif refund_rate > 8:
        bottleneck = "Refund rate is shrinking your ad tolerance."
    elif (AOV > 0 and (AOV - cogs_per_order)/AOV < 0.3):
        bottleneck = "Low gross margin limits safe scaling."
    else:
        bottleneck = "No major structural constraint detected."

    # --- Scaling simulation (consistent scaling) ---
    g = spend_increase_pct / 100.0
    k = (cac_deterioration_per_100 / 100.0)  # per +100% spend

    new_spend = ad_spend * (1 + g)
    new_cac = cac * (1 + k * g) if cac > 0 else 0.0

    # If CAC is zero (no spend), we can't infer volume. Keep orders constant in that edge case.
    if new_cac > 0:
        new_orders = new_spend / new_cac
    else:
        new_orders = float(orders)

    new_revenue = AOV * new_orders
    new_cogs = cogs_per_order * new_orders
    new_refund_cost = new_revenue * rr
    new_profit = new_revenue - new_cogs - new_spend - new_refund_cost

    # --- Output ---
    st.subheader("Baseline")
    st.write(f"AOV: ${AOV:.2f}")
    st.write(f"COGS per order: ${cogs_per_order:.2f}")
    st.write(f"CAC: ${cac:.2f}")
    st.write(f"Break-even CAC: ${break_even_cac:.2f}")
    st.write(f"Baseline Profit: ${baseline_profit:.2f}")
    st.write(f"Margin Buffer: {margin_buffer*100:.1f}%")

    if "HOLD" in status:
        st.markdown(f'<div class="big-status hold">{status}</div>', unsafe_allow_html=True)
    elif "FRAGILE" in status:
        st.markdown(f'<div class="big-status fragile">{status}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="big-status safe">{status}</div>', unsafe_allow_html=True)

    st.subheader("Main Constraint")
    st.write(bottleneck)

    st.subheader("Scaling Simulation")
    st.write(f"New Spend: ${new_spend:.2f}")
    st.write(f"New CAC (deteriorated): ${new_cac:.2f}")
    st.write(f"Forecast Orders: {new_orders:.1f}")
    st.write(f"Forecast Revenue: ${new_revenue:.2f}")
    st.write(f"Forecast Profit: ${new_profit:.2f}")
