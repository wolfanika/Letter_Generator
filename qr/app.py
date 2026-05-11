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

# --- PDF GENERATOR ---
def create_pdf(ref_no, intro, table_raw, closing, qr_url=None):
    pdf = CompanyPDF()
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()
    
    # 1. QR Code (Left Side)
    if qr_url:
        qr = qrcode.QRCode(box_size=8, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img_buf = io.BytesIO()
        qr.make_image().save(img_buf)
        pdf.image(img_buf, 12, 55, 22, 22)
    
    # 2. Ref (Starts after QR) & Date (Far Right)
    pdf.set_font("Times", 'B', 11)
    pdf.set_y(55)
    pdf.set_x(42) 
    pdf.cell(80, 7, f"Ref. {ref_no}")
    
    pdf.set_x(140)
    pdf.cell(50, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R', ln=1)
    pdf.ln(15) 
    
    # 3. Text Body
    pdf.set_font("Times", '', 11)
    if intro:
        pdf.write_html(intro.replace('\n', '<br>'))
        pdf.ln(5)
    
    if table_raw.strip():
        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_raw.strip().split('\n')]
        with pdf.table(borders_layout="HORIZONTAL_LINES", line_height=8) as table:
            for d_row in rows:
                r = table.row()
                for cell in d_row: r.cell(cell.strip())
        pdf.ln(5)
        
    if closing:
        pdf.write_html(closing.replace('\n', '<br>'))
        
    return bytes(pdf.output())

# --- APP LAYOUT ---
st.set_page_config(page_title="UCPL Letter Editor", layout="wide")

col_input, col_preview = st.columns([1, 1.2])

with col_input:
    st.title("📜 Letter Editor")
    ref_no = st.text_input("Reference Number", f"RUSL/UCPL/Update/{datetime.now().year}/001")
    intro_text = st.text_area("1. Intro:", height=150, value="To,\nCEO, UCPL")
    table_data = st.text_area("2. Table:", height=100)
    closing_text = st.text_area("3. Closing:", height=150)
    generate_btn = st.button("🚀 Finalize & Upload")

# --- BULLETPROOF PREVIEW ---
try:
    # Generate the bytes
    preview_pdf = create_pdf(ref_no, intro_text, table_data, closing_text, qr_url="https://sigma-royal.com")
    # Convert to base64
    b64 = base64.b64encode(preview_pdf).decode('utf-8')
    
    # Fixed PDF Display logic
    pdf_html = f'<object data="data:application/pdf;base64,{b64}" type="application/pdf" width="100%" height="900px"><p>Your browser is blocking the preview. <a href="data:application/pdf;base64,{b64}" download="preview.pdf">Download Preview</a> instead.</p></object>'

    with col_preview:
        st.markdown("### 🖥️ Live Preview")
        st.write(f"Ref: {ref_no}") # Small indicator to show app is reacting
        st.components.v1.html(pdf_html, height=910)
        
except Exception as e:
    with col_preview:
        st.error(f"Preview crashed: {e}")

# --- FINAL ACTIONS ---
if generate_btn:
    with st.spinner("Processing..."):
        safe_name = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
        # Step 1: Upload to get link
        link = upload_to_cpanel(preview_pdf, safe_name)
        if link:
            # Step 2: Final version with working QR
            final_bytes = create_pdf(ref_no, intro_text, table_data, closing_text, qr_url=link)
            upload_to_cpanel(final_bytes, safe_name)
            st.success(f"File live: {link}")
            st.download_button("📥 Download PDF", final_bytes, safe_name, "application/pdf")
