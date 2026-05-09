import streamlit as st
import qrcode
from fpdf import FPDF
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime

# 1. Setup Cloudinary using Streamlit Secrets
# Make sure you have added these to the "Secrets" tab in Streamlit Settings!
if "CLOUDINARY_NAME" in st.secrets:
    cloudinary.config( 
      cloud_name = st.secrets["CLOUDINARY_NAME"], 
      api_key = st.secrets["CLOUDINARY_KEY"], 
      api_secret = st.secrets["CLOUDINARY_SECRET"] 
    )
else:
    st.error("Missing Secrets! Go to Settings > Secrets and add CLOUDINARY_NAME, CLOUDINARY_KEY, and CLOUDINARY_SECRET.")

# 2. PDF Class
class CompanyPDF(FPDF):
    def header(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        header_path = os.path.join(base_path, "header.png")
        if os.path.exists(header_path):
            self.image(header_path, 10, 8, 190)
        self.ln(45)

    def footer(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        if os.path.exists(footer_path):
            self.image(footer_path, 10, 265, 190)

# 3. Streamlit Interface
st.title("UCPL Official Letter System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Content:", height=300)

if st.button("Generate & Host PDF"):
    if not body_text:
        st.error("Please enter content.")
    elif "CLOUDINARY_NAME" not in st.secrets:
        st.error("Cannot upload: Secrets are not configured.")
    else:
        with st.spinner("Uploading to Cloud..."):
            try:
                # Create PDF
                pdf = CompanyPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", '', 11)
                pdf.multi_cell(0, 7, body_text)
                
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    pdf.output(),
                    resource_type = "auto",
                    folder = "UCPL_Letters"
                )
                
                pdf_url = upload_result['secure_url']

                # Create Final PDF with QR
                final_pdf = CompanyPDF()
                final_pdf.add_page()
                
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                qr.make_image().save("temp_qr.png")
                
                final_pdf.image("temp_qr.png", 170, 50, 25, 25)
                final_pdf.set_font("Helvetica", 'B', 11)
                final_pdf.cell(0, 10, f"Ref: {ref_no}", new_x="LMARGIN", new_y="NEXT")
                final_pdf.ln(10)
                final_pdf.set_font("Helvetica", '', 11)
                final_pdf.multi_cell(0, 7, body_text)
                
                st.success(f"Hosted at: {pdf_url}")
                st.download_button("Download PDF", bytes(final_pdf.output()), f"{ref_no}.pdf")
                
                if os.path.exists("temp_qr.png"):
                    os.remove("temp_qr.png")
            except Exception as e:
                st.error(f"Error: {e}")
