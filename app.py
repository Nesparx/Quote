import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS ---
SMARTPHONE_TIERS = {
    "My Biz": {"code": "32066", "prices": [70.0, 60.0, 45.0, 39.0, 34.0]},
    "Start 5G": {"code": "67792", "prices": [73.0, 63.0, 48.0, 43.0, 38.0], "tier": "Start"},
    "Plus 5G": {"code": "67793", "prices": [83.0, 73.0, 58.0, 53.0, 48.0], "tier": "Plus"},
    "Pro 5G": {"code": "67832", "prices": [88.0, 78.0, 63.0, 58.0, 53.0], "tier": "Pro"}
}
SMARTPHONE_STATIC = {
    "Biz Unl SP": {"code": "43848", "price": 50.0, "tier": "Base"},
    "Biz Unl Ess": {"code": "43846", "price": 40.0, "tier": "Base"},
    "Second Number": {"code": "72974", "price": 15.0, "tier": "Base"},
    "One Talk Second Number": {"code": "28978", "price": 20.0, "tier": "Base"}
}
TABLETS = {"Start": {"code": "44024", "price": 20.0}, "Pro": {"code": "52599", "price": 40.0}}
WATCHES = {"Standalone": {"code": "41371", "price": 15.0}, "Numbershare": {"code": "99838", "price": 15.0}, "Gizmo": {"code": "99343", "price": 5.0}}
STANDARD_INTERNET = ["10 MBPS", "25 MBPS", "Unl 25 MBPS", "50 MBPS", "100 MBPS", "200 MBPS", "400 MBPS"]
INTERNET = {
    "10 MBPS": {"code": "48390", "price": 69.0}, "25 MBPS": {"code": "48423", "price": 99.0},
    "Unl 25 MBPS": {"code": "38925", "price": 69.0}, "50 MBPS": {"code": "64391", "price": 100.0},
    "100 MBPS": {"code": "51219", "price": 69.0}, "200 MBPS": {"code": "53617", "price": 99.0},
    "400 MBPS": {"code": "60202", "price": 199.0}, "Backup 500 MB LTE": {"code": "64084", "price": 10.0},
    "Backup 1GB LTE": {"code": "64207", "price": 20.0}, "Backup 3GB LTE": {"code": "62854", "price": 30.0},
    "Backup 500 MB 5G": {"code": "64206", "price": 10.0}, "Backup 1GB 5G": {"code": "64208", "price": 20.0},
    "Backup 3GB 5G": {"code": "62853", "price": 30.0}
}
OTHER = {"Jetpack Plus": {"price": 45.0}, "Jetpack Pro": {"price": 75.0}}
ADDONS = {
    "Premium Network Experience": {"price": 10.0}, "Enhanced Video Calling": {"price": 5.0},
    "Google Workspace": {"price": 16.0}, "International Connectivity": {"price": 10.0},
    "50 GB Mobile Hotspot": {"price": 5.0}, "Unlimited Individual Cloud": {"price": 10.0}
}
SINGLE_PROTECTION = {
    "TMP Single (Tier 1)": {"price": 18.0}, "TMP Single (Tier 2)": {"price": 15.0},
    "TEC (Tier 1)": {"price": 13.0}, "WPP (Tier 1)": {"price": 8.0}
}
VBIS_PROTECTION = {"None": 0.0, "VBIS Plus": 10.0, "VBIS Preferred": 20.0}
MULTI_PROTECTION_DATA = [
    {"name": "TMP Multi 3-10 Lines", "min": 3, "max": 10, "price": 49.0},
    {"name": "TMP Multi 11-24 Lines", "min": 11, "max": 24, "price": 149.0}
]

# --- APP SETUP ---
st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- LIVE CALCULATION ---
def get_current_totals():
    tiered_sm_count = sum(1 for l in st.session_state.lines if l.get('plan') in SMARTPHONE_TIERS)
    tier_idx = min(tiered_sm_count, 5) - 1 if tiered_sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    
    for l in st.session_state.lines:
        plan = l.get('plan', 'My Biz')
        # Base Price
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif l.get('type') == "Tablet": base = TABLETS.get(plan, {"price": 0})['price']
        elif l.get('type') == "Watch": base = WATCHES.get(plan, {"price": 0})['price']
        elif l.get('type') == "Internet": base = INTERNET.get(plan, {"price": 0})['price']
        else: base = OTHER.get(plan, {"price": 0})['price']

        # JOINT OFFER
        if st.session_state.get('joint_offer') and l.get('type') == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0

        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        
        # Tier Determination
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
        
        prot_price = VBIS_PROTECTION.get(l.get('vbis', 'None'), 0.0) if l.get('type') == "Internet" else SINGLE_PROTECTION.get(l.get('protection', 'None'), {"price": 0})['price']
        
        total = (base + l.get('dev_pay', 0) + extras + prot_price) - disc
        line_details.append({"total": total, "tier": tier})
        account_mrc += total

    if st.session_state.get('tmp_multi') and st.session_state.tmp_multi != "None":
        account_mrc += next((item['price'] for item in MULTI_PROTECTION_DATA if item['name'] == st.session_state.tmp_multi), 0)
    if st.session_state.get('whole_office'): account_mrc += 55.0
    account_mrc += (len(st.session_state.lines) * 2.98) 
    return line_details, account_mrc

# --- SIDEBAR (Forces update on every click) ---
if st.session_state.step > 1:
    with st.sidebar:
        st.header("💰 Live Summary")
        l_info, a_total = get_current_totals()
        for idx, item in enumerate(l_info):
            st.write(f"Line {idx+1}: **${item['total']:.2f}** ({item['tier']})")
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
            st.session_state.lines[i]['type'] = st.selectbox("Category", ["Smartphone", "Tablet", "Watch", "Internet", "Other"], key=f"t_{i}")
            dtype = st.session_state.lines[i]['type']
            if dtype == "Smartphone": opts = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif dtype == "Tablet": opts = list(TABLETS.keys())
            elif dtype == "Watch": opts = list(WATCHES.keys())
            elif dtype == "Internet": opts = list(INTERNET.keys())
            else: opts = list(OTHER.keys())
            st.session_state.lines[i]['plan'] = st.selectbox("Select Plan", opts, key=f"p_{i}")
    if st.button("Next"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.toggle("Autopay ($5 Smartphone discount)", key="autopay")
    st.toggle("Military ($5 Smartphone discount)", key="military")
    
    has_sm = any(l['type'] == "Smartphone" for l in st.session_state.lines)
    has_int = any(l['type'] == "Internet" and l['plan'] in STANDARD_INTERNET for l in st.session_state.lines)
    if has_sm and has_int:
        st.toggle("Business Unlimited Joint Offer ($30 off Internet)", key="joint_offer")
    
    eligible_count = sum(1 for l in st.session_state.lines if l['type'] in ["Smartphone", "Tablet", "Watch"])
    multi_opts = ["None"]
    for bracket in MULTI_PROTECTION_DATA:
        if eligible_count >= bracket['min']: multi_opts.append(bracket['name'])
    st.selectbox("Multi-Device Protection", multi_opts, key="tmp_multi")
    st.toggle("Whole Office Protect ($55)", key="whole_office")
    
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features")
    l_info, _ = get_current_totals()
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1} Config ({l['plan']})", expanded=(i==0)):
            st.markdown(f"**Tier: `{l_info[i]['tier']}`**")
            
            if l['type'] == "Internet":
                l['vbis'] = st.selectbox("Internet Security", list(VBIS_PROTECTION.keys()), key=f"vbis_{i}")
            else:
                if st.session_state.get('tmp_multi') == "None":
                    l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"pr_{i}")
            
            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]['price']})", key=f"a_{i}_{f}")]
                if not st.session_state.get('military'):
                    l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"id_{i}")
            
            l['dev_pay'] = st.number_input("Monthly Device Payment", min_value=0.0, key=f"dp_{i}")

    if st.button("Final Review"): st.session_state.step = 5; st.rerun()
