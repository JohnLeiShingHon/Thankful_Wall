from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
import os
import csv
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Directory to store uploaded images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CSV_FILE = 'data.csv'
VALID_GROUPS = ["D21", "Nephesh", "成人崇拜", "長青團契"]

# Load data from CSV on startup
def load_data():
    if not os.path.exists(CSV_FILE):
        return []

    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

# Save data to CSV
def save_data():
    with open(CSV_FILE, 'w', newline='') as file:
        fieldnames = ['group', 'text', 'image']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(messages)

# Load messages from CSV and uploads directory
messages = load_data()
for message in messages:
    if message['image'] and not os.path.exists(message['image']):
        messages.remove(message)

@app.route('/messages', methods=['POST'])
def add_message():
    """Endpoint to add a new message."""
    data = request.json

    # Validate group
    if 'group' not in data or data['group'] not in VALID_GROUPS:
        return jsonify({"error": "Invalid or missing group"}), 400

    # Create message
    message = {
        "text": data.get('text', ''),  # Optional text
        "image": data.get('image'),  # Optional image URL
        "group": data['group']
    }
    messages.append(message)
    save_data()  # Save to CSV

    return redirect(url_for('display_messages'))

@app.route('/display', methods=['GET'])
def display_messages():
    """Render the display page."""
    return render_template('display.html', messages=messages)

@app.route('/upload', methods=['POST'])
def upload_image():
    """Endpoint to upload an image."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    return jsonify({"image_url": f"/{image_path}"}), 201

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    """Serve uploaded images."""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/qrcode', methods=['GET'])
def generate_qr_code():
    """Generate and serve a QR code for the public IP URL."""
    public_ip_url = "http://20.243.178.136:5000"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(public_ip_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_path = "qrcode.png"
    img.save(img_path)

    return send_file(img_path, mimetype='image/png')

@app.route('/')
def home():
    """Redirect root URL to the display page."""
    return redirect(url_for('display_messages'))

if __name__ == '__main__':
    print("Server running at: http://20.243.178.136:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)