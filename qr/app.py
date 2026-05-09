import streamlit as st
import qrcode
from fpdf import FPDF
import os
from datetime import datetime

# --- PDF GENERATION CLASS ---
class CompanyPDF(FPDF):
    def header(self):
        # Using absolute paths to find images on the server
        base_path = os.path.dirname(os.path.abspath(__file__))
        header_path = os.path.join(base_path, "header.png")
        
        if os.path.exists(header_path):
            # Left: 10mm, Top: 8mm, Width: 190mm
            self.image(header_path, 10, 8, 190)
        else:
            st.sidebar.warning("Header image not found on GitHub!")
        self.ln(45) # Gap after header

    def footer(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        footer_path = os.path.join(base_path, "footer.png")
        
        if os.path.exists(footer_path):
            # Position at 265mm from top (for A4)
            self.image(footer_path, 10, 265, 190)
        else:
            st.sidebar.warning("Footer image not found on GitHub!")

# --- APP INTERFACE ---
st.set_page_config(page_title="UCPL Letter System", page_icon="📝")
st.title("UCPL Official Letter Generator")

# Inputs
ref_no = st.text_input("Reference Number", "RUSL/UCPL/2026/001")
body_text = st.text_area("Letter Body Content:", height=300)

if st.button("Generate Official PDF"):
    if not body_text:
        st.error("Please enter the letter content first!")
    else:
        with st.spinner("Creating PDF..."):
            try:
                # 1. Create the PDF object
                pdf = CompanyPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                
                # 2. Create the Verification QR (Direct Data Mode)
                # This encodes the letter details directly into the QR
                verify_info = f"UCPL OFFICIAL RECORD\nRef: {ref_no}\nDate: {datetime.now().strftime('%Y-%m-%d')}\nVerified via UCPL System."
                
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(verify_info)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_img.save("temp_qr.png")

                # 3. Add QR and Text to PDF
                # Placing QR on the top right
                pdf.image("temp_qr.png", 170, 50, 25, 25)
                
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 10, f"Ref: {ref_no}", ln=True)
                pdf.set_font("Helvetica", '', 11)
                pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
                pdf.ln(10)
                
                # Letter Content
                pdf.set_font("Helvetica", '', 11)
                pdf.multi_cell(0, 7, body_text)

                # 4. Final Output Processing
                pdf_output = pdf.output()
                
                # CRITICAL: Convert to bytes for Streamlit download button
                if isinstance(pdf_output, (bytearray, list)):
                    final_pdf_bytes = bytes(pdf_output)
                else:
                    final_pdf_bytes = pdf_output

                st.success("✅ PDF Generated Successfully!")
                
                # 5. The Download Button
                st.download_button(
                    label="📥 Download Official PDF",
                    data=final_pdf_bytes,
                    file_name=f"UCPL_{ref_no.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )

                # Cleanup
                if os.path.exists("temp_qr.png"):
                    os.remove("temp_qr.png")

            except Exception as e:
                st.error(f"An error occurred: {e}")

---

### Final Checklist for GitHub:
1.  **`app.py`**: Save the code above as this file.
2.  **`header.png`**: Upload this to the same folder on GitHub (lowercase name).
3.  **`footer.png`**: Upload this to the same folder on GitHub (lowercase name).
4.  **`requirements.txt`**: Ensure it has these 4 lines:
    ```text
    streamlit
    fpdf2
    qrcode
    pillow
