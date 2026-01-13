import streamlit as st
from fpdf import FPDF
import datetime

# --- INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'lines' not in st.session_state:
    st.session_state.lines = []
if 'autopay' not in st.session_state:
    st.session_state.autopay = False
if 'military' not in st.session_state:
    st.session_state.military = False
if 'joint_offer' not in st.session_state:
    st.session_state.joint_offer = False
if 'tmp_multi' not in st.session_state:
    st.session_state.tmp_multi = "None"
if 'whole_office' not in st.session_state:
    st.session_state.whole_office = False

# --- DATA CATALOGS ---
SMARTPHONE_TIERS = {
    "My Biz": {"prices": [70.0, 60.0, 45.0, 39.0, 34.0]},
    "Start 5G": {"prices": [73.0, 63.0, 48.0, 43.0, 38.0], "tier": "Start"},
    "Plus 5G": {"prices": [83.0, 73.0, 58.0, 53.0, 48.0], "tier": "Plus"},
    "Pro 5G": {"prices": [88.0, 78.0, 63.0, 58.0, 53.0], "tier": "Pro"}
}
SMARTPHONE_STATIC = {
    "Biz Unl SP": {"price": 50.0, "tier": "Base"},
    "Biz Unl Ess": {"price": 40.0, "tier": "Base"},
    "Second Number": {"price": 15.0, "tier": "Base"},
    "One Talk Second Number": {"price": 20.0, "tier": "Base"}
}
STANDARD_INTERNET = ["10 MBPS", "25 MBPS", "Unl 25 MBPS", "50 MBPS", "100 MBPS", "200 MBPS", "400 MBPS"]
INTERNET = {
    "10 MBPS": 69.0, "25 MBPS": 99.0, "Unl 25 MBPS": 69.0, "50 MBPS": 100.0, 
    "100 MBPS": 69.0, "200 MBPS": 99.0, "400 MBPS": 199.0, "Backup 1GB LTE": 20.0, "Backup 3GB LTE": 30.0
}
ADDONS = {"Premium Network": 10.0, "Enhanced Video": 5.0, "Google Workspace": 16.0, "Int. Conn": 10.0, "50GB Hotspot": 5.0}
SINGLE_PROT = {"TMP Single (T1)": 18.0, "TMP Single (T2)": 15.0, "TEC (T1)": 13.0, "WPP (T1)": 8.0}
VBIS_PROT = {"None": 0.0, "VBIS Plus": 10.0, "VBIS Preferred": 20.0}
MULTI_PROT = {"TMP Multi 3-10": 49.0, "TMP Multi 11-24": 149.0}

st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

# --- CALCULATION LOGIC ---
def get_totals():
    lines = st.session_state.lines
    sm_count = sum(1 for l in lines if l.get('plan') in SMARTPHONE_TIERS)
    tier_idx = min(sm_count, 5) - 1 if sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    
    for l in lines:
        plan = l.get('plan', 'My Biz')
        dtype = l.get('type', 'Smartphone')
        
        # Base
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif dtype == "Internet": base = INTERNET.get(plan, 0.0)
        else: base = 20.0

        # Joint Offer
        if st.session_state.joint_offer and dtype == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0

        # Autopay
        if st.session_state.autopay and plan in SMARTPHONE_TIERS: base -= 5.0
        
        # Addons & Tier
        extras = sum(ADDONS[f] for f in l.get('features', []))
        if plan == "My Biz":
            if extras >= 20: tier = "Pro"
            elif extras >= 15: tier = "Plus"
            elif extras >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(plan, SMARTPHONE_STATIC.get(plan, {"tier": "Base"}))['tier']

        # Protection
        p_price = VBIS_PROT.get(l.get('vbis', 'None'), 0.0) if dtype == "Internet" else SINGLE_PROT.get(l.get('protection', 'None'), 0.0)

        # Final Line Math
        disc = 0
        if l.get('intro_disc'): disc += (base * 0.15)
        if st.session_state.military and dtype == "Smartphone": disc += 5.0
        
        total = (base + l.get('dev_pay', 0.0) + extras + p_price) - disc
        line_details.append({"total": total, "tier": tier})
        account_mrc += total

    if st.session_state.tmp_multi != "None":
        account_mrc += MULTI_PROT.get(st.session_state.tmp_multi, 0)
    if st.session_state.whole_office: account_mrc += 55.0
    account_mrc += (len(lines) * 2.98)
    
    return line_details, account_mrc

# --- SIDEBAR ---
if st.session_state.step > 1:
    with st.sidebar:
        st.header("💰 Live Summary")
        l_info, a_total = get_totals()
        for i, item in enumerate(l_info):
            st.write(f"Line {i+1}: **${item['total']:.2f}** ({item['tier']})")
        st.divider()
        st.subheader(f"Total: ${a_total:,.2f}")

# --- STEPS ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num = st.number_input("Total lines?", min_value=1, value=1)
    if st.button("Start"):
        st.session_state.num_lines = num
        st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "vbis": "None", "dev_pay": 0.0, "intro_disc": False} for _ in range(num)]
        st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1}", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Category", ["Smartphone", "Internet", "Tablet"], key=f"t_sel_{i}")
            if st.session_state.lines[i]['type'] == "Smartphone": opts = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif st.session_state.lines[i]['type'] == "Internet": opts = list(INTERNET.keys())
            else: opts = ["Start", "Pro"]
            st.session_state.lines[i]['plan'] = st.selectbox("Plan", opts, key=f"p_sel_{i}")
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.session_state.autopay = st.toggle("Autopay", value=st.session_state.autopay)
    st.session_state.military = st.toggle("Military", value=st.session_state.military)
    st.session_state.joint_offer = st.toggle("Joint Offer", value=st.session_state.joint_offer)
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection", ["None"] + list(MULTI_PROT.keys()), index=0)
    st.session_state.whole_office = st.toggle("Whole Office Protect", value=st.session_state.whole_office)
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features")
    l_info, _ = get_totals()
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1} ({l['plan']}) - {l_info[i]['tier']} Tier", expanded=(i==0)):
            if l['type'] == "Internet":
                l['vbis'] = st.selectbox("Security", list(VBIS_PROT.keys()), key=f"vbis_sel_{i}")
            else:
                l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROT.keys()), key=f"pr_sel_{i}")
            
            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]})", key=f"a_sel_{i}_{f}")]
                l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"id_sel_{i}")
            
            l['dev_pay'] = st.number_input("Device Payment", min_value=0.0, key=f"dp_sel_{i}")

    if st.button("Finish"): st.session_state.step = 5; st.rerun()
