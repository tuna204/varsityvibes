from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
import os
import sqlite3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import random
import string

# --- Config ---
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret123"
DB_FILE = 'database.db'

# --- Initialize DB ---
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        filename TEXT,
        owner_address TEXT,
        irys_address TEXT,
        rule TEXT,
        tx_id TEXT,
        status TEXT,
        upload_time TEXT
    )
''')
conn.commit()
conn.close()

# --- Helper function to generate TX ID ---
def generate_tx_id():
    return "devnet_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

@app.route("/loading")
def loading():
    return render_template("loading.html")

# --- Upload Route ---
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        owner_address = request.form.get("owner_address")
        irys_address = request.form.get("irys_address")
        rule = request.form.get("rule")

        if not file or not owner_address or not irys_address or not rule:
            flash("All fields are required!")
            return redirect(url_for("upload_file"))

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        tx_id = generate_tx_id()
        status = "Confirmed"  # immediately confirmed

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO files (id, filename, owner_address, irys_address, rule, tx_id, status, upload_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), filename, owner_address, irys_address, rule, tx_id, status, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

        flash(f"✅ File uploaded successfully! TX ID: {tx_id}")
        return redirect(url_for("upload_file"))

    return render_template("upload.html")

# --- Files Dashboard ---
@app.route("/files")
def files():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, owner_address, irys_address, rule, tx_id, status FROM files ORDER BY upload_time DESC")
    files = c.fetchall()
    conn.close()
    return render_template("files.html", files=files)

# --- Secure Download Route ---
@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    code = request.args.get("code", "")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT rule FROM files WHERE filename = ?", (filename,))
    row = c.fetchone()
    conn.close()

    if not row:
        flash("❌ File not found")
        return redirect(url_for("files"))

    rule = row[0]
    if code.lower() != rule.strip().lower():  # case-insensitive check
        flash("❌ Access denied: Invalid code")
        return redirect(url_for("files"))

    flash("✅ Access granted! Downloading file...")
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




