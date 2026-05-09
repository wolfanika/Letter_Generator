import streamlit as st
import qrcode
from fpdf import FPDF
import os
import requests
import base64
from datetime import datetime

# --- CONFIG ---
IMGBB_API_KEY = "61ab5b00864c4a595c0039eb6cce27e9"

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

st.title("UCPL Instant QR Letter System")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/015")
body_text = st.text_area("Letter Content:", height=250)

if st.button("Generate & Automate"):
    if not body_text or IMGBB_API_KEY == "61ab5b00864c4a595c0039eb6cce27e9":
        st.error("Missing content or API Key!")
    else:
        with st.spinner("Processing..."):
            # 1. Create a "Preview" PDF to turn into a link
            # For simplicity, we upload the QR data as a text-image or a simple host
            # Most scanners just need a URL or the direct text
            
            # Let's use the 'Direct Text' QR but host it as a backup
            verification_text = f"UCPL OFFICIAL RECORD\nRef: {ref_no}\nDate: {datetime.now()}\n\nContent: {body_text[:100]}..."
            
            # 2. Setup the Final PDF
            pdf = CompanyPDF()
            pdf.add_page()
            
            # Since uploading a full PDF to a temporary host is tricky,
            # we make the QR code a 'Verification Link' to a text-based host
            # Or simply encode the text directly into the QR (The most reliable way)
            
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(verification_text)
            qr.make(fit=True)
            qr.make_image().save("qr.png")
            
            pdf.image("qr.png", 170, 50, 25, 25)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"Ref: {ref_no}", ln=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
            pdf.ln(5)
            pdf.multi_cell(0, 7, body_text)
            
            # Force to bytes for Streamlit
            final_pdf = bytes(pdf.output())
            
            st.success("PDF Generated with Embedded Verification!")
            st.download_button("Download Official PDF", final_pdf, f"{ref_no}.pdf")
