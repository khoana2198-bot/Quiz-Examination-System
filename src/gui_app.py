import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from datetime import date
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
            ("Student Results", self.show_results),
        ]
        for text, cmd in menus:
            tk.Button(self.sidebar, text=text, command=cmd, font=("Arial", 11), bg="white", relief="flat", padx=10, pady=10).pack(fill="x", pady=5, padx=5)

        self.content_area = tk.Frame(self.main_split)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ManageSubjectsFrame, ManageQuestionsFrame, CreateExamFrame, TeacherResultsFrame):
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
    def show_results(self): self.switch_content("TeacherResultsFrame")
    
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

class ManualExamFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        sf = tk.Frame(self); sf.pack(fill="x", pady=10)
        tk.Label(sf, text="Name:").pack(side="left"); self.en = tk.Entry(sf); self.en.pack(side="left")
        tk.Label(sf, text="Subject:").pack(side="left"); self.cb = ttk.Combobox(sf, state="readonly"); self.cb.pack(side="left"); self.cb.bind("<<ComboboxSelected>>", self.filt)
        tk.Label(sf, text="Duration:").pack(side="left"); self.dr = tk.Entry(sf, width=5); self.dr.insert(0,"60"); self.dr.pack(side="left")
        qa = tk.Frame(self); qa.pack(fill="both", expand=True)
        self.pool = tk.Listbox(qa, selectmode=tk.EXTENDED); self.pool.pack(side="left", fill="both", expand=True)
        md = tk.Frame(qa); md.pack(side="left")
        tk.Button(md, text=">>", command=self.add_q).pack(); tk.Button(md, text="<<", command=self.rem_q).pack()
        self.sel = tk.Listbox(qa, selectmode=tk.EXTENDED); self.sel.pack(side="left", fill="both", expand=True)
        tk.Button(self, text="Create", command=self.crt, bg="#4CAF50", fg="white", font=BTN_FONT).pack(pady=10)
        self.p_list, self.s_list = [], []
    def on_show(self):
        self.subs = self.controller.master_service.get_all_subjects()
        self.cb['values'] = [s.subject_name for s in self.subs]
        if self.subs: self.cb.current(0); self.filt()
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
        try:
            self.controller.exam_service.create_exam(self.controller.current_user, s, self.en.get(), int(self.dr.get()), self.s_list)
            messagebox.showinfo("OK", "Exam Created"); self.filt()
        except Exception as e: messagebox.showerror("Error", str(e))

class AutoExamFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        f = tk.Frame(self); f.place(relx=0.5, rely=0.3, anchor="center")
        tk.Label(f, text="Auto Exam Creation", font=("Arial",14)).grid(row=0, columnspan=2)
        ls = ["Name:","Subject:","Duration:","Easy:","Medium:","Hard:"]
        self.ws = {}
        for i,t in enumerate(ls):
            tk.Label(f, text=t).grid(row=i+1, column=0, sticky="e")
            w = ttk.Combobox(f, state="readonly") if "Subject" in t else tk.Entry(f)
            w.grid(row=i+1, column=1); self.ws[t] = w
        self.ws["Duration:"].insert(0,"60")
        tk.Button(f, text="Generate", command=self.gen, bg="#673AB7", fg="white", font=BTN_FONT).grid(row=10, columnspan=2, pady=20)
    def on_show(self):
        self.subs = self.controller.master_service.get_all_subjects()
        self.ws["Subject:"]['values'] = [s.subject_name for s in self.subs]
        if self.subs: self.ws["Subject:"].current(0)
    def gen(self):
        s = next((x for x in self.subs if x.subject_name == self.ws["Subject:"].get()), None)
        try:
            self.controller.exam_service.create_auto_exam(
                self.controller.current_user, s, self.ws["Name:"].get(), int(self.ws["Duration:"].get()),
                int(self.ws["Easy:"].get()), int(self.ws["Medium:"].get()), int(self.ws["Hard:"].get())
            )
            messagebox.showinfo("OK", "Created")
        except Exception as e: messagebox.showerror("Error", str(e))

class TeacherResultsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Student Results", font=("Arial", 16, "bold")).pack(pady=10)
        self.tree = ttk.Treeview(self, columns=("st","ex","sub","sc","tm"), show="headings")
        for c,t in zip(("st","ex","sub","sc","tm"), ("Student","Exam","Subject","Score","Time")): self.tree.heading(c, text=t)
        self.tree.pack(fill="both", expand=True, padx=20)
        f = tk.Frame(self); f.pack(pady=10)
        tk.Button(f, text="View Details", command=self.view, font=BTN_FONT).pack(side="left", padx=5)
        tk.Button(f, text="Delete Result", command=self.delete, bg="#F44336", fg="white", font=BTN_FONT).pack(side="left", padx=5)
        tk.Button(f, text="Refresh", command=self.load, font=BTN_FONT).pack(side="left", padx=5)

    def on_show(self): self.load()
    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.res = self.controller.result_service.get_all_results()
        for i,r in enumerate(self.res): self.tree.insert("", "end", iid=i, values=(r.student_name, r.exam_name, r.subject_name, f"{r.score:.1f}", r.submit_time))
    def view(self):
        if not self.tree.selection(): return
        ReviewWindow(self.controller, self.res[int(self.tree.selection()[0])].result_id)
    def delete(self):
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno("Confirm", "Delete Result?"): return
        self.controller.result_service.delete_result(self.res[int(sel[0])].result_id)
        self.load()

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
        self.geometry("800x600")
        
        self.timer_lbl = tk.Label(self, text="Time Left: --:--", font=("Arial", 14, "bold"), fg="red")
        self.timer_lbl.pack(pady=10)
        
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=20)
        canvas = tk.Canvas(container); sb = ttk.Scrollbar(container, command=canvas.yview)
        sf = tk.Frame(canvas); canvas.create_window((0,0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set); canvas.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.vars = {}
        for idx, q in enumerate(exam.questions):
            f = tk.LabelFrame(sf, text=f"Q{idx+1}: {q.content}", font=("Arial", 11, "bold"))
            f.pack(fill="x", padx=5, pady=10)
            
            val = self.saved.get(q.question_id, "none")
            var = tk.StringVar(value=val)
            self.vars[q.question_id] = var
            
            def on_click(qid=q.question_id, v=var):
                self.controller.result_service.save_answer_progress(self.result_id, qid, v.get())

            for opt in ('a','b','c','d'):
                rb = tk.Radiobutton(f, text=f"{opt.upper()}. {getattr(q, 'option_'+opt)}", variable=var, value=opt, command=on_click, font=("Arial", 11))
                rb.pack(anchor="w", padx=10)
        
        tk.Button(sf, text="Finish & Submit", command=self.submit, bg="#4CAF50", fg="white", font=BTN_FONT, pady=10).pack(pady=20)
        
        self.update_timer()

    def update_timer(self):
        if self.remaining <= 0:
            self.timer_lbl.config(text="Time's up!")
            self.submit(force=True)
            return
        
        m, s = divmod(int(self.remaining), 60)
        self.timer_lbl.config(text=f"Time Left: {m:02d}:{s:02d}")
        self.remaining -= 1
        self.after(1000, self.update_timer)

    def submit(self, force=False):
        if not force and not messagebox.askyesno("Submit", "Finish exam?"): return
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

if __name__ == "__main__":
    try:
        app = QuizApp()
        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Critical Error: Press Enter to exit...")
