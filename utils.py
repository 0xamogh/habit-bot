import os
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
signing_secret = os.environ["SIGNING_SECRET"]
signature_verifier = SignatureVerifier(signing_secret=signing_secret)

from datetime import timedelta
from time import sleep

def get_team_info(client):
    response = client.team_info(
        # token=os.environ['SLACK_BOT_TOKEN']
    )
    return response


def schedule_message(client, user, scheduled_time, text, auto = False):
    i = 0

    client.chat_scheduleMessage(
        channel=user,
        post_at=(scheduled_time + timedelta(days=i)).timestamp(),
        text= text if auto else f"Reminder to complete your activity : {text}"
    )
def get_user_timezone(client, user_id):
    user_response = client.users_info(
        # token=os.environ['SLACK_BOT_TOKEN'],
        user=user_id
    )
    return user_response['user']['tz']


def generate_habit_payload(habits, is_edit_modal=False):
    print("These are the habits", habits)
    habit_names = list(habits.keys())
    payload = []

    for habit_name in habit_names:
        print(type(habits[habit_name]), habits[habit_name])
        current_habit = habits[habit_name]
        
        payload.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (f"*{habit_name}*" if current_habit['habit_status'] else f"✅ ~{habit_name}~")
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": 'Delete' if is_edit_modal else ('rk Complete' if current_habit['habit_status'] == 0 else 'Completed')
                },
                "value": habit_name + "#*#" + str(current_habit['habit_status']),
                "action_id": "delete_habit" if is_edit_modal else "activity_button"
            }
        })
        if is_edit_modal or current_habit['habit_status'] == 0:
            payload[-1]['accessory'].update({"style": "danger" if is_edit_modal else (
                "primary" if current_habit['habit_status'] == 0 else None)})

    return payload
