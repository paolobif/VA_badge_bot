import os
import pandas as pd
import random
import re
from datetime import datetime, timedelta

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
PASS = os.getenv('MONGO_PASS')


class DataBase(MongoClient):
    def __init__(self, passkey=PASS):
        CONNECTION_STRING = f"mongodb+srv://bifulcopaolo:{passkey}@mdtest.n6uh2jo.mongodb.net/"
        MongoClient.__init__(self, CONNECTION_STRING)

        client = MongoClient(CONNECTION_STRING, tlsAllowInvalidCertificates=True)
        self.db = client["va_badge_log"]
        self.log = self.db["main_log"]

    def querry_all(self):
        db_items = pd.DataFrame(self.log.find())
        return db_items

    def insert(self, item):
        """
        Insert a new item into the database after validating it.
        Before inserting, ensure there is no existing entry with the same Discord ID.
        """
        if not self.check_insert(item):
            raise ValueError("Item validation failed. Please check the provided data.")

        # Insert the item if no duplicate is found
        self.log.insert_one(item)
        print("Item inserted successfully!")
        return True

    def get_user(self, discord_id):
        """
        Retrieve a user's information from the database using their Discord ID.
        """
        result = self.log.find_one({"discord_id": discord_id})
        return result

    def update_last_login(self, discord_id, new_datetime=None):
        """
        Updates the last_login field for a user identified by their Discord ID.
        - `discord_id`: The Discord ID of the user.
        - `new_datetime`: The new last_login datetime. If None, the current datetime will be used.
        """
        if not new_datetime:
            new_datetime = datetime.now().isoformat()

        result = self.log.update_one(
            {"discord": discord_id},
            {"$set": {"last_login": new_datetime}}
        )

        if result.matched_count > 0:
            print(f"Successfully updated last_login for Discord ID: {discord_id}.")
            return True
        else:
            print(f"No user found with Discord ID: {discord_id}.")
            return False

    def get_highest_id(self):
        result = self.log.find().sort('_id', -1).limit(1)
        for doc in result:
            if '_id' in doc:
                id_max = doc['_id']  # This prints only the integer ID
                return id_max
            else:
                print("No ID found in the document")
                return None

    def check_discord(self, discord_id):
        # Check if the discord ID already exists
        existing_entry = self.log.find_one({"discord": discord_id})
        return existing_entry is not None

    def delete_from_discord_id(self, discord_id):
        # delete the user from discord id
        result = self.log.delete_one({"discord_id": discord_id})
        if result.deleted_count > 0:
            print(f"Successfully deleted user with Discord ID: {discord_id}.")
            return True
        else:
            print(f"No user found with Discord ID: {discord_id}.")
            return False

    @staticmethod
    def check_insert(item):
        """
        Validates the data to ensure it is formatted correctly.
        Specifically:
        - Ensures the 'last_login' field is in ISO 8601 datetime format (e.g., 2025-02-01T12:00:00).
        - Ensures the 'next_login' field is in ISO 8601 datetime format.
        - Ensures the 'email' field is a valid email address.
        - Ensures the 'discord' field is present and non-empty.
        - Ensures the 'count' field is a non-negative integer.
        """
        required_fields = ["discord", "email", "last_login", "next_login", "count"]

        # Check for missing fields
        for field in required_fields:
            if field not in item:
                print(f"Missing required field: {field}")
                return False

        # Validate 'discord'
        if not isinstance(item["discord"], str) or not item["discord"].strip():
            print(f"Invalid 'discord' field: {item['discord']}. Must be a non-empty string.")
            return False

        # Validate 'discord_id'
        if not isinstance(item["discord_id"], int) or not item["discord_id"]:
            print(f"Invalid 'discord_id' field: {item['discord_id']}. Must be a non-empty int.")
            return False

        # Validate 'email'
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, item["email"]):
            print(f"Invalid email format: {item['email']}.")
            return False

        # Validate 'last_login'
        try:
            datetime.fromisoformat(item["last_login"])
        except ValueError:
            print(f"Invalid datetime format for 'last_login': {item['last_login']}. Expected ISO 8601 format.")
            return False

        # Validate 'next_login'
        try:
            datetime.fromisoformat(item["next_login"])
        except ValueError:
            print(f"Invalid datetime format for 'next_login': {item['next_login']}. Expected ISO 8601 format.")
            return False

        # Validate 'count'
        if not isinstance(item["count"], int) or item["count"] < 0:
            print(f"Invalid 'count' field: {item['count']}. Must be a non-negative integer.")
            return False

        # If all validations pass
        return True

    @staticmethod
    def calc_next_login(last_login):
        """
        Given the last login datetime, calculate the next login datetime.
        The next login is set to 30 days after the last login.
        """
        last_login_datetime = datetime.fromisoformat(last_login)
        next_login_datetime = last_login_datetime + timedelta(days=30)
        return next_login_datetime.isoformat()

if __name__ == "__main__":
    # Get the database
    test = DataBase()

    random_date = datetime.now() + timedelta(days=random.randint(0, 60))
    next_login = random_date + timedelta(days=30)

    # Example valid data
    valid_test1 = {
        "discord": "test123",
        "discord_id": 123456789012345678,  # valid field
        "email": "test@gmail.com",  # Valid email
        "last_login": random_date.isoformat(),  # Valid ISO 8601 format
        "next_login": next_login.isoformat(),
        "count": 0
    }

    # Example invalid data (invalid email)
    invalid_test1 = {
        "discord": "test123",
        "discord_id": "123456789012345678",  # Invalid field
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

    # Remove the test entries
    test.log.delete_one(valid_test1)