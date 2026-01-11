import streamlit as st
from fpdf import FPDF
from fpdf.enums import VAlign
import datetime

# --- CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="Verizon Quote Generator", layout="centered")

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'lines' not in st.session_state:
    st.session_state.lines = []

# Styling for a clean mobile look
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ed0000; color: white; }
    .stFormSubmitButton>button { width: 100%; background-color: #000; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- STEP 1: QUANTITY ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    with st.form("step1"):
        num = st.number_input("How many lines are we working with?", min_value=1, step=1, value=1)
        if st.form_submit_button("Next"):
            st.session_state.num_lines = num
            # Initialize lines with defaults if empty
            if not st.session_state.lines or len(st.session_state.lines) != num:
                st.session_state.lines = [{"plan": "My Biz Plan", "price": 34.00, "dev": 0.0, "disc": 0.0} for _ in range(num)]
            st.session_state.step = 2
            st.rerun()

# --- STEP 2 & 3: LINE CONFIGURATION ---
elif st.session_state.step == 2:
    st.header("Step 2 & 3: Line Details")
    st.info("Enter details for each line below. Scroll to the bottom to proceed.")
    
    for i in range(st.session_state.num_lines):
        with st.expander(f"📱 Line {i+1} Setup", expanded=(i==0)):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.lines[i]['plan'] = st.selectbox(f"Plan", ["My Biz Plan", "Business Unlimited", "One Talk"], key=f"p{i}")
                st.session_state.lines[i]['price'] = st.number_input(f"Plan Price ($)", value=34.00, key=f"pr{i}")
            with col2:
                st.session_state.lines[i]['dev'] = st.number_input(f"Device Payment ($)", value=0.0, key=f"d{i}")
                st.session_state.lines[i]['disc'] = st.number_input(f"Discounts/Credits (-$)", value=0.0, key=f"ds{i}")

    c1, c2 = st.columns(2)
    if c1.button("Back"): 
        st.session_state.step = 1
        st.rerun()
    if c2.button("Next: Sale Info"): 
        st.session_state.step = 3
        st.rerun()

# --- STEP 4: SALE INFO ---
elif st.session_state.step == 3:
    st.header("Step 4: Sale Information")
    with st.form("step4"):
        biz_name = st.text_input("Business Name", value="STRONGHOLD ENGINEERING INC") # [cite: 3]
        poc_name = st.text_input("Point of Contact")
        rep_name = st.text_input("Sales Rep", value="Noah Braun") # [cite: 7]
        quote_date = st.date_input("Quote Date", datetime.date.today()) # [cite: 2]
        
        if st.form_submit_button("Preview Quote"):
            st.session_state.biz_name = biz_name
            st.session_state.poc_name = poc_name
            st.session_state.rep_name = rep_name
            st.session_state.quote_date = quote_date
            st.session_state.step = 4
            st.rerun()
    
    if st.button("Back"):
        st.session_state.step = 2
        st.rerun()

# --- STEP 5: PREVIEW & EXPORT ---
elif st.session_state.step == 4:
    st.header("Step 5: Review & Export")
    
    # Financial Logic
    total_plans = sum(l['price'] for l in st.session_state.lines)
    total_devices = sum(l['dev'] for l in st.session_state.lines)
    total_discounts = sum(l['disc'] for l in st.session_state.lines)
    econ_adjustment = st.session_state.num_lines * 2.98 
    grand_total = (total_plans + total_devices + econ_adjustment) - total_discounts

    # Preview Card
    with st.container(border=True):
        st.subheader("Monthly Estimate")
        st.write(f"**Plans & Features:** ${total_plans:,.2f}")
        st.write(f"**Device Payments:** ${total_devices:,.2f}")
        st.write(f"**Discounts:** -${total_discounts:,.2f}")
        st.write(f"**Economic Adjustment:** ${econ_adjustment:,.2f}")
        st.divider()
        st.metric("Total Monthly", f"${grand_total:,.2f}")

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "verizon business", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 5, f"Quote ID: {datetime.datetime.now().strftime('%Y%m%d%H%M')}-Q", ln=True)
        pdf.cell(0, 5, f"Created: {st.session_state.quote_date}", ln=True)
        pdf.ln(5)
        
        # Customer Info
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 6, "Prepared for:", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 5, st.session_state.biz_name, ln=True)
        pdf.ln(10)

        # Table
        with pdf.table(col_widths=(10, 50, 30, 30, 30), text_align="CENTER") as table:
            row = table.row()
            row.cell("Line")
            row.cell("Plan")
            row.cell("Price")
            row.cell("Device")
            row.cell("Savings")
            
            for idx, line in enumerate(st.session_state.lines):
                row = table.row()
                row.cell(str(idx+1))
                row.cell(line['plan'])
                row.cell(f"${line['price']:.2f}")
                row.cell(f"${line['dev']:.2f}")
                row.cell(f"-${line['disc']:.2f}")

        pdf.ln(10)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(140, 7, "Total Due Monthly:", align="R")
        pdf.cell(40, 7, f"${grand_total:,.2f}", align="R", ln=True)
        
        # Returns the PDF as a byte string
        return pdf.output()

    # Generate the bytes once
    pdf_output = generate_pdf()

    # Pass the raw bytes directly to the download button
    st.download_button(
        label="📥 Export to PDF",
        data=bytes(pdf_output), # Ensure it is cast to bytes
        file_name=f"Quote_{st.session_state.biz_name.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
    if st.button("Start New Quote"):
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()

    pdf_bytes = generate_pdf()
    st.download_button(
        label="📥 Export to PDF",
        data=pdf_bytes,
        file_name=f"Quote_{st.session_state.biz_name.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
    if st.button("Start New Quote"):
        st.session_state.step = 1
        st.session_state.lines = []
        st.rerun()
