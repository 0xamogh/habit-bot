from dotenv import load_dotenv
from pathlib import Path
import os
from slack_bolt import App
import firebase_admin
from firebase_admin import credentials, firestore, db
from db_utils import create_habit, read_habit, delete_habit, check_if_team_exists, set_habit_status, read_abs_list, update_abs_list
from utils import get_team_info, get_user_timezone, generate_habit_payload
from modals import open_create_habit_modal, submit_create_habit_modal, build_delete_habit_payload
from buttons import handle_delete_habit_button_click, handle_activity_button_click, handle_give_feedback_button_click
from home import build_home_tab_payload
from datetime import datetime, timedelta
import json
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
gif_link = " "

# Listen for a shortcut invocation
@app.shortcut("create_habit")
def open_modal(ack, body, client):
    open_create_habit_modal(ack, body, client, db)

@app.view("view_1")
def submit_modal(ack, body, client, view):
    submit_create_habit_modal(ack, body, client, view, db)


@app.event("app_home_opened")
def open_home_tab(client, event = None, logger = None, user = None):
    build_home_tab_payload(client, db, gif_link, event, logger=None, user=None)

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
@app.action("give_feedback")
def feedback_button_click(ack):
# Start your app
    handle_give_feedback_button_click(ack)
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
