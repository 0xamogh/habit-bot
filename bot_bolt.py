import logging

from sqlalchemy.sql.expression import text
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
import os
from slack_bolt import App
import firebase_admin
from firebase_admin import credentials, db
from db_utils import read_habit, update_abs_list, refresh_habit_status
from utils import schedule_message
from modals import open_create_habit_modal, submit_create_habit_modal, build_delete_habit_payload
from buttons import handle_delete_habit_button_click, handle_activity_button_click, handle_give_feedback_button_click
from home import build_home_tab_payload
from datetime import datetime, timedelta

from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore
import sqlalchemy
from sqlalchemy.engine import Engine

# env_path = Path('.')/'.env'
# load_dotenv(dotenv_path!!!=env_path)
database_url = 'postgres://rwdqobjuvhvgps:c818d30650552bf80bbf2b8f11094ed719dbe2ffbe508111371fa434818c765d@ec2-34-248-148-63.eu-west-1.compute.amazonaws.com:5432/d6kfah11h5ihe9'
engine: Engine = sqlalchemy.create_engine(database_url)

logger = logging.getLogger(__name__)
installation_store = SQLAlchemyInstallationStore(
    client_id=os.environ["SLACK_CLIENT_ID"],
    engine=engine,
    logger=logger,
)

oauth_state_store = SQLAlchemyOAuthStateStore(
    expiration_seconds=120,
    engine=engine,
    logger=logger,
)

oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=["channels:read", "groups:read", "chat:write", "app_mentions:read", "channels:history", "chat:write", "chat:write.customize", "commands", "im:history", "im:read", "im:write", "reminders:read", "reminders:write", "team:read", "users.profile:read", "users:read"],
    installation_store=installation_store,
    state_store=oauth_state_store
)
try:
    engine.execute("select count(*) from slack_bots")
except Exception as e:
    installation_store.metadata.create_all(engine)
    oauth_state_store.metadata.create_all(engine)
    
app = App(
    signing_secret=os.environ["SIGNING_SECRET"],
    oauth_settings=oauth_settings
)

# Initializes your app with your bot token and signing secret
# app = App(
#     token=os.environ['BOT_USER_TOKEN'],
#     signing_secret=os.environ['SIGNING_SECRET']
# )
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
gif_link = " "

# bot_id = app.client.auth_test(
#     token=os.environ[]
# )['user_id']
# print("bot_id", bot_id)

@app.message("complete")
def reply(client, message):
    print("message", message)
    text = message['text']
    if "Reminder to complete your activity" in text and message['channel_type'] == "im":
        timestamp = datetime.fromtimestamp(float(message['ts']))
        channel = message['channel']
        schedule_message(client, channel, timestamp + timedelta(days=1), text, auto=True)


@app.message("['hi','hey','hello,'heylo']")
def reply_greeting(message, say):
    user = message['user']
    print(message)
    # say("Hey there! Ready for some good habits 🥰")
@app.shortcut("create_habit")
def open_modal(ack, body, client):
    open_create_habit_modal(ack, body, client, db)


@app.shortcut("help_requested")
def request_help(ack, body, client):
    ack()
    print("body:", body)
    client.chat_postMessage(
        channel=body['user']['id'],
        text="*Things you can do with Inhabit Bot 🎉🍾🎊*\n *Create a new habit*\n Use the shortcut /create a habit or head on over to Home to create a new habit\n Add your habit, set a daily reminder and choose your accountability buddies\n*Update Habit status*\n In Home, you can mark the status of your habits as Doing and Done, this will alert your accountability buddies regarding your updates\n*Delete a habit*\n In Home, you can click the \"Delete Habits\" to show a modal to delete your habits"
    )


@app.action("create_habit")
def open_modal_action(ack, body, client):
    open_create_habit_modal(ack, body, client, db)

@app.view("create_habit")
def open_modal_view(ack, body, client):
    open_create_habit_modal(ack, body, client, db)

@app.view("view_1")
def submit_modal(ack, body, client, view):
    submit_create_habit_modal(ack, body, client, view, db)

@app.event("app_home_opened")
def open_home_tab(client, event = None, logger = None, user = None):
    print("opening home ....")
    build_home_tab_payload(client, db, gif_link, event, logger=None, user=None)
    check_stat = read_habit(db, event['user'])
    print("check_stat", check_stat)
    if check_stat['user_not_found']:
        client.chat_postMessage(
            channel = event['user'],
            text = "Welcome to Inhabit! To start create a new habit and choose your accountablity buddy on the Home Page"
        );

@app.action("open_delete_habits")
def open_delete_habit_modal(ack, body, client):
    build_delete_habit_payload(ack, body, client, db)

@app.action("home_user_select")
def home_user_selected(ack, payload, client, body):
    ack()
    team_ref = db.child(body['team']['domain'])
    update_abs_list(team_ref, body['user']['id'], payload['selected_users'])


@app.action('activity_button')
def activity_button_click(payload, ack, body, client):
    handle_activity_button_click(payload, ack, body, client, db, gif_link)

@app.action("delete_habit")
def delete_button_click(payload, ack, body, client):
    handle_delete_habit_button_click(payload, ack, body, client, db, gif_link)
    build_home_tab_payload(client, db, user = body['user']['id'])
    
@app.action("give_feedback")
def feedback_button_click(ack):
# Start your app
    handle_give_feedback_button_click(ack)

def refresh_habit_schedule():
    print(app, app.client)
    refresh_habit_status(app.client, db)

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
