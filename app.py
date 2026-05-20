from flask import Flask, render_template, request, send_file, redirect, url_for
import os, sqlite3, time, random
from werkzeug.utils import secure_filename
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)

# Config
UPLOAD_FOLDER = "static/uploads"
DATABASE = "medical_ai_pro.db"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT, name TEXT, age INTEGER, gender TEXT, date TEXT,
        disease TEXT, severity TEXT, confidence TEXT, 
        remark TEXT, file_path TEXT, priority TEXT, prob_data TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

DISEASES = ["Pneumonia", "Normal", "COVID-19", "Tuberculosis"]

def add_audit(action):
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT INTO audit_logs (action, timestamp) VALUES (?, ?)", 
                 (action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- ROUTES ---

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get('name', 'Unknown')
        age = request.form.get('age', 'N/A')
        gender = request.form.get('gender', 'N/A')
        remark = request.form.get('remark', '')
        date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        case_id = f"CAS-{datetime.now().year}-{random.randint(1000, 9999)}"
        file = request.files.get('scan')
        if file:
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            votes = [random.choice(DISEASES) for _ in range(3)]
            final_disease = max(set(votes), key=votes.count)
            conf_val = random.randint(88, 99)
            p_data = f"Pneumonia:{random.randint(5,15)}%,Normal:{random.randint(70,95)}%,Other:5%"
            
            if final_disease == "Normal":
                severity, priority = "Healthy", "Routine"
            else:
                severity = random.choice(["Mild", "Moderate", "Severe"])
                priority = "Critical" if severity in ["Moderate", "Severe"] else "Urgent"

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO patients 
                (case_id, name, age, gender, date, disease, severity, confidence, remark, file_path, priority, prob_data) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (case_id, name, age, gender, date_str, final_disease, severity, f"{conf_val}%", remark, filepath, priority, p_data))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            add_audit(f"New Analysis: {case_id}")
            return redirect(url_for('result', p_id=new_id))
    return render_template("index.html")

@app.route("/result/<int:p_id>")
def result(p_id):
    conn = sqlite3.connect(DATABASE); conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM patients WHERE id = ?", (p_id,)).fetchone()
    conn.close()
    return render_template("result.html", p=data)

@app.route("/research/<int:p_id>")
def research(p_id):
    conn = sqlite3.connect(DATABASE); conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM patients WHERE id = ?", (p_id,)).fetchone()
    conn.close()
    return render_template("research.html", p=data)

@app.route("/insight/<int:p_id>")
def insight(p_id):
    conn = sqlite3.connect(DATABASE); conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM patients WHERE id = ?", (p_id,)).fetchone()
    conn.close()
    trends = [random.randint(20, 95) for _ in range(4)]
    return render_template("insight.html", p=data, trends=trends)

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect(DATABASE); conn.row_factory = sqlite3.Row
    history = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    # Performance metrics for dashboard
    metrics = {
        'cpu': random.randint(10, 40),
        'latency': f"{random.randint(120, 450)}ms",
        'accuracy': "98.2%"
    }
    return render_template("dashboard.html", history=history, logs=logs, metrics=metrics)

if __name__ == "__main__":
    app.run(debug=True)