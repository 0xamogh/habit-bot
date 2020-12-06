import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, Response, request
from slackeventsapi import SlackEventAdapter
from slack_bolt import App

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

BOT_ID = client.api_call('auth.test')['user_id']
welcome_messages = {}

class WelcomeMessage:
    START_TEXT ={
        'type': 'section',
        'text':{
            'type' : 'mrkdwn',
            'text' : (
                'Hi I am HabitBot \n\n'
                '*Get started by completing tasks*'
            )
        }
    }
    DIVIDER = {'type':'divider'}
    
    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False 
    
    def get_message(self):
        return {
            'ts' : self.timestamp,
            'channel' : self.channel,
            'username' : 'Welcome HabitBot!',
            'icon_emoji' : self.icon_emoji,
            'blocks' : [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]



        }

    def _get_reaction_task(self):
        checkmark = ':heavy_check_mark:'

        if not self.completed:
            checkmark = ':white_large_square:'
        
        text = f'{checkmark} *React to this message!*'

        return {'type':'section', 'text':{'type':'mrkdwn', 'text':text}}
def send_welcome_message(channel, user):
    if channel not in welcome_messages:
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]:
        return
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']
    welcome_messages[channel][user] = welcome
    print("welcome_messages",welcome_messages)


@slack_event_adapter.on('reaction_added')
def reaction(payload):
    print("reaction", payload)
    event = payload.get('event',{})
    channel_id = event.get('item',{}).get('channel')
    user_id = event.get('user', 0)

    if f'@{user_id}' not in welcome_messages:
        return
    
    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']  
    
@app.message("knock knock")
def ask_who(message, say):
    say("_Who's there?_")



@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    print("text",text)
    if user_id != None and BOT_ID != user_id:
        # client.chat_postMessage(channel=channel_id, text="I am not dumb!!")
        if text.lower() == "hello":
            send_welcome_message(channel_id, user_id)
        else:
            ts = event.get('ts')
            client.chat_postMessage(channel=BOT_ID,thread_ts=ts,text="You bet 😌")
@app.route('/habit', methods=['POST'])
def register_habit():
    data = request.form
    print(data)
    user_id = data.get('user_id')
    text = data.get('text')
    channel_id = data.get('channel_id')
    client.chat_postMessage(channel=channel_id, text="Ok, registered habit, " +text)
    return Response(),200

if __name__ == '__main__':
    app.run(debug=True)
