import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(r"ride-sharing\ride-sharing-b7053-firebase-adminsdk-fbsvc-6b93718f27.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()
data = {"name": "Los Angeles", "state": "CA", "country": "USA"}
db.collection("cities").document("test2").set(data)