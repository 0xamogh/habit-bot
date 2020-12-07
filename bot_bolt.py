from dotenv import load_dotenv
from pathlib import Path
import os
from slack_bolt import App
import firebase_admin
from firebase_admin import credentials, firestore, db
from db_utils import create_habit, read_habit, delete_habit, check_if_team_exists
import json
from datetime import datetime

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

@app.message("stupid bot")
def team_info(message, say):


    # response = client.team_info(
    #     token = os.environ['SLACK_TOKEN']
    # )
    # channel_id =message['channel']
    say(text="Not funny he's scolding me 😢😞")
    # print("response", response)

@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
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
      }
    }
                },
            ]
        }
    )
# Handle a view_submission event
@app.view("view_1")
def handle_submission(ack, body, client, view):

    habit_text = view["state"]["values"]["habit_block"]["habit_text"]['value']
    reminder_time = view["state"]["values"]["timepicker_block"]["reminder_time"]['selected_time']
    accountablity_buddies = view["state"]["values"]["abs_block"]["accountablity_buddies"]['selected_users']
    user = body["user"]["id"]
    
    
    team = body['team']['domain']
    print(team)
    check_if_team_exists(db, team)
    team_ref = db.child(team)
    # Validate the inputs
    errors = {}
    print(body['token'])


    if habit_text is not None and len(habit_text) <= 4:
        errors["habit_block"] = "The value must be longer than 4 characters"
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return

    create_habit(team_ref, team, user, habit_text, reminder_time, accountablity_buddies)
    tz = get_user_timezone(client, user)

    
    # Acknowledge the view_submission event and close the modal
    ack()
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

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    client.chat_scheduleMessage(
        channel=event['user'],
        post_at="1607341556",
        text="Summer has come and passed"
    )
    team_info=get_team_info(client)
    team = team_info['team']['domain']
    check_if_team_exists(db, team)
    team_ref = db.child(team)
    user_data = read_habit(team_ref, team, event["user"])
    # print(user_data, user_data['habits']
    #       ['Hahah this finally works']['reminder_time'])
    my_payload = generate_habit_payload(user_data['habits'])
    try:
        # Call views.publish with the built-in client
        client.views_publish(
            # Use the user ID associated with the event
            user_id=event["user"],
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
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                        				"text": "This is a header block",
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
                        				"text": "This is a header block",
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
                                "action_id": "text1234",
                        				"type": "multi_users_select",
                        				"placeholder": {
                                                            "type": "plain_text",
                               					"text": "Select users"
                                                        }
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
                                      						"text": "Click Me",
                                        "emoji": True
                                    },
                                    "value": "click_me_123",
                                    "action_id": "actionId-0"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                      						"text": "Click Me",
                                        "emoji": True
                                    },
                                    "value": "click_me_123",
                                    "action_id": "actionId-1"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                      						"text": "Click Me 👋🏽",
                                        "emoji": True
                                    },
                                    "value": "click_me_123",
                                    "action_id": "actionId-2"
                                }
                            ]
                        }
                    ]
                })
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

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

def generate_habit_payload(habits):
    habit_names = list(habits.keys())
    payload = []
    for habit_name in habit_names:
        payload.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": habit_name
            },
            "accessory": {
                "type": "button",
                "text": {
                        "type": "plain_text",
                        "text": "Mark started"
                },
                "action_id": f"{habit_name}_button"
            }
        })

    return payload


@app.action('button_click')
def action_button_click(body, ack, say):
    ack()
    say(f"Wow <@{body['user']['id']}> didn't know you were a button clicker!!")
# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
