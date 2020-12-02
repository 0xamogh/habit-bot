import firebase_admin
from firebase_admin import credentials,firestore
cd = credentials.Certificate("habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")
# In the above line <path_to_generated_private_key>
# is a placeholder for the generate JSON file containing
# your private key.
firebase_admin.initialize_app(cd)
datab = firestore.client()
usersref = datab.collection(u'staging')
doc_ref = datab.collection(u'staging').document(u'user')
doc_ref.set({
    u'abs': ['Abhijeet','Sneha','Suresh'],
    u'habits': ['Bathe','Sleep'],
})
docs = usersref.stream()

for doc in docs:
    print('{} : {}'.format(doc.id,doc.to_dict()))
