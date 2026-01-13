import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS (Restored with Full Wording) ---
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
    "TEC (Tier 1)": {"code": "81495", "price": 13.0},
    "TEC (Tier 2)": {"code": "85921", "price": 9.0},
    "WPP (Tier 1)": {"code": "85913", "price": 8.0},
    "WPP (Tier 2)": {"code": "85912", "price": 5.0}
}
MULTI_PROTECTION = {
    "TMP Multi 3-10 Lines": {"code": "1332", "price": 49.0},
    "TMP Multi 11-24 Lines": {"code": "1529", "price": 149.0},
    "TMP Multi 25-49 Lines": {"code": "1606", "price": 299.0}
}

st.set_page_config(page_title="Verizon Quote Wizard", layout="centered")

if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("Total lines/devices on this quote?", min_value=1, value=1)
        if st.form_submit_button("Next"):
            st.session_state.num_lines = num
            st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "dev_pay": 0.0, "tier": "Base"} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: PLAN SELECTION ---
elif st.session_state.step == 2:
    st.header("Step 2: Assign Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Device Setup", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Device Type", ["Smartphone", "Tablet", "Watch", "Internet"], key=f"t_{i}")
            all_plans = {**SMARTPHONE_TIERS, **SMARTPHONE_STATIC}
            st.session_state.lines[i]['plan'] = st.selectbox("Select Plan", list(all_plans.keys()), key=f"p_{i}")
    
    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 1; st.rerun()
    if col2.button("Next"): st.session_state.step = 3; st.rerun()

# --- STEP 3: ACCOUNT LEVEL SETTINGS ---
elif st.session_state.step == 3:
    st.header("Step 3: Account-Wide Discounts & Features")
    st.session_state.autopay = st.toggle("Autopay & Paper-Free Discount ($5 off eligible smartphone lines)")
    st.session_state.military = st.toggle("Military / Veteran Discount ($5 off all smartphone lines)")
    
    st.write("**Account-Level Protection**")
    st.session_state.tmp_multi = st.selectbox(
        "Multi-Device Protection (Account Level)", 
        ["None"] + list(MULTI_PROTECTION.keys()),
        format_func=lambda x: x if x == "None" else f"{x} (${MULTI_PROTECTION[x]['price']})"
    )
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55.00/mo)")
    
    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 2; st.rerun()
    if col2.button("Next"): st.session_state.step = 4; st.rerun()

# --- STEP 4: LINE SPECIFIC FEATURES & TIERS ---
elif st.session_state.step == 4:
    st.header("Step 4: Features & Promo Tiers")
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1}: {l['plan']}", expanded=(i==0)):
            
            # 1. ADD-ONS (My Biz logic with restored dollar thresholds)
            addon_total = 0.0
            if l['plan'] == "My Biz":
                st.write("**My Biz Add-ons (Select to unlock Promo Tier)**")
                selected_addons = []
                for name, data in ADDONS.items():
                    if st.checkbox(f"{name} (+${data['price']:.2f})", key=f"add_{i}_{name}"):
                        selected_addons.append(name)
                        addon_total += data['price']
                l['features'] = selected_addons
                
                # Dynamic Tier logic
                if addon_total >= 20: l['tier'] = "Pro"
                elif addon_total >= 15: l['tier'] = "Plus"
                elif addon_total >= 5: l['tier'] = "Start"
                else: l['tier'] = "Base"
                
                st.info(f"Add-on Total: ${addon_total:.2f} ➔ **{l['tier']} Tier** ($20+ = Pro, $15+ = Plus, $5+ = Start)")
            
            # 2. FIXED TIERS (Start/Plus/Pro Plans)
            else:
                l['tier'] = SMARTPHONE_TIERS.get(l['plan'], SMARTPHONE_STATIC.get(l['plan'], {"tier": "Base"}))['tier']
                st.info(f"Plan Category: **{l['tier']} Tier**")

            # 3. PROTECTION (Restricted by Step 3 Multi-Device selection)
            if st.session_state.tmp_multi == "None":
                l['protection'] = st.selectbox("Single Line Protection", ["None"] + list(SINGLE_PROTECTION.keys()), key=f"prot_{i}")
            else:
                l['protection'] = "None"
                st.success("Line covered by Account Multi-Device Protection")
            
            # 4. DISCOUNTS & PAYMENTS
            l['dev_pay'] = st.number_input("Monthly Device Payment ($)", min_value=0.0, key=f"dev_{i}")
            if l['plan'] == "My Biz":
                if not st.session_state.military:
                    l['intro_disc'] = st.checkbox("Apply 15% Intro New Line Discount", key=f"int_{i}")
                else:
                    l['intro_disc'] = False
                    st.caption("Military discount active: 15% Intro Discount cannot be stacked.")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 3; st.rerun()
    if col2.button("Finalize Quote"): st.session_state.step = 5; st.rerun()

# --- STEP 5: PREVIEW ---
elif st.session_state.step == 5:
    st.header("Quote Summary & Preview")
    
    # Calculate smartphone line count for tiered pricing
    sm_count = sum(1 for l in st.session_state.lines if l['plan'] in SMARTPHONE_TIERS)
    tier_idx = min(sm_count, 5) - 1 if sm_count > 0 else 0
    
    total_mrc = 0
    for idx, l in enumerate(st.session_state.lines):
        # Base Price logic
        if l['plan'] in SMARTPHONE_TIERS: 
            base = SMARTPHONE_TIERS[l['plan']]['prices'][tier_idx]
        else: 
            base = SMARTPHONE_STATIC.get(l['plan'], {"price": 20.0})['price']
        
        # Discounts (Order: Autopay -> 15% off base)
        current_base = base
        if st.session_state.autopay and l['plan'] in SMARTPHONE_TIERS: 
            current_base -= 5.0
        
        disc_val = 0.0
        if l.get('intro_disc'): disc_val += (current_base * 0.15)
        if st.session_state.military and l['type'] == "Smartphone": disc_val += 5.0
        
        # Add-ons and single line protection
        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        prot = SINGLE_PROTECTION.get(l['protection'], {"price": 0})['price']
        
        line_total = (current_base + l['dev_pay'] + extras + prot) - disc_val
        total_mrc += line_total
        
        st.write(f"**Line {idx+1} ({l['plan']})**: ${line_total:.2f} /mo (Tier: {l['tier']})")

    # Account Level additions
    if st.session_state.tmp_multi != "None":
        total_mrc += MULTI_PROTECTION[st.session_state.tmp_multi]['price']
    if st.session_state.whole_office:
        total_mrc += 55.0
    
    # Econ Adjustment
    econ_total = st.session_state.num_lines * 2.98
    grand_total = total_mrc + econ_total

    st.divider()
    st.metric("Estimated Monthly Total", f"${grand_total:,.2f}")
    st.caption(f"Includes ${econ_total:.2f} Economic Adjustment Charge")
    
    if st.button("Start New Quote"): 
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()
