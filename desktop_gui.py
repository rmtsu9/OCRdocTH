import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
from pathlib import Path
from datetime import datetime
import logging
from PIL import Image, ImageTk
import io
import sys

# Import OCR system
from OCR import DocumentOCR

# Configure logging for GUI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoginSystem:
    """ระบบ Login แบบ hardcoded พร้อมการเปลี่ยนรหัสผ่าน"""
    
    def __init__(self):
        self.credentials_file = "credentials.json"
        self.default_credentials = {"username": "admin", "password": "pass"}
        self.load_credentials()
    
    def load_credentials(self):
        """โหลด credentials จากไฟล์ หรือใช้ default"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
            else:
                self.credentials = self.default_credentials.copy()
                self.save_credentials()
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self.credentials = self.default_credentials.copy()
    
    def save_credentials(self):
        """บันทึก credentials ลงไฟล์"""
        try:
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(self.credentials, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def verify_login(self, username: str, password: str) -> bool:
        """ตรวจสอบการ login"""
        return (username == self.credentials["username"] and 
                password == self.credentials["password"])
    
    def change_password(self, old_username: str, old_password: str, 
                       new_username: str, new_password: str) -> bool:
        """เปลี่ยน username และ password"""
        if self.verify_login(old_username, old_password):
            self.credentials["username"] = new_username
            self.credentials["password"] = new_password
            self.save_credentials()
            return True
        return False


class LoginWindow:
    """หน้าต่าง Login"""
    
    def __init__(self):
        self.login_system = LoginSystem()
        self.root = tk.Tk()
        self.root.title("OCR Thai Tax Documents - Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        self.create_login_ui()
        self.main_app = None
        
    def center_window(self):
        """จัดตำแหน่งหน้าต่างกลางจอ"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")
    
    def create_login_ui(self):
        """สร้าง UI หน้า Login"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="OCR Thai Tax Documents",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(expand=True)
        
        # Login form
        form_frame = tk.Frame(self.root, padx=50, pady=30)
        form_frame.pack(expand=True, fill="both")
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Arial", 12)).pack(pady=(0, 5))
        self.username_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.username_entry.pack(pady=(0, 15))
        self.username_entry.insert(0, "admin")  # Default value
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Arial", 12)).pack(pady=(0, 5))
        self.password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*")
        self.password_entry.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(form_frame)
        button_frame.pack()
        
        login_btn = tk.Button(
            button_frame,
            text="Login",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=10,
            command=self.handle_login
        )
        login_btn.pack(side="left", padx=(0, 10))
        
        change_pass_btn = tk.Button(
            button_frame,
            text="Change Password",
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            width=15,
            command=self.show_change_password
        )
        change_pass_btn.pack(side="left")
        
        # Bind Enter key
        self.root.bind('<Return>', lambda event: self.handle_login())
        self.username_entry.focus()
    
    def handle_login(self):
        """จัดการการ Login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "กรุณากรอก Username และ Password")
            return
        
        if self.login_system.verify_login(username, password):
            logger.info(f"Login successful: {username}")
            self.open_main_app()
        else:
            messagebox.showerror("Login Failed", "Username หรือ Password ไม่ถูกต้อง")
            self.password_entry.delete(0, tk.END)
    
    def show_change_password(self):
        """แสดงหน้าต่างเปลี่ยนรหัสผ่าน"""
        ChangePasswordWindow(self.login_system)
    
    def open_main_app(self):
        """เปิดแอปพลิเคชันหลัก"""
        self.root.destroy()
        self.main_app = OCRMainApp()
        self.main_app.run()
    
    def run(self):
        """เรียกใช้หน้าต่าง Login"""
        self.root.mainloop()


class ChangePasswordWindow:
    """หน้าต่างเปลี่ยนรหัสผ่าน"""
    
    def __init__(self, login_system: LoginSystem):
        self.login_system = login_system
        self.window = tk.Toplevel()
        self.window.title("Change Password")
        self.window.geometry("350x400")
        self.window.resizable(False, False)
        self.window.grab_set()  # Modal window
        
        # Center window
        self.center_window()
        self.create_ui()
    
    def center_window(self):
        """จัดตำแหน่งหน้าต่างกลางจอ"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"350x400+{x}+{y}")
    
    def create_ui(self):
        """สร้าง UI หน้าเปลี่ยนรหัสผ่าน"""
        main_frame = tk.Frame(self.window, padx=30, pady=30)
        main_frame.pack(expand=True, fill="both")
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="เปลี่ยน Username และ Password",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Current credentials
        tk.Label(main_frame, text="Username ปัจจุบัน:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
        self.old_username_entry = tk.Entry(main_frame, font=("Arial", 11), width=30)
        self.old_username_entry.pack(pady=(0, 10))
        
        tk.Label(main_frame, text="Password ปัจจุบัน:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
        self.old_password_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, show="*")
        self.old_password_entry.pack(pady=(0, 15))
        
        # Separator
        separator = tk.Frame(main_frame, height=2, bg="#bdc3c7")
        separator.pack(fill="x", pady=10)
        
        # New credentials
        tk.Label(main_frame, text="Username ใหม่:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
        self.new_username_entry = tk.Entry(main_frame, font=("Arial", 11), width=30)
        self.new_username_entry.pack(pady=(0, 10))
        
        tk.Label(main_frame, text="Password ใหม่:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
        self.new_password_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, show="*")
        self.new_password_entry.pack(pady=(0, 10))
        
        tk.Label(main_frame, text="ยืนยัน Password ใหม่:", font=("Arial", 11)).pack(anchor="w", pady=(0, 5))
        self.confirm_password_entry = tk.Entry(main_frame, font=("Arial", 11), width=30, show="*")
        self.confirm_password_entry.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        save_btn = tk.Button(
            button_frame,
            text="บันทึก",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            width=10,
            command=self.handle_change_password
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame,
            text="ยกเลิก",
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=10,
            command=self.window.destroy
        )
        cancel_btn.pack(side="left")
    
    def handle_change_password(self):
        """จัดการการเปลี่ยนรหัสผ่าน"""
        old_username = self.old_username_entry.get().strip()
        old_password = self.old_password_entry.get()
        new_username = self.new_username_entry.get().strip()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validate input
        if not all([old_username, old_password, new_username, new_password, confirm_password]):
            messagebox.showerror("Error", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Error", "Password ใหม่และการยืนยันไม่ตรงกัน")
            return
        
        if len(new_password) < 4:
            messagebox.showerror("Error", "Password ใหม่ต้องมีอย่างน้อย 4 ตัวอักษร")
            return
        
        # Change password
        if self.login_system.change_password(old_username, old_password, new_username, new_password):
            messagebox.showinfo("Success", "เปลี่ยน Username และ Password เรียบร้อยแล้ว")
            logger.info(f"Password changed successfully for user: {new_username}")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Username หรือ Password ปัจจุบันไม่ถูกต้อง")


class OCRMainApp:
    """แอปพลิเคชันหลักสำหรับ OCR"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OCR Thai Tax Documents - Main Application")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize OCR system
        self.ocr_system = None
        self.selected_file = None
        self.processing = False
        
        # Initialize OCR in background
        self.init_ocr_system()
        
        self.create_main_ui()
        
    def init_ocr_system(self):
        """Initialize OCR system in background thread"""
        def init_ocr():
            try:
                self.ocr_system = DocumentOCR()
                self.log_debug("OCR system initialized successfully")
            except Exception as e:
                self.log_debug(f"Failed to initialize OCR system: {e}")
                messagebox.showerror("Error", f"ไม่สามารถเริ่มต้นระบบ OCR ได้: {e}")
        
        thread = threading.Thread(target=init_ocr, daemon=True)
        thread.start()
    
    def create_main_ui(self):
        """สร้าง UI หลัก"""
        # Create main frames
        self.create_header()
        self.create_main_content()
        self.create_status_bar()
    
    def create_header(self):
        """สร้าง Header"""
        header_frame = tk.Frame(self.root, bg="#34495e", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="OCR Thai Tax Documents - Main Application",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#34495e"
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Logout button
        logout_btn = tk.Button(
            header_frame,
            text="Logout",
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            command=self.logout
        )
        logout_btn.pack(side="right", padx=20, pady=15)
    
    def create_main_content(self):
        """สร้าง Content หลัก"""
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - File selection and controls
        left_frame = tk.Frame(main_frame, width=400)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)
        
        self.create_file_selection_panel(left_frame)
        self.create_control_panel(left_frame)
        
        # Right panel - Preview and debug
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        
        self.create_preview_panel(right_frame)
        self.create_debug_panel(right_frame)
    
    def create_file_selection_panel(self, parent):
        """สร้างแผง File Selection"""
        # File Selection Frame
        file_frame = tk.LabelFrame(parent, text="1. เลือกไฟล์", font=("Arial", 12, "bold"), padx=10, pady=10)
        file_frame.pack(fill="x", pady=(0, 10))
        
        # Selected file display
        self.file_label = tk.Label(
            file_frame,
            text="ยังไม่ได้เลือกไฟล์",
            font=("Arial", 10),
            fg="#7f8c8d",
            wraplength=350,
            justify="left"
        )
        self.file_label.pack(anchor="w", pady=(0, 10))
        
        # File selection buttons
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill="x")
        
        select_btn = tk.Button(
            btn_frame,
            text="เลือกไฟล์ PDF/Image",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=self.select_file
        )
        select_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = tk.Button(
            btn_frame,
            text="ล้าง",
            font=("Arial", 10),
            bg="#95a5a6",
            fg="white",
            command=self.clear_file
        )
        clear_btn.pack(side="left")
    
    def create_control_panel(self, parent):
        """สร้างแผง Control"""
        # Control Panel Frame
        control_frame = tk.LabelFrame(parent, text="2. ปุ่ม Convert", font=("Arial", 12, "bold"), padx=10, pady=10)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # OCR Engine selection
        engine_frame = tk.Frame(control_frame)
        engine_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(engine_frame, text="OCR Engine:", font=("Arial", 10)).pack(anchor="w")
        self.engine_var = tk.StringVar(value="easyocr")
        engine_combo = ttk.Combobox(
            engine_frame,
            textvariable=self.engine_var,
            values=["easyocr", "tesseract", "paddleocr", "auto"],
            state="readonly",
            width=15
        )
        engine_combo.pack(anchor="w", pady=(5, 0))
        
        # TRCloud Invoice Number Format section
        trcloud_frame = tk.LabelFrame(control_frame, text="รูปแบบเลขใบกำกับ (TRCloud)", font=("Arial", 9, "bold"), fg="#2980b9")
        trcloud_frame.pack(fill="x", pady=(10, 0), padx=5)
        
        # Number format selection
        format_frame = tk.Frame(trcloud_frame)
        format_frame.pack(fill="x", pady=5)
        
        tk.Label(format_frame, text="รูปแบบ:", font=("Arial", 9)).pack(anchor="w")
        self.number_format_var = tk.StringVar(value="YYMMx")
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.number_format_var,
            values=["YYx", "YYMMx", "YYMMDDx", "x"],
            state="readonly",
            width=12,
            font=("Arial", 9)
        )
        format_combo.pack(anchor="w", pady=(2, 0))
        
        # Running number digits
        digits_frame = tk.Frame(trcloud_frame)
        digits_frame.pack(fill="x", pady=5)
        
        tk.Label(digits_frame, text="จำนวนหลัก:", font=("Arial", 9)).pack(anchor="w")
        self.digits_var = tk.StringVar(value="4")
        digits_combo = ttk.Combobox(
            digits_frame,
            textvariable=self.digits_var,
            values=["4", "5", "6", "7", "8", "9", "10"],
            state="readonly",
            width=12,
            font=("Arial", 9)
        )
        digits_combo.pack(anchor="w", pady=(2, 0))
        
        # Sample format display
        self.sample_label = tk.Label(
            trcloud_frame, 
            text="ตัวอย่าง: 25100001", 
            font=("Arial", 8), 
            fg="#7f8c8d",
            wraplength=300
        )
        self.sample_label.pack(anchor="w", pady=(2, 5))
        
        # Bind format changes to update sample
        format_combo.bind("<<ComboboxSelected>>", self.update_sample_format)
        digits_combo.bind("<<ComboboxSelected>>", self.update_sample_format)
        
        # Enhancement option
        self.enhance_var = tk.BooleanVar(value=True)
        enhance_check = tk.Checkbutton(
            control_frame,
            text="เปิดใช้การปรับปรุงภาพ (Gentle Mode)",
            variable=self.enhance_var,
            font=("Arial", 10)
        )
        enhance_check.pack(anchor="w", pady=(10, 10))
        
        # Convert button
        self.convert_btn = tk.Button(
            control_frame,
            text="เริ่ม Convert",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            height=2,
            command=self.start_conversion
        )
        self.convert_btn.pack(fill="x", pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=(10, 0))
    
    def create_preview_panel(self, parent):
        """สร้างแผง Preview"""
        # Preview Frame
        preview_frame = tk.LabelFrame(parent, text="4. Preview ไฟล์ที่อัพโหลด", font=("Arial", 12, "bold"))
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create notebook for tabs
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Image preview tab
        self.image_tab = tk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.image_tab, text="Image Preview")
        
        self.image_canvas = tk.Canvas(self.image_tab, bg="white")
        image_scrollbar_v = tk.Scrollbar(self.image_tab, orient="vertical", command=self.image_canvas.yview)
        image_scrollbar_h = tk.Scrollbar(self.image_tab, orient="horizontal", command=self.image_canvas.xview)
        self.image_canvas.configure(yscrollcommand=image_scrollbar_v.set, xscrollcommand=image_scrollbar_h.set)
        
        self.image_canvas.pack(side="left", fill="both", expand=True)
        image_scrollbar_v.pack(side="right", fill="y")
        image_scrollbar_h.pack(side="bottom", fill="x")
        
        # OCR result tab
        self.result_tab = tk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.result_tab, text="OCR Result")
        
        self.result_text = scrolledtext.ScrolledText(
            self.result_tab,
            wrap=tk.WORD,
            font=("Consolas", 11),
            padx=10,
            pady=10
        )
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Structured data tab
        self.structured_tab = tk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.structured_tab, text="Structured Data")
        
        # Create structured data display
        self.create_structured_data_display(self.structured_tab)
    
    def create_structured_data_display(self, parent):
        """สร้างแผงแสดงข้อมูล structured data"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg="white")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Store reference for later updates
        self.structured_frame = scrollable_frame
        self.structured_canvas = canvas
        
        # Create initial empty display
        self.update_structured_display({})
    
    def create_validation_summary(self, parsed_data):
        """สร้างสรุปการตรวจสอบความครบถ้วนของข้อมูล"""
        if not parsed_data:
            return
        
        # กำหนดฟิลด์ที่สำคัญ
        required_fields = {
            'invoice_number': 'เลขที่ใบกำกับภาษี',
            'tax_id': 'เลขประจำตัวผู้เสียภาษี',
            'issue_date': 'วันที่เอกสาร',
            'organization': 'ชื่อองค์กร',
            'total_amount': 'ยอดรวมสุทธิ'
        }
        
        optional_fields = {
            'company_format': 'รหัสซีรี่ย์เอกสาร',
            'name': 'ชื่อลูกค้า',
            'address': 'ที่อยู่',
            'telephone': 'เบอร์โทรศัพท์',
            'subtotal': 'ยอดรวมก่อนภาษี',
            'vat_amount': 'ภาษีมูลค่าเพิ่ม',
            'due_date': 'กำหนดชำระ'
        }
        
        # ตรวจสอบฟิลด์ที่ขาด
        missing_required = []
        missing_optional = []
        filled_fields = 0
        total_fields = len(required_fields) + len(optional_fields)
        
        for field, label in required_fields.items():
            value = parsed_data.get(field, '')
            if not value or str(value).strip() == '' or str(value).strip() == '0.00':
                missing_required.append(label)
            else:
                filled_fields += 1
        
        for field, label in optional_fields.items():
            value = parsed_data.get(field, '')
            if not value or str(value).strip() == '' or str(value).strip() == '0.00':
                missing_optional.append(label)
            else:
                filled_fields += 1
        
        # คำนวณเปอร์เซ็นต์ความครบถ้วน
        completion_rate = (filled_fields / total_fields) * 100
        
        # สร้าง Validation Summary Frame
        validation_frame = tk.Frame(self.structured_frame, bg="#ecf0f1", relief="raised", bd=2)
        validation_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Header
        if missing_required:
            header_color = "#e74c3c"  # Red
            header_text = "⚠️ ตรวจพบข้อมูลสำคัญขาดหาย"
        elif missing_optional:
            header_color = "#f39c12"  # Orange
            header_text = "⚡ ข้อมูลไม่ครบถ้วน"
        else:
            header_color = "#27ae60"  # Green
            header_text = "✅ ข้อมูลครบถ้วน"
        
        validation_header = tk.Label(
            validation_frame,
            text=header_text,
            font=("Arial", 12, "bold"),
            bg=header_color,
            fg="white",
            pady=8
        )
        validation_header.pack(fill="x", padx=2, pady=2)
        
        # Completion rate
        rate_frame = tk.Frame(validation_frame, bg="#ecf0f1")
        rate_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            rate_frame,
            text=f"ความครบถ้วน: {completion_rate:.1f}% ({filled_fields}/{total_fields} ฟิลด์)",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1"
        ).pack(anchor="w")
        
        # Missing required fields
        if missing_required:
            missing_req_frame = tk.Frame(validation_frame, bg="#ecf0f1")
            missing_req_frame.pack(fill="x", padx=10, pady=2)
            
            tk.Label(
                missing_req_frame,
                text="❌ ฟิลด์สำคัญที่ขาดหาย:",
                font=("Arial", 9, "bold"),
                fg="#e74c3c",
                bg="#ecf0f1"
            ).pack(anchor="w")
            
            missing_text = ", ".join(missing_required)
            tk.Label(
                missing_req_frame,
                text=f"   {missing_text}",
                font=("Arial", 9),
                fg="#c0392b",
                bg="#ecf0f1",
                wraplength=600,
                justify="left"
            ).pack(anchor="w", padx=(10, 0))
        
        # Missing optional fields
        if missing_optional:
            missing_opt_frame = tk.Frame(validation_frame, bg="#ecf0f1")
            missing_opt_frame.pack(fill="x", padx=10, pady=2)
            
            tk.Label(
                missing_opt_frame,
                text="⚠️ ฟิลด์เสริมที่ขาดหาย:",
                font=("Arial", 9, "bold"),
                fg="#f39c12",
                bg="#ecf0f1"
            ).pack(anchor="w")
            
            # แสดงเฉพาะ 5 ฟิลด์แรก
            display_optional = missing_optional[:5]
            if len(missing_optional) > 5:
                display_optional.append(f"และอีก {len(missing_optional) - 5} ฟิลด์")
            
            missing_text = ", ".join(display_optional)
            tk.Label(
                missing_opt_frame,
                text=f"   {missing_text}",
                font=("Arial", 9),
                fg="#d68910",
                bg="#ecf0f1",
                wraplength=600,
                justify="left"
            ).pack(anchor="w", padx=(10, 0))
        
        # Recommendations
        if missing_required or missing_optional:
            rec_frame = tk.Frame(validation_frame, bg="#ecf0f1")
            rec_frame.pack(fill="x", padx=10, pady=(2, 8))
            
            recommendations = []
            if missing_required:
                recommendations.append("ตรวจสอบคุณภาพรูปภาพต้นฉบับ")
                recommendations.append("ลองเปลี่ยน OCR Engine")
            if len(missing_optional) > 3:
                recommendations.append("ใช้โหมด Enhancement")
            
            if recommendations:
                tk.Label(
                    rec_frame,
                    text="💡 คำแนะนำ:",
                    font=("Arial", 9, "bold"),
                    fg="#2980b9",
                    bg="#ecf0f1"
                ).pack(anchor="w")
                
                for i, rec in enumerate(recommendations[:3], 1):
                    tk.Label(
                        rec_frame,
                        text=f"   {i}. {rec}",
                        font=("Arial", 9),
                        fg="#34495e",
                        bg="#ecf0f1"
                    ).pack(anchor="w", padx=(10, 0))

    def update_structured_display(self, parsed_data):
        """อัปเดตการแสดงผล structured data"""
        # Clear existing widgets
        for widget in self.structured_frame.winfo_children():
            widget.destroy()
        
        if not parsed_data:
            # Show empty state
            empty_label = tk.Label(
                self.structured_frame,
                text="ยังไม่มีข้อมูลที่แยกได้\nกรุณาประมวลผลไฟล์ก่อน",
                font=("Arial", 12),
                fg="#7f8c8d"
            )
            empty_label.pack(pady=50)
            return
        
        # Field labels in Thai
        field_labels = {
            'issue_date': 'วันที่เอกสาร',
            'company_format': 'รหัสซีรี่ย์เอกสาร',
            'invoice_number': 'เลขที่ใบกำกับ',
            'reference': 'เอกสารอ้างอิง',
            'tax_option': 'ประเภทภาษี',
            'name': 'ชื่อ',
            'organization': 'ชื่อองค์กร',
            'address': 'ที่อยู่',
            'telephone': 'โทรศัพท์',
            'tax_id': 'เลขประจำตัวผู้เสียภาษี',
            'due_date': 'กำหนดชำระ',
            'subtotal': 'ยอดรวมก่อนภาษี',
            'vat_amount': 'ภาษีมูลค่าเพิ่ม',
            'total_amount': 'ยอดรวมสุทธิ',
            'vat_rate': 'อัตราภาษี (%)'
        }
        
        # Create header
        header_label = tk.Label(
            self.structured_frame,
            text="ข้อมูลที่แยกจากใบภาษี",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            pady=10
        )
        header_label.pack(fill="x", padx=5, pady=(5, 10))
        
        # Add validation summary
        self.create_validation_summary(parsed_data)
        
        # Display fields in organized sections
        sections = [
            ("ข้อมูลเอกสาร", ['issue_date', 'company_format', 'invoice_number', 'reference', 'due_date']),
            ("ข้อมูลผู้เสียภาษี", ['name', 'organization', 'address', 'telephone', 'tax_id']),
            ("ข้อมูลการเงิน", ['tax_option', 'subtotal', 'vat_rate', 'vat_amount', 'total_amount'])
        ]
        
        for section_title, fields in sections:
            # Section header
            section_frame = tk.Frame(self.structured_frame, bg="#ecf0f1", relief="raised", bd=1)
            section_frame.pack(fill="x", padx=5, pady=(10, 0))
            
            section_label = tk.Label(
                section_frame,
                text=section_title,
                font=("Arial", 12, "bold"),
                bg="#ecf0f1"
            )
            section_label.pack(pady=5)
            
            # Fields in this section
            for field in fields:
                # แสดงทั้งฟิลด์ที่มีและไม่มีข้อมูล
                field_frame = tk.Frame(self.structured_frame)
                field_frame.pack(fill="x", padx=10, pady=2)
                
                # Field label
                label_text = field_labels.get(field, field)
                
                # ตรวจสอบว่าเป็นฟิลด์สำคัญหรือไม่
                required_fields = ['invoice_number', 'tax_id', 'issue_date', 'organization', 'total_amount']
                is_required = field in required_fields
                
                # ตรวจสอบว่ามีข้อมูลหรือไม่
                value = parsed_data.get(field, '') if field in parsed_data else ''
                is_empty = not value or str(value).strip() == '' or str(value).strip() == '0.00'
                
                # กำหนดสีตาม status
                if is_empty and is_required:
                    label_color = "#e74c3c"  # Red - Missing required
                    bg_color = "#fadbd8"
                    status_icon = "❌"
                elif is_empty:
                    label_color = "#f39c12"  # Orange - Missing optional  
                    bg_color = "#fdeaa7"
                    status_icon = "⚠️"
                else:
                    label_color = "#27ae60"  # Green - Has data
                    bg_color = "white"
                    status_icon = "✅"
                
                # Label with status icon
                label = tk.Label(
                    field_frame,
                    text=f"{status_icon} {label_text}:",
                    font=("Arial", 10, "bold"),
                    fg=label_color,
                    width=22,
                    anchor="w"
                )
                label.pack(side="left")
                
                # Field value
                if is_empty:
                    display_value = "ไม่พบข้อมูล" if is_required else "ไม่มีข้อมูล"
                    value_font = ("Arial", 10, "italic")
                    value_color = "#7f8c8d"
                else:
                    display_value = str(value)
                    # Truncate long values
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    value_font = ("Arial", 10)
                    value_color = "#2c3e50"
                
                value_label = tk.Label(
                    field_frame,
                    text=display_value,
                    font=value_font,
                    fg=value_color,
                    bg=bg_color,
                    relief="sunken",
                    anchor="w",
                    padx=5
                )
                value_label.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Add export button
        export_frame = tk.Frame(self.structured_frame)
        export_frame.pack(fill="x", padx=5, pady=20)
        
        # Export buttons frame
        export_buttons_frame = tk.Frame(export_frame)
        export_buttons_frame.pack(pady=10)
        
        export_json_btn = tk.Button(
            export_buttons_frame,
            text="Export JSON",
            font=("Arial", 9, "bold"),
            bg="#27ae60",
            fg="white",
            width=12,
            command=lambda: self.export_structured_data(parsed_data)
        )
        export_json_btn.pack(side="left", padx=(0, 5))
        
        export_excel_btn = tk.Button(
            export_buttons_frame,
            text="Export Excel",
            font=("Arial", 9, "bold"),
            bg="#3498db",
            fg="white",
            width=12,
            command=lambda: self.export_to_excel(parsed_data)
        )
        export_excel_btn.pack(side="left", padx=(5, 5))
        
        # เพิ่มปุ่มเปิดโฟลเดอร์ Export
        open_folder_btn = tk.Button(
            export_buttons_frame,
            text="📁 เปิดโฟลเดอร์",
            font=("Arial", 9, "bold"),
            bg="#9b59b6",
            fg="white",
            width=12,
            command=self.open_export_folder
        )
        open_folder_btn.pack(side="left", padx=(0, 0))
    
    def export_structured_data(self, data):
        """Export structured data เป็นไฟล์ JSON"""
        try:
            from tkinter import filedialog
            import json
            from datetime import datetime
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                title="บันทึกข้อมูล Structured Data",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.log_debug(f"Exported structured data to: {filename}")
                messagebox.showinfo("เสร็จสิ้น", f"บันทึกข้อมูลเรียบร้อยแล้ว\n{filename}")
        
        except Exception as e:
            self.log_debug(f"Error exporting structured data: {e}")
            messagebox.showerror("Error", f"ไม่สามารถบันทึกข้อมูลได้: {e}")
    
    def export_to_excel(self, data):
        """Export structured data ไปยัง Excel template"""
        try:
            if not data:
                messagebox.showwarning("Warning", "ไม่มีข้อมูลที่จะส่งออก")
                return
            
            # Create a mock parsed_result structure for Excel export
            parsed_result = {
                'parsed_data': data,
                'metadata': {
                    'source_file': self.selected_file or 'unknown',
                    'ocr_engine': self.engine_var.get(),
                    'enhancement_used': self.enhance_var.get(),
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            from excel_exporter import ExcelExporter
            from pathlib import Path
            exporter = ExcelExporter()
            excel_file = exporter.create_new_excel_file(parsed_result)
            
            self.log_debug(f"สร้างไฟล์ Excel ใหม่: {Path(excel_file).name}")
            
            # Ask if user wants to open Excel file
            result = messagebox.askyesno(
                "สร้างไฟล์ Excel เรียบร้อย", 
                f"สร้างไฟล์ Excel ใหม่เรียบร้อยแล้ว\n\nไฟล์: {Path(excel_file).name}\nตำแหน่ง: {Path(excel_file).parent}\n\nต้องการเปิดไฟล์หรือไม่?"
            )
            
            if result:
                import subprocess
                subprocess.run(['start', excel_file], shell=True, check=False)
        
        except Exception as e:
            self.log_debug(f"Error exporting to Excel: {e}")
            messagebox.showerror("Error", f"ไม่สามารถส่งออกไปยัง Excel ได้: {e}")

    def open_export_folder(self):
        """เปิดโฟลเดอร์ Export ใน File Explorer"""
        try:
            export_path = Path(__file__).parent / "Export"
            if export_path.exists():
                import subprocess
                subprocess.run(['start', str(export_path)], shell=True, check=False)
                self.log_debug(f"เปิดโฟลเดอร์: {export_path}")
            else:
                # สร้างโฟลเดอร์หากไม่มี
                export_path.mkdir(exist_ok=True)
                subprocess.run(['start', str(export_path)], shell=True, check=False)
                self.log_debug(f"สร้างและเปิดโฟลเดอร์: {export_path}")
                
        except Exception as e:
            self.log_debug(f"Error opening export folder: {e}")
            messagebox.showerror("Error", f"ไม่สามารถเปิดโฟลเดอร์ Export ได้: {e}")

    def update_sample_format(self, event=None):
        """อัปเดตตัวอย่างรูปแบบเลข"""
        try:
            from datetime import datetime
            
            format_type = self.number_format_var.get()
            digits = int(self.digits_var.get())
            
            # สร้างตัวอย่าง based on current date
            current_date = datetime.now()
            
            if format_type == "YYx":
                prefix = current_date.strftime("%y")
            elif format_type == "YYMMx":
                prefix = current_date.strftime("%y%m")
            elif format_type == "YYMMDDx":
                prefix = current_date.strftime("%y%m%d")
            else:  # "x"
                prefix = ""
            
            # สร้าง running number ตัวอย่าง
            running_number = "1".zfill(digits)
            sample = f"{prefix}{running_number}"
            
            self.sample_label.config(text=f"ตัวอย่าง: {sample}")
            self.log_debug(f"อัปเดตรูปแบบเลข: {format_type} + {digits} หลัก = {sample}")
            
        except Exception as e:
            self.sample_label.config(text="ตัวอย่าง: ข้อผิดพลาด")
            self.log_debug(f"Error updating sample format: {e}")

    def get_trcloud_format_info(self):
        """ดึงข้อมูล TRCloud format สำหรับส่งไป OCR"""
        return {
            'format_type': self.number_format_var.get(),
            'digits': int(self.digits_var.get()),
            'prefix_enabled': True
        }

    def create_debug_panel(self, parent):
        """สร้างแผง Debug"""
        # Debug Frame
        debug_frame = tk.LabelFrame(parent, text="3. Dashboard Debug การทำงาน", font=("Arial", 12, "bold"))
        debug_frame.pack(fill="x", pady=(0, 10))
        
        # Debug log
        self.debug_text = scrolledtext.ScrolledText(
            debug_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
            padx=10,
            pady=5
        )
        self.debug_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Clear debug button
        clear_debug_btn = tk.Button(
            debug_frame,
            text="ล้าง Debug Log",
            font=("Arial", 9),
            bg="#95a5a6",
            fg="white",
            command=self.clear_debug
        )
        clear_debug_btn.pack(pady=(0, 10))
        
        # Initial debug message
        self.log_debug("OCR Thai Tax Documents - System Ready")
        self.log_debug("กรุณาเลือกไฟล์ PDF หรือรูปภาพเพื่อเริ่มต้น")
    
    def create_status_bar(self):
        """สร้าง Status Bar"""
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor="w",
            font=("Arial", 9),
            padx=10
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def select_file(self):
        """เลือกไฟล์"""
        filetypes = [
            ("All Supported", "*.pdf;*.png;*.jpg;*.jpeg;*.tiff;*.bmp"),
            ("PDF Files", "*.pdf"),
            ("Image Files", "*.png;*.jpg;*.jpeg;*.tiff;*.bmp"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="เลือกไฟล์ PDF หรือรูปภาพ",
            filetypes=filetypes
        )
        
        if filename:
            self.selected_file = filename
            self.file_label.config(
                text=f"ไฟล์ที่เลือก: {os.path.basename(filename)}",
                fg="#2c3e50"
            )
            self.log_debug(f"เลือกไฟล์: {filename}")
            self.update_status(f"เลือกไฟล์: {os.path.basename(filename)}")
            
            # Show preview
            self.show_file_preview()
    
    def clear_file(self):
        """ล้างไฟล์ที่เลือก"""
        self.selected_file = None
        self.file_label.config(
            text="ยังไม่ได้เลือกไฟล์",
            fg="#7f8c8d"
        )
        self.clear_preview()
        self.log_debug("ล้างการเลือกไฟล์")
        self.update_status("Ready")
    
    def show_file_preview(self):
        """แสดง preview ของไฟล์"""
        if not self.selected_file:
            return
        
        try:
            file_path = Path(self.selected_file)
            
            if file_path.suffix.lower() == '.pdf':
                self.log_debug("แสดง preview PDF (แปลงหน้าแรกเป็นรูปภาพ)")
                # For PDF, convert first page to image for preview
                if self.ocr_system and self.ocr_system.pdf_converter:
                    try:
                        # Convert first page only for preview
                        temp_images = self.ocr_system.pdf_converter.convert_pdf_to_images(
                            self.selected_file
                        )
                        if temp_images:
                            self.display_image_preview(temp_images[0])
                    except Exception as e:
                        self.log_debug(f"ไม่สามารถแสดง PDF preview ได้: {e}")
            else:
                # For image files
                self.display_image_preview(self.selected_file)
                
        except Exception as e:
            self.log_debug(f"Error showing preview: {e}")
    
    def display_image_preview(self, image_path):
        """แสดงรูปภาพใน preview"""
        try:
            # Clear previous preview
            self.image_canvas.delete("all")
            
            # Load and resize image for preview
            pil_image = Image.open(image_path)
            
            # Calculate size to fit canvas
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300  # Default size
            
            # Resize image to fit canvas while maintaining aspect ratio
            img_width, img_height = pil_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.preview_image = ImageTk.PhotoImage(pil_image)
            
            # Display on canvas
            self.image_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.preview_image,
                anchor="center"
            )
            
            self.log_debug(f"แสดง preview รูปภาพ: {os.path.basename(image_path)}")
            
        except Exception as e:
            self.log_debug(f"ไม่สามารถแสดงรูปภาพได้: {e}")
    
    def clear_preview(self):
        """ล้าง preview"""
        self.image_canvas.delete("all")
        self.result_text.delete(1.0, tk.END)
    
    def start_conversion(self):
        """เริ่มการ Convert"""
        if not self.selected_file:
            messagebox.showerror("Error", "กรุณาเลือกไฟล์ก่อน")
            return
        
        if not self.ocr_system:
            messagebox.showerror("Error", "ระบบ OCR ยังไม่พร้อม กรุณารอสักครู่")
            return
        
        if self.processing:
            messagebox.showwarning("Warning", "กำลังประมวลผลอยู่ กรุณารอ")
            return
        
        # Start conversion in background thread
        self.processing = True
        self.convert_btn.config(state="disabled", text="กำลังประมวลผล...")
        self.progress.start()
        
        thread = threading.Thread(target=self.run_ocr_conversion, daemon=True)
        thread.start()
    
    def run_ocr_conversion(self):
        """รัน OCR conversion ใน background thread"""
        try:
            engine = self.engine_var.get()
            enhance = self.enhance_var.get()
            trcloud_format = self.get_trcloud_format_info()
            
            self.log_debug(f"เริ่มการประมวลผลด้วย {engine} engine")
            self.log_debug(f"การปรับปรุงภาพ: {'เปิด' if enhance else 'ปิด'}")
            self.log_debug(f"รูปแบบเลข TRCloud: {trcloud_format['format_type']} + {trcloud_format['digits']} หลัก")
            
            # Process file with parsing and TRCloud format info
            self.log_debug("เริ่มประมวลผลและแยกข้อมูลใบภาษี...")
            result = self.ocr_system.process_and_parse_invoice(
                self.selected_file, 
                engine=engine, 
                enhance_images=enhance,
                trcloud_format=trcloud_format
            )
            
            # Update UI in main thread
            self.root.after(0, lambda: self.on_conversion_complete(result))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.on_conversion_error(error_msg))
    
    def on_conversion_complete(self, result):
        """เมื่อ conversion เสร็จสิ้น"""
        from datetime import datetime
        
        self.processing = False
        self.progress.stop()
        self.convert_btn.config(state="normal", text="เริ่ม Convert")
        
        # Check if result is parsed data (dict) or plain text (str)
        if isinstance(result, dict):
            # Display raw OCR text
            ocr_text = result.get('raw_ocr_text', '')
            parsed_data = result.get('parsed_data', {})
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, ocr_text)
            
            # Update structured data display
            self.update_structured_display(parsed_data)
            
            # Switch to structured data tab
            self.preview_notebook.select(self.structured_tab)
            
            # Save results
            try:
                text_file, json_file, excel_file = self.ocr_system.save_parsed_results(result)
                
                self.log_debug(f"ประมวลผลเสร็จสิ้น!")
                self.log_debug(f"OCR Text: {len(ocr_text)} ตัวอักษร")
                
                # วิเคราะห์ความครบถ้วนของข้อมูล
                filled_count = len([v for v in parsed_data.values() if v and str(v).strip() and str(v).strip() != '0.00'])
                total_fields = len(parsed_data)
                completion_rate = (filled_count / total_fields) * 100 if total_fields > 0 else 0
                
                # ตรวจสอบฟิลด์สำคัญที่ขาด
                required_fields = ['invoice_number', 'tax_id', 'issue_date', 'organization', 'total_amount']
                missing_required = []
                for field in required_fields:
                    value = parsed_data.get(field, '')
                    if not value or str(value).strip() == '' or str(value).strip() == '0.00':
                        missing_required.append(field)
                
                self.log_debug(f"Structured Data: {filled_count}/{total_fields} ฟิลด์ ({completion_rate:.1f}%)")
                
                if missing_required:
                    self.log_debug(f"⚠️ ฟิลด์สำคัญที่ขาดหาย: {', '.join(missing_required)}")
                else:
                    self.log_debug("✅ ฟิลด์สำคัญครบถ้วน")
                
                self.log_debug(f"บันทึกที่: {text_file} และ {json_file}")
                if excel_file:
                    self.log_debug(f"ส่งออกไปยัง Excel: {excel_file}")
                
                status_msg = f"เสร็จสิ้น - ครบถ้วน {completion_rate:.1f}%"
                if missing_required:
                    status_msg += f" (ขาดฟิลด์สำคัญ {len(missing_required)} ฟิลด์)"
                self.update_status(status_msg)
                
                message = (f"ประมวลผลเสร็จสิ้น!\n"
                          f"OCR Text: {len(ocr_text)} ตัวอักษร\n"
                          f"Structured Data: {len([v for v in parsed_data.values() if v])} ฟิลด์\n"
                          f"บันทึกไฟล์: {Path(json_file).name}")
                
                if excel_file:
                    message += f"\nExcel: {Path(excel_file).name}"
                
                messagebox.showinfo("เสร็จสิ้น", message)
                
            except Exception as e:
                self.log_debug(f"ไม่สามารถบันทึกผลลัพธ์: {e}")
        
        else:
            # Handle plain text result (backward compatibility)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, str(result))
            
            # Switch to result tab
            self.preview_notebook.select(self.result_tab)
            
            # Save result to file
            try:
                output_dir = Path("outputs")
                output_dir.mkdir(exist_ok=True)
                
                if self.selected_file:
                    filename = Path(self.selected_file).stem
                    output_file = output_dir / f"{filename}_ocr_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(str(result))
                    
                    self.log_debug(f"บันทึกผลลัพธ์ที่: {output_file}")
                
            except Exception as e:
                self.log_debug(f"ไม่สามารถบันทึกผลลัพธ์: {e}")
    
    def on_conversion_error(self, error_msg):
        """เมื่อเกิดข้อผิดพลาดในการ convert"""
        self.processing = False
        self.progress.stop()
        self.convert_btn.config(state="normal", text="เริ่ม Convert")
        
        self.log_debug(f"เกิดข้อผิดพลาด: {error_msg}")
        self.update_status("เกิดข้อผิดพลาด")
        messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการประมวลผล:\n{error_msg}")
    
    def log_debug(self, message):
        """เพิ่มข้อความใน debug log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Add to debug text widget
        self.debug_text.insert(tk.END, log_message)
        self.debug_text.see(tk.END)  # Scroll to bottom
        
        # Also log to file
        logger.info(message)
    
    def clear_debug(self):
        """ล้าง debug log"""
        self.debug_text.delete(1.0, tk.END)
        self.log_debug("Debug log cleared")
    
    def update_status(self, message):
        """อัปเดต status bar"""
        self.status_bar.config(text=message)
    
    def logout(self):
        """Logout"""
        if messagebox.askyesno("Logout", "คุณต้องการออกจากระบบหรือไม่?"):
            logger.info("User logged out")
            self.root.destroy()
            # Restart login window
            login_window = LoginWindow()
            login_window.run()
    
    def run(self):
        """เรียกใช้แอปพลิเคชันหลัก"""
        self.root.mainloop()


def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    try:
        # Start with login window
        login_window = LoginWindow()
        login_window.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"เกิดข้อผิดพลาดในโปรแกรม: {e}")


if __name__ == "__main__":
    main()