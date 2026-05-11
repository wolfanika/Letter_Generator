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
        # Ensure header.png is in your GitHub root folder
        base_path = os.path.dirname(os.path.abspath(__file__))
        header_path = os.path.join(base_path, "header.png")
        if os.path.exists(header_path):
            self.image(header_path, 10, 8, 190)
        self.ln(45)

    def footer(self):
        # Ensure footer.png is in your GitHub root folder
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        if os.path.exists(footer_path):
            self.image(footer_path, 10, 265, 190)

# --- FTP UPLOAD LOGIC ---
def upload_to_cpanel(file_bytes, filename):
    try:
        # Pulling credentials from Streamlit Secrets
        host = st.secrets["FTP_HOST"]
        user = st.secrets["FTP_USER"]
        passwd = st.secrets["FTP_PASS"]
        
        session = ftplib.FTP(host, user, passwd)
        
        # Navigate to your new public folder
        session.cwd('public_html/Letter') 
        
        # Upload from memory to server
        bio = io.BytesIO(file_bytes)
        session.storbinary(f"STOR {filename}", bio)
        session.quit()
        
        # Build the public URL
        return f"{st.secrets['DOMAIN_URL']}{filename}"
    except Exception as e:
        st.error(f"FTP Upload Failed: {e}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📜")
st.title("UCPL Official Letter System")

# Form Inputs
ref_no = st.text_input("Reference Number", "RUSL-UCPL-2026-001")
intro_text = st.text_area("Letter Introduction:", height=100)

st.markdown("### 📊 Optional Table")
table_data_raw = st.text_area("Paste Excel/Table Data here:", height=120, placeholder="Item\tQty\tPrice")

closing_text = st.text_area("Letter Closing:", height=100)

if st.button("Generate & Upload to Website"):
    if not ref_no:
        st.error("Please enter a Reference Number.")
    else:
        with st.spinner("Uploading to sigma-royal.com..."):
            # Clean filename for URL safety
            safe_filename = f"{ref_no.replace('/', '-')}.pdf"
            
            try:
                # 1. Generate PDF Content
                pdf = CompanyPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, intro_text)
                pdf.ln(5)

                if table_data_raw.strip():
                    # Split by Tab (Excel) or Comma
                    rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                    with pdf.table(borders_layout="SINGLE_TOP_AND_BOTTOM", line_height=8) as table:
                        for data_row in rows:
                            row = table.row()
                            for cell in data_row: row.cell(cell.strip())
                    pdf.ln(5)

                pdf.multi_cell(0, 7, closing_text)
                
                # 2. Upload the PDF to your cPanel
                pdf_bytes = pdf.output()
                public_url = upload_to_cpanel(pdf_bytes, safe_filename)

                if public_url:
                    # 3. Create Final Version with QR Code
                    final_pdf = CompanyPDF()
                    final_pdf.add_page()
                    
                    # Generate QR Code pointing to the server URL
                    qr = qrcode.QRCode(box_size=10, border=1)
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    qr.make_image().save("temp_qr.png")
                    
                    # Layout final document
                    final_pdf.image("temp_qr.png", 170, 50, 25, 25)
                    final_pdf.set_font("Helvetica", 'B', 11)
                    final_pdf.cell(0, 10, f"Ref: {ref_no}", new_x="LMARGIN", new_y="NEXT")
                    final_pdf.ln(10)
                    
                    final_pdf.set_font("Helvetica", '', 11)
                    final_pdf.multi_cell(0, 7, intro_text)
                    final_pdf.ln(5)

                    if table_data_raw.strip():
                        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_data_raw.strip().split('\n')]
                        with final_pdf.table(borders_layout="SINGLE_TOP_AND_BOTTOM", line_height=8) as table:
                            for data_row in rows:
                                row = table.row()
                                for cell in data_row: row.cell(cell.strip())
                        final_pdf.ln(5)

                    final_pdf.multi_cell(0, 7, closing_text)

                    st.success(f"✅ Successfully Hosted!")
                    st.info(f"Link: {public_url}")
                    
                    st.download_button(
                        label="📥 Download Final PDF",
                        data=bytes(final_pdf.output()),
                        file_name=safe_filename,
                        mime="application/pdf"
                    )
                    
                    if os.path.exists("temp_qr.png"):
                        os.remove("temp_qr.png")

            except Exception as e:
                st.error(f"Error during processing: {e}")
