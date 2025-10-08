from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import hashlib
import re
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # For future file uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('forensic.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS evidence
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  hash TEXT UNIQUE,
                  profile TEXT,
                  keywords TEXT,
                  description TEXT)''')
    
    # Sample data (known forensic profiles)
    samples = [
        ('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'Empty file profile', '[]', 'Known benign empty file'),
        ('5d41402abc4b2a76b9719d911017c592', 'Hello world profile', '["hello","world"]', 'Known test string'),
        ('d41d8cd98f00b204e9800998ecf8427e', 'MD5 zero hash profile', '[]', 'Known zeroed data in forensics')
    ]
    for hash_val, profile, keywords, desc in samples:
        c.execute("INSERT OR IGNORE INTO evidence (hash, profile, keywords, description) VALUES (?, ?, ?, ?)",
                  (hash_val, profile, keywords, desc))
    conn.commit()
    conn.close()

init_db()

def profile_evidence(evidence_text):
    """Profile evidence: Compute SHA-256 hash and extract keywords."""
    hash_val = hashlib.sha256(evidence_text.encode()).hexdigest()
    # Simple keyword extraction (words longer than 3 chars)
    keywords = re.findall(r'\b\w{4,}\b', evidence_text.lower())
    keywords = list(set(keywords))  # Unique
    profile = f"Length: {len(evidence_text)}, Keywords: {len(keywords)}"
    return hash_val, profile, str(keywords)

def match_evidence(input_hash, input_keywords):
    """Match against DB: Exact hash or similarity score."""
    conn = sqlite3.connect('forensic.db')
    c = conn.cursor()
    c.execute("SELECT * FROM evidence WHERE hash = ?", (input_hash,))
    exact_match = c.fetchone()
    
    if exact_match:
        conn.close()
        return exact_match, 100  # Exact match score
    
    # Similarity: Keyword overlap percentage
    c.execute("SELECT hash, keywords, description FROM evidence")
    results = []
    for row in c.fetchall():
        db_keywords = eval(row[1]) if row[1] else []
        overlap = len(set(input_keywords) & set(db_keywords))
        score = (overlap / max(len(input_keywords), len(db_keywords), 1)) * 100 if input_keywords else 0
        if score > 0:
            results.append((row[0], row[2], score))
    
    # Sort by score descending
    results.sort(key=lambda x: x[2], reverse=True)
    conn.close()
    return results[0] if results else None, 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        evidence = request.form['evidence']
        if not evidence:
            return jsonify({'error': 'No evidence provided'}), 400
        
        input_hash, input_profile, input_keywords = profile_evidence(evidence)
        match_result, score = match_evidence(input_hash, eval(input_keywords) if input_keywords != '[]' else [])
        
        result = {
            'input_evidence': evidence,
            'input_hash': input_hash,
            'input_profile': input_profile,
            'input_keywords': input_keywords,
            'match': match_result[1] if isinstance(match_result, tuple) else match_result,
            'score': score
        }
        return jsonify(result)
    
    return render_template('scan.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        evidence = request.form['evidence']
        desc = request.form['description']
        hash_val, profile, keywords = profile_evidence(evidence)
        conn = sqlite3.connect('forensic.db')
        c = conn.cursor()
        c.execute("INSERT INTO evidence (hash, profile, keywords, description) VALUES (?, ?, ?, ?)",
                  (hash_val, profile, keywords, desc))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    
    conn = sqlite3.connect('forensic.db')
    c = conn.cursor()
    c.execute("SELECT * FROM evidence")
    db_data = c.fetchall()
    conn.close()
    return render_template('admin.html', data=db_data)

if __name__ == '__main__':
    app.run(debug=True)
