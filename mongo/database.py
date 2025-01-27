import os
import pandas as pd
import random
from datetime import datetime, timedelta

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
PASS = os.getenv('MONGO_PASS')


class DataBase(MongoClient):
    def __init__(self):
        CONNECTION_STRING = f"mongodb+srv://bifulcopaolo:{PASS}@mdtest.n6uh2jo.mongodb.net/"
        MongoClient.__init__(self, CONNECTION_STRING)

        client = MongoClient(CONNECTION_STRING, tlsAllowInvalidCertificates=True)
        self.db = client["va_badge_log"]
        self.log = self.db["main_log"]

    def querry_all(self):
        db_items = pd.DataFrame(self.log.find())
        return db_items

    def insert(self, item):
        self.log.insert_one(item)

    def get_highest_id(self):
        result = self.log.find().sort('_id', -1).limit(1)
        for doc in result:
            if '_id' in doc:
                id_max = doc['_id']  # This prints only the integer ID
                return id_max
            else:
                print("No ID found in the document")
                return None

    @staticmethod
    def check_insert(item):
        """
        Validates the data to ensure it is formatted correctly.
        Specifically:
        - Ensures the 'last_login' field (if present) is in ISO 8601 datetime format (e.g., 2025-02-01T12:00:00).
        - Ensures the 'email' field is a valid email address.
        """
        # Validate 'last_login'
        if "last_login" in item:
            try:
                datetime.fromisoformat(item["last_login"])
            except ValueError:
                print(f"Invalid datetime format for 'last_login': {item['last_login']}. Expected ISO 8601 format.")
                return False
        else:
            print("No 'last_login' field found in the item.")
            return False

        # Validate 'email'
        if "email" in item:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, item["email"]):
                print(f"Invalid email format: {item['email']}.")
                return False
        else:
            print("No 'email' field found in the item.")
            return False

        # If all validations pass
        return True


if __name__ == "__main__":
    # Get the database
    test = DataBase()

    random_date = datetime.now() + timedelta(days=random.randint(0, 60))
    next_login = random_date + timedelta(days=30)

    # Example valid data
    valid_test1 = {
        "discord": "test123",
        "email": "test@gmail.com",  # Valid email
        "last_login": random_date,  # Valid ISO 8601 format
        "next_login": next_login,
        "count": 0
    }

    # Example invalid data (invalid email)
    invalid_test1 = {
        "discord": "test123",
        "email": "not-an-email",  # Invalid email
        "last_login": "2025-01-01T10:00:00",  # Valid format
        "next_login": "2025-02-01T12:00:00",
        "count": 0
    }

    # Test valid insertion
    try:
        test.insert(valid_test1)
        print("Valid data inserted successfully!")
    except ValueError as e:
        print(e)

    # Test invalid insertion
    try:
        test.insert(invalid_test1)
        print("Invalid data inserted successfully!")
    except ValueError as e:
        print(e)