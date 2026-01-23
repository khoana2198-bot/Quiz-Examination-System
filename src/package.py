import zipfile
import os

files = [
    "gui_app.py",
    "models.py",
    "services.py",
    "database.py",
    "sample_questions.csv",
    "HUONG_DAN.txt",
    "quiz_app.db"
]

output_zip = "Quiz_Examination_System_Final.zip"

try:
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if os.path.exists(file):
                zf.write(file)
                print(f"Added {file}")
            else:
                print(f"Warning: {file} not found")
    print(f"Successfully created {output_zip}")
except Exception as e:
    print(f"Error: {e}")
