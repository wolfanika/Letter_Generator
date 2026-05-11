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
        self.set_y(55)

    def footer(self):
        self.set_y(-35)
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

# --- APP UI ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📜")
st.title("UCPL Official Letter System")

# Simple Inputs
ref_no = st.text_input("Reference Number", f"RUSL/UCPL/Update/{datetime.now().year}/")

st.markdown("### 1. Introduction Text")
intro_text = st.text_area("Paste everything before the table (Address, Subject, Dear Sir, etc.):", height=200)

st.markdown("### 2. Table (Optional)")
table_data_raw = st.text_area("Paste table cells here (Leave empty if no table needed):", height=100)

st.markdown("### 3. Closing Text")
closing_text = st.text_area("Paste everything after the table (Words in words, Signature, etc.):", height=150)

if st.button("🚀 Generate & Upload Official Letter"):
    if not intro_text and not closing_text:
        st.error("Please enter some content for the letter.")
    else:
        with st.spinner("Processing..."):
            safe_filename = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
            
            try:
                def build_pdf_content(pdf_obj):
                    # Set standard professional font
                    pdf_obj.set_font("Times", size=11)
                    
                    # 1. Intro
                    if intro_text:
                        # Convert newlines to HTML breaks so formatting is preserved
                        pdf_obj.write_html(intro_text.replace('\n', '<br>'))
                        pdf_obj.ln(5)
                    
                    # 2. Table
                    if table_data_raw.strip():
                        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                        with pdf_obj.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
                            for d_row in rows:
                                r = table.row()
                                for cell in d_row: r.cell(cell.strip())
                        pdf_obj.ln(5)
                    
                    # 3. Closing
                    if closing_text:
                        pdf_obj.write_html(closing_text.replace('\n', '<br>'))

                # --- STEP 1: HOSTING PDF (To get the link for the QR) ---
                pdf_host = CompanyPDF()
                pdf_host.add_page()
                build_pdf_content(pdf_host)
                
                public_url = upload_to_cpanel(pdf_host.output(), safe_filename)

                if public_url:
                    # --- STEP 2: FINAL PRINT PDF WITH QR ---
                    final_pdf = CompanyPDF()
                    final_pdf.set_auto_page_break(auto=True, margin=40)
                    final_pdf.add_page()
                    
                    # Generate QR image
                    qr = qrcode.QRCode(box_size=10, border=1)
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    qr_img = "temp_qr.png"
                    qr.make_image().save(qr_img)
                    
                    # Place QR top right
                    final_pdf.image(qr_img, 165, 55, 28, 28)
                    
                    # Add Ref (Left) & Date (Right)
                    final_pdf.set_font("Times", 'B', 11)
                    final_pdf.cell(100, 7, f"Ref. {ref_no}")
                    final_pdf.set_x(-65)
                    final_pdf.cell(50, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R', ln=1)
                    final_pdf.ln(10)
                    
                    # Build all text blocks onto the final page
                    build_pdf_content(final_pdf)

                    st.success("✅ Letter generated, hosted, and QR linked!")
                    st.info(f"Public Link: {public_url}")
                    
                    st.download_button(
                        label="📥 Download Official PDF",
                        data=bytes(final_pdf.output()),
                        file_name=safe_filename,
                        mime="application/pdf"
                    )
                    
                    if os.path.exists(qr_img):
                        os.remove(qr_img)

            except Exception as e:
                st.error(f"Error: {e}")
