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
        self.set_y(50)

    def footer(self):
        self.set_y(-25)
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        if os.path.exists(footer_path):
            self.image(footer_path, 10, 272, 190)

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
    except Exception as e:
        st.error(f"FTP Error: {e}")
        return None

# --- PDF GENERATOR ---
def create_pdf(ref_no, recipient, subject, intro, table_raw, closing, qr_url=None):
    pdf = CompanyPDF()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()
    
    # 1. TOP ROW (Ref, QR, Date)
    current_y = 50
    pdf.set_font("Times", 'B', 10)
    
    # Ref Left
    pdf.set_y(current_y + 6)
    pdf.set_x(10)
    pdf.cell(60, 7, f"Ref. {ref_no}")
    
    # QR - 18mm, Shifted Right of Center
    if qr_url:
        qr = qrcode.QRCode(box_size=6, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img_buf = io.BytesIO()
        qr.make_image().save(img_buf)
        pdf.image(img_buf, 115, current_y, 18, 18)
    
    # Date Right
    pdf.set_y(current_y + 6)
    pdf.set_x(145)
    pdf.cell(50, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R')
    
    pdf.set_y(current_y + 22) 
    
    # 2. CONTENT SETTINGS
    pdf.set_font("Times", '', 10.5)
    # Global line height for HTML (replaces the broken line_height argument)
    L_HEIGHT = 6 

    if recipient:
        pdf.write_html(recipient.replace('\n', '<br>'))
        pdf.ln(5)
    
    if subject:
        # Bold Subject, Underlined Content
        subject_html = f"<b>Subject: <u>{subject}</u></b>"
        pdf.write_html(subject_html)
        pdf.ln(8)

    # 3. BODY CONTENT
    if intro:
        pdf.write_html(intro.replace('\n', '<br>'))
        pdf.ln(4)
    
    if table_raw.strip():
        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_raw.strip().split('\n')]
        # Tables still use line_height argument correctly in fpdf2
        with pdf.table(borders_layout="HORIZONTAL_LINES", line_height=L_HEIGHT) as table:
            for d_row in rows:
                r = table.row()
                for cell in d_row: r.cell(cell.strip())
        pdf.ln(4)
        
    if closing:
        pdf.write_html(closing.replace('\n', '<br>'))
        
    return bytes(pdf.output())

# --- APP UI ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📜")
st.title("📜 UCPL Official Letter Generator")

ref_no = st.text_input("Reference Number", f"RUSL/UCPL/{datetime.now().year}/")

col1, col2 = st.columns(2)
with col1:
    recipient_info = st.text_area("Recipient Address:", height=100, value="To,\nCEO, UCPL\nChattogram, Bangladesh")
with col2:
    subject_line = st.text_area("Subject Content:", height=100, placeholder="e.g. Appointment of New Consultant")

intro_text = st.text_area("1. Salutation & Opening Body:", height=150, value="Dear Sir,\n")
table_data = st.text_area("2. Table Data (Optional):", height=100)
closing_text = st.text_area("3. Closing & Signature:", height=150)

if st.button("🚀 Generate & Host"):
    if not subject_line:
        st.warning("Please enter a subject.")
    else:
        with st.spinner("Finalizing document..."):
            safe_name = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
            
            # Phase 1: Upload to get link
            temp_pdf = create_pdf(ref_no, recipient_info, subject_line, intro_text, table_data, closing_text, qr_url="https://sigma-royal.com")
            public_link = upload_to_cpanel(temp_pdf, safe_name)
            
            if public_link:
                # Phase 2: Final render with real QR
                final_pdf = create_pdf(ref_no, recipient_info, subject_line, intro_text, table_data, closing_text, qr_url=public_link)
                upload_to_cpanel(final_pdf, safe_name)
                
                st.success(f"✅ Document ready: {public_link}")
                st.download_button("📥 Download Final PDF", final_pdf, safe_name, "application/pdf")
