import streamlit as st
import qrcode
from fpdf import FPDF
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime
import io

# --- CLOUDINARY CONFIG ---
# Replace these with your actual details from the Cloudinary Dashboard
cloudinary.config( 
  cloud_name = "drqgppww9", 
  api_key = "216228229691118", 
  api_secret = "b_Eox2_xb3eBlwzhbQ1FZTqjIyk" 
)

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

st.title("UCPL Cloud-Linked Letter System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Content:", height=300)

if st.button("Generate & Host Official PDF"):
    if not body_text:
        st.error("Please enter letter content.")
    else:
        with st.spinner("Uploading to Cloud & Generating QR..."):
            # 1. First, create a PDF WITHOUT the QR code to upload
            # (We need the link to the file BEFORE we can make the QR)
            pdf_draft = CompanyPDF()
            pdf_draft.add_page()
            pdf_draft.set_font("Helvetica", '', 11)
            pdf_draft.multi_cell(0, 7, body_text)
            
            # Save PDF to a byte stream
            pdf_bytes = pdf_draft.output()
            
            # 2. Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                pdf_bytes, 
                resource_type = "auto", 
                public_id = f"UCPL_{ref_no.replace('/', '_')}",
                format = "pdf"
            )
            
            # This is the permanent link to your PDF!
            pdf_url = upload_result['secure_url']
            
            # 3. Now create the FINAL PDF with the QR code pointing to that link
            final_pdf = CompanyPDF()
            final_pdf.add_page()
            
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(pdf_url)
            qr.make(fit=True)
            qr.make_image().save("temp_qr.png")
            
            final_pdf.image("temp_qr.png", 170, 50, 25, 25)
            final_pdf.set_font("Helvetica", 'B', 11)
            final_pdf.cell(0, 10, f"Ref: {ref_no}", new_x="LMARGIN", new_y="NEXT")
            final_pdf.set_font("Helvetica", '', 11)
            final_pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
            final_pdf.ln(10)
            final_pdf.multi_cell(0, 7, body_text)
            
            final_pdf_output = bytes(final_pdf.output())
            
            st.success(f"✅ PDF Hosted at: {pdf_url}")
            st.download_button(
                label="📥 Download Official Copy", 
                data=final_pdf_output, 
                file_name=f"UCPL_{ref_no.replace('/', '_')}.pdf"
            )
