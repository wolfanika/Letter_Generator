import streamlit as st
import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import requests
from datetime import datetime

# --- PDF SETTINGS ---
class CompanyPDF(FPDF):
    def header(self):
        if os.path.exists('header.png'):
            self.image('header.png', 10, 8, 190)
        self.ln(45)
    def footer(self):
        if os.path.exists('footer.png'):
            self.image('footer.png', 10, 265, 190)

def upload_to_cloud(file_path):
    """Uploads to File.io - very stable for Streamlit Cloud."""
    try:
        with open(file_path, 'rb') as f:
            # File stays alive for 2 weeks
            response = requests.post('https://file.io/?expires=2w', files={'file': f})
        if response.status_code == 200:
            return response.json().get('link')
        return None
    except:
        return None

# --- WEB UI ---
st.set_page_config(page_title="UCPL Letter Gen", page_icon="📝")
st.title("UCPL Official Letter Generator")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/005")
body_text = st.text_area("Letter Writing", height=250)

if st.button("Generate & Create Online Link"):
    if not body_text:
        st.error("Please enter the letter text!")
    else:
        with st.spinner("Uploading to cloud..."):
            temp_name = "temp_letter.pdf"
            
            # 1. First PDF (to get a link)
            pdf = CompanyPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            pdf.multi_cell(0, 7, body_text)
            pdf.output(temp_name)

            online_link = upload_to_cloud(temp_name)

            if online_link:
                # 2. Final PDF with the working QR
                pdf = CompanyPDF()
                pdf.add_page()
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data(online_link)
                qr.make(fit=True)
                qr.make_image(fill_color="black", back_color="white").save("qr.png")
                
                pdf.image("qr.png", 170, 50, 25, 25)
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", '', 11)
                pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)
                pdf.multi_cell(0, 7, body_text)
                
                # Get PDF as bytes for the download button
                final_pdf = pdf.output(dest='S').encode('latin-1')
                
                st.success(f"File is live at: {online_link}")
                st.download_button(
                    label="Download Official PDF",
                    data=final_pdf,
                    file_name=f"Letter_{ref_no.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )
                
                # Cleanup
                if os.path.exists("qr.png"): os.remove("qr.png")
                if os.path.exists(temp_name): os.remove(temp_name)
            else:
                st.error("The cloud server rejected the upload. Please try again.")
