from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import re

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate(r"C:\git files\ride-sharing-b7053-firebase-adminsdk-fbsvc-45494f1901.json")
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

@app.route('/ride_creation_page')
def ride_creation_page():
    return render_template('ride_creation.html')


@app.route('/filter_page')
def filter_page():
    return render_template('filter.html')


@app.route('/ride_history_page')
def ride_history_page():
    return render_template('ride_history.html')


@app.route('/my_rides_page')
def my_rides_page():
    return render_template('my_rides.html')


@app.route('/register', methods=['POST'])
def register():
    try:
        email = request.form.get('email')
        full_name = request.form.get('full-name')
        university_id = request.form.get('university-id')
        gender = request.form.get('gender')
        password = request.form.get('password')

        if not (email and full_name and university_id and gender and password):
            return jsonify({'error': 'All fields are required!'}), 400

        if not is_valid_vit_email(email):
            return jsonify({'error': 'Invalid email domain. Please use your VIT email.'}), 400

        # Check if user already exists
        doc_ref = db.collection('users').document(email)
        doc = doc_ref.get()

        if doc.exists:
            return jsonify({'error': 'Email already registered. Please log in.'}), 400

        # Store user data in Firestore
        doc_ref.set({
            'email': email,
            'full_name': full_name,
            'university_id': university_id,
            'gender': gender,
            'password': password  # NOTE: Hash passwords in real-world applications!
        })

        print(f"User {email} registered successfully!")
        return jsonify({'message': 'Registration successful! Redirecting to login...'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Something went wrong!'}), 500

@app.route('/signin', methods=['POST'])
def signin():
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if not (email and password):
            return jsonify({'error': 'Email and password are required!'}), 400

        if not is_valid_vit_email(email):
            return jsonify({'error': 'Invalid email domain. Please use your VIT email.'}), 400

        doc_ref = db.collection('users').document(email)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({'error': 'Invalid email or password!'}), 401

        user_data = doc.to_dict()
        stored_password = user_data.get('password')

        # Directly compare plain text passwords
        if stored_password != password:
            return jsonify({'error': 'Invalid email or password!'}), 401

        print(f"User {email} signed in successfully!")
        return jsonify({'message': 'Login successful! Redirecting...'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Something went wrong!'}), 500
    

if __name__ == '__main__':
    app.run(debug=True)

