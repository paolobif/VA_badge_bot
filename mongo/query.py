# Get the database using the method we defined in pymongo_test_insert file
from mongo.database import get_database
import pandas as pd
dbname = get_database()



def query_all():
    # Retrieve a collection named "user_1_items" from database
    collection_name = dbname["main_log"]
    item_details = collection_name.find()
    return pd.DataFrame(item_details)

if __name__ == "__main__":
    df = query_all()
    print(df)