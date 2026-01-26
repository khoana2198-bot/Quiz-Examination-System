import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from datetime import date, datetime
import calendar
import database
from models import User, Admin, Student, Subject, Question, Exam, Result
from services import UserService, ExamService, ResultService, MasterDataService

class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Examination System V8")
        self.geometry("1024x768")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        database.init_db()
        database.seed_data()
        self.user_service = UserService()
        self.exam_service = ExamService()
        self.result_service = ResultService()
        self.master_service = MasterDataService()
        self.current_user = None
        
        self.container = tk.Frame(self)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (LoginFrame, RegisterFrame, AdminDashboard, StudentDashboard):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"): frame.on_show()

    def set_user(self, user): self.current_user = user
    def logout(self):
        self.current_user = None
        self.show_frame("LoginFrame")

BTN_FONT = ("Arial", 11, "bold")

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        wrapper = tk.Frame(self)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(wrapper, text="Quiz System Login", font=("Arial", 24)).pack(pady=30)
        f = tk.Frame(wrapper)
        f.pack(pady=10)
        tk.Label(f, text="Username", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
        self.username_entry = tk.Entry(f, font=("Arial", 12))
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(f, text="Password", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
        self.password_entry = tk.Entry(f, show="*", font=("Arial", 12))
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(wrapper, text="Login", command=self.login, width=20, bg="#4CAF50", fg="white", font=BTN_FONT, pady=10).pack(pady=10)
        tk.Button(wrapper, text="Register New Student", command=lambda: controller.show_frame("RegisterFrame"), width=20, font=BTN_FONT, pady=5).pack(pady=5)

    def login(self):
        user = self.controller.user_service.login(self.username_entry.get(), self.password_entry.get())
        if user:
            self.controller.set_user(user)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            if user.role == "admin": self.controller.show_frame("AdminDashboard")
            else: self.controller.show_frame("StudentDashboard")
        else: messagebox.showerror("Error", "Invalid Credentials")

class RegisterFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        wrapper = tk.Frame(self)
        wrapper.pack(expand=True)
        tk.Label(wrapper, text="Student Registration", font=("Arial", 20)).pack(pady=20)
        self.form_frame = tk.Frame(wrapper)
        self.form_frame.pack()
        self.entries = {}
        fields = [("Username (*)", "username"), ("Password (*)", "password"), ("Confirm Password (*)", "confirm_password"), ("Full Name (*)", "full_name"), ("Date of Birth (YYYY-MM-DD)", "dob")]
        for idx, (label, key) in enumerate(fields):
            tk.Label(self.form_frame, text=label, font=("Arial", 11)).grid(row=idx, column=0, padx=10, pady=10, sticky="e")
            entry = tk.Entry(self.form_frame, show="*" if "Password" in label else None, font=("Arial", 11))
            entry.grid(row=idx, column=1, padx=10, pady=10)
            self.entries[key] = entry
        tk.Button(wrapper, text="Register", command=self.register, bg="#2196F3", fg="white", font=BTN_FONT, pady=10).pack(pady=20)
        tk.Button(wrapper, text="Back", command=lambda: controller.show_frame("LoginFrame"), font=BTN_FONT, pady=5).pack()

    def register(self):
        data = {k: v.get() for k, v in self.entries.items()}
        if not all(data[k] for k in ["username", "password", "confirm_password", "full_name"]):
            messagebox.showwarning("Validation", "Please fill in all mandatory (*) fields.")
            return
        try:
            self.controller.user_service.register_student(data["username"], data["password"], data["confirm_password"], data["full_name"], data["dob"])
            messagebox.showinfo("Success", "Registration Successful! Please Login.")
            for e in self.entries.values(): e.delete(0, tk.END)
            self.controller.show_frame("LoginFrame")
        except ValueError as e: messagebox.showerror("Validation Error", str(e))
        except Exception as e: messagebox.showerror("Error", str(e))

class AdminDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=1)
        header = tk.Frame(self, bg="#2196F3", height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        tk.Label(header, text="Teacher Dashboard", font=("Arial", 18, "bold"), bg="#2196F3", fg="white").pack(side="left", padx=20)
        tk.Button(header, text="Logout", command=self.controller.logout, font=("Arial", 10)).pack(side="right", padx=20)
        self.main_split = tk.Frame(self)
        self.main_split.grid(row=1, column=0, sticky="nsew")
        self.main_split.grid_columnconfigure(1, weight=1)
        self.main_split.grid_rowconfigure(0, weight=1)
        self.sidebar = tk.Frame(self.main_split, width=220, bg="#E0E0E0")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        menus = [
            ("Manage Subjects", self.show_subjects),
            ("Manage Questions", self.show_questions),
            ("Create Exam", self.show_create_exam),
            ("Exam Management", self.show_exam_management),
        ]
        for text, cmd in menus:
            tk.Button(self.sidebar, text=text, command=cmd, font=("Arial", 11), bg="white", relief="flat", padx=10, pady=10).pack(fill="x", pady=5, padx=5)

        self.content_area = tk.Frame(self.main_split)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ManageSubjectsFrame, ManageQuestionsFrame, CreateExamFrame, ExamManagementFrame):
            page_name = F.__name__
            frame = F(parent=self.content_area, controller=self.controller)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_subjects()

    def switch_content(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"): frame.on_show()

    def show_subjects(self): self.switch_content("ManageSubjectsFrame")
    def show_questions(self): self.switch_content("ManageQuestionsFrame")
    def show_create_exam(self): self.switch_content("CreateExamFrame")
    def show_exam_management(self): self.switch_content("ExamManagementFrame")
    
class ManageSubjectsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Manage Subjects", font=("Arial", 16, "bold")).pack(pady=10)
        f = tk.Frame(self)
        f.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(f)
        self.listbox = tk.Listbox(f, selectmode=tk.EXTENDED, yscrollcommand=sb.set, font=("Arial", 11))
        sb.config(command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        bf = tk.Frame(self)
        bf.pack(pady=20)
        tk.Button(bf, text="Refresh", command=self.refresh, font=BTN_FONT, pady=5).pack(side="left", padx=5)
        self.entry_name = tk.Entry(bf, font=("Arial", 12))
        self.entry_name.pack(side="left", padx=5)
        tk.Button(bf, text="Add", command=self.add, bg="#4CAF50", fg="white", font=BTN_FONT, pady=5).pack(side="left", padx=5)
        tk.Button(bf, text="Delete", command=self.delete, bg="#F44336", fg="white", font=BTN_FONT, pady=5).pack(side="left", padx=5)

    def on_show(self): self.refresh()
    def refresh(self):
        self.listbox.delete(0, tk.END)
        self.subjects = self.controller.master_service.get_all_subjects()
        for idx, s in enumerate(self.subjects, 1): self.listbox.insert(tk.END, f"{idx} - {s.subject_name}")
    def add(self):
        try: self.controller.master_service.add_subject(self.entry_name.get()); self.refresh(); self.entry_name.delete(0, tk.END)
        except Exception as e: messagebox.showerror("Error", str(e))
    def delete(self):
        sel = self.listbox.curselection()
        if not sel or not messagebox.askyesno("Confirm", "Delete selected?"): return
        for i in reversed(sel): self.controller.master_service.delete_subject(self.subjects[i].subject_id)
        self.refresh()

class ManageQuestionsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Manage Questions", font=("Arial", 16, "bold")).pack(pady=10)
        ff = tk.Frame(self)
        ff.pack(fill="x")
        tk.Label(ff, text="Subject:", font=("Arial", 11)).pack(side="left")
        self.cb = ttk.Combobox(ff, state="readonly", font=("Arial", 11)); self.cb.pack(side="left"); self.cb.bind("<<ComboboxSelected>>", self.refresh)
        tk.Button(ff, text="Import CSV", command=self.import_csv, bg="#FF9800", fg="white", font=BTN_FONT, pady=5).pack(side="right")
        self.lb = tk.Listbox(self, selectmode=tk.EXTENDED, font=("Consolas", 10))
        self.lb.pack(fill="both", expand=True, padx=10, pady=5)
        af = tk.Frame(self); af.pack(pady=10)
        tk.Button(af, text="Add", command=self.add, font=BTN_FONT, pady=5).pack(side="left", padx=5)
        tk.Button(af, text="Delete", command=self.delete, bg="#F44336", fg="white", font=BTN_FONT, pady=5).pack(side="left", padx=5)

    def on_show(self): 
        self.subs = self.controller.master_service.get_all_subjects()
        self.cb['values'] = [s.subject_name for s in self.subs]
        if self.subs and not self.cb.get(): self.cb.current(0)
        self.refresh()
    def refresh(self, e=None):
        self.lb.delete(0, tk.END)
        s = next((x for x in self.subs if x.subject_name == self.cb.get()), None)
        if not s: return
        self.qs = self.controller.master_service.get_questions_by_subject(s.subject_id)
        for q in self.qs: self.lb.insert(tk.END, f"[{q.difficulty_level.upper()}] {q.content}")
    def delete(self):
        sel = self.lb.curselection()
        if not sel or not messagebox.askyesno("Confirm", "Delete?"): return
        for i in reversed(sel): self.controller.master_service.delete_question(self.qs[i].question_id)
        self.refresh()
    def import_csv(self):
        fp = filedialog.askopenfilename()
        if fp: 
            try: self.controller.master_service.import_questions_from_csv(fp); messagebox.showinfo("OK", "Imported"); self.on_show()
            except Exception as e: messagebox.showerror("Error", str(e))
    def add(self):
        win = tk.Toplevel(self)
        win.title("Add New Question")
        win.geometry("600x700")
        
        main_frame = tk.Frame(win, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Subject:", font=BTN_FONT).pack(anchor="w")
        cb_sub = ttk.Combobox(main_frame, values=[s.subject_name for s in self.subs], state="readonly", font=("Arial", 11))
        cb_sub.pack(fill="x", pady=5)
        if self.cb.get(): cb_sub.set(self.cb.get())
        
        tk.Label(main_frame, text="Question Content:", font=BTN_FONT).pack(anchor="w", pady=(10,0))
        txt_content = tk.Text(main_frame, height=5, font=("Arial", 11))
        txt_content.pack(fill="x", pady=5)
        
        entries = {}
        for opt in ['a', 'b', 'c', 'd']:
            tk.Label(main_frame, text=f"Option {opt.upper()}:", font=BTN_FONT).pack(anchor="w")
            e = tk.Entry(main_frame, font=("Arial", 11))
            e.pack(fill="x", pady=2)
            entries[opt] = e
            
        tk.Label(main_frame, text="Correct Answer:", font=BTN_FONT).pack(anchor="w", pady=(10,0))
        cb_correct = ttk.Combobox(main_frame, values=['a', 'b', 'c', 'd'], state="readonly", font=("Arial", 11))
        cb_correct.pack(fill="x", pady=5)
        
        tk.Label(main_frame, text="Difficulty:", font=BTN_FONT).pack(anchor="w", pady=(10,0))
        cb_level = ttk.Combobox(main_frame, values=['easy', 'medium', 'hard'], state="readonly", font=("Arial", 11))
        cb_level.pack(fill="x", pady=5)
        cb_level.current(0)

        def save():
            sub_name = cb_sub.get()
            if not sub_name:
                messagebox.showwarning("Warning", "Please select a Subject")
                return
            
            subject = next((s for s in self.subs if s.subject_name == sub_name), None)
            content = txt_content.get("1.0", tk.END).strip()
            if not content or not cb_correct.get():
                messagebox.showwarning("Warning", "Content and Correct Answer required")
                return

            try:
                q = Question(0, subject.subject_id, content, 
                             entries['a'].get(), entries['b'].get(), entries['c'].get(), entries['d'].get(), 
                             cb_correct.get(), cb_level.get())
                self.controller.master_service.add_question(q)
                self.refresh()
                win.destroy()
                messagebox.showinfo("Success", "Question Added")
            except Exception as e: messagebox.showerror("Error", str(e))
            
        tk.Button(main_frame, text="Save Question", command=save, bg="#4CAF50", fg="white", font=BTN_FONT, pady=10).pack(fill="x", pady=20)

class CreateExamFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Create Exam", font=("Arial", 16, "bold")).pack(pady=10)
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        self.manual = ManualExamFrame(nb, controller); nb.add(self.manual, text="Manual")
        self.auto = AutoExamFrame(nb, controller); nb.add(self.auto, text="Auto")
    def on_show(self): self.manual.on_show(); self.auto.on_show()

import calendar

class DateTimePicker(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.output_frames = []
        
        # Variables
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        
        # Layout
        # DD/MM/YYYY  -  HH:MM
        
        # Date
        tk.Label(self, text="Date:").pack(side="left")
        
        self.cb_day = ttk.Combobox(self, textvariable=self.day_var, width=3, state="readonly")
        self.cb_day.pack(side="left")
        tk.Label(self, text="/").pack(side="left")
        
        self.cb_month = ttk.Combobox(self, textvariable=self.month_var, values=[f"{i:02d}" for i in range(1, 13)], width=3, state="readonly")
        self.cb_month.pack(side="left")
        tk.Label(self, text="/").pack(side="left")

        current_year = datetime.now().year
        years = [str(i) for i in range(current_year, current_year + 6)]
        self.cb_year = ttk.Combobox(self, textvariable=self.year_var, values=years, width=5, state="readonly")
        self.cb_year.pack(side="left")

        # Time
        tk.Label(self, text="  Time:").pack(side="left")
        self.cb_hour = ttk.Combobox(self, textvariable=self.hour_var, values=[f"{i:02d}" for i in range(24)], width=3, state="readonly")
        self.cb_hour.pack(side="left")
        tk.Label(self, text=":").pack(side="left")
        self.cb_minute = ttk.Combobox(self, textvariable=self.minute_var, values=[f"{i:02d}" for i in range(60)], width=3, state="readonly")
        self.cb_minute.pack(side="left", padx=(0, 10))
        
        # Bindings
        self.cb_month.bind("<<ComboboxSelected>>", self.update_days)
        self.cb_year.bind("<<ComboboxSelected>>", self.update_days)
        
        # Init Default
        self.set_to_now()

    def set_to_now(self):
        now = datetime.now()
        self.year_var.set(str(now.year))
        self.month_var.set(f"{now.month:02d}")
        self.update_days() # Populate days first
        self.day_var.set(f"{now.day:02d}")
        self.hour_var.set(f"{now.hour:02d}")
        self.minute_var.set(f"{now.minute:02d}")

    def update_days(self, event=None):
        y = self.year_var.get()
        m = self.month_var.get()
        if not y or not m: return
        
        try:
            _, num_days = calendar.monthrange(int(y), int(m))
            days = [f"{i:02d}" for i in range(1, num_days + 1)]
            self.cb_day['values'] = days
            
            # If current selection is invalid (e.g., 31st then switch to Feb), reset to 01
            current = self.day_var.get()
            if current and int(current) > num_days:
                self.day_var.set("01")
        except: pass

    def get_datetime_str(self):
        # Returns YYYY-MM-DD HH:MM:00
        try:
            return f"{self.year_var.get()}-{self.month_var.get()}-{self.day_var.get()} {self.hour_var.get()}:{self.minute_var.get()}:00"
        except: return None

class ManualExamFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        
        sf = tk.Frame(self); sf.pack(fill="x", pady=10)
        tk.Label(sf, text="Name:").pack(side="left"); self.en = tk.Entry(sf); self.en.pack(side="left", padx=5)
        tk.Label(sf, text="Subject:").pack(side="left"); self.cb = ttk.Combobox(sf, state="readonly", width=15); self.cb.pack(side="left", padx=5); self.cb.bind("<<ComboboxSelected>>", self.filt)
        tk.Label(sf, text="Dur(min):").pack(side="left"); self.dr = tk.Entry(sf, width=5); self.dr.insert(0,"60"); self.dr.pack(side="left", padx=5)
        
        # Date Pickers
        df = tk.Frame(self); df.pack(fill="x", pady=5)
        
        tk.Label(df, text="Start:").grid(row=0, column=0, padx=5, sticky="e")
        self.start_picker = DateTimePicker(df)
        self.start_picker.grid(row=0, column=1, padx=5, sticky="w")
        
        tk.Label(df, text="End:").grid(row=1, column=0, padx=5, sticky="e")
        self.end_picker = DateTimePicker(df)
        self.end_picker.grid(row=1, column=1, padx=5, sticky="w")

        qa = tk.Frame(self); qa.pack(fill="both", expand=True, pady=10)
        self.pool = tk.Listbox(qa, selectmode=tk.EXTENDED); self.pool.pack(side="left", fill="both", expand=True)
        md = tk.Frame(qa); md.pack(side="left")
        tk.Button(md, text=">>", command=self.add_q).pack(); tk.Button(md, text="<<", command=self.rem_q).pack()
        self.sel = tk.Listbox(qa, selectmode=tk.EXTENDED); self.sel.pack(side="left", fill="both", expand=True)
        tk.Button(self, text="Create Exam (Draft)", command=self.crt, bg="#4CAF50", fg="white", font=BTN_FONT).pack(pady=10)
        self.p_list, self.s_list = [], []

    def on_show(self):
        self.subs = self.controller.master_service.get_all_subjects()
        self.cb['values'] = [s.subject_name for s in self.subs]
        if self.subs: self.cb.current(0); self.filt()
        if hasattr(self, 'start_picker'): self.start_picker.set_to_now()
        if hasattr(self, 'end_picker'): self.end_picker.set_to_now()

    def filt(self, e=None):
        s = next((x for x in self.subs if x.subject_name == self.cb.get()), None)
        if not s: return
        self.p_list = self.controller.master_service.get_questions_by_subject(s.subject_id); self.s_list = []
        self.refs()
    def refs(self):
        self.pool.delete(0, tk.END); self.sel.delete(0, tk.END)
        for q in self.p_list: self.pool.insert(tk.END, q.content)
        for q in self.s_list: self.sel.insert(tk.END, q.content)
    def add_q(self):
        ids = self.pool.curselection()
        to_move = [self.p_list[i] for i in ids]
        for i in reversed(ids): del self.p_list[i]
        self.s_list.extend(to_move); self.refs()
    def rem_q(self):
        ids = self.sel.curselection()
        to_move = [self.s_list[i] for i in ids]
        for i in reversed(ids): del self.s_list[i]
        self.p_list.extend(to_move); self.refs()

    def crt(self):
        s = next((x for x in self.subs if x.subject_name == self.cb.get()), None)
        name = self.en.get().strip()
        dur = self.dr.get().strip()
        
        # Validation
        if not name:
            messagebox.showwarning("Validation", "Exam Name is required")
            return
        if not dur.isdigit() or int(dur) <= 0:
            messagebox.showwarning("Validation", "Duration must be a positive number")
            return
        if not self.s_list:
            messagebox.showwarning("Validation", "Please select at least one question")
            return
            
        try:
            start_d = self.start_picker.get_datetime_str()
            end_d = self.end_picker.get_datetime_str()
            
            if start_d and end_d and start_d > end_d:
                messagebox.showwarning("Validation", "Start Date must be before End Date")
                return
            
            self.controller.exam_service.create_exam(
                self.controller.current_user, s, name, int(dur), self.s_list,
                start_date=start_d, end_date=end_d
            )
            messagebox.showinfo("OK", "Exam Created (Status: Draft)"); self.filt()
            self.s_list = []; self.refs(); self.en.delete(0, tk.END)
            self.start_picker.set_to_now(); self.end_picker.set_to_now()
        except Exception as e: messagebox.showerror("Error", str(e))

class AutoExamFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        f = tk.Frame(self); f.place(relx=0.5, rely=0.3, anchor="center")
        tk.Label(f, text="Auto Exam Creation", font=("Arial",14)).grid(row=0, columnspan=2, pady=10)
        
        # Simple fields
        ls = ["Name:","Subject:","Duration:","Easy:","Medium:","Hard:"]
        self.ws = {}
        for i,t in enumerate(ls):
            tk.Label(f, text=t).grid(row=i+1, column=0, sticky="e", pady=5)
            w = ttk.Combobox(f, state="readonly") if "Subject" in t else tk.Entry(f)
            w.grid(row=i+1, column=1, pady=5); self.ws[t] = w
        
        self.ws["Duration:"].insert(0,"60")
        
        # Date Pickers
        row_offset = len(ls) + 1
        tk.Label(f, text="Start Date:").grid(row=row_offset, column=0, sticky="e", pady=5)
        self.start_picker = DateTimePicker(f)
        self.start_picker.grid(row=row_offset, column=1, pady=5, sticky="w")
        
        tk.Label(f, text="End Date:").grid(row=row_offset+1, column=0, sticky="e", pady=5)
        self.end_picker = DateTimePicker(f)
        self.end_picker.grid(row=row_offset+1, column=1, pady=5, sticky="w")

        tk.Button(f, text="Generate (Draft)", command=self.gen, bg="#673AB7", fg="white", font=BTN_FONT).grid(row=row_offset+2, columnspan=2, pady=20)
        
    def on_show(self):
        self.subs = self.controller.master_service.get_all_subjects()
        self.ws["Subject:"]['values'] = [s.subject_name for s in self.subs]
        if self.subs: self.ws["Subject:"].current(0)
        if hasattr(self, 'start_picker'): self.start_picker.set_to_now()
        if hasattr(self, 'end_picker'): self.end_picker.set_to_now()
        
    def gen(self):
        s = next((x for x in self.subs if x.subject_name == self.ws["Subject:"].get()), None)
        name = self.ws["Name:"].get().strip()
        dur = self.ws["Duration:"].get().strip()
        e_c = self.ws["Easy:"].get().strip() or "0"
        m_c = self.ws["Medium:"].get().strip() or "0"
        h_c = self.ws["Hard:"].get().strip() or "0"

        # Validation
        if not name:
             messagebox.showwarning("Validation", "Exam Name is required")
             return
        if not dur.isdigit() or int(dur) <= 0:
             messagebox.showwarning("Validation", "Duration must be a positive number")
             return
        if not (e_c.isdigit() and m_c.isdigit() and h_c.isdigit()):
             messagebox.showwarning("Validation", "Question counts must be numbers")
             return
        if int(e_c) + int(m_c) + int(h_c) <= 0:
             messagebox.showwarning("Validation", "Total questions must be > 0")
             return

        try:
            sd = self.start_picker.get_datetime_str()
            ed = self.end_picker.get_datetime_str()
            
            if sd and ed and sd > ed:
                messagebox.showwarning("Validation", "Start Date must be before End Date")
                return
            
            self.controller.exam_service.create_auto_exam(
                self.controller.current_user, s, name, int(dur),
                int(e_c), int(m_c), int(h_c),
                start_date=sd, end_date=ed
            )
            messagebox.showinfo("OK", "Created (Status: Draft)")
        except Exception as e: messagebox.showerror("Error", str(e))

class ExamManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        tk.Label(self, text="Exam Management", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10)
        
        self.tree = ttk.Treeview(self, columns=("id", "nm", "sub", "st", "sd", "ed"), show="headings")
        self.tree.heading("id", text="STT"); self.tree.column("id", width=50) # Changed from ID to STT
        self.tree.heading("nm", text="Name")
        self.tree.heading("sub", text="Subject")
        self.tree.heading("st", text="Status")
        self.tree.heading("sd", text="Start")
        self.tree.heading("ed", text="End")
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10)
        
        btn_f = tk.Frame(self)
        btn_f.grid(row=2, column=0, pady=10)
        tk.Button(btn_f, text="Refresh", command=self.load, font=BTN_FONT).pack(side="left", padx=5)
        tk.Button(btn_f, text="View Details / Results", command=self.view, bg="#2196F3", fg="white", font=BTN_FONT).pack(side="left", padx=5)
        tk.Button(btn_f, text="Edit Exam", command=self.edit, bg="#FF9800", fg="white", font=BTN_FONT).pack(side="left", padx=5)
        tk.Button(btn_f, text="Delete Exam", command=self.delete, bg="#F44336", fg="white", font=BTN_FONT).pack(side="left", padx=5)

    def on_show(self): self.load()
    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.exams = self.controller.exam_service.get_all_exams_for_admin()
        for idx, e in enumerate(self.exams, 1):
            self.tree.insert("", "end", iid=e.exam_id, values=(idx, e.exam_name, e.subject_name, e.status.upper(), e.start_date or "-", e.end_date or "-"))
            
    def view(self):
        sel = self.tree.selection()
        if not sel: return
        exam_id = int(sel[0])
        exam = next((x for x in self.exams if x.exam_id == exam_id), None)
        if exam: ExamDetailWindow(self.controller, exam, self.load)

    def edit(self):
        sel = self.tree.selection()
        if not sel: return
        exam_id = int(sel[0])
        exam = next((x for x in self.exams if x.exam_id == exam_id), None)
        if not exam: return
        
        # Determine subject to fetch all possible questions
        # We need to know the subject_id, but exam object might only have subject_name if loaded from get_all_exams_for_admin
        # We need the real subject object or ID.
        # Let's find the subject object from master_service based on name
        all_subs = self.controller.master_service.get_all_subjects()
        real_sub = next((s for s in all_subs if s.subject_name == exam.subject_name), None)
        
        if not real_sub:
             messagebox.showerror("Error", "Associated Subject not found")
             return

        # Fetch question IDs currently in this exam
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT question_id FROM exam_details WHERE exam_id=?",(exam.exam_id,))
        current_q_ids = [r[0] for r in c.fetchall()]
        conn.close()
        
        # Fetch all questions for this subject (to have full objects)
        all_qs = self.controller.master_service.get_questions_by_subject(real_sub.subject_id)
        
        # Filter to get the Question objects for this exam
        exam.questions = [q for q in all_qs if q.question_id in current_q_ids]
        
        EditExamWindow(self.controller, exam, self.load)
        
    def delete(self):
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", "Delete Exam? This will delete all student results/history for this exam."): return
        try:
            self.controller.exam_service.delete_exam(int(sel[0]))
            self.load()
        except Exception as e: messagebox.showerror("Error", str(e))

class ExamDetailWindow(tk.Toplevel):
    def __init__(self, controller, exam, on_close_cb):
        super().__init__()
        self.controller = controller
        self.exam = exam
        self.on_close_cb = on_close_cb
        self.title(f"Exam Dashboard: {exam.exam_name}")
        self.state('zoomed')
        self.configure(bg="#F5F7FB") # Light dashboard background
        
        # Main container with padding
        main_cont = tk.Frame(self, bg="#F5F7FB")
        main_cont.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 1. Header Section
        header = tk.Frame(main_cont, bg="#F5F7FB")
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(header, text=exam.exam_name, font=("Arial", 24, "bold"), bg="#F5F7FB", fg="#333").pack(side="left")
        
        # Status Badge
        st_color = "#4CAF50" if exam.status == 'published' else "#FF9800" if exam.status == 'closed' else "#9E9E9E"
        tk.Label(header, text=exam.status.upper(), font=("Arial", 10, "bold"), bg=st_color, fg="white", padx=10, pady=5).pack(side="left", padx=20)
        
        # Actions (Right aligned)
        act_f = tk.Frame(header, bg="#F5F7FB")
        act_f.pack(side="right")
        
        if exam.status == 'draft':
            tk.Button(act_f, text="PUBLISH EXAM", command=self.publish, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, relief="flat").pack(side="left", padx=5)
        elif exam.status == 'published':
            tk.Button(act_f, text="CLOSE EXAM", command=self.close_exam, bg="#F44336", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, relief="flat").pack(side="left", padx=5)
        elif exam.status == 'closed':
            tk.Button(act_f, text="REOPEN EXAM", command=self.reopen_exam, bg="#FF9800", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, relief="flat").pack(side="left", padx=5)


        # 2. Stats Cards
        stats_frame = tk.Frame(main_cont, bg="#F5F7FB")
        stats_frame.pack(fill="x", pady=20)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)
        
        self.stat_vars = {
            "total": tk.StringVar(value="0"),
            "avg": tk.StringVar(value="0"),
            "high": tk.StringVar(value="0"),
            "low": tk.StringVar(value="0")
        }
        
        self.create_card(stats_frame, 0, "Total Participants", self.stat_vars["total"])
        self.create_card(stats_frame, 1, "Average Score", self.stat_vars["avg"])
        self.create_card(stats_frame, 2, "Highest Score", self.stat_vars["high"], val_color="#4CAF50")
        self.create_card(stats_frame, 3, "Lowest Score", self.stat_vars["low"], val_color="#F44336")
        
        # 3. Results Section
        res_frame = tk.Frame(main_cont, bg="white", padx=20, pady=20) # Card look
        res_frame.pack(fill="both", expand=True)
        
        rf_header = tk.Frame(res_frame, bg="white")
        rf_header.pack(fill="x", pady=(0, 15))
        tk.Label(rf_header, text="Student Results", font=("Arial", 16, "bold"), bg="white").pack(side="left")
        
        # List Actions
        tk.Button(rf_header, text="Export Report", command=self.export_report, font=("Arial", 10), bg="#E0E0E0", relief="flat", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(rf_header, text="Review Selected", command=self.review, font=("Arial", 10), bg="#E0E0E0", relief="flat", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(rf_header, text="Delete Result", command=self.del_res, font=("Arial", 10), bg="#FFEBEE", fg="#D32F2F", relief="flat", padx=10, pady=5).pack(side="right", padx=5)

        # Treeview
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), padding=10)
        style.configure("Treeview", font=("Arial", 11), rowheight=30)
        
        self.tree = ttk.Treeview(res_frame, columns=("id", "st", "sc", "tm"), show="headings", selectmode="browse")
        self.tree.heading("id", text="#"); self.tree.column("id", width=50, anchor="center")
        self.tree.heading("st", text="Student Name"); self.tree.column("st", width=300)
        self.tree.heading("sc", text="Score"); self.tree.column("sc", width=100, anchor="center")
        self.tree.heading("tm", text="Submission Time"); self.tree.column("tm", width=200)
        
        self.tree.pack(fill="both", expand=True)
        
        self.load_results()
        
    def create_card(self, parent, col, title, var, val_color="#212121"):
        card = tk.Frame(parent, bg="white", padx=20, pady=20)
        card.grid(row=0, column=col, sticky="ew", padx=10)
        
        tk.Label(card, text=title, font=("Arial", 10), fg="#757575", bg="white").pack(anchor="w")
        tk.Label(card, textvariable=var, font=("Arial", 24, "bold"), fg=val_color, bg="white").pack(anchor="w", pady=(5, 0))

    def update_status(self, st):
        try:
            self.controller.exam_service.update_exam_status(self.exam.exam_id, st)
            messagebox.showinfo("OK", f"Exam {st.upper()}")
            if self.on_close_cb: self.on_close_cb()
            self.destroy()
        except Exception as e: messagebox.showerror("Error", str(e))
        
    def publish(self): self.update_status('published')
    def close_exam(self): self.update_status('closed')
    
    def reopen_exam(self):
        # Check dates
        now = datetime.now()
        end = datetime.strptime(self.exam.end_date, "%Y-%m-%d %H:%M:%S")
        if now > end:
            messagebox.showwarning("Cannot Reopen", "Current time is past the End Date.\nPlease Edit the exam to extend the End Date first.")
            return
        self.update_status('published')

    def load_results(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.res = self.controller.result_service.get_results_by_exam_id(self.exam.exam_id)
        
        scores = []
        for i,r in enumerate(self.res, 1):
            self.tree.insert("", "end", iid=i-1, values=(i, r.student_name, f"{r.score:.1f}", r.submit_time))
            try: scores.append(float(r.score))
            except: pass
            
        # Update Stats
        self.stat_vars["total"].set(str(len(scores)))
        if scores:
            self.stat_vars["avg"].set(f"{sum(scores)/len(scores):.2f}")
            self.stat_vars["high"].set(f"{max(scores):.1f}")
            self.stat_vars["low"].set(f"{min(scores):.1f}")
        else:
            self.stat_vars["avg"].set("0")
            self.stat_vars["high"].set("0")
            self.stat_vars["low"].set("0")

    def export_report(self):
        if not self.res: return messagebox.showinfo("Info", "No results to export")
        
        f_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not f_path: return
        
        try:
            import csv
            with open(f_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Exam Report", self.exam.exam_name])
                writer.writerow(["Total Participants", self.stat_vars["total"].get()])
                writer.writerow(["Average Score", self.stat_vars["avg"].get()])
                writer.writerow(["Highest Score", self.stat_vars["high"].get()])
                writer.writerow(["Lowest Score", self.stat_vars["low"].get()])
                writer.writerow([])
                writer.writerow(["#", "Student Name", "Score", "Submission Time"])
                
                for i, r in enumerate(self.res, 1):
                    writer.writerow([i, r.student_name, r.score, r.submit_time])
            messagebox.showinfo("Success", "Report exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def review(self):
        sel = self.tree.selection()
        if not sel: return
        ReviewWindow(self.controller, self.res[int(sel[0])].result_id)
        
    def del_res(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Confirm", "Delete Result?"): return
        self.controller.result_service.delete_result(self.res[int(sel[0])].result_id)
        self.load_results()

class StudentDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        header = tk.Frame(self, bg="#FF9800", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Student Dashboard", font=("Arial", 18, "bold"), bg="#FF9800", fg="white").pack(side="left", padx=20)
        tk.Button(header, text="Logout", command=self.controller.logout, font=("Arial", 10)).pack(side="right", padx=20)

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=20, pady=20)
        self.avail = tk.Frame(nb); nb.add(self.avail, text="Exams")
        self.hist = tk.Frame(nb); nb.add(self.hist, text="History")

        self.lb_exams = tk.Listbox(self.avail, font=("Arial", 11))
        self.lb_exams.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self.avail, text="Start/Continue Exam", command=self.take, bg="#2196F3", fg="white", font=BTN_FONT, pady=10).pack(pady=10)

        self.lb_hist = tk.Listbox(self.hist, font=("Arial", 11))
        self.lb_hist.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self.hist, text="Review", command=self.view, font=BTN_FONT).pack(pady=5)
        tk.Button(self.hist, text="Refresh", command=self.load_hist, font=BTN_FONT).pack(pady=5)

    def on_show(self): self.load_exams(); self.load_hist()
    def load_exams(self):
        self.lb_exams.delete(0, tk.END); self.display_exams = []
        subs = self.controller.master_service.get_all_subjects()
        for s in subs:
            exams = self.controller.exam_service.get_exams_by_subject(s.subject_id)
            for e in exams:
                res = self.controller.result_service.get_student_history(self.controller.current_user.user_id)
                completed_ids = [r.exam_id for r in res]
                if e.exam_id not in completed_ids:
                    self.display_exams.append(e)
                    self.lb_exams.insert(tk.END, f"{s.subject_name} - {e.exam_name} ({e.duration}m)")

    def load_hist(self):
        self.lb_hist.delete(0, tk.END)
        self.history = self.controller.result_service.get_student_history(self.controller.current_user.user_id)
        for r in self.history: self.lb_hist.insert(tk.END, f"[{r.submit_time[:16]}] {r.exam_name} - {r.score:.1f}")
    
    def take(self):
        if not self.lb_exams.curselection(): return
        exam = self.display_exams[self.lb_exams.curselection()[0]]
        state = self.controller.result_service.start_exam(self.controller.current_user, exam)
        if state["status"] == "completed":
            messagebox.showinfo("Info", "You already finished this exam.")
            self.load_exams()
            return

        ExamWindow(self.controller, exam, state)

    def view(self):
        if not self.lb_hist.curselection(): return
        ReviewWindow(self.controller, self.history[self.lb_hist.curselection()[0]].result_id)

class ExamWindow(tk.Toplevel):
    def __init__(self, controller, exam, state):
        super().__init__()
        self.controller = controller
        self.exam = exam
        self.result_id = state["result_id"]
        self.remaining = state["remaining_seconds"]
        self.saved = state["saved_answers"]
        
        self.title(f"Exam: {exam.exam_name}")
        self.state('zoomed') # Maximize
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        
        # Header
        header = tk.Frame(self, bg="#EEE", height=60, padx=20)
        header.pack(fill="x")
        tk.Label(header, text=f"{exam.exam_name}", font=("Arial", 16, "bold"), bg="#EEE").pack(side="left")
        
        self.timer_lbl = tk.Label(header, text="--:--", font=("Arial", 16, "bold"), fg="red", bg="#EEE")
        self.timer_lbl.pack(side="left", expand=True) # Center timer
        
        self.prog_lbl = tk.Label(header, text="0 / 0", font=("Arial", 14), bg="#EEE")
        self.prog_lbl.pack(side="right")
        
        # Main Canvas Area
        self.canvas = tk.Canvas(self)
        self.sb = ttk.Scrollbar(self, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.sb.set)
        
        self.sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Center Frame inside Canvas
        self.center_frame = tk.Frame(self.canvas)
        # Fix: Anchor 'n' centers at X coord. X should be width/2.
        self.canvas_window = self.canvas.create_window((0, 0), window=self.center_frame, anchor="n")
        
        # Bindings for resizing and scrolling
        self.center_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Content
        self.vars = {}
        self.qs_frames = {}
        
        # Padding wrapper for visual centering
        self.content_wrapper = tk.Frame(self.center_frame, padx=50, pady=20)
        self.content_wrapper.pack(fill="both", expand=True)

        for idx, q in enumerate(exam.questions):
            f = tk.LabelFrame(self.content_wrapper, text=f"Question {idx+1}", font=("Arial", 12, "bold"), padx=10, pady=10)
            f.pack(fill="x", pady=15)
            self.qs_frames[q.question_id] = f
            
            tk.Label(f, text=q.content, font=("Arial", 14), wraplength=800, justify="left").pack(anchor="w", pady=(0, 10))
            
            val = self.saved.get(q.question_id, "none")
            var = tk.StringVar(value=val)
            self.vars[q.question_id] = var
            
            def on_click(qid=q.question_id, v=var, fr=f):
                self.controller.result_service.save_answer_progress(self.result_id, qid, v.get())
                self.update_progress()
                fr.config(bg="#E3F2FD") 

            for opt in ('a','b','c','d'):
                txt = getattr(q, 'option_'+opt)
                rb = tk.Radiobutton(f, text=f"{opt.upper()}. {txt}", variable=var, value=opt, command=on_click, font=("Arial", 12))
                rb.pack(anchor="w", padx=20, pady=2)
            
            if val != "none": f.config(bg="#E3F2FD")
                
        tk.Button(self.content_wrapper, text="FINISH & SUBMIT", command=self.submit, bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), pady=15, width=30).pack(pady=40)
        
        # Anti-Cheat Bindings
        self.bind("<Control-c>", lambda e: "break")
        self.bind("<Control-v>", lambda e: "break")
        self.bind("<Control-x>", lambda e: "break")
        self.bind("<Control-a>", lambda e: "break")
        self.bind("<Button-3>", lambda e: "break") # Right click
        
        self.violation_count = 0
        self.bind("<FocusOut>", self.on_focus_loss)
        
        self.update_timer()
        self.update_progress()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_canvas_configure(self, event):
        width = event.width
        self.canvas.coords(self.canvas_window, width // 2, 0)
        frame_w = min(width - 40, 1000) 
        self.canvas.itemconfig(self.canvas_window, width=frame_w)
        
    def on_focus_loss(self, event):
        # Prevent rapid firing checks if user is just clicking around mostly invalid
        # But this event fires when window loses focus.
        if self.attributes("-fullscreen"):
             self.violation_count += 1
             left = 3 - self.violation_count
             if left <= 0:
                 messagebox.showerror("Violation", "You have switched windows too many times.\nExam will be submitted automatically.")
                 self.submit(force=True)
             else:
                 messagebox.showwarning("Warning", f"Do not switch windows during the exam!\nViolations: {self.violation_count}/3\nRemaining chances: {left}")
                 self.focus_force() # Bring back

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def update_progress(self):
        done = sum(1 for v in self.vars.values() if v.get() != "none")
        total = len(self.exam.questions)
        self.prog_lbl.config(text=f"Completed: {done} / {total}")

    def update_timer(self):
        if self.remaining <= 0:
            self.timer_lbl.config(text="Time's up!")
            self.submit(force=True)
            return
        
        m, s = divmod(int(self.remaining), 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self.remaining -= 1
        self.after(1000, self.update_timer)

    def submit(self, force=False):
        if not force:
            done = sum(1 for v in self.vars.values() if v.get() != "none")
            total = len(self.exam.questions)
            if not messagebox.askyesno("Submit", f"You have answered {done}/{total} questions.\nFinish exam?"): return
            
        self.unbind_all("<MouseWheel>")
        res = self.controller.result_service.finish_exam(self.result_id, self.exam)
        messagebox.showinfo("Done", f"Score: {res.score:.1f}")
        self.destroy()

class ReviewWindow(tk.Toplevel):
    def __init__(self, controller, result_id):
        super().__init__()
        self.title("Exam Review")
        self.geometry("800x600")
        
        result = controller.result_service.get_result_details(result_id)
        if not result: return

        tk.Label(self, text=f"Review: {result.exam_name} (Score: {result.score:.1f})", font=("Arial", 16, "bold")).pack(pady=10)
        
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for idx, detail in enumerate(result.details):
            color = "#C8E6C9" if detail.is_correct else "#FFCDD2"
            f = tk.LabelFrame(scrollable_frame, text=f"Q{idx+1}: {detail.question_content}", bg=color, font=("Arial", 11, "bold"))
            f.pack(fill="x", padx=5, pady=10)
            
            ops = detail.options
            for opt_key, opt_text in ops.items():
                prefix = ""
                lbl_fg = "black"
                lbl_font = ("Arial", 11)
                
                if opt_key == detail.correct_answer:
                    prefix = " [CORRECT]"
                    lbl_fg = "#2E7D32" 
                    lbl_font = ("Arial", 11, "bold")
                
                if opt_key == detail.selected_answer:
                    if not detail.is_correct:
                        prefix = " [YOUR ANSWER]"
                        lbl_fg = "#C62828" 
                        lbl_font = ("Arial", 11, "bold")
                    else:
                        prefix = " [YOUR ANSWER]" 

                tk.Label(f, text=f"{opt_key.upper()}. {opt_text} {prefix}", fg=lbl_fg, font=lbl_font, bg=color).pack(anchor="w", padx=10)

class EditExamWindow(tk.Toplevel):
    def __init__(self, controller, exam, on_close_cb):
        super().__init__()
        self.controller = controller
        self.exam = exam
        self.on_close_cb = on_close_cb
        self.title(f"Edit Exam: {exam.exam_name}")
        self.geometry("900x700")
        
        # Determine subject (need object)
        subs = self.controller.master_service.get_all_subjects()
        self.subject = next((s for s in subs if s.subject_name == exam.subject_name), None)
        
        # Reuse logic is hard with inheritance because of layout differences, so we rebuild UI
        # Top: Meta
        tf = tk.Frame(self, padx=10, pady=10)
        tf.pack(fill="x")
        
        tk.Label(tf, text="Name:").pack(side="left")
        self.en_name = tk.Entry(tf, width=30, font=("Arial", 11)); self.en_name.pack(side="left", padx=5)
        self.en_name.insert(0, exam.exam_name)
        
        tk.Label(tf, text="Duration(min):").pack(side="left", padx=10)
        self.en_dur = tk.Entry(tf, width=5, font=("Arial", 11)); self.en_dur.pack(side="left")
        self.en_dur.insert(0, str(exam.duration))
        
        # Dates
        df = tk.Frame(self, padx=10, pady=5); df.pack(fill="x")
        tk.Label(df, text="Start:").pack(side="left")
        self.start_picker = DateTimePicker(df); self.start_picker.pack(side="left", padx=5)
        
        tk.Label(df, text="End:").pack(side="left", padx=10)
        self.end_picker = DateTimePicker(df); self.end_picker.pack(side="left", padx=5)
        
        # Pre-fill dates
        self.set_picker(self.start_picker, exam.start_date)
        self.set_picker(self.end_picker, exam.end_date)
        
        # Questions
        qf = tk.Frame(self, padx=10, pady=10); qf.pack(fill="both", expand=True)
        
        # Pool (Left)
        lf = tk.LabelFrame(qf, text=f"Available Questions ({exam.subject_name})"); lf.pack(side="left", fill="both", expand=True)
        sb1 = ttk.Scrollbar(lf); self.lb_pool = tk.Listbox(lf, selectmode=tk.EXTENDED, yscrollcommand=sb1.set)
        sb1.config(command=self.lb_pool.yview)
        sb1.pack(side="right", fill="y"); self.lb_pool.pack(side="left", fill="both", expand=True)
        
        # Buttons (Center)
        bf = tk.Frame(qf, padx=5); bf.pack(side="left")
        tk.Button(bf, text=">>", command=self.add_q).pack(pady=5)
        tk.Button(bf, text="<<", command=self.rem_q).pack(pady=5)
        
        # Selected (Right)
        rf = tk.LabelFrame(qf, text="Selected Questions"); rf.pack(side="left", fill="both", expand=True)
        sb2 = ttk.Scrollbar(rf); self.lb_sel = tk.Listbox(rf, selectmode=tk.EXTENDED, yscrollcommand=sb2.set)
        sb2.config(command=self.lb_sel.yview)
        sb2.pack(side="right", fill="y"); self.lb_sel.pack(side="left", fill="both", expand=True)
        
        # Save
        tk.Button(self, text="SAVE CHANGES", command=self.save, bg="#4CAF50", fg="white", font=BTN_FONT, pady=10).pack(pady=10)
        
        # Init Lists
        self.s_list = exam.questions # Already active
        self.p_list = []
        if self.subject:
            all_qs = self.controller.master_service.get_questions_by_subject(self.subject.subject_id)
            # Filter out already selected
            sel_ids = [q.question_id for q in self.s_list]
            self.p_list = [q for q in all_qs if q.question_id not in sel_ids]
            
        self.refresh_lists()
        
    def set_picker(self, picker, dt_str):
        if not dt_str: return
        try:
            # Expect YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            picker.year_var.set(str(dt.year))
            picker.month_var.set(f"{dt.month:02d}")
            picker.update_days()
            picker.day_var.set(f"{dt.day:02d}")
            picker.hour_var.set(f"{dt.hour:02d}")
            picker.minute_var.set(f"{dt.minute:02d}")
        except: pass

    def refresh_lists(self):
        self.lb_pool.delete(0, tk.END); self.lb_sel.delete(0, tk.END)
        for q in self.p_list: self.lb_pool.insert(tk.END, q.content)
        for q in self.s_list: self.lb_sel.insert(tk.END, q.content)

    def add_q(self):
        ids = self.lb_pool.curselection()
        to_move = [self.p_list[i] for i in ids]
        for i in reversed(ids): del self.p_list[i]
        self.s_list.extend(to_move); self.refresh_lists()

    def rem_q(self):
        ids = self.lb_sel.curselection()
        to_move = [self.s_list[i] for i in ids]
        for i in reversed(ids): del self.s_list[i]
        self.p_list.extend(to_move); self.refresh_lists()

    def save(self):
        name = self.en_name.get().strip()
        dur = self.en_dur.get().strip()
        
        if not name: messagebox.showwarning("Val", "Name required"); return
        if not dur.isdigit() or int(dur) <= 0: messagebox.showwarning("Val", "Duration > 0"); return
        if not self.s_list: messagebox.showwarning("Val", "Select > 0 questions"); return
        
        sd = self.start_picker.get_datetime_str()
        ed = self.end_picker.get_datetime_str()
        if sd and ed and sd > ed: messagebox.showwarning("Val", "Start <= End"); return
        
        try:
            self.controller.exam_service.update_exam(
                self.exam.exam_id, name, int(dur), self.s_list, sd, ed
            )
            
            # Auto-Reopen Logic
            if self.exam.status == 'closed':
                 now = datetime.now()
                 end_dt = datetime.strptime(ed, "%Y-%m-%d %H:%M:%S")
                 if now < end_dt:
                     if messagebox.askyesno("Reopen?", "The new End Date is in the future.\nDo you want to Reopen this exam now?"):
                         self.controller.exam_service.update_exam_status(self.exam.exam_id, 'published')
            
            messagebox.showinfo("OK", "Exam Updated")
            self.on_close_cb()
            self.destroy()
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    try:
        app = QuizApp()
        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Critical Error: Press Enter to exit...")
