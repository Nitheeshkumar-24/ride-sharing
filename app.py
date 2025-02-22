from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
import datetime
from firebase_admin import credentials, firestore
import re

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate(r"e:\git files\ride-sharing-b7053-firebase-adminsdk-fbsvc-45494f1901.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Email validation for VIT domains
def is_valid_vit_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@(vitstudent\.ac\.in|vit\.ac\.in)$')
    return pattern.match(email)

# Function to get next ride_id
def get_next_ride_id():
    rides_ref = db.collection('rides').order_by('ride_id', direction=firestore.Query.DESCENDING).limit(1)
    last_ride = rides_ref.stream()
    for ride in last_ride:
        return ride.to_dict

# Flask Routes
@app.route('/')
def authentication():
    return render_template('authentication.html')
'''
@app.route('/index')
def index():
    return render_template('index.html')'''



@app.route('/ride_creation_page', methods=['GET', 'POST'])
def ride_creation_page():
    if request.method == 'GET':
        return render_template('ride_creation.html')

    try:
        data = request.get_json()
        ride_id = get_next_ride_id()
        from_location = data.get('from_location')
        to_location = data.get('to_location')
        ride_date_and_time = datetime.datetime.strptime(data.get('ride_date_and_time'), '%Y-%m-%dT%H:%M')
        total_seats = int(data.get('total_seats'))
        available_seats = total_seats
        total_price = float(data.get('total_price'))
        per_person_cost = total_price / total_seats
        vehicle_id = int(data.get('vehicle_id'))
        passenger_emails = data.get('passenger_emails', [])

        # Store data in rides collection
        ride_data = {
            'ride_id': ride_id,
            'from_location': from_location,
            'to_location': to_location,
            'ride_date_and_time': ride_date_and_time,
            'total_seats': total_seats,
            'available_seats': available_seats,
            'total_price': total_price,
            'per_person_cost': per_person_cost,
            'vehicle_id': vehicle_id
        }
        db.collection('rides').document(str(ride_id)).set(ride_data)

        # Store data in passenger_booking collection
        for email in passenger_emails:
            booking_data = {
                'ride_id': ride_id,
                'passenger_email': email,
                'seat_count': len(passenger_emails),
                'total_amount': total_price
            }
            db.collection('passenger_booking').add(booking_data)

        return render_template('ride_creation.html')

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Failed to create ride and store bookings'}), 500


@app.route('/filter_page')
def filter_page():
    return render_template('filter.html')


@app.route('/ride_history_page')
def ride_history_page():
    return render_template('ride_history.html')


@app.route('/my_rides_page')
def my_rides_page():
    return render_template('my_rides.html')

@app.route('/index')
def index():
    try:
        # Get all ride documents from Firestore
        rides_ref = db.collection('rides')
        rides = [ride.to_dict() for ride in rides_ref.stream()]

        return render_template('index.html', rides=rides)

    except Exception as e:
        print("Error:", str(e))
        return "Failed to fetch rides", 500


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

