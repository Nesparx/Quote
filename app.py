import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURATION & SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'quote_data' not in st.session_state:
    st.session_state.quote_data = {"lines": []}

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1

st.title("📄 Pro Quote Generator")

# --- STEP 1: LINE COUNT ---
if st.session_state.step == 1:
    st.header("Step 1: Quantity")
    num_lines = st.number_input("How many lines are we working with?", min_value=1, value=1)
    if st.button("Next"):
        st.session_state.num_lines = num_lines
        # Initialize line data if empty
        if not st.session_state.quote_data["lines"]:
            st.session_state.quote_data["lines"] = [{} for _ in range(num_lines)]
        next_step()

# --- STEP 2 & 3: LINE DETAILS & DISCOUNTS ---
elif st.session_state.step == 2:
    st.header("Step 2 & 3: Line Configuration")
    for i in range(st.session_state.num_lines):
        with st.expander(f"Line {i+1} Details", expanded=(i==0)):
            plan = st.selectbox(f"Plan (Line {i+1})", ["My Biz Plan", "Business Unlimited", "One Talk"], key=f"plan_{i}")
            device_payment = st.number_input(f"Monthly Device Payment ($)", min_value=0.0, key=f"dev_{i}")
            discount = st.selectbox(f"Discount Type", ["None", "15% Off", "Military", "AutoPay"], key=f"disc_type_{i}")
            st.session_state.quote_data["lines"].append({"plan": plan, "device": device_payment, "discount": discount})
    
    col1, col2 = st.columns(2)
    if col1.button("Back"): prev_step()
    if col2.button("Next"): next_step()

# --- STEP 4: SALES INFO ---
elif st.session_state.step == 3:
    st.header("Step 4: Sale Information")
    st.session_state.quote_data['rep'] = st.text_input("Sales Rep Name")
    st.session_state.quote_data['biz_name'] = st.text_input("Business Name")
    st.session_state.quote_data['date'] = st.date_input("Quote Date", datetime.date.today())

    col1, col2 = st.columns(2)
    if col1.button("Back"): prev_step()
    if col2.button("Preview & Export"): next_step()

# --- STEP 5: PREVIEW & EXPORT ---
elif st.session_state.step == 4:
    st.header("Step 5: Finalize Quote")
    st.write(f"**Business:** {st.session_state.quote_data['biz_name']}")
    st.write(f"**Rep:** {st.session_state.quote_data['rep']}")
    
    # PDF Generation Logic
    def create_pdf(data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="QUOTATION", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Business: {data['biz_name']}", ln=True)
        pdf.cell(200, 10, txt=f"Date: {data['date']}", ln=True)
        pdf.output("quote.pdf")
        return "quote.pdf"

    if st.button("Generate PDF"):
        file_path = create_pdf(st.session_state.quote_data)
        with open(file_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="Quote.pdf")
    
    if st.button("Start Over"):
        st.session_state.step = 1
        st.session_state.quote_data = {"lines": []}