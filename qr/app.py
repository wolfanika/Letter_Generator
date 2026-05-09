import streamlit as st
import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
from datetime import datetime
import base64

# --- PDF CLASS ---
class CompanyPDF(FPDF):
    def header(self):
        if os.path.exists('header.png'):
            self.image('header.png', 10, 8, 190)
        self.ln(45)
    def footer(self):
        if os.path.exists('footer.png'):
            self.image('footer.png', 10, 265, 190)

# --- WEB UI ---
st.set_page_config(page_title="UCPL Letter Gen", page_icon="📝")
st.title("UCPL Official Letter Generator")
st.info("Direct Mode: No cloud upload required. The QR code contains the letter data directly!")

ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/005")
body_text = st.text_area("Letter Writing", height=250)

# ... [rest of your code above stays the same] ...

if st.button("Generate Final PDF"):
    if not body_text:
        st.error("Please enter the letter text!")
    else:
        with st.spinner("Creating PDF..."):
            # Create a "Text-Only" version for the QR code
            qr_data = f"REF: {ref_no}\nDATE: {datetime.now().strftime('%B %d, %Y')}\n\n{body_text}"
            
            # 1. Create the Final PDF
            pdf = CompanyPDF()
            pdf.add_page()
            
            # Generate QR from the text data (No Link Needed!)
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr.make_image(fill_color="black", back_color="white").save("qr.png")
            
            pdf.image("qr.png", 170, 50, 25, 25)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            pdf.multi_cell(0, 7, body_text)
            
            # THE FIX: Simply call pdf.output() with nothing inside the parentheses.
            # In fpdf2, this returns the PDF as bytes automatically.
            final_pdf_bytes = pdf.output()
            
            st.success("PDF Generated Successfully!")
            st.download_button(
                label="📥 Download Official PDF",
                data=final_pdf_bytes,  # Use the bytes directly here
                file_name=f"Letter_{ref_no.replace('/', '_')}.pdf",
                mime="application/pdf"
            )
            
            # Cleanup temp file
            if os.path.exists("qr.png"):
                os.remove("qr.png")
