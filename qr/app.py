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

# --- STREAMLIT UI ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📜", layout="wide")
st.title("UCPL High-Fidelity Letter System")

# Formatting Sidebar
with st.sidebar:
    st.header("Document Settings")
    font_choice = st.selectbox("Font Family", ["Arial", "Times", "Courier"])
    base_size = st.slider("Font Size", 8, 14, 11)
    st.markdown("""
    **Formatting Shortcuts:**
    - `<u>Underlined Text</u>`
    - `<b>Bold Text</b>`
    - `<center>Centered Text</center>`
    """)

# Inputs
ref_no = st.text_input("Reference Number", f"RUSL/UCPL/Update/{datetime.now().year}/")
body_content = st.text_area("Paste Letter Content (Use <b> and <u> tags for styling):", height=400)

st.markdown("### 📊 Optional Table")
table_data_raw = st.text_area("Paste Table Data (Tabs or Commas):", height=100)

if st.button("🚀 Generate Official Letter & Host"):
    if not body_content:
        st.error("Letter content cannot be empty.")
    else:
        with st.spinner("Rendering High-Fidelity PDF..."):
            safe_filename = f"{ref_no.replace('/', '-')}.pdf".replace(" ", "_")
            
            try:
                def render_content(pdf_obj, body, table_raw):
                    pdf_obj.set_font(font_choice, size=base_size)
                    
                    # Convert newlines to HTML breaks and render
                    html_content = body.replace('\n', '<br>')
                    pdf_obj.write_html(html_content)
                    
                    if table_raw.strip():
                        pdf_obj.ln(10)
                        rows = [line.split('\t') if '\t' in line else line.split(',') for line in table_raw.strip().split('\n')]
                        # Use a bold font for table headers if first row
                        with pdf_obj.table(borders_layout="HORIZONTAL_LINES", line_height=base_size*0.8) as table:
                            for d_row in rows:
                                r = table.row()
                                for cell in d_row: r.cell(cell.strip())
                
                # 1. Create Host PDF
                pdf_host = CompanyPDF()
                pdf_host.add_page()
                render_content(pdf_host, body_content, table_data_raw)
                
                # Upload
                public_url = upload_to_cpanel(pdf_host.output(), safe_filename)

                if public_url:
                    # 2. Create Final Document with QR
                    final_pdf = CompanyPDF()
                    final_pdf.set_auto_page_break(auto=True, margin=40)
                    final_pdf.add_page()
                    
                    # QR Code (No label)
                    qr = qrcode.QRCode(box_size=10, border=1)
                    qr.add_data(public_url)
                    qr.make(fit=True)
                    qr_img = "temp_qr.png"
                    qr.make_image().save(qr_img)
                    
                    # Position QR top right
                    final_pdf.image(qr_img, 165, 55, 28, 28)
                    
                    # Reference and Date Header
                    final_pdf.set_font(font_choice, 'B', base_size)
                    final_pdf.cell(100, 7, f"Ref. {ref_no}")
                    final_pdf.set_x(-60)
                    final_pdf.cell(50, 7, f"Date: {datetime.now().strftime('%B %d, %Y')}", align='R', ln=1)
                    final_pdf.ln(10)
                    
                    # Main Body
                    render_content(final_pdf, body_content, table_data_raw)

                    st.success("✅ Document generated and hosted successfully!")
                    st.download_button("📥 Download Official Signed PDF", bytes(final_pdf.output()), safe_filename)
                    
                    if os.path.exists(qr_img):
                        os.remove(qr_img)

            except Exception as e:
                st.error(f"Rendering Error: {e}")
