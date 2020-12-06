from dotenv import load_dotenv
from pathlib import Path
import os
from slack_bolt import App

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)
# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ['SLACK_TOKEN'],
    signing_secret=os.environ['SIGNING_SECRET']
)
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
                            "text": "Select users"
      }
    }
                },
            ]
        }
    )
# Handle a view_submission event
@app.view("view_1")
def handle_submission(ack, body, client, view):
    # Assume there's an input block with `block_c` as the block_id and `dreamy_input`
    habit_text = view["state"]["values"]["habit_block"]["habit_text"]['value']
    reminder_time = view["state"]["values"]["timepicker_block"]["reminder_time"]['selected_time']
    accountablity_buddies = view["state"]["values"]["abs_block"]["accountablity_buddies"]['selected_users']
    user = body["user"]["id"]
    # Validate the inputs
    errors = {}
    print(habit_text, type(habit_text))
    print(reminder_time, type(reminder_time))
    print(accountablity_buddies, type(accountablity_buddies))

    if habit_text is not None and len(habit_text) <= 4:
        errors["habit_block"] = "The value must be longer than 4 characters"
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return
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
    try:
        # Call views.publish with the built-in client
        client.views_publish(
            # Use the user ID associated with the event
            user_id=event["user"],
            # Home tabs must be enabled in your app configuration
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome home, <@" + event["user"] + "> :house:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                          "type": "mrkdwn",
                          "text": "Learn how home tabs can be more useful and interactive <https://api.slack.com/surfaces/tabs/using|*in the documentation*>."
                        }
                    }
                ]
            }
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

@app.action('button_click')
def action_button_click(body, ack, say):
    ack()
    say(f"Wow <@{body['user']['id']}> didn't know you were a button clicker!!")
# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
