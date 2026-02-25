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
st.write("Check if your scaling is safe or dangerous.")

# --- Inputs ---
revenue = st.number_input("Total Revenue ($)", min_value=0.0)
cogs = st.number_input("COGS ($)", min_value=0.0)
ad_spend = st.number_input("Ad Spend ($)", min_value=0.0)
orders = st.number_input("Orders", min_value=1)
refund_rate = st.number_input("Refund Rate (%)", min_value=0.0, max_value=100.0)

cac_increase = st.slider("Simulate CAC Increase (%)", 0, 50, 10)

if st.button("Analyze"):

    # --- Core Calculations ---
    cac = ad_spend / orders
    refund_cost = revenue * (refund_rate / 100)
    net_contribution = revenue - cogs - ad_spend - refund_cost

    break_even_cac = (revenue - cogs - refund_cost) / orders

    margin_buffer = (
        (break_even_cac - cac) / break_even_cac
        if break_even_cac != 0 else 0
    )

    # --- Status ---
    if net_contribution < 0:
        status = "🔴 HOLD — Scaling increases losses."
    elif margin_buffer < 0.15:
        status = "🟠 FRAGILE — Small CAC increase makes you unprofitable."
    else:
        status = "🟢 CONTROLLED — Scaling is safe."
    # --- Bottleneck Detection ---
    if cac > break_even_cac:
        bottleneck = "High CAC is your primary scaling risk."
    elif refund_rate > 8:
        bottleneck = "Refund rate is damaging your margin buffer."
    elif (revenue - cogs)/revenue < 0.3 and revenue > 0:
        bottleneck = "Low product margin limits safe scaling."
    else:
        bottleneck = "No major structural constraint detected."

    # --- Simulation ---
    simulated_cac = cac * (1 + cac_increase / 100)
    simulated_contribution = revenue - cogs - (simulated_cac * orders) - refund_cost

    # --- Output ---
    st.subheader("Results")
    st.write(f"CAC: ${cac:.2f}")
    st.write(f"Break-even CAC: ${break_even_cac:.2f}")
    st.write(f"Net Contribution: ${net_contribution:.2f}")
    st.write(f"Margin Buffer: {margin_buffer*100:.1f}%")
    if "HOLD" in status:
    	st.markdown(f'<div class="big-status hold">{status}</div>', unsafe_allow_html=True)
    elif "FRAGILE" in status:
    	st.markdown(f'<div class="big-status fragile">{status}</div>', unsafe_allow_html=True)
    else:
    	st.markdown(f'<div class="big-status safe">{status}</div>', unsafe_allow_html=True)

    st.subheader("Main Constraint")
    st.write(bottleneck)

    st.subheader("Simulation Result")
    st.write(f"Simulated CAC: ${simulated_cac:.2f}")
    st.write(f"Simulated Net Contribution: ${simulated_contribution:.2f}")
