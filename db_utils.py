import firebase_admin
from firebase_admin import credentials, firestore, db
cd = credentials.Certificate("habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")
# In the above line <path_to_generated_private_key>
# is a placeholder for the generate JSON file containing
# your private key.
# firebase_admin.initialize_app(cd, {
#     'databaseURL': 'https://habitbotdb-297416.firebaseio.com/'
# })
# datab = db.reference('staging/team/')
# print(datab.get())

def create_habit(datab, team, user, habit_text, reminder_time, abs_list):

    team_data = datab.get()
    error_status = False
    print(team_data)

    if user not in team_data.keys():
        print("entering first if statement")
        datab.set({
            user: {
                "abs": abs_list,
                "habits":{
                    habit_text: {
                        "reminder_time" : reminder_time,
                        "activity_underway" : False
                    }
                }
            }

        })
    else:
        habits = team_data[user]['habits']
        habits[habit_text] = {'reminder_time': reminder_time}
        datab.update(
            {
                f"{user}/habits": habits,
                f"{user}/abs": abs_list
            }
        )
        abs_list = team_data[user]['abs']

def read_habit(datab, team, user, habit_text=None):
    team_data = datab.get()

    error_status = False
    if user not in team_data.keys():
        return {"user_not_found" : True}
    if habit_text:
        return team_data[user][habit_text]
    return team_data[user]

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

def check_if_team_exists(db, team):
    db_data = db.get()

    if team not in db_data.keys():
        db.update({team: {"temp_key": "0"}})
