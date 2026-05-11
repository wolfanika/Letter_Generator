import streamlit as st
import qrcode
from fpdf import FPDF
import os
import ftplib
from datetime import datetime
import io
import base64

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

# --- FTP UPLOAD ---
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
    except Exception:
        return None

# --- PDF GENERATOR CORE ---
def create_pdf(ref_no, intro, table_raw, closing, qr_url=None):
    pdf = CompanyPDF()
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()
    
    # 1. QR Code on the LEFT
    if qr_url:
        qr = qrcode.QRCode(box_size=8, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img_buffer = io.BytesIO()
        qr.make_image().save(img_buffer)
        pdf.image(img_buffer, 12, 55, 22, 22)
    
    # 2. Ref & Date Headers
    pdf.set_font("Times", 'B', 11)
    pdf.set_y(55)
    pdf.set_x(42) 
    pdf.cell(80, 7, f"Ref. {ref_no}")
    
    pdf.set_x(140)
    pdf.cell(55, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R', ln=1)
    pdf.ln(15) 
    
    # 3. Content Body
    pdf.set_font("Times", '', 11)
    if intro:
        pdf.write_html(intro.replace('\n', '<br>'))
        pdf.ln(5)
    
    if table_raw.strip():
        # Corrected variable name from 'table_data' to 'table_raw'
        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_raw.strip().split('\n')]
        with pdf.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
            for d_row in rows:
                r = table.row()
                for cell in d_row: r.cell(cell.strip())
        pdf.ln(5)
        
    if closing:
        pdf.write_html(closing.replace('\n', '<br>'))
        
    return pdf.output()

# --- STREAMLIT APP ---
st.set_page_config(page_title="UCPL Letter Editor", layout="wide")

# Custom CSS to fix iframe height
st.markdown("""<style>iframe {border-radius: 10px; border: 1px solid #ddd;}</style>""", unsafe_allow_html=True)

col_input, col_preview = st.columns([1, 1.2])

with col_input:
    st.title("📜 Letter Editor")
    ref_no = st.text_input("Reference Number", f"RUSL/UCPL/Update/{datetime.now().year}/001")
    intro_text = st.text_area("1. Intro (Address, Subject, etc.):", height=180, value="To,\nCEO, UCPL")
    table_data = st.text_area("2. Table (Optional):", height=100)
    closing_text = st.text_area("3. Closing (Body, Sign-off):", height=150)

    generate_btn = st.button("🚀 Upload & Finalize Letter")

# --- IMPROVED PREVIEW LOGIC ---
try:
    preview_bytes = create_pdf(ref_no, intro_text, table_data, closing_text, qr_url="https://sigma-royal.com")
    base64_pdf = base64.b64encode(preview_bytes).decode('utf-8')
    
    # Increased height and added #toolbar=0 to make it cleaner
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="1000" type="application/pdf">'

    with col_preview:
        st.markdown("### 🖥️ Live Preview")
        st.markdown(pdf_display, unsafe_allow_html=True)
except Exception as e:
    with col_preview:
        st.error(f"Preview could not be generated: {e}")

# --- UPLOAD ACTION ---
if generate_btn:
    if not intro_text and not closing_text:
        st.error("Please add content.")
    else:
        with st.spinner("Uploading to Server..."):
            safe_name = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
            
            # Step 1: Upload to get link
            temp_link = upload_to_cpanel(preview_bytes, safe_name)
            
            if temp_link:
                # Step 2: Regenerate with actual URL
                final_bytes = create_pdf(ref_no, intro_text, table_data, closing_text, qr_url=temp_link)
                upload_to_cpanel(final_bytes, safe_name)
                
                st.success(f"✅ Successfully Hosted at: {temp_link}")
                st.download_button("📥 Download Final PDF", final_bytes, safe_name)
            else:
                st.error("Upload failed. Verify FTP Secrets.")
