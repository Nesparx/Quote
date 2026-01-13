import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS (From CSV) ---
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
TABLETS = {"Start": {"code": "44024", "price": 20.0}, "Pro": {"code": "52599", "price": 40.0}}
WATCHES = {"Standalone": {"code": "41371", "price": 15.0}, "Numbershare": {"code": "99838", "price": 15.0}, "Gizmo": {"code": "99343", "price": 5.0}}
INTERNET = {"10 MBPS": {"price": 69.0}, "100 MBPS": {"price": 69.0}, "Backup 1GB LTE": {"price": 20.0}}
OTHER = {"Jetpack Plus": {"price": 45.0}, "Jetpack Pro": {"price": 75.0}}

ADDONS = {
    "Premium Network Experience": {"price": 10.0},
    "Enhanced Video Calling": {"price": 5.0},
    "Google Workspace": {"price": 16.0},
    "International Connectivity": {"price": 10.0},
    "50 GB Mobile Hotspot": {"price": 5.0},
    "Unlimited Individual Cloud": {"price": 10.0}
}
SINGLE_PROTECTION = {
    "TMP Single (Tier 1)": {"price": 18.0},
    "TMP Single (Tier 2)": {"price": 15.0},
    "TEC (Tier 1)": {"price": 13.0},
    "WPP (Tier 1)": {"price": 8.0}
}
MULTI_PROTECTION_DATA = [
    {"name": "TMP Multi 3-10 Lines", "min": 3, "max": 10, "price": 49.0},
    {"name": "TMP Multi 11-24 Lines", "min": 11, "max": 24, "price": 149.0},
    {"name": "TMP Multi 25-49 Lines", "min": 25, "max": 49, "price": 299.0}
]

# --- APP SETUP ---
st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- CALCULATION LOGIC ---
def get_current_totals():
    # Only My Biz and 5G plans count toward the tiered smartphone pricing
    tiered_sm_count = sum(1 for l in st.session_state.lines if l['plan'] in SMARTPHONE_TIERS)
    tier_idx = min(tiered_sm_count, 5) - 1 if tiered_sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    
    for l in st.session_state.lines:
        # 1. Base Price
        if l['plan'] in SMARTPHONE_TIERS: 
            base = SMARTPHONE_TIERS[l['plan']]['prices'][tier_idx]
        elif l['plan'] in SMARTPHONE_STATIC: 
            base = SMARTPHONE_STATIC[l['plan']]['price']
        elif l['type'] == "Tablet": base = TABLETS.get(l['plan'], {"price": 0})['price']
        elif l['type'] == "Watch": base = WATCHES.get(l['plan'], {"price": 0})['price']
        else: base = 0.0

        # 2. Add-ons & Tier determination
        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        if l['plan'] == "My Biz":
            if extras >= 20: tier = "Pro"
            elif extras >= 15: tier = "Plus"
            elif extras >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(l['plan'], SMARTPHONE_STATIC.get(l['plan'], {"tier": "Base"}))['tier']
        
        # 3. Discounts
        if st.session_state.get('autopay') and l['plan'] in SMARTPHONE_TIERS: 
            base -= 5.0
        
        disc = 0
        if l.get('intro_disc'): disc += (base * 0.15)
        if st.session_state.get('military') and l['type'] == "Smartphone": disc += 5.0
        
        # 4. Total per line
        prot_price = SINGLE_PROTECTION.get(l['protection'], {"price": 0})['price']
        line_total = (base + l.get('dev_pay', 0) + extras + prot_price) - disc
        
        line_details.append({"total": line_total, "tier": tier})
        account_mrc += line_total

    # 5. Account Charges
    if st.session_state.get('tmp_multi') and st.session_state.tmp_multi != "None":
        m_price = next((item['price'] for item in MULTI_PROTECTION_DATA if item['name'] == st.session_state.tmp_multi), 0)
        account_mrc += m_price
    if st.session_state.get('whole_office'): account_mrc += 55.0
    
    account_mrc += (len(st.session_state.lines) * 2.98) # Econ Adj
    return line_details, account_mrc

# --- SIDEBAR ---
if st.session_state.step > 1:
    with st.sidebar:
        st.header("💰 Live Billing")
        l_info, a_total = get_current_totals()
        for idx, item in enumerate(l_info):
            st.write(f"Line {idx+1}: **${item['total']:.2f}** ({item['tier']})")
        st.divider()
        st.subheader(f"Account: ${a_total:,.2f}")

# --- STEPS ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num = st.number_input("How many total devices?", min_value=1, value=1)
    if st.button("Start Quote"):
        st.session_state.num_lines = num
        st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "dev_pay": 0.0} for _ in range(num)]
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Plan Selection", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Device Category", ["Smartphone", "Tablet", "Watch", "Internet"], key=f"t_{i}")
            if st.session_state.lines[i]['type'] == "Smartphone":
                opts = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif st.session_state.lines[i]['type'] == "Tablet": opts = list(TABLETS.keys())
            elif st.session_state.lines[i]['type'] == "Watch": opts = list(WATCHES.keys())
            else: opts = list(INTERNET.keys())
            st.session_state.lines[i]['plan'] = st.selectbox("Plan", opts, key=f"p_{i}")
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.session_state.autopay = st.toggle("Autopay ($5 Smartphone discount)")
    st.session_state.military = st.toggle("Military ($5 Smartphone discount)")
    
    # Dynamic Multi-Protection Logic
    eligible_count = sum(1 for l in st.session_state.lines if l['type'] in ["Smartphone", "Tablet", "Watch"])
    multi_opts = ["None"]
    for bracket in MULTI_PROTECTION_DATA:
        if eligible_count >= bracket['min']:
            multi_opts.append(bracket['name'])
    
    if len(multi_opts) > 1:
        st.session_state.tmp_multi = st.selectbox("Multi-Device Protection", multi_opts)
    else:
        st.session_state.tmp_multi = "None"
        st.info("Less than 3 eligible lines: Multi-Device Protection unavailable.")
        
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55)")
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features & Line Level")
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1} Configuration ({l['plan']})", expanded=(i==0)):
            # Tier Badge Visibility
            _, current_data = get_current_totals()
            line_tier = next(item['tier'] for idx, item in enumerate(get_current_totals()[0]) if idx == i)
            st.markdown(f"**Current Status: `{line_tier} Tier`**")
            
            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]['price']})", key=f"a_{i}_{f}")]
                if not st.session_state.military:
                    l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"id_{i}")
            
            if st.session_state.tmp_multi == "None":
                l['protection'] = st.selectbox("Single Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"pr_{i}")
            else:
                l['protection'] = "None"
                st.caption("✅ Covered by Multi-Device Protection")
            
            l['dev_pay'] = st.number_input("Monthly Device Payment", min_value=0.0, key=f"dp_{i}")

    if st.button("Review Final Quote"): st.session_state.step = 5; st.rerun()

elif st.session_state.step == 5:
    st.header("Step 5: Final Review")
    _, final_total = get_current_totals()
    st.metric("Final Monthly Total", f"${final_total:,.2f}")
    if st.button("New Quote"): 
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()
