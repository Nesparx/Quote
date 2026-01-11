import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="Verizon Quote Generator", layout="centered")

# Basic Plan Pricing Placeholder (To be updated with your specific pricing later)
PLAN_PRICING = {
    "My Biz Plan": 34.00,
    "Business Unlimited Plus": 45.00,
    "Business Unlimited Pro": 55.00,
    "One Talk": 15.00
}

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'lines' not in st.session_state:
    st.session_state.lines = []

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("How many lines are we working with?", min_value=1, step=1, value=1)
        if st.form_submit_button("Next"):
            st.session_state.num_lines = num
            # Initialize/Reset lines
            st.session_state.lines = [{"plan": "My Biz Plan", "features": [], "addons": [], "discounts": [], "dev_pay": 0.0} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: PLAN SELECTION ---
elif st.session_state.step == 2:
    st.header("Step 2: Select Plans")
    for i in range(st.session_state.num_lines):
        st.session_state.lines[i]['plan'] = st.selectbox(
            f"Select Plan for Line {i+1}", 
            list(PLAN_PRICING.keys()), 
            key=f"plan_select_{i}"
        )
    
    col1, col2 = st.columns(2)
    if col1.button("Back"):
        st.session_state.step = 1
        st.rerun()
    if col2.button("Next: Features & Add-ons"):
        st.session_state.step = 3
        st.rerun()

# --- STEP 3: FEATURES, ADD-ONS & DISCOUNTS ---
elif st.session_state.step == 3:
    st.header("Step 3: Features & Discounts")
    
    FEATURE_CATALOG = {"Total Mobile Protection": 18.00, "Wireless Phone Protection": 7.98}
    ADDON_CATALOG = {"Premium Network Experience": 10.00, "Unlimited Verizon Cloud": 10.00, "50 GB Mobile Hotspot": 5.00}
    # Discount values: fixed dollar amounts or the 15% flag
    DISCOUNT_CATALOG = {"Military Discount": 5.00, "Autopay": 5.00, "Intro New Line Discount (15%)": "15_percent"}

    for i in range(st.session_state.num_lines):
        with st.expander(f"🛠️ Line {i+1} Setup ({st.session_state.lines[i]['plan']})", expanded=(i==0)):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Features**")
                st.session_state.lines[i]['features'] = [f for f in FEATURE_CATALOG if st.checkbox(f"{f} (${FEATURE_CATALOG[f]})", key=f"feat_{i}_{f}")]
                st.write("**Add-ons**")
                st.session_state.lines[i]['addons'] = [a for a in ADDON_CATALOG if st.checkbox(f"{a} (${ADDON_CATALOG[a]})", key=f"addon_{i}_{a}")]
            with col2:
                st.write("**Discounts**")
                st.session_state.lines[i]['discounts'] = [d for d in DISCOUNT_CATALOG if st.checkbox(f"{d}", key=f"disc_{i}_{d}")]
                st.session_state.lines[i]['dev_pay'] = st.number_input(f"Device Payment ($)", value=0.0, key=f"dev_p_{i}")

    col1, col2 = st.columns(2)
    if col1.button("Back"):
        st.session_state.step = 2
        st.rerun()
    if col2.button("Next: Sale Info"):
        st.session_state.step = 4
        st.rerun()

# --- STEP 4: SALE INFO ---
elif st.session_state.step == 4:
    st.header("Step 4: Sale Information")
    with st.form("step4"):
        [cite_start]biz = st.text_input("Business Name", value="STRONGHOLD ENGINEERING INC") # [cite: 3]
        [cite_start]rep = st.text_input("Sales Rep", value="Noah Braun") # [cite: 7]
        [cite_start]dt = st.date_input("Quote Date", datetime.date.today()) # [cite: 2]
        if st.form_submit_button("Preview Quote"):
            st.session_state.biz_name, st.session_state.rep_name, st.session_state.quote_date = biz, rep, dt
            st.session_state.step = 5
            st.rerun()
    if st.button("Back"):
        st.session_state.step = 3
        st.rerun()

# --- STEP 5: PREVIEW & EXPORT ---
elif st.session_state.step == 5:
    st.header("Step 5: Review & Export")
    
    FEATURE_CATALOG = {"Total Mobile Protection": 18.00, "Wireless Phone Protection": 7.98}
    ADDON_CATALOG = {"Premium Network Experience": 10.00, "Unlimited Verizon Cloud": 10.00, "50 GB Mobile Hotspot": 5.00}
    
    total_monthly = 0
    [cite_start]econ_adjustment = st.session_state.num_lines * 2.98 # [cite: 85, 86]
    
    for line in st.session_state.lines:
        base_price = PLAN_PRICING.get(line['plan'], 0)
        line_total = base_price + line['dev_pay']
        line_total += sum(FEATURE_CATALOG[f] for f in line['features'])
        line_total += sum(ADDON_CATALOG[a] for a in line['addons'])
        
        # Apply Discounts
        for d in line['discounts']:
            if d == "Intro New Line Discount (15%)":
                line_total -= (base_price * 0.15) # 15% off base plan price
            else:
                line_total -= 5.0 # Military/Autopay fixed $5
        
        total_monthly += line_total
    
    grand_total = total_monthly + econ_adjustment

    st.metric("Estimated Monthly Total", f"${grand_total:,.2f}")

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        [cite_start]pdf.cell(0, 10, "verizon business", ln=True) # [cite: 12]
        pdf.set_font("helvetica", "", 10)
        [cite_start]pdf.cell(0, 5, f"Prepared for: {st.session_state.biz_name}", ln=True) # [cite: 3]
        [cite_start]pdf.cell(0, 5, f"Prepared by: {st.session_state.rep_name}", ln=True) # [cite: 6]
        [cite_start]pdf.cell(0, 5, f"Date: {st.session_state.quote_date}", ln=True) # [cite: 2]
        pdf.ln(10)
        
        with pdf.table(col_widths=(10, 40, 60, 40), text_align="LEFT") as table:
            row = table.row()
            for h in ["Line", "Plan", "Features/Addons", "Subtotal"]: row.cell(h)
            for idx, line in enumerate(st.session_state.lines):
                r = table.row()
                r.cell(str(idx+1))
                r.cell(line['plan'])
                r.cell(", ".join(line['features'] + line['addons']))
                r.cell("Detail Pending...") 
        
        pdf.ln(5)
        [cite_start]pdf.cell(0, 10, f"Economic Adjustment Charge: ${econ_adjustment:,.2f}", ln=True) # [cite: 24, 85]
        pdf.set_font("helvetica", "B", 12)
        [cite_start]pdf.cell(0, 10, f"Total Due Monthly: ${grand_total:,.2f}", ln=True) # [cite: 71]
        return pdf.output()

    st.download_button("📥 Export to PDF", data=bytes(generate_pdf()), file_name="Quote.pdf", mime="application/pdf")
    if st.button("Start New Quote"):
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()
