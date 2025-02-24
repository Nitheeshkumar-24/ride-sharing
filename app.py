from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import firebase_admin
import datetime
from firebase_admin import credentials, firestore
import re
import secrets, pytz

def provide_secret_key():
    return secrets.token_hex(16)

app = Flask(__name__)

app.secret_key = provide_secret_key()

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
    last_ride = list(rides_ref.stream())  # Convert to list

    if last_ride:  # Check if there are any rides
        return last_ride[0].to_dict().get('ride_id', 0) + 1
    else:
        return 1  # Start from 1 if no rides exist

# Flask Routes
@app.route('/')
def authentication():
    return render_template('authentication.html')
'''
@app.route('/index')
def index():
    return render_template('index.html')'''



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

        session['user_email'] = email
        print(f"User {email} signed in successfully!")
        return jsonify({'message': 'Login successful! Redirecting...'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Something went wrong!'}), 500
    
@app.route('/create_ride', methods=['POST'])
def create_ride():
    try:
        data = request.get_json()
        ride_id = get_next_ride_id()
        user_email = session['user_email']
        
        from_location = data.get('from')
        to_location = data.get('to')
        ride_date = data.get('date')
        ride_time = data.get('time')
        vehicle_id = data.get('vehicle')
        total_seats = int(data.get('passengers'))
        total_price = float(data.get('price'))
        current_member_count = 1
        per_person_cost = total_price / current_member_count

        # Convert to datetime
        ride_date_and_time = datetime.datetime.strptime(f"{ride_date} {ride_time}", "%Y-%m-%d %H:%M")

        # Firestore document
        ride_data = {
            'ride_id': ride_id,
            'current_member_count': current_member_count,
            'from_location': from_location,
            'to_location': to_location,
            'ride_date_and_time': ride_date_and_time,
            'total_seats': total_seats,
            'available_seats': total_seats,
            'total_price': total_price,
            'per_person_cost': per_person_cost,
            'vehicle_id': vehicle_id,
            'owner': user_email
        }

        db.collection('rides').document(str(ride_id)).set(ride_data)

        return jsonify({'message': 'Ride created successfully!'}), 200

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': f'Failed to create ride: {str(e)}'}), 500
    

# Add this inside the /get_my_rides route
@app.route('/get_my_rides', methods=['GET'])
def get_my_rides():
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized access!'}), 401

        user_email = session['user_email']

        # Ensure current_time is timezone-aware
        current_time = datetime.datetime.now(datetime.timezone.utc)

        page = int(request.args.get('page', 1))
        rides_per_page = 10

        rides_ref = db.collection('rides').where('owner', '==', user_email)
        rides_stream = rides_ref.stream()

        all_rides = []
        for ride in rides_stream:
            ride_data = ride.to_dict()

            # Debugging log to check retrieved data
            print("Fetched Ride Data:", ride_data)

            # Ensure ride_date_and_time is correctly formatted
            if 'ride_date_and_time' in ride_data:
                ride_date_time = ride_data['ride_date_and_time']

                if isinstance(ride_date_time, datetime.datetime):
                    if ride_date_time.tzinfo is None:
                        ride_date_time = ride_date_time.replace(tzinfo=datetime.timezone.utc)
                else:
                    ride_date_time = ride_date_time.to_datetime()

                ride_data['ride_date_and_time'] = ride_date_time

                # Ensure all required fields exist
                ride_data['vehicle_type'] = ride_data.get('vehicle_id', 'Unknown')  # Fallback if missing

                # Compare only if both are timezone-aware
                if ride_date_time > current_time:
                    all_rides.append(ride_data)

        # Pagination logic
        total_rides = len(all_rides)
        total_pages = (total_rides + rides_per_page - 1) // rides_per_page
        start = (page - 1) * rides_per_page
        end = start + rides_per_page
        rides_to_display = all_rides[start:end]

        return jsonify({'rides': rides_to_display, 'total_pages': total_pages}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Failed to fetch rides: {str(e)}'}), 500

@app.route('/filter_rides', methods=['POST'])
def filter_rides():
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized access!'}), 401

        user_email = session['user_email']

        data = request.get_json()
        from_location = data.get('from')
        to_location = data.get('to')
        ride_date = data.get('date')
        vehicle_id = data.get('vehicle_type')
        max_price = data.get('max_price')

        # Base query to exclude user's own rides
        query = db.collection('rides').where('owner', '!=', user_email)

        # Add filters dynamically
        if from_location:
            query = query.where('from_location', '==', from_location)
        if to_location:
            query = query.where('to_location', '==', to_location)
        if ride_date:
            ride_date = datetime.datetime.strptime(ride_date, "%Y-%m-%d")
            query = query.where('ride_date_and_time', '>=', ride_date)
        
        rides = [ride.to_dict() for ride in query.stream()]

        # Filter by vehicle type manually since Firestore doesn't support OR queries
        if vehicle_id and vehicle_id != "Any":
            rides = [ride for ride in rides if ride.get('vehicle_id') == vehicle_id]

        elif vehicle_id == "Any":
            rides = [ride for ride in rides if ride.get('vehicle_id') in ['Car', 'Auto']]

        # Max price filter
        if max_price:
            rides = [ride for ride in rides if ride.get('per_person_cost', 0) <= float(max_price)]

        return jsonify({'rides': rides}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Failed to filter rides'}), 500



if __name__ == '__main__':
    app.run(debug=True)

