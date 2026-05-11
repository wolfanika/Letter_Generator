import streamlit as st
import qrcode
from fpdf import FPDF
import os
import ftplib
from datetime import datetime
import io

# --- PDF CLASS SETUP ---
class CompanyPDF(FPDF):
    def header(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        header_path = os.path.join(base_path, "header.png")
        if os.path.exists(header_path):
            # Header image at the very top
            self.image(header_path, 10, 8, 190)
        # Large gap after header to prevent overlap (55mm)
        self.set_y(55)

    def footer(self):
        # Position at 30mm from bottom
        self.set_y(-30)
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        if os.path.exists(footer_path):
            self.image(footer_path, 10, 265, 190)

# --- FTP UPLOAD LOGIC ---
def upload_to_cpanel(file_bytes, filename):
    try:
        host = st.secrets["FTP_HOST"]
        user = st.secrets["FTP_USER"]
        passwd = st.secrets["FTP_PASS"]
        
        session = ftplib.FTP(host, user, passwd)
        # Ensure this matches your cPanel folder
        session.cwd('public_html/Letter') 
        
        bio = io.BytesIO(file_bytes)
        session.storbinary(f"STOR {filename}", bio)
        session.quit()
        
        return f"{st.secrets['DOMAIN_URL']}{filename}"
    except Exception as e:
        st.error(f"FTP Upload Failed: {e}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📜")
st.title("UCPL Official Letter System")

ref_no = st.text_input("Reference Number", f"RUSL-UCPL-{datetime.now().year}-001")
intro_text = st.text_area("Letter Introduction:", height=150)

st.markdown("### 📊 Optional Table")
table_data_raw = st.text_area("Paste Excel/Table Data here:", height=120, placeholder="SL No.\tDescription\tAmount (BDT)")

closing_text = st.text_area("Letter Closing:", height=100)

if st.button("🚀 Generate & Upload"):
    if not ref_no:
        st.error("Please enter a Reference Number.")
    else:
        with st.spinner("Hosting PDF and generating QR..."):
            safe_filename = f"{ref_no.replace('/', '-')}.pdf"
            
            try:
                # 1. Create temporary PDF to host and get URL
                temp_pdf = CompanyPDF()
                temp_pdf.add_page()
                temp_pdf.set_font("Helvetica", size=11)
                temp_pdf.multi_cell(0, 7, intro_text)
                
                if table_data_raw.strip():
                    rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                    with temp_pdf.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
                        for data_row in rows:
                            row = table.row()
                            for cell in data_row: row.cell(cell.strip())
                
                temp_pdf.ln(5)
                temp_pdf.multi_cell(0, 7, closing_text)
                
                # Upload
                public_url = upload_to_cpanel(temp_pdf.output(), safe_filename)

                if public_url:
                    # 2. Create FINAL PRINT VERSION with QR Code
                    final_pdf = CompanyPDF()
                    # Set Auto Page Break to avoid footer overlap
                    final_pdf.set_auto_page_break(auto=True, margin=35)
                    final_pdf.add_page()
                    
                    # Generate QR
                    qr = qrcode.QRCode(box_size=10, border=1)
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    qr_image_path = "temp_qr.png"
                    qr.make_image().save(qr_image_path)
                    
                    # --- LAYOUT ---
                    # QR Code at the top right
                    final_pdf.image(qr_image_path, 165, 55, 28, 28)
                    
                    # Reference and Date
                    final_pdf.set_font("Helvetica", 'B', 11)
                    final_pdf.cell(0, 7, f"Ref: {ref_no}", ln=1)
                    final_pdf.cell(0, 7, f"Date: {datetime.now().strftime('%d %B, %Y')}", ln=1)
                    final_pdf.ln(10)
                    
                    # Body Text
                    final_pdf.set_font("Helvetica", '', 11)
                    if intro_text:
                        final_pdf.multi_cell(0, 7, intro_text)
                        final_pdf.ln(5)

                    # Table
                    if table_data_raw.strip():
