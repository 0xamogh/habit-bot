import firebase_admin
from firebase_admin import credentials,firestore
cd = credentials.Certificate("habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")
# In the above line <path_to_generated_private_key>
# is a placeholder for the generate JSON file containing
# your private key.
firebase_admin.initialize_app(cd)
datab = firestore.client()
# usersref = datab.collection(u'staging')
team_ref = datab.collection(u'staging').document(u'team')
user_ref = team_ref.collection('user').document('habits')
user_ref.set({
    u'abs': ['Abhijeet','Sneha','Suresh'],
    u'habits': ['Bathe','Sleep'],
})
# A new user is created when he makes his first habit
def create_habit(datab, env, team, user, habit_text, reminder_time, abs):
    team_ref = datab.collection(env).document(team)
    habit_ref = team_ref.collection(user).document('habits')
    ab_ref = team_ref.collection(user).document('abs')
    habit_info = habit_ref.get().to_dict()
    ab_info = ab_ref.get().to_dict()
    if habit_text not in habit_info:
        habit_ref.set({
            habit
        })
# docs = usersref.stream()

# for doc in docs:
#     print('{} : {}'.format(doc.id,doc.to_dict()))
