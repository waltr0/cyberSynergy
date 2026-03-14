import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = 'CTF_SECRET_KEY_DONT_SHARE'
DATABASE = 'university.db'

# --- DATABASE SETUP ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        # Create Users Table
        db.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, bio TEXT)''')
        # Create Feedback Table
        db.execute('''CREATE TABLE IF NOT EXISTS feedback 
                     (id INTEGER PRIMARY KEY, message TEXT)''')
        
        # Check if empty, then add dummy data
        cur = db.execute('SELECT count(*) FROM users')
        if cur.fetchone()[0] == 0:
            db.execute("INSERT INTO users (username, password, role, bio) VALUES (?, ?, ?, ?)",
                       ('admin', 'Sup3rS3cr3tP@ssw0rd!', 'admin', 'System Administrator - Do Not Touch'))
            db.execute("INSERT INTO users (username, password, role, bio) VALUES (?, ?, ?, ?)",
                       ('john_doe', 'password123', 'student', 'Just a regular CS student.'))
            db.execute("INSERT INTO users (username, password, role, bio) VALUES (?, ?, ?, ?)",
                       ('alice_wonder', 'alice2024', 'student', 'I love cryptography!'))
            db.commit()

# --- THE "AI TRAP" WAF ---
def is_malicious(input_str):
    """
    A basic WAF that blocks standard AI SQLi payloads.
    Participants must use encoding or alternative SQL comments to bypass this.
    """
    blacklist = [" OR ", " UNION ", "DROP ", "--", "/*"]
    input_upper = input_str.upper()
    for bad in blacklist:
        if bad in input_upper:
            return True
    return False

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

# VULNERABILITY 1: SQL Injection (Login Bypass) 
# AI Trap: The 'is_malicious' check prevents lazy 'OR 1=1' attacks.
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # The AI Trap: Block standard attacks
        if is_malicious(username) or is_malicious(password):
            return render_template('login.html', error="⚠️ WAF BLOCKED: Malicious Pattern Detected.")

        # The Vulnerability: String formatting allows injection if WAF is bypassed
        # Hint: Try using ' # to comment out the rest
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        try:
            db = get_db()
            cur = db.execute(query)
            user = cur.fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                error = "Access Denied: Invalid Credentials."
        except Exception as e:
            # Blind SQLi: Don't show the actual error to the user!
            error = "Database Error: Transaction Failed."

    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# VULNERABILITY 2: Insecure Direct Object Reference (IDOR) 
# The 'id' parameter is visible and changeable.
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = request.args.get('id', session['user_id']) # Defaults to current user, but changeable
    db = get_db()
    # Vulnerability: No check if session['user_id'] == user_id
    cur = db.execute('SELECT username, role, bio FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    
    return render_template('profile.html', user=user)

# VULNERABILITY 3: Stored XSS 
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        msg = request.form['message']
        
        # AI Trap: AI usually tries <script>alert(1)</script>
        # We strip <script> tags, forcing them to use <img onerror=...>
        if "<script>" in msg:
            return render_template('feedback.html', error="Nice try, script kiddy.")
            
        db = get_db()
        db.execute("INSERT INTO feedback (message) VALUES (?)", (msg,))
        db.commit()
        return redirect(url_for('feedback'))

    db = get_db()
    messages = db.execute('SELECT message FROM feedback').fetchall()
    return render_template('feedback.html', messages=messages)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)