import streamlit as st
from fpdf import FPDF
import datetime

# --- DATA CATALOGS (Derived from CSV with Codes) ---
# Format: "Display Name": {"code": "00000", "price": 0.0 or [tier_list]}
SMARTPHONE_TIERS = {
    "My Biz": {"code": "32066", "prices": [70.0, 60.0, 45.0, 39.0, 34.0]},
    "Start 5G": {"code": "67792", "prices": [73.0, 63.0, 48.0, 43.0, 38.0]},
    "Plus 5G": {"code": "67793", "prices": [83.0, 73.0, 58.0, 53.0, 48.0]},
    "Pro 5G": {"code": "67832", "prices": [88.0, 78.0, 63.0, 58.0, 53.0]}
}
SMARTPHONE_STATIC = {
    "Biz Unl SP": {"code": "43848", "price": 50.0},
    "Biz Unl Ess": {"code": "43846", "price": 40.0},
    "Second Number": {"code": "72974", "price": 15.0},
    "One Talk Second Number": {"code": "28978", "price": 20.0}
}
TABLETS = {"Start": {"code": "44024", "price": 20.0}, "Pro": {"code": "52599", "price": 40.0}}
WATCHES = {"Standalone": {"code": "41371", "price": 15.0}, "Numbershare": {"code": "99838", "price": 15.0}, "Gizmo": {"code": "99343", "price": 5.0}}
INTERNET = {
    "10 MBPS": {"code": "48390", "price": 69.0}, "25 MBPS": {"code": "48423", "price": 99.0},
    "Unl 25 MBPS": {"code": "38925", "price": 69.0}, "50 MBPS": {"code": "64391", "price": 100.0},
    "100 MBPS": {"code": "51219", "price": 69.0}, "200 MBPS": {"code": "53617", "price": 99.0},
    "400 MBPS": {"code": "60202", "price": 199.0}, "Backup 1GB LTE": {"code": "64207", "price": 20.0}
}
OTHER = {"Camera": {"code": "67651", "price": 25.0}, "Jetpack Plus": {"code": "53537", "price": 45.0}, "Jetpack Pro": {"code": "53538", "price": 75.0}}
ADDONS = {
    "Premium Network Experience": {"code": "3373", "price": 10.0}, "Enhanced Video Calling": {"code": "SPO", "price": 5.0},
    "Google Workspace": {"code": "3381", "price": 16.0}, "International Connectivity": {"code": "3317", "price": 10.0},
    "50 GB Mobile Hotspot": {"code": "3377", "price": 5.0}
}
SINGLE_PROTECTION = {
    "TMP Single (Tier 1)": {"code": "88619", "price": 18.0}, "TMP Single (Tier 2)": {"code": "88618", "price": 15.0},
    "TEC (Tier 1)": {"code": "81495", "price": 13.0}, "TEC (Tier 2)": {"code": "85921", "price": 9.0},
    "WPP (Tier 1)": {"code": "85913", "price": 8.0}, "WPP (Tier 2)": {"code": "85912", "price": 5.0}
}
MULTI_PROTECTION = {
    "TMP Multi 3-10": {"code": "1332", "price": 49.0}, "TMP Multi 11-24": {"code": "1529", "price": 149.0}, "TMP Multi 25-49": {"code": "1606", "price": 299.0}
}

# --- APP SETUP ---
st.set_page_config(page_title="Verizon Quote Wizard", layout="centered")

if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("Total lines (Smartphone + Data)?", min_value=1, step=1, value=1)
        if st.form_submit_button("Start Quote"):
            st.session_state.num_lines = num
            st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "protection": "None", "intro_disc": False, "dev_pay": 0.0} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: PLAN SELECTION ---
elif st.session_state.step == 2:
    st.header("Step 2: Assign Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Setup", expanded=True):
            d_type = st.selectbox("Device Category", ["Smartphone", "Tablet", "Watch", "Internet", "Other"], key=f"t_{i}")
            st.session_state.lines[i]['type'] = d_type
            
            if d_type == "Smartphone":
                cat = {**SMARTPHONE_TIERS, **SMARTPHONE_STATIC}
            elif d_type == "Tablet": cat = TABLETS
            elif d_type == "Watch": cat = WATCHES
            elif d_type == "Internet": cat = INTERNET
            else: cat = OTHER
            
            st.session_state.lines[i]['plan'] = st.selectbox("Plan Name", list(cat.keys()), 
                format_func=lambda x: f"{x} ({cat[x]['code']})", key=f"p_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 1; st.rerun()
    if col2.button("Next: Account Settings"): st.session_state.step = 3; st.rerun()

# --- STEP 3: ACCOUNT OPTIONS ---
elif st.session_state.step == 3:
    st.header("Step 3: Account-Wide Features")
    st.session_state.autopay = st.toggle("Autopay/Paper-Free ($5 discount)")
    st.session_state.military = st.toggle("Military Discount ($5 Smartphone discount)")
    
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection", ["None"] + list(MULTI_PROTECTION.keys()),
        format_func=lambda x: x if x == "None" else f"{x} ({MULTI_PROTECTION[x]['code']}) - ${MULTI_PROTECTION[x]['price']}")
    
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55) (SPO: 99341)")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 2; st.rerun()
    if col2.button("Next: Features & Discounts"): st.session_state.step = 4; st.rerun()

# --- STEP 4: LINE CONFIG ---
elif st.session_state.step == 4:
    st.header("Step 4: Line Details")
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        with st.expander(f"Line {i+1}: {l['plan']}", expanded=(i==0)):
            if st.session_state.tmp_multi == "None":
                l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROTECTION.keys()),
                    format_func=lambda x: x if x == "None" else f"{x} ({SINGLE_PROTECTION[x]['code']})", key=f"prot_{i}")
            else:
                l['protection'] = "None"
                st.info("Covered by Account Multi-Protection")

            if l['plan'] == "My Biz":
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} ({ADDONS[f]['code']})", key=f"feat_{i}_{f}")]
                if not st.session_state.military:
                    l['intro_disc'] = st.checkbox("15% Intro Discount (New Line)", key=f"int_{i}")
                else:
                    l['intro_disc'] = False
                    st.write("Military Active: 15% Disabled")
            
            l['dev_pay'] = st.number_input("Device Payment ($)", min_value=0.0, key=f"dp_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"): st.session_state.step = 3; st.rerun()
    if col2.button("Next: Final Info"): st.session_state.step = 5; st.rerun()

# --- STEP 5: SALE INFO ---
elif st.session_state.step == 5:
    st.header("Step 5: Sale Information")
    with st.form("sale"):
        st.session_state.biz_name = st.text_input("Business Name", "Stronghold Engineering Inc")
        st.session_state.rep_name = st.text_input("Sales Rep", "Noah Braun")
        if st.form_submit_button("Generate Summary"):
            st.session_state.step = 6
            st.rerun()

# --- STEP 6: PREVIEW & EXPORT ---
elif st.session_state.step == 6:
    st.header("Step 6: Review Quote")
    
    # CALCULATE TIER
    tier_count = sum(1 for l in st.session_state.lines if l['plan'] in SMARTPHONE_TIERS)
    tier_idx = min(tier_count, 5) - 1 if tier_count > 0 else 0
    
    total_mrc = 0
    for l in st.session_state.lines:
        # Resolve Base Price
        if l['plan'] in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[l['plan']]['prices'][tier_idx]
        elif l['plan'] in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[l['plan']]['price']
        elif l['type'] == "Tablet": base = TABLETS[l['plan']]['price']
        elif l['type'] == "Watch": base = WATCHES[l['plan']]['price']
        elif l['type'] == "Internet": base = INTERNET[l['plan']]['price']
        else: base = OTHER[l['plan']]['price']
        
        # Discounts
        if st.session_state.autopay and l['plan'] in SMARTPHONE_TIERS: base -= 5.0
        
        m_disc = 5.0 if st.session_state.military and l['type'] == "Smartphone" else 0.0
        i_disc = (base * 0.15) if l.get('intro_disc') else 0.0
        
        # Extras
        extras = sum(ADDONS[f]['price'] for f in l.get('features', []))
        prot = SINGLE_PROTECTION[l['protection']]['price'] if l['protection'] != "None" else 0.0
        
        total_mrc += (base + l['dev_pay'] + extras + prot) - (m_disc + i_disc)

    # Account Charges
    if st.session_state.tmp_multi != "None": total_mrc += MULTI_PROTECTION[st.session_state.tmp_multi]['price']
    if st.session_state.whole_office: total_mrc += 55
    total_mrc += (st.session_state.num_lines * 2.98) # Econ Adj

    st.metric("Estimated Monthly Total", f"${total_mrc:,.2f}")
    
    # PDF VERSION TOGGLE
    rep_version = st.checkbox("Include Plan/SPO Codes in PDF (Rep Version)")

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "verizon business", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 5, f"Prepared for: {st.session_state.biz_name}", ln=True)
        pdf.cell(0, 5, f"Date: {datetime.date.today()}", ln=True)
        pdf.ln(10)
        
        # Logic to include or hide codes based on toggle
        with pdf.table(col_widths=(10, 50, 60, 40), text_align="LEFT") as table:
            header = table.row()
            header.cell("Line")
            header.cell("Plan")
            header.cell("Features")
            header.cell("Subtotal")
            
            for idx, l in enumerate(st.session_state.lines):
                row = table.row()
                row.cell(str(idx+1))
                plan_name = f"{l['plan']} ({SMARTPHONE_TIERS[l['plan']]['code']})" if rep_version and l['plan'] in SMARTPHONE_TIERS else l['plan']
                row.cell(plan_name)
                row.cell(", ".join(l['features']))
                row.cell("Calculated")
        
        return pdf.output()

    st.download_button("📥 Export PDF", data=bytes(generate_pdf()), file_name="Quote.pdf")
    if st.button("New Quote"): st.session_state.step = 1; st.rerun()
