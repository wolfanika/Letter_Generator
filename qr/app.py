import streamlit as st
import qrcode
from fpdf import FPDF
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime

# --- CLOUDINARY CONFIGURATION ---
# Using Streamlit Secrets to prevent 401 Unauthorized Errors
try:
    cloudinary.config( 
      cloud_name = st.secrets["CLOUDINARY_NAME"], 
      api_key = st.secrets["CLOUDINARY_KEY"], 
      api_secret = st.secrets["CLOUDINARY_SECRET"] 
    )
except Exception:
    st.error("Cloudinary Secrets are missing! Please add them in Streamlit Settings.")

# --- PDF CLASS WITH HEADER/FOOTER ---
class CompanyPDF(FPDF):
    def header(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        header_path = os.path.join(base_path, "header.png")
        if os.path.exists(header_path):
            self.image(header_path, 10, 8, 190)
        else:
            st.sidebar.warning("header.png not found in GitHub.")
        self.ln(45)

    def footer(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        if os.path.exists(footer_path):
            self.image(footer_path, 10, 265, 190)

# --- MAIN APP INTERFACE ---
st.set_page_config(page_title="UCPL Official System", page_icon="📜")
st.title("UCPL Letter & QR Cloud System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Enter Letter Content:", height=300)

if st.button("Generate & Upload to Cloud"):
    if not body_text:
        st.error("Please enter the letter content.")
    else:
        with st.spinner("Processing PDF and Cloud Hosting..."):
            try:
                # STEP 1: Create Draft PDF (to get the URL)
                pdf_draft = CompanyPDF()
                pdf_draft.add_page()
                pdf_draft.set_font("Helvetica", '', 11)
                pdf_draft.multi_cell(0, 7, body_text)
                
                # Output draft to bytes
                pdf_bytes = pdf_draft.output()

                # STEP 2: Upload to Cloudinary
                # We use resource_type='auto' for better compatibility
                upload_result = cloudinary.uploader.upload(
                    pdf_bytes,
                    resource_type = "auto",
                    folder = "UCPL_Letters",
                    public_id = f"Letter_{ref_no.replace('/', '_')}",
                    format = "pdf"
                )
                
                hosted_url = upload_result.get('secure_url')

                # STEP 3: Create Final PDF with the QR Code
                final_pdf = CompanyPDF()
                final_pdf.add_page()
                
                # Generate QR Code pointing to the Cloudinary URL
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(hosted_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_img.save("temp_qr.png")

                # Add QR to top right
                final_pdf.image("temp_qr.png", 170, 50, 25, 25)
                
                # Add Header Info
                final_pdf.set_font("Helvetica", 'B', 12)
                final_pdf.cell(0, 10, f"Ref: {ref_no}", new_x="LMARGIN", new_y="NEXT")
                final_pdf.set_font("Helvetica", '', 11)
                final_pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
                final_pdf.ln(10)
                
                # Add Body Text
                final_pdf.multi_cell(0, 7, body_text)

                # Final Output
                final_pdf_bytes = bytes(final_pdf.output())

                st.success(f"✅ Hosted Successfully!")
                st.info(f"QR Link: {hosted_url}")
                
                st.download_button(
                    label="📥 Download Final PDF",
                    data=final_pdf_bytes,
                    file_name=f"UCPL_{ref_no.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )

                # Clean up local temp file
                if os.path.exists("temp_qr.png"):
                    os.remove("temp_qr.png")

            except Exception as e:
                st.error(f"Error: {e}")
