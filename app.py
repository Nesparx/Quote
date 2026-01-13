import streamlit as st
from fpdf import FPDF
import datetime

# --- INITIALIZATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []
for key in ['autopay', 'military', 'joint_offer', 'tmp_multi', 'whole_office']:
    if key not in st.session_state:
        st.session_state[key] = False if key != 'tmp_multi' else "None"

# --- FULL DATA CATALOGS (Restored from CSV) ---
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
    "10 MBPS": 69.0, "25 MBPS": 99.0, "Unl 25 MBPS": 69.0, "50 MBPS": 100.0, "100 MBPS": 69.0, "200 MBPS": 99.0, "400 MBPS": 199.0,
    "Backup 500 MB LTE": 10.0, "Backup 1GB LTE": 20.0, "Backup 3GB LTE": 30.0, "Backup 500 MB 5G": 10.0, "Backup 1GB 5G": 20.0, "Backup 3GB 5G": 30.0
}
TABLETS = {"Start": 20.0, "Pro": 40.0}
WATCHES = {"Standalone": 15.0, "Numbershare": 15.0, "Gizmo": 5.0}
OTHER = {"Camera": 25.0, "Jetpack Plus": 45.0, "Jetpack Pro": 75.0, "One Talk Mobile Client": 20.0, "One Talk Auto Receptionist": 20.0}

ADDONS = {
    "Premium Network Experience": 10.0, "Enhanced Video Calling": 5.0, "Google Workspace": 16.0, "International Connectivity": 10.0,
    "Int. LD (Asia Pacific)": 5.0, "Int. LD (Europe)": 5.0, "Int. LD (Latin America)": 5.0, "Business Mobile Secure Plus": 5.0,
    "Verizon Internet Security": 0.0, "50 GB Mobile Hotspot": 5.0, "Unlimited Cloud Storage": 10.0
}
SINGLE_PROT = {
    "TMP Single (Tier 1)": 18.0, "TMP Single (Tier 2)": 15.0, "TEC (Tier 1)": 13.0, "TEC (Tier 2)": 9.0, "WPP (Tier 1)": 8.0, "WPP (Tier 2)": 5.0
}
VBIS_PROT = {"None": 0.0, "VBIS Plus": 10.0, "VBIS Preferred": 20.0}
MULTI_PROT_DATA = [
    {"name": "TMP Multi 3-10 Lines", "min": 3, "price": 49.0},
    {"name": "TMP Multi 11-24 Lines", "min": 11, "price": 149.0},
    {"name": "TMP Multi 25-49 Lines", "min": 25, "price": 299.0}
]

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
        
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif dtype == "Internet": base = INTERNET.get(plan, 0.0)
        elif dtype == "Tablet": base = TABLETS.get(plan, 0.0)
        elif dtype == "Watch": base = WATCHES.get(plan, 0.0)
        else: base = OTHER.get(plan, 0.0)

        if st.session_state.joint_offer and dtype == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0

        if st.session_state.autopay and plan in SMARTPHONE_TIERS: base -= 5.0
        
        extras = sum(ADDONS[f] for f in l.get('features', []))
        if plan == "My Biz":
            if extras >= 20: tier = "Pro"
            elif extras >= 15: tier = "Plus"
            elif extras >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(plan, SMARTPHONE_STATIC.get(plan, {"tier": "Base"})).get('tier', 'Base')

        p_price = VBIS_PROT.get(l.get('vbis', 'None'), 0.0) if dtype == "Internet" else SINGLE_PROT.get(l.get('protection', 'None'), 0.0)

        disc = 0
        if l.get('intro_disc'): disc += (base * 0.15)
        if st.session_state.military and dtype == "Smartphone": disc += 5.0
        
        total = (base + l.get('dev_pay', 0.0) + extras + p_price) - disc
        line_details.append({"total": total, "tier": tier})
        account_mrc += total

    if st.session_state.tmp_multi != "None":
        m_price = next((item['price'] for item in MULTI_PROT_DATA if item['name'] == st.session_state.tmp_multi), 0)
        account_mrc += m_price
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
    num = st.number_input("Total devices/lines?", min_value=1, value=1)
    if st.button("Start Quote"):
        st.session_state.num_lines = num
        st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "vbis": "None", "dev_pay": 0.0, "intro_disc": False} for _ in range(num)]
        st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Assign Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Setup", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Category", ["Smartphone", "Internet", "Tablet", "Watch", "Other"], key=f"t_sel_{i}")
            dtype = st.session_state.lines[i]['type']
            if dtype == "Smartphone": opts = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif dtype == "Internet": opts = list(INTERNET.keys())
            elif dtype == "Tablet": opts = list(TABLETS.keys())
            elif dtype == "Watch": opts = list(WATCHES.keys())
            else: opts = list(OTHER.keys())
            st.session_state.lines[i]['plan'] = st.selectbox("Select Plan", opts, key=f"p_sel_{i}")
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.session_state.autopay = st.toggle("Autopay ($5 off eligible smartphone lines)", value=st.session_state.autopay)
    st.session_state.military = st.toggle("Military Discount ($5 off all smartphone lines)", value=st.session_state.military)
    
    has_sm = any(l['type'] == "Smartphone" for l in st.session_state.lines)
    has_int = any(l['type'] == "Internet" and l['plan'] in STANDARD_INTERNET for l in st.session_state.lines)
    if has_sm and has_int:
        st.session_state.joint_offer = st.toggle("Joint Offer ($30 off Internet)", value=st.session_state.joint_offer)
    else: st.session_state.joint_offer = False

    eligible_count = sum(1 for l in st.session_state.lines if l['type'] in ["Smartphone", "Tablet", "Watch"] or "Jetpack" in str(l['plan']))
    multi_opts = ["None"]
    for bracket in MULTI_PROT_DATA:
        if eligible_count >= bracket['min']: multi_opts.append(bracket['name'])
    
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection", multi_opts, index=0)
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55.00/mo)", value=st.session_state.whole_office)
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features & Line Config")
    l_info, _ = get_totals()
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1} ({l['plan']}) - {l_info[i]['tier']} Tier", expanded=(i==0)):
            if l['type'] == "Internet":
                l['vbis'] = st.selectbox("Internet Security", list(VBIS_PROT.keys()), key=f"vbis_sel_{i}")
            else:
                if st.session_state.tmp_multi == "None":
                    l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROT.keys()), key=f"pr_sel_{i}")
                else: st.caption("✅ Covered by Multi-Device Protection")
            
            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]})", key=f"a_sel_{i}_{f}")]
                if not st.session_state.military:
                    l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"id_sel_{i}")
            
            l['dev_pay'] = st.number_input("Monthly Device Payment ($)", min_value=0.0, key=f"dp_sel_{i}")

    if st.button("Finish"): st.session_state.step = 5; st.rerun()
