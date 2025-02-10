from flask import Flask, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
from ics import Calendar, Event
from datetime import datetime, timedelta

from mongo.database import DataBase

app = Flask(__name__)

# MongoDB setup
db = DataBase()
log = db.log
entrys = db["next_login"]

@app.route('/')
def home():
    return 'Hello, World! This is a test route. Adding some stuff.'

@app.route('/download_calendar/<discord_id>')
def download_calendar(discord_id):
    # Create a new calendar
    cal = Calendar()
    
    # Fetch user-specific events from MongoDB
    try:
        events = log.find({'discord_id': discord_id})
    except:
        return "Invalid user ID", 400

    for event_data in events:
        # calc 30 days later
        thirty_days_later = datetime.fromisoformat(event_data['last_login']) + timedelta(days=90)

        event = Event()
        event.name = "30 Day VA Badge Login"
        event.begin = thirty_days_later.isoformat()
        event.duration = timedelta(minutes=15)
        event.description = "Go to the VA to login"
        event.location = "Portland VA"
        cal.events.add(event)

        # Calculate date for 90 days later
        ninety_days_later = datetime.fromisoformat(event_data['last_login']) + timedelta(days=90)

        # Second event
        second_event = Event()
        second_event.name = "Final 90-Day Follow-Up VA Badge Login"
        second_event.begin = ninety_days_later.isoformat()
        second_event.duration = timedelta(minutes=15)
        second_event.description = "If you miss this... goodbye VA access"
        second_event.location = "Portland VA"
        cal.events.add(second_event)

    # Convert calendar to string
    calendar_string = str(cal)
    print(calendar_string)

    # Return the calendar file
    response = Response(calendar_string, mimetype="text/calendar")
    response.headers["Content-Disposition"] = f"attachment; filename=calendar_{discord_id}.ics"
    return response

def run_flask():
    app.run(host='0.0.0.0', port=8000, threaded=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
    print("Flask is running")