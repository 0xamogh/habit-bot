from utils import get_team_info
from db_utils import check_if_team_exists, read_abs_list, read_habit
from utils import generate_habit_payload
import requests
import random
import json
import os


def build_home_tab_payload(client, db, gif_link=None, event=None, logger=None, user=None):
    r = requests.get(
        "https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s" % ("motivation", os.environ['TENOR_TOKEN'], 13))
    my_json = json.loads(r.content)
    randomizer = random.randint(0, 10)
    gif_link = my_json['results'][randomizer]['media'][0]['gif']['url']
    team_info = get_team_info(client)
    team = team_info['team']['domain']
    check_if_team_exists(db, team)
    team_ref = db.child(team)
    user_id = user if user else event['user']
    abs_list = read_abs_list(team_ref, user_id)

    user_data = read_habit(team_ref, user_id)

    my_payload = []
    placeholder = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "You have no active habits 😢 \n Remember! Start small and *dream big*! Start your new habit now! 🚀 "},
        "accessory": {
            "action_id": "create_habit",
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Create Habit"
            }
        }
    }
    if user_data and 'habits' in user_data.keys():
        my_payload = generate_habit_payload(user_data['habits'])
    else:
        my_payload.append(placeholder)
    try:
        # Call views.publish with the built-in client

        client.views_publish(
            # Use the user ID associated with the event
            user_id=user_id,
            # Home tabs must be enabled in your app configuration
            view={
                "type": "home",

                "blocks": [
                        {
                            "type": "section",
                            "text": {
				"type": "mrkdwn",
				"text": "*Lets start a new habit!*"
                            },
                            "accessory": {
				"action_id": "create_habit",
                                "type": "button",
				"text": {
                                    "type": "plain_text",
                                    "text": "New Habit"
                                }
                            }
                        },


                    {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                        				"text": "Your Tasks 🎯",
                                "emoji": True
                            }
                    },
                    *my_payload,
                    {
                            "type": "divider"
                    },
                    {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                        				"text": "Your Accountability Buddies :dancers:",
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
                                "initial_users": abs_list
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
                                    "url": "https://s.surveyplanet.com/zjLl_ruv9",
                                    "action_id": "give_feedback"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                      						"text": "Share Streak",
                                        "emoji": True
                                    },
                                    "value" : "share_streak",
                                    "action_id": "share_streak"
                                }
                            ]
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
                    }
                ]
            })
        # print("Try catch running")
    except Exception as e:
        print("Oh no exception", e)
        if logger:
            logger.error(f"Error publishing home tab: {e}")
