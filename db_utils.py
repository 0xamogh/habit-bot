import firebase_admin
import pytz
from datetime import datetime, timedelta
from firebase_admin import credentials, firestore, db
cd = credentials.Certificate("habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")

def create_habit(datab, team, user, habit_text, reminder_time, abs_list, timezone):

    team_data = datab.get()
    error_status = False

    if user not in team_data.keys() or 'habits' not in  team_data[user].keys():
        print("entering first if statement")
        datab.update({
            user: {
                "abs": abs_list,
                "habits":{
                    habit_text: {
                        "reminder_time" : reminder_time,
                        "habit_status" : 0
                    },
                "timezone": timezone
                }
            }

        })
    else:
        habits = team_data[user]['habits']
        habits[habit_text] = {
            'reminder_time': reminder_time, 'habit_status': 0}
        datab.update(
            {
                f"{user}/habits": habits,
                f"{user}/abs": abs_list,
                f"{user}/timezone":timezone
            }
        )
        abs_list = team_data[user]['abs']

def read_habit(datab, user, habit_text=None):
    team_data = datab.get()

    error_status = False
    if user not in team_data.keys():
        return None
    if habit_text:
        return team_data[user][habit_text]
    return team_data[user]
def read_abs_list(datab, user):
    team_data = datab.get()

    error_status = False
    if user not in team_data.keys():
        return []
    elif 'abs' in team_data[user].keys():
        return team_data[user]['abs']
    else:
        return None
def update_abs_list(datab, user, abs_list):
    datab.update({
        f"{user}/abs": abs_list
    })

def set_habit_status(datab, user, habit_text, habit_status):
    team_data = datab.get()
    error_status = False
    if user not in team_data.keys():
        return {"user_not_found" : True}
    if habit_text:
        habits = team_data[user]['habits']

        habits[habit_text]['habit_status'] = int((habit_status+1)%3)
        datab.update(
            {
                f"{user}/habits": habits,
            }
        )
def delete_habit(datab, user, habit_text):
    print("deleting habit", habit_text)
    user_ref = datab.child(user)
    user_data = user_ref.get()
    if 'habits' in user_data.keys():
        delete_habit_ref = user_ref.child('habits').child(habit_text)
        delete_habit_ref.delete()
    else: 
        return
def check_if_team_exists(db, team):
    db_data = db.get()

    if team not in db_data.keys():
        db.update({team: {"temp_key": "0"}})

def refresh_habit_status(datab):
    data = datab.get()
    for team in data.keys():
        if team != "temp_key":

            team_data = data[team]

            for user in team_data.keys():
                # user_ref = team_ref.child(user)
                if user != "temp_key":
                    user_data = team_data[user]

                    tz = None
                    if "timezone" in user_data.keys():
                        tz = user_data["timezone"]
                        local = pytz.timezone(tz)
                        user_time_now = datetime.now().astimezone(local)
                        if user_time_now.hour >= 23:
                            if "habits" in user_data.keys():
                                for habit in user_data['habits'].keys():

                                    user_data['habits'][habit]['habit_status'] = 0
    datab.update(data)