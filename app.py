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
    "Biz Unl Ess": {"code": "43846", "price": 40.0, "tier": "Base"}
}
ADDONS = {
    "Premium Network Experience": {"code": "3373", "price": 10.0},
    "Enhanced Video Calling": {"code": "SPO", "price": 5.0},
    "Google Workspace": {"code": "3381", "price": 16.0},
    "International Connectivity": {"code": "3317", "price": 10.0},
    "50 GB Mobile Hotspot": {"code": "3377", "price": 5.0},
    "Unlimited Individual Cloud": {"code": "3316", "price": 10.0}
}
SINGLE_PROTECTION = {
    "TMP Single (Tier 1)": {"code": "88619", "price": 18.0},
    "TMP Single (Tier 2)": {"code": "88618", "price": 15.0},
    "WPP (Tier 1)": {"code": "85913", "price": 8.0},
    "WPP (Tier 2)": {"code": "85912", "price": 5.0}
}

st.set_page_config(page_title="Verizon Quote Wizard", layout="centered")

if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("Total lines/devices?", min_value=1, value=1)
        if st.form_submit_button("Next"):
            st.session_state.num_lines = num
            st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "dev_pay": 0.0, "tier": "Base"} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: PLAN SELECTION ---
elif st.session_state.step == 2:
    st.header("Step 2: Assign Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Setup", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Device Type", ["Smartphone", "Tablet", "Watch", "Internet"], key=f"t_{i}")
            all_plans = {**SMARTPHONE_TIERS, **SMARTPHONE_STATIC}
            st.session_state.lines[i]['plan'] = st.selectbox("Plan", list(all_plans.keys()), key=f"p_{i}")
    
    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 1; st.rerun()
    if col2.button("Next"): st.session_state.step = 3; st.rerun()

# --- STEP 3: ACCOUNT LEVEL ---
elif st.session_state.step == 3:
    st.header("Step 3: Account Options")
    st.session_state.autopay = st.toggle("Autopay Active ($5 off)")
    st.session_state.military = st.toggle("Military Active ($5 off Smartphone)")
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection", ["None", "TMP Multi 3-10 ($49)", "TMP Multi 11-24 ($149)"])
    
    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 2; st.rerun()
    if col2.button("Next"): st.session_state.step = 4; st.rerun()

# --- STEP 4: FEATURES & DYNAMIC TIERS ---
elif st.session_state.step == 4:
    st.header("Step 4: Features & Promo Tiers")
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1}: {l['plan']}", expanded=(i==0)):
            
            # 1. ADD-ONS (My Biz Specific)
            addon_total = 0.0
            if l['plan'] == "My Biz":
                st.write("**Select Add-ons (Calculates Promo Tier)**")
                selected_addons = []
                for name, data in ADDONS.items():
                    if st.checkbox(f"{name} (+${data['price']})", key=f"add_{i}_{name}"):
                        selected_addons.append(name)
                        addon_total += data['price']
                l['features'] = selected_addons
                
                # Determine Tier based on dollar amount
                if addon_total >= 20: l['tier'] = "Pro"
                elif addon_total >= 15: l['tier'] = "Plus"
                elif addon_total >= 5: l['tier'] = "Start"
                else: l['tier'] = "Base"
                
                st.info(f"Add-on Total: ${addon_total:.2f} ➔ **{l['tier']} Promo Tier**")
            
            # 2. FIXED TIERS (Non-My Biz)
            else:
                l['tier'] = SMARTPHONE_TIERS.get(l['plan'], SMARTPHONE_STATIC.get(l['plan'], {"tier": "Base"}))['tier']
                st.info(f"Plan-defined Promo Tier: **{l['tier']}**")

            # 3. PROTECTION
            if st.session_state.tmp_multi == "None":
                l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"prot_{i}")
            
            l['dev_pay'] = st.number_input("Monthly Device Payment", min_value=0.0, key=f"dev_{i}")
            if l['plan'] == "My Biz" and not st.session_state.military:
                l['intro_disc'] = st.checkbox("15% Intro Discount", key=f"int_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 3; st.rerun()
    if col2.button("Finalize Quote"): st.session_state.step = 5; st.rerun()

# --- STEP 5: PREVIEW ---
elif st.session_state.step == 5:
    st.header("Quote Summary")
    
    # Tier count for multi-line pricing
    smartphone_count = sum(1 for l in st.session_state.lines if l['plan'] in SMARTPHONE_TIERS)
    tier_idx = min(smartphone_count, 5) - 1 if smartphone_count > 0 else 0
    
    total_mrc = 0
    for l in st.session_state.lines:
        # Get Base
        if l['plan'] in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[l['plan']]['prices'][tier_idx]
        else: base = SMARTPHONE_STATIC.get(l['plan'], {"price": 20.0})['price']
        
        # Adjustments
        if st.session_state.autopay and l['plan'] in SMARTPHONE_TIERS: base -= 5.0
        
        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        prot = SINGLE_PROTECTION.get(l['protection'], {"price": 0})['price']
        
        sub = base + l['dev_pay'] + extras + prot
        if st.session_state.military and l['type'] == "Smartphone": sub -= 5.0
        if l.get('intro_disc'): sub -= (base * 0.15)
        
        total_mrc += sub
        
        # Display Line Card
        st.write(f"**Line {st.session_state.lines.index(l)+1}** | Tier: {l['tier']} | Total: ${sub:.2f}")

    st.divider()
    st.metric("Total Monthly Due", f"${total_mrc + (st.session_state.num_lines * 2.98):,.2f}")
    
    if st.button("New Quote"): st.session_state.step = 1; st.rerun()
