import sqlite3
import os
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_app.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")  # Enable Write-Ahead Logging for concurrency
    conn.execute("PRAGMA busy_timeout = 30000;") # Wait up to 30s if locked
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # PRAGMA foreign_keys is now set in get_connection()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        dob TEXT,
        role TEXT NOT NULL,
        must_change_password BOOLEAN DEFAULT 0
    )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0")
    except: pass 

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        difficulty_level TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        exam_name TEXT NOT NULL,
        duration INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'draft',
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id),
        FOREIGN KEY (created_by) REFERENCES users (user_id)
    )
    """)
    try: cursor.execute("ALTER TABLE exams ADD COLUMN start_date TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE exams ADD COLUMN end_date TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE exams ADD COLUMN status TEXT DEFAULT 'draft'")
    except: pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_details (
        exam_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        FOREIGN KEY (exam_id) REFERENCES exams (exam_id),
        FOREIGN KEY (question_id) REFERENCES questions (question_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        score REAL NOT NULL,
        submit_time TEXT,
        status TEXT DEFAULT 'completed',
        start_time TEXT,
        FOREIGN KEY (exam_id) REFERENCES exams (exam_id),
        FOREIGN KEY (student_id) REFERENCES users (user_id)
    )
    """)
    try: cursor.execute("ALTER TABLE results ADD COLUMN status TEXT DEFAULT 'completed'")
    except: pass
    try: cursor.execute("ALTER TABLE results ADD COLUMN start_time TEXT")
    except: pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS result_details (
        result_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected_answer TEXT,
        is_correct BOOLEAN NOT NULL,
        FOREIGN KEY (result_id) REFERENCES results (result_id),
        FOREIGN KEY (question_id) REFERENCES questions (question_id)
    )
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, dob, role) VALUES (?, ?, ?, ?, ?)",
                       ("teacher", "teacher@1234", "Default Teacher", "1980-01-01", "admin"))
    except Exception: pass

    try:
        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, dob, role) VALUES (?, ?, ?, ?, ?)",
                       ("student", "student@1234", "Default Student", "2000-01-01", "student"))
    except Exception: pass

    subjects = ["Mathematics", "Physics", "Chemistry"]
    for sub in subjects:
        try:
            cursor.execute("INSERT OR IGNORE INTO subjects (subject_name) VALUES (?)", (sub,))
        except Exception: pass

    conn.commit()
    conn.close()
