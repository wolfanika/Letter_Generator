import streamlit as st
import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import requests
from datetime import datetime
from io import BytesIO

# --- PDF GENERATION LOGIC ---
class CompanyPDF(FPDF):
    def header(self):
        # Note: On the web, we'll need to upload header/footer images to the site
        if os.path.exists('header.png'):
            self.image('header.png', 10, 8, 190)
        self.ln(45)
    def footer(self):
        if os.path.exists('footer.png'):
            self.image('footer.png', 10, 265, 190)

def upload_to_catbox(file_path):
    url = 'https://catbox.moe/user/api.php'
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = {'reqtype': 'fileupload'}
    with open(file_path, 'rb') as f:
        response = requests.post(url, data=data, files={'fileToUpload': f}, headers=headers)
    return response.text.strip() if response.status_code == 200 else None

# --- WEB INTERFACE ---
st.set_page_config(page_title="UCPL Letter Gen", page_icon="📄")
st.title("UCPL Official Letter Generator")
st.subheader("Generate PDF with Auto-QR Link")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Content", height=300)

if st.button("Generate & Go Live"):
    if not body_text:
        st.error("Please write the letter content!")
    else:
        with st.spinner("Processing..."):
            file_name = f"Letter_{ref_no.replace('/', '_')}.pdf"
            
            # Step 1: Create PDF
            pdf = CompanyPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            pdf.multi_cell(0, 7, body_text)
            pdf.output(file_name)

            # Step 2: Upload
            online_link = upload_to_catbox(file_name)

            if online_link:
                # Step 3: Regenerate with QR
                pdf = CompanyPDF()
                pdf.add_page()
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data(online_link)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save("temp_qr.png")
                
                pdf.image("temp_qr.png", 170, 50, 25, 25)
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", '', 11)
                pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)
                pdf.multi_cell(0, 7, body_text)
                
                final_pdf = pdf.output(dest='S').encode('latin-1')
                
                st.success(f"Successfully uploaded! Link: {online_link}")
                st.download_button("Download Final PDF", data=final_pdf, file_name=file_name, mime="application/pdf")
            else:
                st.error("Upload failed. Try again.")
