from db_utils import read_habit, delete_habit, set_habit_status, read_abs_list
from utils import generate_habit_payload
from home import build_home_tab_payload
import os

def handle_give_feedback_button_click(ack):
    ack()

def handle_activity_button_click(payload, ack, body, client, db, gif_link):
    print(payload['value'])
    user = body['user']['id']
    team = body['team']['domain']
    habit_text, habit_status = payload['value'].split("#*#")
    habit_status = int(habit_status)
    team_ref = db.child(team)
    abs_list = read_abs_list(team_ref, user)
    ack()
    if not abs_list:
        client.chat_postMessage(
            channel = user, text = "You have not selected anybody to track your habits with, please do so on the home page"
            )
        return
    set_habit_status(team_ref, user, habit_text, habit_status)
    build_home_tab_payload(client, db, gif_link, user=user)
    for accountablity_buddy in abs_list:
        if habit_status == 0:
            client.chat_postMessage(
                channel=accountablity_buddy, text=f"<@{user}> has started {habit_text}. Time to get going! 😏")
        elif habit_status == 1:
            client.chat_postMessage(
                channel=accountablity_buddy, text=f"<@{user}> has finished {habit_text}. They might be getting ahead of you... 😨")

def handle_delete_habit_button_click(payload, ack, body, client, db, gif_link):
    ack()
    user = body['user']['id']
    team = body['team']['domain']
    habit_text, _ = payload['value'].split("#*#")
    team_ref = db.child(team)
    user_data = read_habit(team_ref, user)
    delete_habit(team_ref, user, habit_text)
    user_data = read_habit(team_ref, user)

    if 'habits' in user_data.keys():
        my_payload = generate_habit_payload(
            user_data['habits'], is_edit_modal=True)
    else:
        my_payload = {
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": "You have no habits left to delete 😢",
				"emoji": True
			}
		}
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
        token=os.environ['SLACK_TOKEN'],
    )

    # update_home_tab(client=client, user=user)
    # print(scheduled_message_list)
    for message in scheduled_message_list['scheduled_messages']:
        if message['text'] == habit_text:
            client.chat_deleteScheduledMessage(
                token=os.environ['SLACK_TOKEN'],
                channel=user,
                scheduled_message_id=message['id'],
            )
            return
    build_home_tab_payload(client, db, gif_link, user=user)
