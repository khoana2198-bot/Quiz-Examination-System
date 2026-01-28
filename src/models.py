from datetime import date, datetime
from typing import List, Dict, Optional

class User:
    def __init__(self, user_id: int, username: str, password_hash: str, full_name: str, dob: date, role: str):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.dob = dob
        self.role = role

    def __str__(self):
        return f"User(id={self.user_id}, name={self.full_name}, role={self.role})"


class Admin(User):
    def __init__(self, user_id: int, username: str, password_hash: str, full_name: str, dob: date):
        super().__init__(user_id, username, password_hash, full_name, dob, role="admin")


class Student(User):
    def __init__(self, user_id: int, username: str, password_hash: str, full_name: str, dob: date):
        super().__init__(user_id, username, password_hash, full_name, dob, role="student")


class Subject:
    def __init__(self, subject_id: int, subject_name: str):
        self.subject_id = subject_id
        self.subject_name = subject_name

    def __str__(self):
        return self.subject_name


class Question:
    def __init__(self, question_id: int, subject_id: int, content: str, 
                 option_a: str, option_b: str, option_c: str, option_d: str, 
                 correct_answer: str, difficulty_level: str):
        self.question_id = question_id
        self.subject_id = subject_id
        self.content = content
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d
        self.correct_answer = correct_answer  # 'a', 'b', 'c', or 'd'
        self.difficulty_level = difficulty_level

    def __str__(self):
        return f"Question({self.question_id}): {self.content[:30]}..."


class Exam:
    def __init__(self, exam_id: int, subject_id: int, exam_name: str, duration: int, created_by: int, 
                 start_date: str = None, end_date: str = None, status: str = 'draft'):
        self.exam_id = exam_id
        self.subject_id = subject_id
        self.exam_name = exam_name
        self.duration = duration  # in minutes
        self.created_by = created_by
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.questions: List[Question] = [] # Can satisfy ExamDetails logic by ordering this list

    def add_question(self, question: Question):
        self.questions.append(question)

    def __str__(self):
        return f"Exam: {self.exam_name} ({self.duration} mins)"


class ResultDetail:
    def __init__(self, result_detail_id: int, result_id: int, question_id: int, selected_answer: str, is_correct: bool):
        self.result_detail_id = result_detail_id
        self.result_id = result_id
        self.question_id = question_id
        self.selected_answer = selected_answer
        self.is_correct = is_correct


class Result:
    def __init__(self, result_id: int, exam_id: int, student_id: int, score: float, submit_time: datetime):
        self.result_id = result_id
        self.exam_id = exam_id
        self.student_id = student_id
        self.score = score
        self.submit_time = submit_time
        self.details: List[ResultDetail] = []

    def add_detail(self, detail: ResultDetail):
        self.details.append(detail)

    def __str__(self):
        return f"Result(student={self.student_id}, exam={self.exam_id}, score={self.score})"
