import streamlit as st
import qrcode
from fpdf import FPDF
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime

# --- CONFIGURATION ---
if "CLOUDINARY_NAME" in st.secrets:
    cloudinary.config( 
      cloud_name = st.secrets["CLOUDINARY_NAME"], 
      api_key = st.secrets["CLOUDINARY_KEY"], 
      api_secret = st.secrets["CLOUDINARY_SECRET"],
      secure = True
    )
else:
    st.error("Secrets missing in Streamlit Settings!")

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

st.title("UCPL Letter System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Content:", height=300)

if st.button("Generate & Host PDF"):
    if not body_text:
        st.error("Please enter content.")
    else:
        with st.spinner("Uploading..."):
            try:
                # 1. Generate the PDF content first
                pdf = CompanyPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", '', 11)
                pdf.multi_cell(0, 7, body_text)
                
                # 2. Upload to Cloudinary using 'auto' to avoid 401 on 'raw'
                # This returns the dictionary containing the URL
                result = cloudinary.uploader.upload(
                    pdf.output(),
                    resource_type="auto",
                    folder="UCPL_Letters",
                    use_filename=True,
                    unique_filename=True
                )
                
                # Get the link
                pdf_url = result.get('secure_url')

                if pdf_url:
                    # 3. Create the FINAL PDF with the QR code
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
                    st.info(f"Access Link: {pdf_url}")
                    st.download_button("📥 Download PDF", bytes(final_pdf.output()), f"{ref_no}.pdf")
                    
                    if os.path.exists("temp_qr.png"):
                        os.remove("temp_qr.png")
                else:
                    st.error("Upload failed: No URL returned.")

            except Exception as e:
                # This will tell us if it's a 401 or something else
                st.error(f"System Error: {e}")
