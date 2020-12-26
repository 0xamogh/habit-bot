from db_utils import read_abs_list, check_if_team_exists, create_habit, read_habit
from datetime import datetime, timedelta
from utils import get_user_timezone, schedule_message, generate_habit_payload
from home import build_home_tab_payload
import pytz
def open_create_habit_modal(ack, body, client, db):
    # Acknowledge the command request
    ack()
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
            "title": {"type": "plain_text", "text": "InhabitBot"},
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
                     "initial_users": abs_list
                 },
                 
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
                }
            ]
        }
    )
 

def submit_create_habit_modal(ack, body, client, view, db):
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

    intersection = list(set(abs_list) & set(accountablity_buddies))

    for ab in accountablity_buddies:
        if ab not in intersection:

            client.chat_postMessage(
                channel=ab, text=f"Wohoo! <@{user}> has made you their accountablity buddy. You will now recieve updates regarding their habits")

    tz = get_user_timezone(client, user)
    local = pytz.timezone(tz)
    user_time_now = datetime.now().astimezone(local)
    scheduled_time = user_time_now.replace(
        hour=reminder_hour, minute=reminder_minutes)

    if user_time_now.hour < reminder_hour or (user_time_now.hour == reminder_hour and user_time_now.minute < reminder_minutes):
        schedule_message(client, user, scheduled_time, habit_text)
    else:
        schedule_message(client, user, scheduled_time +
                                        timedelta(days=1), habit_text)

    create_habit(team_ref, team, user, habit_text, reminder_time,
                 accountablity_buddies)
    # Acknowledge the view_submission event and close the modal
    # Do whatever you want with the input data - here we're saving it to a DB
    # then sending the user a verification of their submission

    # Message to send user
    msg = ""
    build_home_tab_payload(client, db, user = user)
    try:
        # Save to DB
        msg = f"Your submission of {habit_text} was successful"
    except Exception as e:
        # Handle error
        msg = "There was an error with your submission"
    finally:
        # Message the user
        client.chat_postMessage(channel=user, text=msg)


def build_delete_habit_payload(ack, body, client, db):
    ack()
    team = body['team']['domain']
    user = body['user']['id']
    team_ref = db.child(team)

    user_data = read_habit(team_ref, user)
    my_payload = generate_habit_payload(
        user_data['habits'], is_edit_modal=True)

    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            # View identifier
            "callback_id": "delete_habits_modal",
            "title": {"type": "plain_text", "text": "InhabitBot"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Choose habits you want to delete ❌"},
                },
                *my_payload
            ]
        }
    )
