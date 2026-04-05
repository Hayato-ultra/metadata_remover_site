import os
import subprocess
import uuid
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = "temp"
EXIFTOOL_PATH = r"C:\exiftool\exiftool.exe" # Verified path

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    file = request.files.get("file")

    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Create a unique filename to avoid collisions
    unique_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    input_filename = f"{unique_id}{ext}"
    input_path = os.path.join(UPLOAD_FOLDER, input_filename)
    
    file.save(input_path)

    try:
        # Remove metadata using exiftool
        result = subprocess.run([
            EXIFTOOL_PATH,
            "-all=",
            "-overwrite_original",
            input_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            os.remove(input_path)
            return jsonify({"error": f"ExifTool error: {result.stderr}"}), 500

        # Send the cleaned file
        return send_file(input_path, as_attachment=True, download_name=f"cleaned_{file.filename}")

    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)