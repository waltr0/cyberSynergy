import sqlite3
import time
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = 'OMEGA_SECURE_KEY_99'

def init_db():
    conn = sqlite3.connect('secure_portal.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admin_keys (id INTEGER, key_value TEXT)')
    c.execute('DELETE FROM admin_keys')
    
    # Flag 1: Hidden deep in the database. No webpage will ever display this text.
    c.execute("INSERT INTO admin_keys VALUES (1, 'CTF{TIME_BASED_BLIND_SQLI_MASTER}')")
    conn.commit()
    conn.close()

init_db()

# --- FLAG 1: THE HONEYPOT & TIME-BASED SQL INJECTION ---
@app.route('/api/v3/auth', methods=['POST'])
def auth():
    data = request.get_json() or request.form
    username = data.get('username', '')
    password = data.get('password', '')
    
    # THE TRAP: Intelligent Deception Honeypot
    # If an AI or a script-kiddie uses obvious SQLi payloads, feed them a fake success.
    if "' OR" in username or "'=" in username or "UNION" in username.upper():
        return jsonify({
            "status": "success",
            "message": "Welcome Admin. Decoy Node Activated.",
            "flag": "CTF{HONEYPOT_DECEPTION_ACTIVATED_FAKE_FLAG}"
        })
        
    # THE HURDLE: The Hidden Header
    if request.headers.get('X-Admin-Debug-Route') != 'true':
        return jsonify({"error": "Standard login disabled. Use secure biometrics portal."}), 403

    # THE VULNERABILITY: Blind SQLi
    conn = sqlite3.connect('secure_portal.db')
    c = conn.cursor()
    
    query = f"SELECT * FROM admin_keys WHERE key_value LIKE '{password}%'"
    
    try:
        # If the hacker injects a time-delay payload (e.g. testing if the first letter is 'C'),
        # the server will hang. This is the ONLY way they can extract the flag.
        c.execute(query)
        result = c.fetchone()
        conn.close()
        
        # The server returns the exact same generic response whether the guess is right or wrong.
        if result:
            session['auth_level'] = 'admin'
            return jsonify({"status": "OK"})
        return jsonify({"status": "Failed"})
    except Exception as e:
        conn.close()
        return jsonify({"status": "Error"}), 500


# --- FLAG 2: CONTINUOUS BEHAVIORAL BIOMETRICS ---
@app.route('/admin_root')
def admin_root():
    if session.get('auth_level') != 'admin':
        return "ACCESS DENIED. Missing Authentication.", 401
        
    # The dashboard loads, but if the biometric heartbeat isn't established, it instantly dies.
    return render_template_string("""
        <html>
        <body style="background:#050505; color:#0f0; font-family:monospace; padding: 50px;">
            <h1 id="warning" style="color: #ff003c; text-shadow: 0 0 10px red;">VERIFYING BIOMETRIC RHYTHM... DO NOT MOVE.</h1>
            
            <div id="dashboard" style="display:none;">
                <h1>// MASTER CONTROL TERMINAL</h1>
                <h2 style="color: #0ff;">FLAG 2: CTF{BEHAVIORAL_BIOMETRICS_SPOOFED_SUCCESS}</h2>
                <hr style="border-color: #333;">
                <h3 style="color: #777;">Active Subsystems:</h3>
                <ul>
                    <li>Intelligent Deception Honeypot: <span style="color:#0f0">[ONLINE]</span></li>
                    <li>Android Remote PC Link (Live Location & Lock): <span style="color:#0f0">[CONNECTED]</span></li>
                    <li>Network Security Node: <span style="color:#0f0">[ACTIVE]</span></li>
                </ul>
            </div>
            
            <script>
                // The frontend trap: If the spoofed telemetry doesn't arrive every 500ms, kick them out.
                let rhythmValidated = false;
                
                setInterval(() => {
                    if (!rhythmValidated) {
                        document.body.innerHTML = "<h1 style='color:red; margin-top: 20%; text-align: center;'>SESSION TERMINATED:<br>BEHAVIORAL ANOMALY DETECTED.<br>CURSOR VELOCITY AND TYPING RHYTHM DO NOT MATCH ADMIN PROFILE.</h1>";
                    }
                    rhythmValidated = false; // reset for the next heartbeat
                }, 1500);
            </script>
        </body>
        </html>
    """)

@app.route('/api/v3/telemetry', methods=['POST'])
def telemetry():
    if session.get('auth_level') != 'admin':
        return "Unauthorized", 401
        
    data = request.get_json()
    
    # The specific behavioral rhythm required to keep the session alive
    cursor_variance = data.get('cursor_variance', 0)
    typing_speed_wpm = data.get('typing_wpm', 0)
    
    # The hacker must spoof these exact mathematical parameters!
    if 45 <= cursor_variance <= 55 and 110 <= typing_speed_wpm <= 120:
        return jsonify({
            "status": "biometrics_accepted", 
            "script": "document.getElementById('warning').style.display='none'; document.getElementById('dashboard').style.display='block'; rhythmValidated=true;"
        })
        
    return jsonify({"error": "biometric_mismatch"}), 403

if __name__ == '__main__':
    app.run(debug=True, port=5000)
