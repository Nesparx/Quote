import streamlit as st
from fpdf import FPDF
import datetime

# --- INITIALIZATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- DATA CATALOGS ---
SMARTPHONE_TIERS = {
    "My Biz": {"prices": [70.0, 60.0, 45.0, 39.0, 34.0]},
    "Start 5G": {"prices": [73.0, 63.0, 48.0, 43.0, 38.0], "tier": "Start"},
    "Plus 5G": {"prices": [83.0, 73.0, 58.0, 53.0, 48.0], "tier": "Plus"},
    "Pro 5G": {"prices": [88.0, 78.0, 63.0, 58.0, 53.0], "tier": "Pro"}
}
SMARTPHONE_STATIC = {
    "Biz Unl SP": {"price": 50.0, "tier": "Base"},
    "Biz Unl Ess": {"price": 40.0, "tier": "Base"}
}
STANDARD_INTERNET = ["10 MBPS", "25 MBPS", "Unl 25 MBPS", "50 MBPS", "100 MBPS", "200 MBPS", "400 MBPS"]
INTERNET = {"10 MBPS": 69.0, "25 MBPS": 99.0, "Unl 25 MBPS": 69.0, "50 MBPS": 100.0, "100 MBPS": 69.0, "200 MBPS": 99.0, "400 MBPS": 199.0}
ADDONS = {"Premium Network": 10.0, "Enhanced Video": 5.0, "Google Workspace": 16.0, "Int. Conn": 10.0, "50GB Hotspot": 5.0}
SINGLE_PROT = {"TMP Single (T1)": 18.0, "TMP Single (T2)": 15.0, "TEC (T1)": 13.0, "WPP (T1)": 8.0}
VBIS_PROT = {"None": 0.0, "VBIS Plus": 10.0, "VBIS Preferred": 20.0}
MULTI_PROT = {"TMP Multi 3-10": 49.0, "TMP Multi 11-24": 149.0}

st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

# --- CALCULATION LOGIC ---
def get_totals():
    # We pull directly from st.session_state keys to avoid the "one-step delay"
    lines = st.session_state.get('lines', [])
    
    # Calculate Smartphone Tier Index
    sm_count = 0
    for i in range(len(lines)):
        if st.session_state.get(f"p_{i}") in SMARTPHONE_TIERS:
            sm_count += 1
    tier_idx = min(sm_count, 5) - 1 if sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    
    for i in range(len(lines)):
        plan = st.session_state.get(f"p_{i}", "My Biz")
        dtype = st.session_state.get(f"t_{i}", "Smartphone")
        
        # Base
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif dtype == "Internet": base = INTERNET.get(plan, 0.0)
        else: base = 20.0 # Default

        # Joint Offer
        if st.session_state.get('joint_offer') and dtype == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0

        # Autopay
        if st.session_state.get('autopay') and plan in SMARTPHONE_TIERS: base -= 5.0
        
        # Addons & Tier
        extras = 0
        if plan == "My Biz":
            for addon_name in ADDONS:
                if st.session_state.get(f"a_{i}_{addon_name}"):
                    extras += ADDONS[addon_name]
            if extras >= 20: tier = "Pro"
            elif extras >= 15: tier = "Plus"
            elif extras >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(plan, SMARTPHONE_STATIC.get(plan, {"tier": "Base"}))['tier']

        # Protection
        p_price = 0
        if dtype == "Internet":
            p_price = VBIS_PROT.get(st.session_state.get(f"vbis_{i}"), 0.0)
        else:
            p_price = SINGLE_PROT.get(st.session_state.get(f"pr_{i}"), 0.0)

        # Final Line Math
        disc = 0
        if st.session_state.get(f"id_{i}"): disc += (base * 0.15)
        if st.session_state.get('military') and dtype == "Smartphone": disc += 5.0
        
        total = (base + st.session_state.get(f"dp_{i}", 0.0) + extras + p_price) - disc
        line_details.append({"total": total, "tier": tier})
        account_mrc += total

    # Account Level
    if st.session_state.get('tmp_multi') != "None":
        account_mrc += MULTI_PROT.get(st.session_state.tmp_multi, 0)
    if st.session_state.get('whole_office'): account_mrc += 55.0
    account_mrc += (len(lines) * 2.98)
    
    return line_details, account_mrc

# --- SIDEBAR ---
if st.session_state.step > 1:
    with st.sidebar:
        st.header("💰 Live Summary")
        l_info, a_total = get_totals() # Recalculate based on widget keys
        for idx, item in enumerate(l_info):
            st.write(f"Line {idx+1}: **${item['total']:.2f}** ({item['tier']})")
        st.divider()
        st.subheader(f"Total: ${a_total:,.2f}")

# --- APP STEPS ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num = st.number_input("Total lines?", min_value=1, value=1)
    if st.button("Next"):
        st.session_state.num_lines = num
        st.session_state.lines = [{} for _ in range(num)]
        st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1}", expanded=True):
            st.selectbox("Category", ["Smartphone", "Internet", "Tablet"], key=f"t_{i}")
            if st.session_state[f"t_{i}"] == "Smartphone": opts = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif st.session_state[f"t_{i}"] == "Internet": opts = list(INTERNET.keys())
            else: opts = ["Start", "Pro"]
            st.selectbox("Plan", opts, key=f"p_{i}")
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.toggle("Autopay", key="autopay")
    st.toggle("Military", key="military")
    st.toggle("Joint Offer", key="joint_offer")
    st.selectbox("Multi-Device Protection", ["None", "TMP Multi 3-10", "TMP Multi 11-24"], key="tmp_multi")
    st.toggle("Whole Office Protect", key="whole_office")
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features")
    l_info, _ = get_totals()
    for i in range(st.session_state.num_lines):
        plan = st.session_state[f"p_{i}"]
        with st.expander(f"Line {i+1} ({plan}) - {l_info[i]['tier']} Tier", expanded=(i==0)):
            if st.session_state[f"t_{i}"] == "Internet":
                st.selectbox("Security", ["None", "VBIS Plus", "VBIS Preferred"], key=f"vbis_{i}")
            else:
                st.selectbox("Protection", ["None"] + list(SINGLE_PROT.keys()), key=f"pr_{i}")
            
            if plan == "My Biz":
                for addon in ADDONS:
                    st.checkbox(f"{addon} (${ADDONS[addon]})", key=f"a_{i}_{addon}")
                st.checkbox("15% Intro Discount", key=f"id_{i}")
            
            st.number_input("Device Payment", min_value=0.0, key=f"dp_{i}")

    if st.button("Finish"): st.session_state.step = 5; st.rerun()
