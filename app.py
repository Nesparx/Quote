import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS (Consolidated) ---
SMARTPHONE_TIERS = {
    "My Biz": {"code": "32066", "prices": [70.0, 60.0, 45.0, 39.0, 34.0]},
    "Start 5G": {"code": "67792", "prices": [73.0, 63.0, 48.0, 43.0, 38.0], "tier": "Start"},
    "Plus 5G": {"code": "67793", "prices": [83.0, 73.0, 58.0, 53.0, 48.0], "tier": "Plus"},
    "Pro 5G": {"code": "67832", "prices": [88.0, 78.0, 63.0, 58.0, 53.0], "tier": "Pro"}
}
SMARTPHONE_STATIC = {
    "Biz Unl SP": {"code": "43848", "price": 50.0, "tier": "Base"},
    "Biz Unl Ess": {"code": "43846", "price": 40.0, "tier": "Base"}
}
STANDARD_INTERNET = ["10 MBPS", "25 MBPS", "Unl 25 MBPS", "50 MBPS", "100 MBPS", "200 MBPS", "400 MBPS"]
INTERNET = {
    "10 MBPS": {"price": 69.0}, "25 MBPS": {"price": 99.0}, "Unl 25 MBPS": {"price": 69.0},
    "50 MBPS": {"price": 100.0}, "100 MBPS": {"price": 69.0}, "200 MBPS": {"price": 99.0}, "400 MBPS": {"price": 199.0},
    "Backup 1GB LTE": {"price": 20.0}, "Backup 3GB LTE": {"price": 30.0}
}
ADDONS = {
    "Premium Network Experience": {"price": 10.0}, "Enhanced Video Calling": {"price": 5.0},
    "Google Workspace": {"price": 16.0}, "International Connectivity": {"price": 10.0},
    "50 GB Mobile Hotspot": {"price": 5.0}, "Unlimited Individual Cloud": {"price": 10.0}
}
SINGLE_PROTECTION = {"TMP Single (Tier 1)": 18.0, "TMP Single (Tier 2)": 15.0, "TEC (Tier 1)": 13.0, "WPP (Tier 1)": 8.0}
VBIS_PROTECTION = {"None": 0.0, "VBIS Plus": 10.0, "VBIS Preferred": 20.0}
MULTI_PROTECTION_DATA = {"TMP Multi 3-10 Lines": 49.0, "TMP Multi 11-24 Lines": 149.0}

# --- APP SETUP ---
st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

# This function forces a UI refresh
def trigger_refresh():
    pass # Streamlit reruns the script automatically on widget change

# --- CALCULATION ENGINE ---
def get_current_totals():
    tiered_sm_count = sum(1 for l in st.session_state.get('lines', []) if l.get('plan') in SMARTPHONE_TIERS)
    tier_idx = min(tiered_sm_count, 5) - 1 if tiered_sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    
    for idx, l in enumerate(st.session_state.get('lines', [])):
        plan = l.get('plan', 'My Biz')
        # Base Price
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif l.get('type') == "Internet": base = INTERNET.get(plan, {"price": 0})['price']
        else: base = 20.0 # Default for Tablet/Watch

        # Joint Offer
        if st.session_state.get('joint_offer') and l.get('type') == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0

        # Add-ons and Tier
        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        if plan == "My Biz":
            if extras >= 20: tier = "Pro"
            elif extras >= 15: tier = "Plus"
            elif extras >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(plan, SMARTPHONE_STATIC.get(plan, {"tier": "Base"})).get('tier', 'Base')
        
        # Discounts
        if st.session_state.get('autopay') and plan in SMARTPHONE_TIERS: base -= 5.0
        disc = 0
        if l.get('intro_disc'): disc += (base * 0.15)
        if st.session_state.get('military') and l.get('type') == "Smartphone": disc += 5.0
        
        # Protection
        prot = VBIS_PROTECTION.get(l.get('vbis', 'None'), 0.0) if l.get('type') == "Internet" else SINGLE_PROTECTION.get(l.get('protection', 'None'), 0.0)
        
        total = (base + l.get('dev_pay', 0) + extras + prot) - disc
        line_details.append({"total": total, "tier": tier})
        account_mrc += total

    if st.session_state.get('tmp_multi') and st.session_state.tmp_multi != "None":
        account_mrc += MULTI_PROTECTION_DATA.get(st.session_state.tmp_multi, 0)
    if st.session_state.get('whole_office'): account_mrc += 55.0
    account_mrc += (len(st.session_state.get('lines', [])) * 2.98) 
    return line_details, account_mrc

# --- SIDEBAR (ALWAY AT TOP) ---
if st.session_state.get('step', 1) > 1:
    with st.sidebar:
        st.header("💰 Live Summary")
        l_info, a_total = get_current_totals()
        for i, item in enumerate(l_info):
            st.write(f"Line {i+1}: **${item['total']:.2f}** ({item['tier']})")
        st.divider()
        st.subheader(f"Total: ${a_total:,.2f}")

# --- STEPS ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num = st.number_input("Total devices?", min_value=1, value=1)
    if st.button("Start"):
        st.session_state.num_lines = num
        st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "vbis": "None", "dev_pay": 0.0} for _ in range(num)]
        st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Plan", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Category", ["Smartphone", "Internet", "Tablet", "Watch"], key=f"t_{i}", on_change=trigger_refresh)
            st.session_state.lines[i]['plan'] = st.selectbox("Select Plan", list(SMARTPHONE_TIERS.keys()) if st.session_state.lines[i]['type']=="Smartphone" else list(INTERNET.keys()), key=f"p_{i}", on_change=trigger_refresh)
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.toggle("Autopay", key="autopay", on_change=trigger_refresh)
    st.toggle("Military", key="military", on_change=trigger_refresh)
    st.toggle("Joint Offer", key="joint_offer", on_change=trigger_refresh)
    st.selectbox("Multi-Device Protection", ["None"] + list(MULTI_PROTECTION_DATA.keys()), key="tmp_multi", on_change=trigger_refresh)
    st.toggle("Whole Office Protect", key="whole_office", on_change=trigger_refresh)
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features")
    l_info, _ = get_current_totals() # Get fresh tiers for the display
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1} ({l['plan']}) - {l_info[i]['tier']} Tier", expanded=(i==0)):
            if l['type'] == "Internet":
                l['vbis'] = st.selectbox("Security", list(VBIS_PROTECTION.keys()), key=f"vbis_{i}", on_change=trigger_refresh)
            else:
                l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"pr_{i}", on_change=trigger_refresh)
            
            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]['price']})", key=f"a_{i}_{f}", on_change=trigger_refresh)]
                l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"id_{i}", on_change=trigger_refresh)
            
            l['dev_pay'] = st.number_input("Monthly Device Payment", min_value=0.0, key=f"dp_{i}", on_change=trigger_refresh)

    if st.button("Review Final"): st.session_state.step = 5; st.rerun()
