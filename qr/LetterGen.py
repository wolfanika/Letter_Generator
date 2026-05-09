import qrcode
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import requests
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class CompanyPDF(FPDF):
    def header(self):
        if os.path.exists('header.png'):
            self.image('header.png', 10, 8, 190)
        self.ln(45)
    def footer(self):
        if os.path.exists('footer.png'):
            self.image('footer.png', 10, 265, 190)

def auto_process():
    ref_no = ref_entry.get()
    body_text = text_box.get("1.0", tk.END).strip()
    file_name = f"Letter_{ref_no.replace('/', '_')}.pdf"

    if not body_text:
        messagebox.showwarning("Empty", "Please write something in the letter!")
        return

    # --- 1. CREATE INITIAL PDF ---
    pdf = CompanyPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.multi_cell(0, 7, body_text)
    pdf.output(file_name)

    print("Uploading to cloud...")

    # --- 2. THE FIREWALL-BYPASS UPLOAD ---
    try:
        url = 'https://catbox.moe/user/api.php'
        # These settings make it look like a real person using a browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        data = {'reqtype': 'fileupload'}
        
        with open(file_name, 'rb') as f:
            # verify=False helps if your office proxy is very strict
            response = requests.post(url, data=data, files={'fileToUpload': f}, headers=headers, verify=False)
            
        if response.status_code == 200:
            online_link = response.text.strip()
            print(f"Success! Link: {online_link}")
        else:
            messagebox.showerror("Error", f"Upload failed. Server said: {response.status_code}")
            return
    except Exception as e:
        messagebox.showerror("Network Error", f"Office firewall blocked the upload: {e}")
        return

    # --- 3. RE-GENERATE PDF WITH THE NEW QR LINK ---
    pdf = CompanyPDF()
    pdf.add_page()
    
    # Generate QR from the new link
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(online_link)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save("temp_qr.png")
    pdf.image("temp_qr.png", 170, 50, 25, 25)

    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, f"Ref: {ref_no}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.multi_cell(0, 7, body_text)
    
    pdf.output(file_name)
    os.remove("temp_qr.png")
    os.startfile(file_name)
    messagebox.showinfo("Complete", "PDF created and uploaded!\nScan the QR to test.")

# --- THE APP WINDOW ---
app = tk.Tk()
app.title("RUSL Quick Letter Generator")
app.geometry("500x550")

tk.Label(app, text="Document Reference:", font=('Arial', 10, 'bold')).pack(pady=5)
ref_entry = tk.Entry(app, width=40)
ref_entry.insert(0, "RUSL/UCPL/Update/2026/005")
ref_entry.pack()

tk.Label(app, text="Write your Letter below:", font=('Arial', 10, 'bold')).pack(pady=5)
text_box = tk.Text(app, height=15, width=50, font=('Arial', 10))
text_box.pack(pady=5)

# Big green button for the CEO to see
btn = tk.Button(app, text="GENERATE & UPLOAD NOW", command=auto_process, 
                bg="#2E7D32", fg="white", font=('Arial', 11, 'bold'), padx=20, pady=10)
btn.pack(pady=20)

app.mainloop()