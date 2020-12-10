from dotenv import load_dotenv
from pathlib import Path
import os
from slack_bolt import App
import firebase_admin
from firebase_admin import credentials, firestore, db
from db_utils import create_habit, read_habit, delete_habit, check_if_team_exists, set_habit_status, read_abs_list, update_abs_list
import json
from datetime import datetime, timedelta
import pytz
import time
import requests
import random

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)
# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ['SLACK_TOKEN'],
    signing_secret=os.environ['SIGNING_SECRET']
)
cd = credentials.Certificate(
    "habitbotdb-297416-firebase-adminsdk-kn9zk-b63e8c9960.json")

firebase_admin.initialize_app(
    cd, {
    'databaseURL': os.environ['DB_URL']
    }
)
db = db.reference('staging/')
habit_status_dict = {
        'Start Activity':0,
        'Mark Complete':1,
        'Completed':2
    }
r = requests.get(
"https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s" % ("motivation", os.environ['TENOR_TOKEN'], 13))
my_json = json.loads(r.content)
randomizer = random.randint(0, 10) 
gif_link = my_json['results'][randomizer]['media'][0]['gif']['url']

@app.message("stupid bot")
def team_info(message, say):


    # response = client.team_info(
    #     token = os.environ['SLACK_TOKEN']
    # )
    # channel_id =message['channel']
    say(text="Not funny he's scolding me 😢😞")
    # print("response", response)

@app.message(":wave:")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    # print(message)
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click Me"},
                    "action_id": "button_click"
                }
            }
        ],
        text=f"Hey there <@{message['user']}>!"
    )
# Listen for a shortcut invocation
@app.shortcut("create_habit")
def open_modal(ack, body, client):
    # Acknowledge the command request
    ack();
    # print(body)
    team = body['team']['domain']
    user = body['user']['id']
    team_ref = db.child(team)
    abs_list = read_abs_list(team_ref, user)
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            # View identifier
            "callback_id": "view_1",
            "title": {"type": "plain_text", "text": "HabitBot"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Hi there! Let's make a better *you*"},
                },
                           {
                    "type": "input",
                    "block_id": "habit_block",
                    "label": {"type": "plain_text", "text": "What is the new habit you are looking to build?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "habit_text",
                        "multiline": False
                    }
                },
                {
                    "type": "input",
                    "block_id": "timepicker_block",
                    "label": {"type": "plain_text", "text": "When do you want to be reminded about this habit?"},
                    "element": {
                        "type": "timepicker",
                        "action_id": "reminder_time",
                        "initial_time": "11:40",
                        "placeholder": {
                        "type": "plain_text",
                        "text": "Select a time"
                        }
                        },
                },
                
                    {"type": "input",
                    "block_id": "abs_block",
                    "label": {"type": "plain_text", "text": "Whom do you want to be accountable to?"},
                    "element": {
                        "action_id": "accountablity_buddies",
                        "type": "multi_users_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "View your accountablity buddies"
      },
      "initial_users":abs_list	
    }
                },
            ]
        }
    )
# Handle a view_submission event
@app.view("view_1")
def handle_submission(ack, body, client, view):
    ack()
    habit_text = view["state"]["values"]["habit_block"]["habit_text"]['value']
    reminder_time = view["state"]["values"]["timepicker_block"]["reminder_time"]['selected_time']
    reminder_hour, reminder_minutes = reminder_time.split(":")
    reminder_hour, reminder_minutes = int(reminder_hour), int(reminder_minutes)
    accountablity_buddies = view["state"]["values"]["abs_block"]["accountablity_buddies"]['selected_users']

    user = body["user"]["id"]
    username = body["user"]["username"]
    # print(user)
    
    team = body['team']['domain']
    # print(team)
    check_if_team_exists(db, team)
    team_ref = db.child(team)
    # Validate the inputs
    errors = {}
    # print(body['token'])


    if habit_text is not None and len(habit_text) <= 4:
        errors["habit_block"] = "The value must be longer than 4 characters"
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return

    #Get current abs_list stored on server
    abs_list = read_abs_list(team_ref, user)

    intersection = list(set(abs_list)&set(accountablity_buddies))

    for ab in accountablity_buddies:
        # print(ab)
        if ab not in intersection:

            client.chat_postMessage(channel=ab, text=f"Wohoo! <@{user}> has made you their accountablity buddy. You will now recieve updates regarding their habits")

    tz = get_user_timezone(client, user)
    local = pytz.timezone(tz)
    user_time_now = datetime.now().astimezone(local)
    scheduled_time = user_time_now.replace(hour=reminder_hour, minute=reminder_minutes)

    if user_time_now.hour < reminder_hour or (user_time_now.hour == reminder_hour and user_time_now.minute < reminder_minutes):
        schedule_message(client, user, scheduled_time.timestamp(), habit_text)
    else:
        schedule_message( client, user, (scheduled_time + timedelta(days=1)).timestamp(), habit_text)

    create_habit(team_ref, team, user, habit_text, reminder_time,
                 accountablity_buddies)
    # Acknowledge the view_submission event and close the modal
    # Do whatever you want with the input data - here we're saving it to a DB
    # then sending the user a verification of their submission

    # Message to send user
    msg = ""
    try:
        # Save to DB
        msg = f"Your submission of {habit_text} was successful"
    except Exception as e:
        # Handle error
        msg = "There was an error with your submission"
    finally:
        # Message the user
        client.chat_postMessage(channel=user, text=msg)

def schedule_message(client, user, unix_timestamp, text):
    client.chat_scheduleMessage(
        channel=user,
        post_at=unix_timestamp,
        text=text
    )

@app.event("app_home_opened")
def update_home_tab(client, event = None, logger = None, user = None):
    # print("updating home tab")
    team_info=get_team_info(client)
    team = team_info['team']['domain']
    check_if_team_exists(db, team)
    team_ref = db.child(team)
    user_id = user if user else event['user'] 
    abs_list = read_abs_list(team_ref, user_id)
    # print("abs_list :", abs_list)
    user_data = read_habit(team_ref, user_id)
    # print("user_data :", user_data)
    #       ['Hahah this finally works']['reminder_time'])
    my_payload = []
    if 'habits' in user_data.keys():
        my_payload = generate_habit_payload(user_data['habits'])
    try:
        # Call views.publish with the built-in client
        
        client.views_publish(
            # Use the user ID associated with the event
            user_id=user_id,
            # Home tabs must be enabled in your app configuration
            view={
                "type":"home",
                
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                        				"text": "This is a plain text section block.",
                                "emoji": True
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "image",
                            "title": {
                                "type": "plain_text",
                                "text": "A GIF to get you pumped up."
                            },
                            "block_id": "image4",
                            "image_url": gif_link,
                            "alt_text": "A GIF to get you pumped up 💪"
                        },

                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                        				"text": "Your Habits 🎯",
                                "emoji": True
                            }
                        },
                        *my_payload
                        ,
                        {
                            "type": "divider"
                        },
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                        				"text": "Your Accountability Buddies 👯‍♀️",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "block_id": "section678",
                            "text": {
                                "type": "mrkdwn",
                        				"text": "Pick users from the list"
                            },
                            "accessory": {
                                "action_id": "home_user_select",
                        				"type": "multi_users_select",
                        				"placeholder": {
                                                            "type": "plain_text",
                               					"text": "Select users"
                                                        },
                                                        "initial_users":abs_list
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Delete Habits ❌",
                                        "emoji": True
                                    },
                                    "value": "open_delete_habits",
                                    "action_id": "open_delete_habits"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                      						"text": "Give Feedback 📃",
                                        "emoji": True
                                    },
                                    "value": "click_me_123",
                                    "action_id": "actionId-1"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                      						"text": "Donate ☕",
                                        "emoji": True
                                    },
                                    "value": "click_me_123",
                                    "action_id": "actionId-2"
                                }
                            ]
                        }
                    ]
                })
        # print("Try catch running")
    except Exception as e:
        print("Oh no exception", e)
        if logger:
            logger.error(f"Error publishing home tab: {e}")

@app.action("open_delete_habits")
def open_delete_habit_modal(ack, body, client):
    ack()
    team = body['team']['domain']
    user = body['user']['id']    
    team_ref = db.child(team)
    
    user_data = read_habit(team_ref, user)
    my_payload = generate_habit_payload(user_data['habits'], is_edit_modal= True)

    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            # View identifier
            "callback_id": "delete_habits_modal",
            "title": {"type": "plain_text", "text": "HabitBot"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Choose habits you want to delete ❌"},
                },
                *my_payload
            ]
        }
    )


@app.action("home_user_select")
def home_user_selected(ack, payload, client, body):
    ack()
    team_ref = db.child(body['team']['domain'])
    update_abs_list(team_ref, body['user']['id'], payload['selected_users'])

def get_team_info(client):
    response = client.team_info(
        token = os.environ['SLACK_TOKEN']
    )
    # print(team)
    return response

def get_user_timezone(client, user_id):
    user_response = client.users_info(
        token = os.environ['SLACK_TOKEN'],
        user=user_id
    )
    return user_response['user']['tz']

def generate_habit_payload(habits, is_edit_modal = False):
    habit_names = list(habits.keys())
    # print(habits)
    payload = []
    style_arr = []
    for habit_name in habit_names:
        # print(habit_name)
        payload.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": habit_name if habits[habit_name]['habit_status'] == 0 else (f"*{habit_name}*" if habits[habit_name]['habit_status'] == 1 else f"✔ ~{habit_name}~")
        },
        "accessory": {
            "type": "button",
            "text": {
                    "type": "plain_text",
                    "text": 'Delete' if is_edit_modal else ('Start Activity 📝' if habits[habit_name]['habit_status'] == 0 else ('Mark Complete ▶' if habits[habit_name]['habit_status'] == 1 else 'Completed 🏁'))
            },
            "value": habit_name,
            "action_id" : "delete_habit" if is_edit_modal else "activity_button"
        }
    })
        if is_edit_modal or habits[habit_name]['habit_status'] == 0:
            payload[-1]['accessory'].update({"style": "danger" if is_edit_modal else ("primary" if habits[habit_name]['habit_status'] == 0 else None)})
            

    return payload
    
@app.action('activity_button')
def activity_button_click(payload, ack, body, client):
    # print(body)
    user = body['user']['id']
    team = body['team']['domain']
    habit_text = payload['value']
    habit_status = payload['text']['text']
    habit_status_id = habit_status_dict[habit_status]
    team_ref = db.child(team)
    set_habit_status(team_ref, user, habit_text, habit_status_id)
    ack()
    update_home_tab(client=client, user=user)
    abs_list = read_abs_list(team_ref, user)
    for accountablity_buddy in abs_list:
        if habit_status_id == 0:
            client.chat_postMessage( channel=accountablity_buddy, text=f"<@{user}> has started {habit_text}. Time to get going! 😏")
        elif habit_status_id == 1:
            client.chat_postMessage(
                channel=accountablity_buddy, text=f"<@{user}> has finished {habit_text}. They might be getting ahead of you... 😨")
@app.action("delete_habit")
def delete_habit_clicked(payload, ack, body, client):
    ack()
    user = body['user']['id']
    team = body['team']['domain']
    habit_text = payload['value']
    team_ref = db.child(team)
    user_data = read_habit(team_ref, user)
    delete_habit(team_ref, user, habit_text)
    user_data = read_habit(team_ref, user)

    my_payload = generate_habit_payload(user_data['habits'], is_edit_modal= True)

    client.views_update(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view_id=body["view"]["id"],
        view={
            "type": "modal",
            # View identifier

            "callback_id": "delete_habits_modal",
            "title": {"type": "plain_text", "text": "HabitBot"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Choose habits you want to delete ❌"},
                },
                *my_payload
            ]
        }
    )
    scheduled_message_list = client.chat_scheduledMessages_list(
        token = os.environ['SLACK_TOKEN'],
    )


    # update_home_tab(client=client, user=user)
    # print(scheduled_message_list)
    for message in scheduled_message_list['scheduled_messages']:
        if message['text'] == habit_text:
            client.chat_deleteScheduledMessage(
                token = os.environ['SLACK_TOKEN'],
                channel = user,
                scheduled_message_id = message['id'],
            )
            return 

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
