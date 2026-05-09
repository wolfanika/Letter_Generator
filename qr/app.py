import streamlit as st
import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
from datetime import datetime

# --- PDF CLASS ---
class CompanyPDF(FPDF):
    def header(self):
        # Get the directory where app.py is located
        curr_dir = os.path.dirname(__file__)
        header_path = os.path.join(curr_dir, 'header.png')
        
        if os.path.exists(header_path):
            # 10=left, 8=top, 190=width
            self.image(header_path, 10, 8, 190)
        self.ln(45)

    def footer(self):
        curr_dir = os.path.dirname(__file__)
        footer_path = os.path.join(curr_dir, 'footer.png')
        
        if os.path.exists(footer_path):
            # 10=left, 265=from top (for A4), 190=width
            self.image(footer_path, 10, 265, 190)

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
            
           # Force the output into a standard bytes format
            final_pdf_raw = pdf.output()
            
            # This is the important part: convert to bytes
            if isinstance(final_pdf_raw, bytearray):
                final_pdf_bytes = bytes(final_pdf_raw)
            else:
                final_pdf_bytes = final_pdf_raw

            st.success("PDF Created Successfully!")
            st.download_button(
                label="📥 Download PDF",
                data=final_pdf_bytes, # Now Streamlit will accept it
                file_name=file_name,
                mime="application/pdf"
            )
