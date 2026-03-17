import sqlite3
import time
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g, make_response

app = Flask(__name__)
app.secret_key = 'OMEGA_ROOT_KEY_9988'
DATABASE = 'secure_portal.db'

# --- DATABASE SETUP ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None) 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY, admin_pin TEXT)')
        db.execute('DELETE FROM system_config')
        # FLAG 3 is the PIN itself!
        db.execute("INSERT INTO system_config (id, admin_pin) VALUES (1, 'CTF{TIME_BASED_BLIND_EXTRACTION_SUCCESS}')")

init_db()

# --- ROUTES ---

# THIS FIXES THE 404 ERROR! Both URLs now point to the decoy front door.
@app.route('/')
@app.route('/login')
def index():
    return render_template('login.html')

# RABBIT HOLES (To waste AI and scanner time)
@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

# STAGE 1, 2, & 3: THE HONEYPOT, THE WAF, AND THE BLIND EXTRACTION
@app.route('/api/v3/auth', methods=['POST'])
def auth():
    data = request.get_json() or {}
    username = data.get('username', '')
    pin_attempt = data.get('pin', '')
    
    # FLAG 1: THE HONEYPOT TRAP
    if "' OR" in username or "UNION" in username.upper() or "'=" in username:
        return jsonify({
            "status": "success",
            "message": "WARNING: DECEPTION NODE ACTIVATED. UNAUTHORIZED SCAN DETECTED.",
            "flag_1": "CTF{HONEYPOT_DECEPTION_TRAP_TRIGGERED}"
        })
        
    # --- YOUR HOST BACKDOOR (Bypasses everything!) ---
    if username == 'host_admin' and pin_attempt == '1234':
        session['auth_level'] = 'admin'
        return jsonify({"status": "processing_complete", "auth": "success"})
    # -------------------------------------------------
        
    # FLAG 2: THE WAF BYPASS 
    if request.headers.get('X-WAF-Debug-Bypass') != 'true':
        return jsonify({"error": "WAF BLOCK: Malformed Request. Secure Header Missing."}), 403

    # FLAG 3: TIME-BASED BLIND EXTRACTION
    db = get_db()
    cur = db.execute("SELECT admin_pin FROM system_config WHERE id = 1")
    real_pin = cur.fetchone()[0]
    
    response = make_response(jsonify({"status": "processing_complete", "auth": "failed"}))
    response.headers['X-Flag-2-WAF-Bypassed'] = 'CTF{WAF_BYPASS_HEADER_SMUGGLING}'
    
    # The vulnerability: Timing attack
    if pin_attempt and real_pin.startswith(pin_attempt):
        time.sleep(0.5) 
        if pin_attempt == real_pin:
            session['auth_level'] = 'admin'
            response.set_data(jsonify({"status": "processing_complete", "auth": "success"}).data)
            
    return response

# STAGE 4 & 6: BIOMETRICS AND ROOT CONTROL
@app.route('/dashboard')
def dashboard():
    if session.get('auth_level') != 'admin':
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/api/v3/telemetry', methods=['POST'])
def telemetry():
    if session.get('auth_level') != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    
    # FLAG 4: BIOMETRIC SPOOFING
    cursor_variance = data.get('cursor_variance', 0)
    typing_wpm = data.get('typing_wpm', 0)
    
    if 45 <= cursor_variance <= 55 and 110 <= typing_wpm <= 120:
        return jsonify({
            "status": "biometrics_accepted",
            "flag_4": "CTF{BEHAVIORAL_BIOMETRICS_CONTINUOUS_SPOOF}",
            "script": "document.getElementById('biometric-lock').style.display='none'; document.getElementById('core-ui').style.display='block'; window.sessionStabilized=true;"
        })
        
    return jsonify({"error": "biometric_anomaly_detected"}), 403

# STAGE 5: FIRMWARE REVERSE ENGINEERING
@app.route('/download/firmware')
def download_firmware():
    if session.get('auth_level') != 'admin':
        return "Unauthorized", 401
    
    fake_binary_content = b'\x00\x01\x00\x00' * 10 + b'__wasm_module_init__' + b'\x00\x00' * 5
    secret_data = b"DEBUG_MODE_ENABLED... FLAG_5: CTF{WASM_FIRMWARE_REVERSE_ENGINEERED} ... OVERRIDE_MASTER_KEY: 0x99AABBCC_OMEGA"
    
    response = make_response(fake_binary_content + base64.b64encode(secret_data) + b'\x00\x00\xFF\xFF')
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=iot_node_firmware.wasm'
    return response

# STAGE 6: THE ENDGAME
@app.route('/api/core_override', methods=['POST'])
def core_override():
    if session.get('auth_level') != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    if data.get('master_key') == '0x99AABBCC_OMEGA':
        return jsonify({
            "status": "ROOT_GRANTED",
            "flag_6": "CTF{ROOT_IOT_NETWORK_COMPROMISED}"
        })
    return jsonify({"error": "INVALID MASTER KEY"}), 403

if __name__ == '__main__':
    app.run(debug=True, port=5000)
