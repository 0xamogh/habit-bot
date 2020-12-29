import os
from datetime import timedelta
def get_team_info(client):
    response = client.team_info(
        token=os.environ['SLACK_BOT_TOKEN']
    )
    return response


def schedule_message(client, user, scheduled_time, text):
    for i in range(0,21):
        client.chat_scheduleMessage(
            channel=user,
            post_at=(scheduled_time + timedelta(days=i)).timestamp(),
            text=text
        )
def get_user_timezone(client, user_id):
    user_response = client.users_info(
        token=os.environ['SLACK_BOT_TOKEN'],
        user=user_id
    )
    return user_response['user']['tz']


def generate_habit_payload(habits, is_edit_modal=False):
    habit_names = list(habits.keys())
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
                    "text": 'Delete' if is_edit_modal else ('Start Activity' if habits[habit_name]['habit_status'] == 0 else ('Mark Complete' if habits[habit_name]['habit_status'] == 1 else 'Completed'))
                },
                "value": habit_name + "#*#" + str(habits[habit_name]['habit_status']),
                "action_id": "delete_habit" if is_edit_modal else "activity_button"
            }
        })
        if is_edit_modal or habits[habit_name]['habit_status'] == 0:
            payload[-1]['accessory'].update({"style": "danger" if is_edit_modal else (
                "primary" if habits[habit_name]['habit_status'] == 0 else None)})

    return payload
