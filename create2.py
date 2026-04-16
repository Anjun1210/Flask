import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "蕭安均2",
  "mail": "xiaoanjun1210@gmail.com",
  "lab": "888"
}

doc_ref = db.collection("資管二B").document("xiao1")
doc_ref.set(doc)
