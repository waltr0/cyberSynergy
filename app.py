import sqlite3
import jwt
from flask import Flask, request, jsonify, make_response, render_template_string

app = Flask(__name__)

# THE VULNERABILITY: An incredibly weak cryptographic secret that Hashcat can crack using rockyou.txt
JWT_SECRET = "matrix" 

def init_db():
    conn = sqlite3.connect('university.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, role TEXT, hidden_flag TEXT)')
    
    # Clear old data and insert our targets
    c.execute('DELETE FROM users')
    c.execute("INSERT INTO users VALUES ('admin', 'SuperSecureComplexPass123!@#', 'admin', 'CTF{SQLMAP_DATABASE_DUMP_EXPERT}')")
    c.execute("INSERT INTO users VALUES ('student', 'password', 'user', 'none')")
    
    conn.commit()
    conn.close()

init_db()

# --- PHASE 1: THE DECOY FRONT DOOR ---
@app.route('/')
def index():
    # A completely secure, static page. Hackers must use Gobuster to find the real target.
    return render_template_string("""
    <html>
        <body style="background:#f4f4f4; font-family:monospace; text-align:center; padding-top:10vh; color:#333;">
            <h2>UNIVERSITY IT SERVICES</h2>
            <p>The standard student login portal is currently undergoing maintenance.</p>
            <p>All legacy systems have been migrated.</p>
            </body>
    </html>
    """)

# --- PHASE 2: THE BLIND SQL INJECTION ENDPOINT ---
@app.route('/api/v2/legacy_auth', methods=['GET', 'POST'])
def legacy_auth():
    if request.method == 'GET':
        return jsonify({"status": "ONLINE", "message": "Submit POST request with 'username' and 'password'", "FLAG_1": "CTF{GOBUSTER_RECON_MASTER}"})

    data = request.get_json() or request.form
    username = data.get('username', '')
    password = data.get('password', '')

    conn = sqlite3.connect('university.db')
    c = conn.cursor()
    
    # THE FLAW: Raw string concatenation. The database engine will process any injected SQL operators.
    query = f"SELECT username, role FROM users WHERE username = '{username}' AND password = '{password}'"
    
    try:
        c.execute(query)
        user = c.fetchone()
        conn.close()

        if user:
            # Generate a JSON Web Token
            token = jwt.encode({"user": user[0], "role": user[1]}, JWT_SECRET, algorithm="HS256")
            
            resp = make_response(jsonify({"message": "Authentication successful", "redirect": "/dashboard"}))
            resp.set_cookie('auth_token', token)
            return resp
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        # Silent failure. No helpful error messages for the hacker.
        conn.close()
        return jsonify({"error": "Internal Server Error"}), 500

# --- PHASE 3: THE JWT FORGERY VAULT ---
@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('auth_token')
    
    if not token:
        return jsonify({"error": "Access Denied. Missing Token."}), 401
        
    try:
        # The server verifies the cryptographic signature
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        if decoded.get('role') == 'admin':
            return render_template_string("""
                <body style="background:#000; color:#0f0; font-family:monospace; text-align:center; padding-top:20vh;">
                    <h1>SYSTEM ROOT ACCESSED</h1>
                    <h2>FLAG 3: CTF{JWT_CRYPTOGRAPHIC_FORGERY_SUCCESS}</h2>
                </body>
            """)
        else:
            return render_template_string("""
                <body style="background:#111; color:#ccc; font-family:monospace; text-align:center; padding-top:20vh;">
                    <h1>Student Dashboard</h1>
                    <p>Welcome, {{ user }}. You have basic user privileges.</p>
                    <p>Admin clearance required for internal network access.</p>
                </body>
            """, user=decoded.get('user'))
            
    except jwt.InvalidSignatureError:
        return jsonify({"error": "FATAL: Cryptographic Signature Invalid. Incident Logged."}), 403
    except Exception as e:
        return jsonify({"error": "Token parsing failed."}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
