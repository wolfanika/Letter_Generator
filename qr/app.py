import streamlit as st
import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
from datetime import datetime

# --- PDF CLASS ---
class CompanyPDF(FPDF):
    def header(self):
        if os.path.exists('header.png'):
            self.image('header.png', 10, 8, 190)
        self.ln(45)
    def footer(self):
        if os.path.exists('footer.png'):
            self.image('footer.png', 10, 265, 190)

st.title("UCPL Official Letter Generator")

# Instructions
st.info("Direct Link Mode: No automated upload to fail. Simply paste your Drive Folder link.")

# Inputs
ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
folder_link = st.text_input("Google Drive Folder Link (Paste once and keep it):")
body_text = st.text_area("Letter Content:", height=300)

if st.button("Generate Official PDF"):
    if not body_text or not folder_link:
        st.error("Please provide both content and your Drive Folder link.")
    else:
        with st.spinner("Building PDF..."):
            file_name = f"Letter_{ref_no.replace('/', '_')}.pdf"
            
            pdf = CompanyPDF()
            pdf.add_page()
            
            # 1. Generate QR that points to the folder where the file will live
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(folder_link)
            qr.make(fit=True)
            qr.make_image(fill_color="black", back_color="white").save("qr.png")
            
            # 2. Build the PDF
            pdf.image("qr.png", 170, 50, 25, 25)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            pdf.multi_cell(0, 7, body_text)
            
            # 3. Output
            final_pdf_bytes = pdf.output()
            
            st.success("PDF Created Successfully!")
            st.download_button(
                label="📥 Download PDF",
                data=final_pdf_bytes,
                file_name=file_name,
                mime="application/pdf"
            )
