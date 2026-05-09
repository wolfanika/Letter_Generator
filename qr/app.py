import streamlit as st
import qrcode
from fpdf import FPDF
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime

# --- CONFIGURATION (NO SECRET NEEDED) ---
if "CLOUDINARY_NAME" in st.secrets:
    cloudinary.config( 
      cloud_name = st.secrets["CLOUDINARY_NAME"], 
      api_key = st.secrets["CLOUDINARY_KEY"],
      secure = True
    )
else:
    st.error("Please add CLOUDINARY_NAME and CLOUDINARY_KEY to Streamlit Secrets.")

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

st.title("UCPL Official Letter System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Content:", height=300)

if st.button("Generate & Host PDF"):
    if not body_text:
        st.error("Please enter letter content.")
    else:
        with st.spinner("Uploading to Cloud (Unsigned Mode)..."):
            try:
                # 1. Generate Draft PDF
                pdf = CompanyPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", '', 11)
                pdf.multi_cell(0, 7, body_text)
                
                # 2. THE FIX: Unsigned Upload
                # This bypasses the 401 error because it doesn't use the Secret key
                upload_result = cloudinary.uploader.upload(
                    pdf.output(),
                    resource_type = "auto",
                    unsigned = True,
                    upload_preset = "ml_default" # This must match Step 1
                )
                
                pdf_url = upload_result.get('secure_url')

                # 3. Create Final PDF with QR
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
                
                st.success("Successfully Hosted!")
                st.download_button("📥 Download Official PDF", bytes(final_pdf.output()), f"{ref_no}.pdf")
                
                if os.path.exists("temp_qr.png"):
                    os.remove("temp_qr.png")

            except Exception as e:
                st.error(f"Upload Error: {e}")
