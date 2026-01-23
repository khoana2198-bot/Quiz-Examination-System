from datetime import datetime, timedelta
from typing import List, Optional, Dict
import re
import csv
import io
import random
from database import get_connection
from models import User, Admin, Student, Subject, Question, Exam, Result, ResultDetail

class UserService:
    def _validate_password(self, password: str, confirm_password: str = None) -> str:
        if confirm_password is not None and password != confirm_password:
            return "Passwords do not match."
        if len(password) > 20:
            return "Password must be at most 20 characters."
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            return "Password must contain both letters and numbers."
        return None

    def register_student(self, username, password, confirm_password, full_name, dob) -> Student:
        val_error = self._validate_password(password, confirm_password)
        if val_error:
            raise ValueError(val_error)
            
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password_hash, full_name, dob, role) VALUES (?, ?, ?, ?, ?)",
                           (username, password, full_name, dob, 'student'))
            user_id = cursor.lastrowid
            conn.commit()
            return Student(user_id, username, password, full_name, dob)
        except Exception as e:
            conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("Username already exists")
            raise e
        finally:
            conn.close()

    def change_password(self, user_id, new_pass):
        val_error = self._validate_password(new_pass)
        if val_error: raise ValueError(val_error)
        conn = get_connection()
        conn.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_pass, user_id))
        conn.commit()
        conn.close()

    def login(self, username, password) -> Optional[User]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, password_hash, full_name, dob, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            stored_password = row[2]
            if password == stored_password:
                role = row[5]
                if role == 'admin':
                    return Admin(row[0], row[1], row[2], row[3], row[4])
                else:
                    return Student(row[0], row[1], row[2], row[3], row[4])
        return None

class MasterDataService:
    def get_all_subjects(self) -> List[Subject]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject_id, subject_name FROM subjects")
        rows = cursor.fetchall()
        conn.close()
        return [Subject(r[0], r[1]) for r in rows]

    def add_subject(self, name: str):
        conn = get_connection()
        try:
            conn.execute("INSERT INTO subjects (subject_name) VALUES (?)", (name,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_subject(self, subject_id: int):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_questions_by_subject(self, subject_id: int) -> List[Question]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question_id, subject_id, content, option_a, option_b, option_c, option_d, correct_answer, difficulty_level 
            FROM questions WHERE subject_id = ?
        """, (subject_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Question(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows]

    def add_question(self, q: Question):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT question_id FROM questions WHERE subject_id = ? AND content = ?", (q.subject_id, q.content))
            row = cursor.fetchone()
            
            if row:
                q_id = row[0]
                conn.execute("""
                    UPDATE questions 
                    SET option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_answer = ?, difficulty_level = ?
                    WHERE question_id = ?
                """, (q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer, q.difficulty_level, q_id))
            else:
                conn.execute("""
                    INSERT INTO questions (subject_id, content, option_a, option_b, option_c, option_d, correct_answer, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (q.subject_id, q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer, q.difficulty_level))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_question(self, question_id: int):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM questions WHERE question_id = ?", (question_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def import_questions_from_csv(self, file_path: str):
        rows_to_process = []
        with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None) 
            
            if headers and "Subject" not in headers[0]:
                pass

            for row in reader:
                if len(row) < 8: continue
                rows_to_process.append(row)
        
        if not rows_to_process:
            raise ValueError("No valid questions found in CSV")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            for row in rows_to_process:
                subj_name, content, a, b, c, d, correct, level = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                
                cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = ?", (subj_name,))
                s_row = cursor.fetchone()
                if not s_row:
                    cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (subj_name,))
                    subject_id = cursor.lastrowid
                else:
                    subject_id = s_row[0]

                cursor.execute("SELECT question_id FROM questions WHERE subject_id = ? AND content = ?", (subject_id, content))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("""
                        UPDATE questions 
                        SET option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_answer = ?, difficulty_level = ?
                        WHERE question_id = ?
                    """, (a, b, c, d, correct, level, existing[0]))
                else:
                    cursor.execute("""
                        INSERT INTO questions (subject_id, content, option_a, option_b, option_c, option_d, correct_answer, difficulty_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (subject_id, content, a, b, c, d, correct, level))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class ExamService:
    def create_exam(self, admin: Admin, subject: Subject, name: str, duration: int, questions: List[Question]):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO exams (subject_id, exam_name, duration, created_by) VALUES (?, ?, ?, ?)",
                           (subject.subject_id, name, duration, admin.user_id))
            exam_id = cursor.lastrowid
            
            details = [(exam_id, q.question_id) for q in questions]
            cursor.executemany("INSERT INTO exam_details (exam_id, question_id) VALUES (?, ?)", details)
            conn.commit()
            return exam_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_auto_exam(self, admin: Admin, subject: Subject, name: str, duration: int, 
                         count_easy: int, count_medium: int, count_hard: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question_id, difficulty_level FROM questions WHERE subject_id = ?", (subject.subject_id,))
        rows = cursor.fetchall()
        conn.close()

        easy_qs = [r[0] for r in rows if r[1].lower() == 'easy']
        medium_qs = [r[0] for r in rows if r[1].lower() == 'medium']
        hard_qs = [r[0] for r in rows if r[1].lower() == 'hard']

        if len(easy_qs) < count_easy:
            raise ValueError(f"Not enough EASY questions (Requested: {count_easy}, Available: {len(easy_qs)})")
        if len(medium_qs) < count_medium:
            raise ValueError(f"Not enough MEDIUM questions (Requested: {count_medium}, Available: {len(medium_qs)})")
        if len(hard_qs) < count_hard:
            raise ValueError(f"Not enough HARD questions (Requested: {count_hard}, Available: {len(hard_qs)})")

        selected_ids = (
            random.sample(easy_qs, count_easy) +
            random.sample(medium_qs, count_medium) +
            random.sample(hard_qs, count_hard)
        )
        
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO exams (subject_id, exam_name, duration, created_by) VALUES (?, ?, ?, ?)",
                           (subject.subject_id, name, duration, admin.user_id))
            exam_id = cursor.lastrowid
            
            details = [(exam_id, qid) for qid in selected_ids]
            cursor.executemany("INSERT INTO exam_details (exam_id, question_id) VALUES (?, ?)", details)
            conn.commit()
            return exam_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_exams_by_subject(self, subject_id: int) -> List[Exam]:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT exam_id, subject_id, exam_name, duration, created_by FROM exams WHERE subject_id = ?", (subject_id,))
        exam_rows = cursor.fetchall()
        
        exams = []
        for r in exam_rows:
            e = Exam(r[0], r[1], r[2], r[3], r[4])
            cursor.execute("""
                SELECT q.question_id, q.subject_id, q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer, q.difficulty_level
                FROM questions q
                JOIN exam_details ed ON q.question_id = ed.question_id
                WHERE ed.exam_id = ?
            """, (e.exam_id,))
            q_rows = cursor.fetchall()
            for qr in q_rows:
                e.add_question(Question(qr[0], qr[1], qr[2], qr[3], qr[4], qr[5], qr[6], qr[7], qr[8]))
            exams.append(e)
            
        conn.close()
        return exams

class ResultService:
    def start_exam(self, student: Student, exam: Exam) -> Dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT result_id, start_time, score, status 
            FROM results 
            WHERE student_id = ? AND exam_id = ?
        """, (student.user_id, exam.exam_id))
        row = cursor.fetchone()
        
        if row:
            if row[3] == 'completed':
                conn.close()
                return {"status": "completed", "score": row[2]}
            else:
                conn.close()
                start_time = datetime.fromisoformat(row[1])
                elapsed = (datetime.now() - start_time).total_seconds()
                remaining = (exam.duration * 60) - elapsed
                
                return {
                    "status": "in_progress", 
                    "result_id": row[0], 
                    "remaining_seconds": max(0, remaining),
                    "saved_answers": self.get_saved_answers(row[0])
                }
        else:
            start_time = datetime.now()
            cursor.execute("""
                INSERT INTO results (exam_id, student_id, score, submit_time, status, start_time) 
                VALUES (?, ?, 0, ?, 'in_progress', ?)
            """, (exam.exam_id, student.user_id, "", start_time.isoformat()))
            result_id = cursor.lastrowid
            
            for q in exam.questions:
                cursor.execute("INSERT INTO result_details (result_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, 0)",
                               (result_id, q.question_id, ""))
            
            conn.commit()
            conn.close()
            return {
                "status": "new",
                "result_id": result_id,
                "remaining_seconds": exam.duration * 60,
                "saved_answers": {}
            }

    def get_saved_answers(self, result_id) -> Dict[int, str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question_id, selected_answer FROM result_details WHERE result_id = ?", (result_id,))
        rows = cursor.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def save_answer_progress(self, result_id, question_id, answer):
        conn = get_connection()
        try:
            conn.execute("UPDATE result_details SET selected_answer = ? WHERE result_id = ? AND question_id = ?",
                         (answer, result_id, question_id))
            conn.commit()
        except: pass
        finally: conn.close()

    def finish_exam(self, result_id, exam: Exam) -> Result:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT question_id, selected_answer FROM result_details WHERE result_id = ?", (result_id,))
        rows = cursor.fetchall()
        answers = {r[0]: r[1] for r in rows}
        
        correct_count = 0
        total = len(exam.questions)
        
        for q in exam.questions:
            user_ans = answers.get(q.question_id, "")
            is_correct = user_ans == q.correct_answer
            if is_correct: correct_count += 1
            
            cursor.execute("UPDATE result_details SET is_correct = ? WHERE result_id = ? AND question_id = ?",
                           (1 if is_correct else 0, result_id, q.question_id))
        
        score = (correct_count / total * 10.0) if total > 0 else 0
        now_str = datetime.now().isoformat()
        
        cursor.execute("UPDATE results SET score = ?, status = 'completed', submit_time = ? WHERE result_id = ?",
                       (score, now_str, result_id))
        conn.commit()
        conn.close()
        
        return Result(result_id, exam.exam_id, 0, score, now_str)

    def delete_result(self, result_id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM result_details WHERE result_id = ?", (result_id,))
            conn.execute("DELETE FROM results WHERE result_id = ?", (result_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_student_history(self, student_id: int) -> List[Result]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.result_id, r.exam_id, r.score, r.submit_time, e.exam_name, s.subject_name
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            JOIN subjects s ON e.subject_id = s.subject_id
            WHERE r.student_id = ? AND r.status = 'completed'
            ORDER BY r.submit_time DESC
        """, (student_id,))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            res = Result(r[0], r[1], student_id, r[2], r[3])
            res.exam_name = r[4]
            res.subject_name = r[5]
            history.append(res)
        return history

    def get_all_results(self) -> List[Result]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.result_id, r.exam_id, r.student_id, r.score, r.submit_time, 
                   e.exam_name, s.subject_name, u.full_name, r.status
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            JOIN subjects s ON e.subject_id = s.subject_id
            JOIN users u ON r.student_id = u.user_id
            WHERE r.status = 'completed'
            ORDER BY r.submit_time DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            res = Result(r[0], r[1], r[2], r[3], r[4])
            res.exam_name = r[5]
            res.subject_name = r[6]
            res.student_name = r[7]
            history.append(res)
        return history

    def get_result_details(self, result_id: int) -> Result:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.result_id, r.exam_id, r.student_id, r.score, r.submit_time, e.exam_name
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            WHERE r.result_id = ?
        """, (result_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        result = Result(row[0], row[1], row[2], row[3], row[4])
        result.exam_name = row[5]
        
        cursor.execute("""
            SELECT rd.result_detail_id, rd.question_id, rd.selected_answer, rd.is_correct,
                   q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer
            FROM result_details rd
            JOIN questions q ON rd.question_id = q.question_id
            WHERE rd.result_id = ?
        """, (result_id,))
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
             rd = ResultDetail(r[0], result_id, r[1], r[2], r[3])
             rd.question_content = r[4]
             rd.options = {'a': r[5], 'b': r[6], 'c': r[7], 'd': r[8]}
             rd.correct_answer = r[9]
             result.add_detail(rd)
             
        return result
