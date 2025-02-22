import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(r"E:\git files\ride-sharing-b7053-firebase-adminsdk-fbsvc-45494f1901.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()
data = {"name": "Los Angeles", "state": "CA", "country": "USA"}
db.collection("cities").document("test6").set(data)