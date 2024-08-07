import os
import pandas as pd

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
PASS = os.getenv('MONGO_PASS')


class DataBase(MongoClient):
    def __init__(self):
        CONNECTION_STRING = f"mongodb+srv://bifulcopaolo:{PASS}@mdtest.n6uh2jo.mongodb.net/"
        MongoClient.__init__(self, CONNECTION_STRING)

        client = MongoClient(CONNECTION_STRING)
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


if __name__ == "__main__":

    # Get the database
    test = DataBase()

    test1 = {
        "discord" : "test123",
        "email" : "test@gmail.com",
        "last_login" : "0000",
        "next_login" : "0001",
        "count" : 0
    }