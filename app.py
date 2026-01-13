import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS (Derived from your CSV) ---
SMARTPHONE_TIERS = {
    "My Biz": [70.0, 60.0, 45.0, 39.0, 34.0],
    "Start 5G": [73.0, 63.0, 48.0, 43.0, 38.0],
    "Plus 5G": [83.0, 73.0, 58.0, 53.0, 48.0],
    "Pro 5G": [88.0, 78.0, 63.0, 58.0, 53.0]
}
SMARTPHONE_STATIC = {"Biz Unl SP": 50.0, "Biz Unl Ess": 40.0, "Second Number": 15.0, "One Talk Second Number": 20.0}
TABLETS = {"Start": 20.0, "Pro": 40.0}
WATCHES = {"Standalone": 15.0, "Numbershare": 15.0, "Gizmo": 5.0}
INTERNET = {"10 MBPS": 69.0, "25 MBPS": 99.0, "Unl 25 MBPS": 69.0, "50 MBPS": 100.0, "100 MBPS": 69.0, "200 MBPS": 99.0, "400 MBPS": 199.0}
OTHER = {"Camera": 25.0, "Jetpack Plus": 45.0, "Jetpack Pro": 75.0, "One Talk Mobile Client": 20.0}
ADDONS = {"Premium Network Experience": 10.0, "Enhanced Video Calling": 5.0, "Google Workspace": 16.0, "International Connectivity": 10.0, "50 GB Mobile Hotspot": 5.0}
SINGLE_PROTECTION = {"TMP Single (Tier 1)": 18.0, "TMP Single (Tier 2)": 15.0, "TEC (Tier 1)": 13.0, "TEC (Tier 2)": 9.0, "WPP (Tier 1)": 8.0, "WPP (Tier 2)": 5.0}

# --- CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="Verizon Quote Generator", layout="centered")

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'lines' not in st.session_state:
    st.session_state.lines = []

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("Total number of devices/lines?", min_value=1, step=1, value=1)
        if st.form_submit_button("Next"):
            st.session_state.num_lines = num
            st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "intro_disc": False, "dev_pay": 0.0} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: DEVICE & PLAN TYPE ---
elif st.session_state.step == 2:
    st.header("Step 2: Device & Plan Selection")
    for i in range(st.session_state.num_lines):
        with st.expander(f"📱 Line {i+1} Device Setup", expanded=True):
            d_type = st.selectbox("Device Type", ["Smartphone", "Tablet", "Watch", "Internet", "Other"], key=f"type_{i}")
            st.session_state.lines[i]['type'] = d_type
            
            if d_type == "Smartphone":
                options = list(SMARTPHONE_TIERS.keys()) + list(SMARTPHONE_STATIC.keys())
            elif d_type == "Tablet": options = list(TABLETS.keys())
            elif d_type == "Watch": options = list(WATCHES.keys())
            elif d_type == "Internet": options = list(INTERNET.keys())
            else: options = list(OTHER.keys())
            
            st.session_state.lines[i]['plan'] = st.selectbox("Select Plan", options, key=f"plan_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 1; st.rerun()
    if col2.button("Next: Account Settings"): st.session_state.step = 3; st.rerun()

# --- STEP 3: ACCOUNT SETTINGS ---
elif st.session_state.step == 3:
    st.header("Step 3: Account-Level Options")
    st.session_state.autopay = st.toggle("Autopay/Paper-Free Enabled ($5 off eligible plans)")
    st.session_state.military = st.toggle("Military Discount ($5 off all Smartphones)")
    
    # Calculate protectable lines for TMP Multi logic
    protectable_count = sum(1 for l in st.session_state.lines if l['type'] in ["Smartphone", "Tablet", "Watch", "Other"] and "Jetpack" in str(l['plan']) or l['type'] != "Internet")
    
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection (Account Level)", ["None", "TMP Multi 3-10 ($49)", "TMP Multi 11-24 ($149)", "TMP Multi 25-49 ($299)"])
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55)")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 2; st.rerun()
    if col2.button("Next: Line Details"): st.session_state.step = 4; st.rerun()

# --- STEP 4: LINE SPECIFIC CONFIG ---
elif st.session_state.step == 4:
    st.header("Step 4: Features & Specifics")
    for i in range(st.session_state.num_lines):
        line = st.session_state.lines[i]
        with st.expander(f"Line {i+1} Config ({line['plan']})", expanded=(i==0)):
            # Protection
            if st.session_state.tmp_multi == "None" and line['type'] in ["Smartphone", "Tablet", "Watch"]:
                line['protection'] = st.selectbox("Single Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"prot_{i}")
            else:
                line['protection'] = "None"
                if st.session_state.tmp_multi != "None": st.write("✅ Covered by Multi-Device Protection")

            # Add-ons (My Biz Only)
            if line['plan'] == "My Biz":
                line['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]})", key=f"add_{i}_{f}")]
                # 15% Intro Discount logic
                if not st.session_state.military:
                    line['intro_disc'] = st.checkbox("Apply 15% Intro Discount (New Line)", key=f"intro_{i}")
                else:
                    st.info("Military discount applied (15% disabled)")
                    line['intro_disc'] = False
            
            line['dev_pay'] = st.number_input("Device Payment ($)", min_value=0.0, key=f"dev_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 3; st.rerun()
    if col2.button("Next: Sale Info"): st.session_state.step = 5; st.rerun()

# --- STEP 5 & 6: SALE INFO & PREVIEW ---
elif st.session_state.step == 5:
    st.header("Finalize Quote")
    with st.form("sale_info"):
        biz = st.text_input("Business Name", "Stronghold Engineering Inc")
        rep = st.text_input("Sales Rep", "Noah Braun")
        if st.form_submit_button("Preview & Export"):
            st.session_state.biz_name, st.session_state.rep_name = biz, rep
            st.session_state.step = 6
            st.rerun()

elif st.session_state.step == 6:
    st.header("Step 6: Review & Export")
    
    # CALCULATIONS
    tiered_count = sum(1 for l in st.session_state.lines if l['plan'] in SMARTPHONE_TIERS)
    tier_idx = min(tiered_count, 5) - 1
    
    total_monthly = 0
    for l in st.session_state.lines:
        # Base Price
        if l['plan'] in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[l['plan']][tier_idx]
        elif l['plan'] in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[l['plan']]
        elif l['type'] == "Tablet": base = TABLETS[l['plan']]
        elif l['type'] == "Watch": base = WATCHES[l['plan']]
        elif l['type'] == "Internet": base = INTERNET[l['plan']]
        else: base = OTHER[l['plan']]
        
        # Monthly Discounts
        line_disc = 0
        if st.session_state.autopay and l['plan'] in SMARTPHONE_TIERS:
            base -= 5.0
        if st.session_state.military and l['type'] == "Smartphone":
            line_disc += 5.0
        if l.get('intro_disc'):
            line_disc += (base * 0.15)
            
        # Add-ons & Protection
        extras = sum(ADDONS[f] for f in l.get('features', []))
        prot = SINGLE_PROTECTION.get(l['protection'], 0)
        
        total_monthly += (base + l['dev_pay'] + extras + prot) - line_disc

    # Account Level charges
    if "3-10" in st.session_state.tmp_multi: total_monthly += 49
    elif "11-24" in st.session_state.tmp_multi: total_monthly += 149
    elif "25-49" in st.session_state.tmp_multi: total_monthly += 299
    if st.session_state.whole_office: total_monthly += 55
    
    econ_adj = st.session_state.num_lines * 2.98
    grand_total = total_monthly + econ_adj

    st.metric("Estimated Monthly Total", f"${grand_total:,.2f}")
    
    if st.button("Start New Quote"):
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()
