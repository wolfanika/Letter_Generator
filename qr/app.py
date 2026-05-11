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
        return None

# --- PDF GENERATOR FUNCTION ---
def create_pdf(ref_no, intro, table_raw, closing, qr_url=None):
    pdf = CompanyPDF()
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()
    
    # 1. QR Code on the LEFT (if URL provided)
    if qr_url:
        qr = qrcode.QRCode(box_size=8, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = io.BytesIO()
        qr.make_image().save(qr_img)
        pdf.image(qr_img, 12, 55, 22, 22)
    
    # 2. Ref (Moved right to avoid QR) and Date (Far Right)
    pdf.set_font("Times", 'B', 11)
    pdf.set_y(55)
    pdf.set_x(40) # Start Ref after the QR code
    pdf.cell(80, 7, f"Ref. {ref_no}")
    
    pdf.set_x(140)
    pdf.cell(55, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R', ln=1)
    pdf.ln(12)
    
    # 3. Content
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
        
    return pdf.output()

# --- STREAMLIT UI ---
st.set_page_config(page_title="UCPL Letter Editor", layout="wide")

col_input, col_preview = st.columns([1, 1])

with col_input:
    st.title("📜 Letter Editor")
    ref_no = st.text_input("Reference Number", f"RUSL/UCPL/Update/{datetime.now().year}/001")
    intro_text = st.text_area("Introduction Content:", height=180, value="To,\nChief Executive Officer (CEO)\nUnited Chattogram Power Ltd. (UCPL)")
    table_data = st.text_area("Table Data (Optional):", height=100, placeholder="SL No.\tDescription\tAmount")
    closing_text = st.text_area("Closing Content:", height=150, value="Dear Sir,\nPlease recall that...")

    generate_btn = st.button("🚀 Upload to Website & Finalize")

# --- LIVE PREVIEW LOGIC ---
# We use a fake URL for the preview QR so it shows the layout
preview_pdf_bytes = create_pdf(ref_no, intro_text, table_data, closing_text, qr_url="https://sigma-royal.com")
base64_pdf = base64.b64encode(preview_pdf_bytes).decode('utf-8')
pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" type="application/pdf"></iframe>'

with col_preview:
    st.markdown("### 🖥️ Live Preview")
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- FINAL UPLOAD LOGIC ---
if generate_btn:
    with st.spinner("Uploading to Server..."):
        safe_filename = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
        
        # Step 1: Create a temporary PDF to get the live URL
        initial_pdf = create_pdf(ref_no, intro_text, table_data, closing
