import streamlit as st
from fpdf import FPDF
import datetime

# --- INITIALIZATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'lines' not in st.session_state: st.session_state.lines = []
for key in ['autopay', 'military', 'joint_offer', 'tmp_multi', 'whole_office']:
    if key not in st.session_state:
        st.session_state[key] = False if key != 'tmp_multi' else "None"

# --- PROMO CATALOG ---
PROMO_CATALOG = {
    "Pro": [
        {"name": "$1000 Off iPhone 16 Pro", "value": 1000.0, "term": 36},
        {"name": "$800 Off Galaxy S24", "value": 800.0, "term": 36},
        {"name": "$400 Off Pixel 9 Pro", "value": 400.0, "term": 36}
    ],
    "Plus": [
        {"name": "$830 Off iPhone 16", "value": 830.0, "term": 36},
        {"name": "$400 Off Pixel 9", "value": 400.0, "term": 36}
    ],
    "Start": [
        {"name": "$200 Off Select Androids", "value": 200.0, "term": 36}
    ],
    "Base": [
        {"name": "Switching Switcher (BIC)", "value": 200.0, "term": "One-Time"}
    ]
}

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
SMARTPHONE_FEATURES = {
    "International Monthly": {"code": "1949", "price": 100.0},
    "International One Month": {"code": "1948", "price": 100.0},
    "Verizon Roadside Assistance": {"code": "88041", "price": 3.0},
    "Call Filter Plus": {"code": "83439", "price": 3.0},
    "VBMIS (Paid)": {"code": "90530", "price": 2.0}
}
SINGLE_PROT = {
    "TMP Single (Tier 1)": 18.0, "TMP Single (Tier 2)": 15.0, "TEC (Tier 1)": 13.0, "TEC (Tier 2)": 9.0, "WPP (Tier 1)": 8.0, "WPP (Tier 2)": 5.0
}
VBIS_PROT = {
    "None": {"code": "", "price": 0.0},
    "VBIS Plus": {"code": "90273", "price": 10.0},
    "VBIS Preferred": {"code": "90274", "price": 20.0}
}
MULTI_PROT_DATA = [
    {"name": "TMP Multi 3-10 Lines", "min": 3, "price": 49.0},
    {"name": "TMP Multi 11-24 Lines", "min": 11, "price": 149.0},
    {"name": "TMP Multi 25-49 Lines", "min": 25, "price": 299.0}
]

st.set_page_config(page_title="Verizon Quote Wizard", layout="wide")

# --- CALCULATION ENGINE ---
def get_totals():
    lines = st.session_state.lines
    sm_count = sum(1 for l in lines if l.get('plan') in SMARTPHONE_TIERS)
    tier_idx = min(sm_count, 5) - 1 if sm_count > 0 else 0
    
    line_details = []
    account_mrc = 0
    total_base_plan_cost = 0 # For tax calc
    one_time_promo_total = 0
    
    for l in lines:
        plan = l.get('plan', 'My Biz')
        dtype = l.get('type', 'Smartphone')
        
        # Base Price
        if plan in SMARTPHONE_TIERS: base = SMARTPHONE_TIERS[plan]['prices'][tier_idx]
        elif plan in SMARTPHONE_STATIC: base = SMARTPHONE_STATIC[plan]['price']
        elif dtype == "Internet": base = INTERNET.get(plan, 0.0)
        elif dtype == "Tablet": base = TABLETS.get(plan, 0.0)
        elif dtype == "Watch": base = WATCHES.get(plan, 0.0)
        else: base = OTHER.get(plan, 0.0)

        # Apply Joint Offer to Base
        if st.session_state.joint_offer and dtype == "Internet" and plan in STANDARD_INTERNET:
            base -= 30.0
        
        # Track base for tax calc (before discounts)
        total_base_plan_cost += base

        # Discounts
        ap_disc = 5.0 if (st.session_state.autopay and plan in SMARTPHONE_TIERS) else 0.0
        mil_disc = 5.0 if (st.session_state.military and dtype == "Smartphone") else 0.0
        intro_disc = (base * 0.15) if l.get('intro_disc') else 0.0
        
        # Add-ons
        extras_cost = 0
        feature_list = []
        
        # Generic Features
        for f in l.get('features', []):
            cost = ADDONS[f]
            extras_cost += cost
            feature_list.append(f"{f[:10]}..(${cost:.0f})")
            
        for f in l.get('sp_features', []):
            cost = SMARTPHONE_FEATURES[f]['price']
            extras_cost += cost
            feature_list.append(f"{f[:10]}..(${cost:.0f})")

        # Tier Logic
        if plan == "My Biz":
            if extras_cost >= 20: tier = "Pro"
            elif extras_cost >= 15: tier = "Plus"
            elif extras_cost >= 5: tier = "Start"
            else: tier = "Base"
        else:
            tier = SMARTPHONE_TIERS.get(plan, SMARTPHONE_STATIC.get(plan, {"tier": "Base"})).get('tier', 'Base')

        # Protection
        if dtype == "Internet":
            p_price = VBIS_PROT.get(l.get('vbis', 'None'), {"price": 0.0})['price']
            p_name = l.get('vbis', 'None')
        else:
            p_price = SINGLE_PROT.get(l.get('protection', 'None'), 0.0)
            p_name = l.get('protection', 'None')

        # Promos
        promo_credit = 0
        p_sel = l.get('promo_selection', 'None')
        val = 0.0
        term = 36
        
        if p_sel != "None":
            if p_sel == "Custom":
                val = l.get('custom_promo_val', 0.0)
                cust_term = l.get('custom_promo_term', '36 Months')
                term = "One-Time" if cust_term == "One-Time" else int(cust_term.split()[0])
            else:
                eligible = PROMO_CATALOG.get(tier, []) + PROMO_CATALOG.get("Base", [])
                for p in eligible:
                    if p['name'] == p_sel:
                        val = p['value']
                        term = p['term']
                        break
            
            if term == "One-Time": one_time_promo_total += val
            else: promo_credit = val / term

        total = (base - ap_disc - mil_disc - intro_disc) + l.get('dev_pay', 0.0) + extras_cost + p_price - promo_credit
        
        line_details.append({
            "base": base, "ap_disc": ap_disc, "mil_disc": mil_disc, "intro_disc": intro_disc,
            "dev_pay": l.get('dev_pay', 0.0), "extras_cost": extras_cost, "extras_list": feature_list,
            "prot_cost": p_price, "prot_name": p_name,
            "promo_credit": promo_credit, "promo_name": p_sel, "promo_term": term, "promo_val": val,
            "total": total, "tier": tier
        })
        account_mrc += total

    # Account Level
    acct_extras = 0
    if st.session_state.tmp_multi != "None":
        m_price = next((item['price'] for item in MULTI_PROT_DATA if item['name'] == st.session_state.tmp_multi), 0)
        account_mrc += m_price
        acct_extras += m_price
    if st.session_state.whole_office: 
        account_mrc += 55.0
        acct_extras += 55.0
        
    return line_details, account_mrc, one_time_promo_total, total_base_plan_cost, acct_extras

# --- PROFESSIONAL PDF CLASS ---
class ProfessionalQuote(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Verizon Business', ln=True) # Capitalized correctly
        self.set_draw_color(205, 4, 11)
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.multi_cell(0, 4, "This quote is valid for 30 days. All pricing is subject to credit approval and agreement terms. Activation fees, taxes, and government surcharges are estimates and may vary by location. Monthly access fees are billed in advance. Early termination fees may apply.")
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pro_pdf(biz_name, rep_name, due_today_data, monthly_total, first_bill_data, ot_promos):
    pdf = ProfessionalQuote()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 30)
    pdf.cell(90, 5, "PREPARED FOR:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 5, biz_name, ln=True)
    pdf.cell(90, 5, f"Date: {datetime.date.today().strftime('%B %d, %Y')}", ln=True)
    pdf.set_xy(110, 30)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 5, "PREPARED BY:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(110, 35)
    pdf.cell(90, 5, rep_name, ln=True)
    pdf.set_xy(110, 40)
    pdf.cell(90, 5, "Verizon Business", ln=True)
    pdf.ln(15)

    # --- 1. DUE TODAY ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "ESTIMATED DUE TODAY", 0, 1, 'L', fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(150, 7, f"Estimated Sales Tax ({due_today_data['tax_rate']}%) on Devices & Accessories", 1)
    pdf.cell(40, 7, f"${due_today_data['tax_amt']:,.2f}", 1, 1, 'R')
    if due_today_data['setup_cost'] > 0:
        pdf.cell(150, 7, "Setup, Go & Service Charges", 1)
        pdf.cell(40, 7, f"${due_today_data['setup_cost']:,.2f}", 1, 1, 'R')
    if due_today_data['bundle_cost'] > 0:
        pdf.cell(150, 7, "Accessory Bundles", 1)
        pdf.cell(40, 7, f"${due_today_data['bundle_cost']:,.2f}", 1, 1, 'R')
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(150, 8, "TOTAL DUE TODAY", 1)
    pdf.cell(40, 8, f"${due_today_data['total']:,.2f}", 1, 1, 'R')
    pdf.ln(8)

    # --- 2. MONTHLY RECURRING ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "MONTHLY RECURRING CHARGES", 0, 1, 'L', fill=True)
    
    # EXPANDED HEADERS
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 220, 220)
    # Total Width = 190. 
    # # (8), Plan (45), Dev(22), Promo(25), Feat(30), Prot(25), Tot(35)
    pdf.cell(8, 8, "#", 1, 0, 'C', fill=True)
    pdf.cell(45, 8, "Plan Breakdown", 1, 0, 'L', fill=True)
    pdf.cell(22, 8, "Dev Pmt", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "Promo/Crdt", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "Feat/AddOns", 1, 0, 'L', fill=True)
    pdf.cell(25, 8, "Protection", 1, 0, 'L', fill=True)
    pdf.cell(35, 8, "Line Total", 1, 1, 'R', fill=True)
    
    pdf.set_font("Helvetica", "", 7) # Smaller font for detail
    l_info, _, _, base_total_for_tax, acct_extras = get_totals()
    
    for idx, l in enumerate(st.session_state.lines):
        data = l_info[idx]
        
        # 1. PLAN DETAIL STRING
        plan_str = f"{l['plan']} (${data['base']:.2f})"
        if data['ap_disc'] > 0: plan_str += f"\n- ${data['ap_disc']:.0f} Autopay"
        if data['mil_disc'] > 0: plan_str += f"\n- ${data['mil_disc']:.0f} Military"
        if data['intro_disc'] > 0: plan_str += f"\n- ${data['intro_disc']:.2f} Intro"
        
        # 2. PROMO STRING
        if data['promo_val'] > 0 and data['promo_term'] != "One-Time":
            promo_str = f"-${data['promo_credit']:.2f}"
        else: promo_str = "-"

        # 3. FEATURE STRING
        feat_str = ", ".join(data['extras_list']) if data['extras_list'] else "-"
        
        # 4. PROT STRING
        prot_str = f"{data['prot_name']} (${data['prot_cost']:.2f})" if data['prot_cost'] > 0 else "-"

        # Render Row
        # Use simple cells with abbreviated text to prevent breaking layout
        # (Real MultiCell row alignment is complex in FPDF, using condensed strings)
        pdf.cell(8, 8, str(idx+1), 1, 0, 'C')
        
        # Condense Plan String for single line
        short_plan = f"{l['plan']} (${data['base']:.0f})"
        if data['ap_disc']: short_plan += " -AP"
        if data['mil_disc']: short_plan += " -Mil"
        if data['intro_disc']: short_plan += " -Int"
        
        pdf.cell(45, 8, short_plan, 1, 0, 'L')
        pdf.cell(22, 8, f"${data['dev_pay']:.2f}", 1, 0, 'C')
        pdf.cell(25, 8, promo_str, 1, 0, 'C')
        pdf.cell(30, 8, feat_str[:22], 1, 0, 'L')
        pdf.cell(25, 8, prot_str[:18], 1, 0, 'L')
        pdf.cell(35, 8, f"${data['total']:.2f}", 1, 1, 'R')

    # Account Level
    if acct_extras > 0:
        pdf.cell(155, 8, "Account Level Protection (Multi-Device / Whole Office)", 1, 0, 'L')
        pdf.cell(35, 8, f"${acct_extras:.2f}", 1, 1, 'R')
    
    # TAX RANGE
    low_tax = base_total_for_tax * 0.18
    high_tax = base_total_for_tax * 0.42
    pdf.cell(155, 8, f"Estimated Taxes, Surcharges and Fees (18%-42% of Base Plan)", 1, 0, 'L')
    pdf.cell(35, 8, f"${low_tax:.2f} - ${high_tax:.2f}", 1, 1, 'R')

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(155, 8, "TOTAL ESTIMATED MONTHLY", 1, 0, 'R')
    pdf.cell(35, 8, f"${monthly_total:,.2f}", 1, 1, 'R')
    pdf.ln(8)

    # --- 3. FIRST BILL ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, "FIRST BILL ONE TIME CHARGES AND CREDITS", 0, 1, 'L', fill=True) # Renamed
    pdf.set_font("Helvetica", "", 9)
    
    if first_bill_data['act_fees'] > 0:
        pdf.cell(150, 7, "Activation / Upgrade Fees", 1)
        pdf.cell(40, 7, f"${first_bill_data['act_fees']:,.2f}", 1, 1, 'R')
    
    total_creds = first_bill_data['credits'] + ot_promos
    if total_creds > 0:
        pdf.cell(150, 7, "Bill Credits / One-Time Promos", 1)
        pdf.cell(40, 7, f"-${total_creds:,.2f}", 1, 1, 'R')

    return pdf.output()

# --- SIDEBAR ---
if st.session_state.step > 1:
    with st.sidebar:
        st.header("💰 Live Summary")
        l_info, a_total, ot_promos, _, _ = get_totals()
        for i, item in enumerate(l_info):
            st.write(f"Line {i+1}: **${item['total']:.2f}** ({item['tier']})")
        st.divider()
        st.subheader(f"Monthly: ${a_total:,.2f}")
        if ot_promos > 0:
            st.caption(f"One-Time Credits: -${ot_promos:,.2f}")

# --- STEPS ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num = st.number_input("Total devices/lines?", min_value=1, value=1)
    if st.button("Start Quote"):
        st.session_state.num_lines = num
        st.session_state.lines = [{"type": "Smartphone", "plan": "My Biz", "features": [], "sp_features": [], "protection": "None", "vbis": "None", "dev_pay": 0.0, "intro_disc": False, "promo_selection": "None", "custom_promo_term": "36 Months"} for _ in range(num)]
        st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Assign Plans")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Setup", expanded=True):
            st.session_state.lines[i]['type'] = st.selectbox("Device Category", ["Smartphone", "Internet", "Tablet", "Watch", "Other"], key=f"t_sel_{i}")
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
    st.session_state.autopay = st.toggle("Autopay & Paper-Free Discount ($5 off eligible smartphone lines)", value=st.session_state.autopay)
    st.session_state.military = st.toggle("Military / Veteran Discount ($5 off all smartphone lines)", value=st.session_state.military)
    
    has_sm = any(l['type'] == "Smartphone" for l in st.session_state.lines)
    has_int = any(l['type'] == "Internet" and l['plan'] in STANDARD_INTERNET for l in st.session_state.lines)
    if has_sm and has_int:
        st.session_state.joint_offer = st.toggle("Business Unlimited Joint Offer ($30 off Internet)", value=st.session_state.joint_offer)
    else: st.session_state.joint_offer = False

    eligible_count = sum(1 for l in st.session_state.lines if l['type'] in ["Smartphone", "Tablet", "Watch"] or "Jetpack" in str(l['plan']))
    multi_opts = ["None"]
    for bracket in MULTI_PROT_DATA:
        if eligible_count >= bracket['min']: multi_opts.append(bracket['name'])
    
    st.session_state.tmp_multi = st.selectbox("Multi-Device Protection (3+ Eligible Lines)", multi_opts, index=0)
    st.session_state.whole_office = st.toggle("Whole Office Protect ($55.00/mo)", value=st.session_state.whole_office)
    if st.button("Next"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.header("Step 4: Features & Promos")
    l_info, _, _, _, _ = get_totals()
    for i in range(st.session_state.num_lines):
        l = st.session_state.lines[i]
        curr_tier = l_info[i]['tier']
        
        with st.expander(f"Line {i+1} ({l['plan']}) - {curr_tier} Tier", expanded=(i==0)):
            # Protection
            if l['type'] == "Internet":
                l['vbis'] = st.selectbox("Internet Security", list(VBIS_PROT.keys()), key=f"vbis_sel_{i}")
            else:
                if st.session_state.tmp_multi == "None":
                    l['protection'] = st.selectbox("Protection", ["None"] + list(SINGLE_PROT.keys()), key=f"pr_sel_{i}")
                else: st.caption("✅ Covered by Multi-Device Protection")
            
            # Features
            if l['plan'] == "My Biz":
                st.markdown("---")
                st.caption("My Biz Add-ons")
                l['features'] = [f for f in ADDONS if st.checkbox(f"{f} (${ADDONS[f]})", key=f"a_sel_{i}_{f}")]
                if not st.session_state.military:
                    l['intro_disc'] = st.checkbox("Apply 15% Intro Discount", key=f"id_sel_{i}")

            if l['type'] == "Smartphone":
                st.markdown("---")
                st.caption("Smartphone Features")
                avail_feats = ["International Monthly", "International One Month", "Verizon Roadside Assistance", "Call Filter Plus"]
                if l['plan'] != "My Biz": avail_feats.append("VBMIS (Paid)")
                l['sp_features'] = [f for f in avail_feats if st.checkbox(f"{f} (${SMARTPHONE_FEATURES[f]['price']})", key=f"sf_sel_{i}_{f}")]
            
            # Promo
            st.markdown("---")
            st.caption(f"Available Promotions for {curr_tier} Tier")
            tier_promos = PROMO_CATALOG.get(curr_tier, []) + PROMO_CATALOG.get("Base", [])
            promo_names = ["None"] + [p['name'] for p in tier_promos] + ["Custom"]
            l['promo_selection'] = st.selectbox("Select Promo", promo_names, key=f"promo_sel_{i}")
            
            if l['promo_selection'] != "None":
                if l['promo_selection'] == "Custom":
                    c1, c2 = st.columns(2)
                    l['custom_promo_val'] = c1.number_input("Value ($)", min_value=0.0, step=10.0, key=f"cust_val_{i}")
                    l['custom_promo_term'] = c2.selectbox("Term", ["36 Months", "24 Months", "12 Months", "One-Time"], key=f"cust_term_{i}")
                else:
                    sel_p = next((p for p in tier_promos if p['name'] == l['promo_selection']), None)
                    if sel_p: st.info(f"Term: {sel_p['term']} Months" if isinstance(sel_p['term'], int) else "One-Time")

            st.markdown("---")
            l['dev_pay'] = st.number_input("Monthly Device Payment ($)", min_value=0.0, key=f"dp_sel_{i}")

    if st.button("Review & Export"): st.session_state.step = 5; st.rerun()

elif st.session_state.step == 5:
    st.header("Step 5: Finalize & OTD")
    
    with st.container(border=True):
        st.subheader("Sale Information")
        c1, c2, c3 = st.columns(3)
        biz_name = c1.text_input("Business Name", "Business Name")
        rep_name = c2.text_input("Sales Rep", "Sales Rep Name")
        tax_rate = c3.number_input("Sales Tax (%)", value=6.75)

    with st.container(border=True):
        st.subheader("Due Today Calculator")
        dev_retail = st.number_input("Total Device Retail Price ($)", min_value=0.0)
        c1, c2 = st.columns(2)
        su_smart = c1.number_input("Smartphone Setup ($39.99)", min_value=0, step=1)
        su_std = c2.number_input("Standard Setup ($29.99)", min_value=0, step=1)
        c3, c4 = st.columns(2)
        bund_craft = c3.number_input("Crafted Bundle ($150)", min_value=0, step=1)
        bund_ess = c4.number_input("Custom Essentials ($215)", min_value=0, step=1)
        
        setup_cost = (su_smart * 39.99) + (su_std * 29.99)
        bundle_cost = (bund_craft * 150.0) + (bund_ess * 215.0)
        taxable = dev_retail + setup_cost + bundle_cost
        tax_amt = taxable * (tax_rate / 100)
        total_today = tax_amt + setup_cost + bundle_cost
        
        st.success(f"**TOTAL DUE TODAY: ${total_today:,.2f}**")
        due_today_data = {"tax_rate": tax_rate, "tax_amt": tax_amt, "setup_cost": setup_cost, "bundle_cost": bundle_cost, "total": total_today}

    with st.container(border=True):
        st.subheader("First Bill / Credits")
        c1, c2 = st.columns(2)
        act_fees = c1.number_input("Activation Fees ($40)", min_value=0) * 40.0
        credits = c2.number_input("Bill Credits ($)", min_value=0.0)
        first_bill_data = {"act_fees": act_fees, "credits": credits}

    _, m_total, ot_promos, _, _ = get_totals()
    if st.button("Generate PDF Quote"):
        pdf_bytes = create_pro_pdf(biz_name, rep_name, due_today_data, m_total, first_bill_data, ot_promos)
        st.download_button("📥 Download PDF", data=bytes(pdf_bytes), file_name="quote.pdf", mime="application/pdf")
    
    if st.button("Start New Quote"): 
        st.session_state.step = 1; st.session_state.lines = []; st.rerun()
