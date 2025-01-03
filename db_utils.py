import firebase_admin
import pytz
from datetime import datetime, timedelta
from firebase_admin import credentials, firestore, db
from utils import schedule_message
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
                        "habit_status" : 0,
                        "streak" : 0
                    },
                },
                "timezone": timezone

            }

        })
    else:
        habits = team_data[user]['habits']
        habits[habit_text] = {
            'reminder_time': reminder_time, 'habit_status': 0, 'streak' : 0}
        datab.update(
            {
                f"{user}/habits": habits,
                f"{user}/abs": abs_list,
                f"{user}/timezone":timezone,
            }
        )
        abs_list = team_data[user]['abs']

def read_habit(datab, user, habit_text=None):
    team_data = datab.get()

    if user not in team_data.keys():
        return {"user_not_found": True}
    if habit_text:
        return team_data[user][habit_text]
    return team_data[user]

def read_abs_list(datab, user):
    team_data = datab.get()

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

        stat = int((habit_status+1)%2)
        habits[habit_text]['habit_status'] = stat
        if stat == 1:
            habits[habit_text]['streak'] = habits[habit_text]['streak'] + 1
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

def check_if_user_exists(db, user):
    db_data = db.get()

    if user not in db_data.keys():
        db.update({
            user: {
                "temp_key": 0}
        })
        return False
    else:
        return True

def refresh_habit_status(client, datab):
    data = datab.get()
    for team in data.keys():
        if team != "temp_key":
            team_data = data[team]
            for user in team_data.keys():
                if user != "temp_key":
                    print(user)
                    tz = None
                    if "timezone" in data[team][user].keys():
                        tz = data[team][user]["timezone"]
                        local = pytz.timezone(tz)
                        user_time_now = datetime.now().astimezone(local)
                        if user_time_now.hour == 0:
                            if "habits" in data[team][user].keys():
                                for habit in data[team][user]['habits'].keys():
                                    data[team][user]['habits'][habit]['habit_status'] = 0
    datab.update(data)
