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
cred = credentials.Certificate(r"C:\git files\ride-sharing-b7053-firebase-adminsdk-fbsvc-45494f1901.json")
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

"""
# Filter page (HTML form)
@app.route('/filter_page', methods=['GET'])
def filter_page():
    if 'user_email' not in session:
        return redirect('/login')
    return render_template('filter.html')

"""
@app.route('/filter_page')
def filter_page():
    return render_template('filter.html')


@app.route('/ride_history_page')
def ride_history_page():
    return render_template('ride_history.html')


@app.route('/my_rides_page')
def my_rides_page():
    return render_template('my_rides.html')

@app.route('/ride_creation_page')
def ride_creation_page():
    return render_template('ride_creation.html')  # or your actual template name



"""
@app.route('/index')
def index():
    try:
        # Get all ride documents from Firestore
        rides_ref = db.collection('rides')
        rides = [ride.to_dict() for ride in rides_ref.stream()]

        return render_template('index.html', rides=rides)

    except Exception as e:
        print("Error:", str(e))
        return "Failed to fetch rides", 500"""
@app.route('/index')
def index():
    try:
        current_time = datetime.datetime.now(datetime.timezone.utc)

        rides_ref = db.collection('rides')
        rides = []

        for ride in rides_ref.stream():
            ride_data = ride.to_dict()
            ride_datetime = ride_data.get('ride_date_and_time')

            # Ensure the date is a datetime object
            if isinstance(ride_datetime, datetime.datetime):
                if ride_datetime.tzinfo is None:
                    ride_datetime = ride_datetime.replace(tzinfo=datetime.timezone.utc)
            else:
                ride_datetime = ride_datetime.to_datetime()

            if ride_datetime > current_time:
                ride_data['ride_date_and_time'] = ride_datetime  # Optional: include if used in HTML
                rides.append(ride_data)

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
        # Safe check for login
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.get_json()
        ride_id = get_next_ride_id()
        
        from_location = data.get('from')
        to_location = data.get('to')
        ride_date = data.get('date')
        ride_time = data.get('time')
        vehicle_id = data.get('vehicle')
        total_seats = int(data.get('passengers'))
        total_price = float(data.get('price'))
        current_member_count = 1
        per_person_cost = total_price / current_member_count

        ride_date_and_time = datetime.datetime.strptime(f"{ride_date} {ride_time}", "%Y-%m-%d %H:%M")

        ride_data = {
            'ride_id': ride_id,
            'current_member_count': current_member_count,
            'from_location': from_location,
            'to_location': to_location,
            'ride_date_and_time': ride_date_and_time,
            'total_seats': total_seats,
            'available_seats': total_seats - 1,  # 1 seat taken by creator
            'total_price': total_price,
            'per_person_cost': per_person_cost,
            'vehicle_id': vehicle_id,
            'owner': user_email,
            'passengers': [user_email]  # Creator is first passenger
        }

        db.collection('rides').document(str(ride_id)).set(ride_data)

        return jsonify({'message': 'Ride created successfully!'}), 200

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': f'Failed to create ride: {str(e)}'}), 500

@app.route('/select_ride', methods=['POST'])
def select_ride():
    try:
        data = request.get_json()
        ride_id = str(data.get('ride_id'))
        user_email = session['user_email']

        # Get ride document
        ride_ref = db.collection('rides').document(ride_id)
        ride_doc = ride_ref.get()

        if not ride_doc.exists:
            return jsonify({'error': 'Ride not found'}), 404

        ride_data = ride_doc.to_dict()
        passengers = ride_data.get('passengers', [])

        # Prevent duplicate booking
        if user_email in passengers:
            return jsonify({'message': 'You have already joined this ride.'}), 200

        # Check seat availability
        available_seats = ride_data.get('available_seats', 0)
        if available_seats <= 0:
            return jsonify({'error': 'No available seats'}), 400

        # Update passengers list and counters
        passengers.append(user_email)
        current_member_count = ride_data.get('current_member_count', 1) + 1
        available_seats -= 1

        ride_ref.update({
            'passengers': passengers,
            'current_member_count': current_member_count,
            'available_seats': available_seats
        })

        return jsonify({'message': 'Ride selected successfully'}), 200

    except Exception as e:
        print("Error selecting ride:", str(e))
        return jsonify({'error': f'Failed to select ride: {str(e)}'}), 500



"""# Add this inside the /get_my_rides route
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
        return jsonify({'error': f'Failed to fetch rides: {str(e)}'}), 500"""



@app.route('/get_my_rides', methods=['GET'])
def get_my_rides():
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized access!'}), 401

        user_email = session['user_email']
        current_time = datetime.datetime.now(datetime.timezone.utc)
        page = int(request.args.get('page', 1))
        rides_per_page = 10

        # Rides created by the user
        owner_rides_ref = db.collection('rides').where('owner', '==', user_email)
        owner_rides_stream = owner_rides_ref.stream()

        # Rides joined by the user (as a passenger)
        all_rides_ref = db.collection('rides')
        all_rides_stream = all_rides_ref.stream()

        all_rides = []

        # Add owner rides
        for ride in owner_rides_stream:
            ride_data = ride.to_dict()
            ride_datetime = ride_data.get('ride_date_and_time')

            if isinstance(ride_datetime, datetime.datetime):
                if ride_datetime.tzinfo is None:
                    ride_datetime = ride_datetime.replace(tzinfo=datetime.timezone.utc)
            else:
                ride_datetime = ride_datetime.to_datetime()

            if ride_datetime > current_time:
                ride_data['ride_date_and_time'] = ride_datetime
                ride_data['vehicle_type'] = ride_data.get('vehicle_id', 'Unknown')
                ride_data['joined_as'] = 'owner'
                all_rides.append(ride_data)

        # Add rides where user is a passenger (but not owner)
        for ride in all_rides_stream:
            ride_data = ride.to_dict()

            if ride_data.get('owner') == user_email:
                continue  # Already included

            passengers = ride_data.get('passengers', [])
            if user_email in passengers:
                ride_datetime = ride_data.get('ride_date_and_time')

                if isinstance(ride_datetime, datetime.datetime):
                    if ride_datetime.tzinfo is None:
                        ride_datetime = ride_datetime.replace(tzinfo=datetime.timezone.utc)
                else:
                    ride_datetime = ride_datetime.to_datetime()

                if ride_datetime > current_time:
                    ride_data['ride_date_and_time'] = ride_datetime
                    ride_data['vehicle_type'] = ride_data.get('vehicle_id', 'Unknown')
                    ride_data['joined_as'] = 'passenger'
                    all_rides.append(ride_data)

        # Sort rides by date
        all_rides.sort(key=lambda x: x['ride_date_and_time'])

        # Pagination
        total_rides = len(all_rides)
        total_pages = (total_rides + rides_per_page - 1) // rides_per_page
        start = (page - 1) * rides_per_page
        end = start + rides_per_page
        rides_to_display = all_rides[start:end]

        return jsonify({'rides': rides_to_display, 'total_pages': total_pages}), 200

    except Exception as e:
        print("Error in get_my_rides:", str(e))
        return jsonify({'error': f'Failed to fetch rides: {str(e)}'}), 500

@app.route('/filter_rides', methods=['POST'])
def filter_rides():
    if 'user_email' not in session:
        return "Unauthorized", 401

    data = request.get_json()

    from_location = data.get('from', '').strip().lower()
    to_location = data.get('to', '').strip().lower()
    vehicle = data.get('vehicle', 'Any')
    max_price = data.get('max_price')
    ride_date = data.get('date')  # format: YYYY-MM-DD

    # Get all rides from Firestore
    rides_ref = db.collection('rides')
    rides = rides_ref.stream()

    matched_rides = []

    for ride in rides:
        ride_data = ride.to_dict()
        ride_id = ride.id
        ride_data['ride_id'] = ride_id

        ride_from = ride_data.get('from_location', '').strip().lower()
        ride_to = ride_data.get('to_location', '').strip().lower()
        ride_vehicle = ride_data.get('vehicle_id', '').strip()
        ride_price = ride_data.get('per_person_cost')
        ride_datetime = ride_data.get('ride_date_and_time')

        # Ensure ride_datetime is a datetime object
        if not isinstance(ride_datetime, datetime.datetime):
            continue

        # 🧠 Filtering logic
        if from_location and from_location not in ride_from:
            continue
        if to_location and to_location not in ride_to:
            continue
        if vehicle != 'Any' and vehicle.lower() != ride_vehicle.lower():
            continue
        if max_price:
            try:
                if float(ride_price) > float(max_price):
                    continue
            except:
                continue
        if ride_date:
            try:
                if ride_datetime.date() != datetime.datetime.strptime(ride_date, '%Y-%m-%d').date():
                    continue
            except:
                continue

        matched_rides.append(ride_data)

    return jsonify({'rides': matched_rides})



@app.route('/get_past_rides', methods=['GET'])
def get_past_rides():
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized access!'}), 401

        user_email = session['user_email']
        current_time = datetime.datetime.now(datetime.timezone.utc)

        rides_ref = db.collection('rides').where('owner', '==', user_email)
        rides_stream = rides_ref.stream()

        past_rides = []
        for ride in rides_stream:
            ride_data = ride.to_dict()

            if 'ride_date_and_time' in ride_data:
                ride_date_time = ride_data['ride_date_and_time']
                if isinstance(ride_date_time, datetime.datetime):
                    if ride_date_time.tzinfo is None:
                        ride_date_time = ride_date_time.replace(tzinfo=datetime.timezone.utc)
                else:
                    ride_date_time = ride_date_time.to_datetime()

                if ride_date_time < current_time:
                    past_rides.append(ride_data)

        return jsonify({'rides': past_rides}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Failed to fetch past rides'}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    ride_id = str(data['ride_id'])
    sender = data['sender']
    text = data['text']

    message_data = {
        'sender': sender,
        'text': text,
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    }

    db.collection('rides').document(ride_id).collection('messages').add(message_data)
    return jsonify({'status': 'Message sent'}), 200

@app.route('/get_messages/<ride_id>', methods=['GET'])
def get_messages(ride_id):
    messages_ref = db.collection('rides').document(ride_id).collection('messages')
    messages = messages_ref.order_by('timestamp').stream()

    messages_list = []
    for msg in messages:
        msg_dict = msg.to_dict()
        messages_list.append({
            'sender': msg_dict.get('sender', ''),
            'text': msg_dict.get('text', '')
        })

    return jsonify({'messages': messages_list}), 200

@app.route('/chat/<ride_id>')
def chat_page(ride_id):
    if 'user_email' not in session:
        return redirect('/login')
    return render_template('chat.html', ride_id=ride_id)


#*********************************************************************************************************
def is_user_in_ride(ride_id, user_email):
    ride_doc = db.collection('rides').document(str(ride_id)).get()
    if not ride_doc.exists:
        return False
    ride_data = ride_doc.to_dict()
    return user_email in ride_data.get('passengers', []) or user_email == ride_data.get('owner')

@app.route('/send_chat/<ride_id>', methods=['POST'])
def send_chat(ride_id):
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Empty message'}), 400
        
        if not is_user_in_ride(ride_id, session['user_email']):
            return jsonify({'error': 'Access denied'}), 403

        chat_ref = db.collection('chats').document(ride_id).collection('messages')

        chat_ref.add({
            'sender': session['user_email'],
            'message': message,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })

        return jsonify({'message': 'Message sent'}), 200

    except Exception as e:
        print("Error in send_chat:", str(e))
        return jsonify({'error': 'Failed to send message'}), 500
    

@app.route('/get_chat/<ride_id>', methods=['GET'])
def get_chat(ride_id):
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not is_user_in_ride(ride_id, session['user_email']):
            return jsonify({'error': 'Access denied'}), 403
        
        chat_ref = db.collection('chats').document(ride_id).collection('messages').order_by('timestamp')
        chat_docs = chat_ref.stream()

        messages = []
        for doc in chat_docs:
            msg_data = doc.to_dict()
            messages.append({
                'sender': msg_data.get('sender'),
                'message': msg_data.get('message'),
                'timestamp': msg_data.get('timestamp').isoformat()
            })

        return jsonify({'messages': messages}), 200

    except Exception as e:
        print("Error in get_chat:", str(e))
        return jsonify({'error': 'Failed to fetch chat'}), 500
    
@app.route('/chat')
def chat_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    ride_id = request.args.get('ride_id')
    if not ride_id:
        return "Ride ID not provided", 400
    
    return render_template('chat.html', ride_id=ride_id, session=session, user_email=session['user']['email'])
#*********************************************************************************************************





if __name__ == '__main__':
    app.run(debug=True)

