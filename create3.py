import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "蕭安均3",
  "mail": "xiaoanjun1210@gmail.com",
  "lab": "123"
}

doc_ref = db.collection("資管二B")
doc_ref.add(doc)
