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
            self.image(header_path, 10, 8, 190)
        self.set_y(55) # Space for header

    def footer(self):
        self.set_y(-35) # Position for footer
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
table_data_raw = st.text_area("Paste Table Data:", height=120, placeholder="SL No.\tDescription\tAmount (BDT)")

closing_text = st.text_area("Letter Closing:", height=100)

if st.button("🚀 Generate & Upload"):
    if not ref_no:
        st.error("Please enter a Reference Number.")
    else:
        with st.spinner("Processing..."):
            safe_filename = f"{ref_no.replace('/', '-')}.pdf"
            
            try:
                # 1. Create PDF for hosting
                pdf_host = CompanyPDF()
                pdf_host.add_page()
                pdf_host.set_font("Helvetica", size=11)
                pdf_host.multi_cell(0, 7, intro_text)
                if table_data_raw.strip():
                    rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                    with pdf_host.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
                        for d_row in rows:
                            r = table.row()
                            for cell in d_row: r.cell(cell.strip())
                pdf_host.ln(5)
                pdf_host.multi_cell(0, 7, closing_text)
                
                # Upload and get URL
                public_url = upload_to_cpanel(pdf_host.output(), safe_filename)

                if public_url:
                    # 2. Create FINAL VERSION with QR
                    final_pdf = CompanyPDF()
                    final_pdf.set_auto_page_break(auto=True, margin=40)
                    final_pdf.add_page()
                    
                    # Generate QR
                    qr = qrcode.QRCode(box_size=10, border=1)
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    qr_img = "temp_qr.png"
                    qr.make_image().save(qr_img)
                    
                    # Layout
                    final_pdf.image(qr_img, 165, 55, 28, 28)
                    final_pdf.set_font("Helvetica", 'B', 11)
                    final_pdf.cell(0, 7, f"Ref: {ref_no}", ln=1)
                    final_pdf.cell(0, 7, f"Date: {datetime.now().strftime('%d %B, %Y')}", ln=1)
                    final_pdf.ln(10)
                    
                    final_pdf.set_font("Helvetica", '', 11)
                    if intro_text:
                        final_pdf.multi_cell(0, 7, intro_text)
                        final_pdf.ln(5)

                    if table_data_raw.strip():
                        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                        with final_pdf.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
                            for d_row in rows:
                                r = table.row()
                                for cell in d_row: r.cell(cell.strip())
                        final_pdf.ln(5)

                    if closing_text:
                        final_pdf.multi_cell(0, 7, closing_text)

                    st.success(f"✅ Successfully Hosted!")
                    st.info(f"Link: {public_url}")
                    
                    st.download_button(
                        label="📥 Download Final PDF",
                        data=bytes(final_pdf.output()),
                        file_name=safe_filename,
                        mime="application/pdf"
                    )
                    
                    if os.path.exists(qr_img):
                        os.remove(qr_img)

            except Exception as e:
                st.error(f"System Error: {e}")
