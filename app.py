from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import re

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate(r"E:\git files\ride-sharing-b7053-firebase-adminsdk-fbsvc-45494f1901.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Email validation for VIT domains
def is_valid_vit_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@(vitstudent\.ac\.in|vit\.ac\.in)$')
    return pattern.match(email)

# Flask Routes
@app.route('/')
def authentication():
    return render_template('authentication.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    full_name = request.form.get('full-name')
    university_id = request.form.get('university-id')
    gender = request.form.get('gender')
    password = request.form.get('password')

    if not (email and full_name and university_id and gender and password):
        return "All fields are required!", 400

    if not is_valid_vit_email(email):
        return "Invalid email domain. Please use your VIT email.", 400

    # Check if user already exists
    doc_ref = db.collection('users').document(email)
    doc = doc_ref.get()

    if doc.exists:
        return "Email already registered. Please log in.", 400

    # Store user data
    doc_ref.set({
        'email': email,
        'full_name': full_name,
        'university_id': university_id,
        'gender': gender,
        'password': password
    })

    print("User registered successfully!")
    return redirect(url_for('authentication'))

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form.get('email')
    password = request.form.get('password')

    if not (email and password):
        return "Email and password are required!", 400

    if not is_valid_vit_email(email):
        return "Invalid email domain. Please use your VIT email.", 400

    # Check if user exists in Firebase Firestore
    doc_ref = db.collection('users').document(email)
    doc = doc_ref.get()

    if not doc.exists or doc.to_dict().get('password') != password:
        return "Invalid email or password!", 401

    print(f"User {email} signed in successfully!")
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)

