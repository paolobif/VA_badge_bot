from flask import Flask, Response, request
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

@app.route('/download_calendar/<user_id>')
def download_calendar(user_id):
    # Create a new calendar
    cal = Calendar()

    # Fetch user-specific events from MongoDB
    try:
        user_object_id = ObjectId(user_id)  # Convert to ObjectId
    except:
        return "Invalid user ID", 400

    events = log.find({'_id': user_object_id})

    for event_data in events:
        event = Event()
        event.name = "VA Badge Login"
        event.begin = event_data['next_login']
        event.duration = timedelta(minutes=15)
        event.description = "Go to the VA to login"
        event.location = "Portland VA"
        cal.events.add(event)

    # Convert calendar to string
    calendar_string = str(cal)
    print(calendar_string)

    # Return the calendar file
    response = Response(calendar_string, mimetype="text/calendar")
    response.headers["Content-Disposition"] = f"attachment; filename=calendar_{user_id}.ics"
    return response

def run_flask():
    app.run(debug=True, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    run_flask()
    print("Flask is running")