import streamlit as st
import qrcode
from fpdf import FPDF
import os
from datetime import datetime

# --- PDF CLASS ---
class CompanyPDF(FPDF):
    def header(self):
        # Using absolute path to find images on Streamlit Cloud
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

# --- THE APP ---
st.set_page_config(page_title="UCPL QR Gen", layout="centered")
st.title("UCPL Official Letter & QR System")

# STEP 1: Input Reference and Body
ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/010")
body_text = st.text_area("Letter Writing", height=200)

# STEP 2: The Google Drive Connection
st.markdown("---")
st.subheader("🔗 QR Link Setup")
st.write("1. Upload your draft to Google Drive.")
st.write("2. Copy the 'File ID' from the share link (The long code between /d/ and /view).")
drive_id = st.text_input("Paste Google Drive File ID here:")

if st.button("Generate Final Official PDF"):
    if not body_text or not drive_id:
        st.error("Please fill in the Letter Content and the Drive ID!")
    else:
        # Create the direct download link for the QR code
        direct_link = f"https://drive.google.com/uc?export=download&id={drive_id}"
        
        # 1. Setup PDF
        pdf = CompanyPDF()
        pdf.add_page()
        
        # 2. Generate QR
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(direct_link)
        qr.make(fit=True)
        qr.make_image(fill_color="black", back_color="white").save("qr.png")
        
        # 3. Add Content to PDF
        pdf.image("qr.png", 170, 50, 25, 25) # QR Position
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 10, f"Ref: {ref_no}", ln=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 7, body_text)
        
        # 4. Final Output (Fixed for Streamlit Cloud)
        pdf_output = pdf.output()
        # Convert bytearray to bytes if necessary
        pdf_bytes = bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output
        
        st.success("✅ Official PDF Generated!")
        st.download_button(
            label="📥 Download Official PDF",
            data=pdf_bytes,
            file_name=f"UCPL_{ref_no.replace('/', '_')}.pdf",
            mime="application/pdf"
        )
        
        # Cleanup
        if os.path.exists("qr.png"):
            os.remove("qr.png")
