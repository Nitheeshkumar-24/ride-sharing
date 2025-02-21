from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase FIRST
cred = credentials.Certificate(r"E:\git files\ride-sharing\ride-sharing-b7053-firebase-adminsdk-fbsvc-6b3474ac7d.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Flask Routes
@app.route('/')
def authentication():
    return render_template('authentication.html')

@app.route('/index')
def index():
    return render_template('index.html')

# Store data when the app starts
doc_ref = db.collection("users").document("alovelace")
doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})
print("Data stored successfully!")

if __name__ == '__main__':
    app.run(debug=True)
