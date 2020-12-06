import firebase_admin
from firebase_admin import credentials, firestore, db
cd = credentials.Certificate("habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")
# In the above line <path_to_generated_private_key>
# is a placeholder for the generate JSON file containing
# your private key.
firebase_admin.initialize_app(cd, {
    'databaseURL': 'https://habitbotdb-297416.firebaseio.com/'
})
datab = db.reference('staging/team/')
print(datab.get())
# usersref = datab.collection(u'staging')
# user_ref = datab.collection(u'staging') #.document(u'team').collections()
# user_ref = team_ref.collection('user').document('habits')
# user_ref.set({
#     u'abs': ['Abhijeet','Sneha','Suresh'],
#     u'habits': ['Bathe','Sleep'],
# })
# A new user is created when he makes his first habit
def create_habit(datab, env, team, user, habit_text, reminder_time, abs_list):
    team_ref = datab.reference(f"{env}/{team}")
    team_data = team_ref.get()
    error_status = False
    try:
        if user not in team_data:
            team_ref.set({
                user: {
                    "abs": abs_list,
                    "habits":{
                        habit_text: {
                            "reminder_time" : reminder_time
                        }
                    }
                }

            })
        else:
            habits = team_data[user]['habits']
            if habit_text in habits:
                habits[habit_text] = {'reminder_time': reminder_time}
            else:
                habits.append({habit_text: {'reminder_time': reminder_time}})
            team_ref.update(
                {
                    f"{user}/'habits'": habits,
                    f"{user}/'abs'": abs_list
                }
            )
            abs_list = team_data[user]['abs']
            
    except:
        error_status = False
        print("Unknown Error has occured")
    finally:
        return error_status

def read_habit(datab,env, team, user, habit_text=None):
    team_ref = datab.reference(f"{env}/{team}")
    team_data = team_ref.get()
    error_status = False
    try:
    
        if user not in team_data:
            raise Exception("User not found")
        if habit_text:
            return team_data[user][habit_text]
        return team_data[user]
    
    except:
        if error_status:
            return {'error_status' : error_status}
            
def delete_habit(datab,env, team, user, habit_text):
    user_ref = datab.reference(f"{env}/{team}/{user}")
    user_data = user_ref.get()
    error_status = False
    try:

        if habit_text not in user_data:
            raise Exception("Habit not found")
        if habit_text:
            delete_habit_ref = user_ref.child(habit_text)
            delete_habit_ref.delete()

    except:
        print("An error has occured")
    finally:
        return {'error_status': error_status}
# for doc in docs:
#     print('{} : {}'.format(doc.id,doc.to_dict()))
